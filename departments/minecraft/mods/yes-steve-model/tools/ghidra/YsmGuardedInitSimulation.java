// Explicitly approved bounded DT_INIT simulation. Never connects host/native/syscall models.
// Self-tests use only assistant-authored toy bytes, not the target image.
import ghidra.app.script.GhidraScript;
import ghidra.pcode.emu.*;
import ghidra.pcode.exec.*;
import ghidra.pcode.exec.PcodeArithmetic.Purpose;
import ghidra.pcode.exec.PcodeExecutorStatePiece.Reason;
import ghidra.program.model.address.*;
import ghidra.program.model.lang.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.pcode.*;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.*;

public class YsmGuardedInitSimulation extends GhidraScript {
 static final long STACK_LOW=0x700000000000L, STACK_HIGH=STACK_LOW+0x10000L, SP=STACK_LOW+0x8008L;
 static final long TOY=0x100000L;
 static final String IMAGE_SHA="15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22";
 // Single-thread, no asynchronous observers: these markers have no memory side effects.
 // Guard validates their identity, shape and pairing. All other userops remain blocked.
 public static class AtomicMarkers extends AnnotatedPcodeUseropLibrary<byte[]> {
  @PcodeUserop public void LOCK() {}
  @PcodeUserop public void UNLOCK() {}
 }
 static class ModeledStep extends RuntimeException {}
 static class Halt extends RuntimeException { Halt(String s){super(s);} }
 class Guard implements PcodeEmulationCallbacks<byte[]> {
  final AddressSet code; final PrintWriter out; final int limit; final long opLimit;
  boolean opaqueCopy=false; int modeledCopies=0,opaqueCopies=0; final Map<Long,Long> opaque=new HashMap<>();
  boolean inspecting=false,inspectMissing=false; boolean active=false,locked=false; String mnemonic=""; int atomicPairs=0; int attempted=0,completed=0;long ops=0,deadline,pc=0,stopAddress=-1,timeBudgetNanos=60_000_000_000L;int stopSize=0;String stop=null,via=null;
  Guard(AddressSet c,PrintWriter o,int n,long opN){code=c;out=o;limit=n;opLimit=opN;}
  void halt(String why,String route,long addr,int size){if(stop==null){stop=why;via=route;stopAddress=addr;stopSize=size;out.println("STOP\t"+why+"\t"+route+"\tpc="+Long.toHexString(pc)+"\taddress="+Long.toHexString(addr)+"\tsize="+size);}throw new Halt(why);}
  void oracle(PcodeThread<byte[]> t,String name,long expected){
   Register r=currentProgram.getRegister(name);if(r==null)halt("MISSING_ORACLE_REGISTER",name,pc,0);
   long actual=t.getState().inspectRegisterValue(r).getUnsignedValue().longValue();
   out.println("ORACLE\t"+Long.toHexString(pc)+"\t"+name+"\tactual="+Long.toHexString(actual)+"\texpected="+Long.toHexString(expected));
   if(actual!=expected)halt("ORACLE_DISAGREEMENT",name,pc,0);
  }
  void checkOracle(PcodeThread<byte[]> t){
   if(pc==0x174d06fL){oracle(t,"ZF",0);oracle(t,"RSP",SP-128);}
   if(pc==0x16668ffL){oracle(t,"CF",0);oracle(t,"RCX",1);oracle(t,"R11D",0xd99b4c01L);}
   if(pc==0x16b05feL)oracle(t,"CF",0);
   if(pc==0x171695bL)oracle(t,"RSI",0x1499584L);
   if(pc==0x14995c7L){oracle(t,"CF",1);oracle(t,"SF",0);}
   if(pc==0x1603de3L)oracle(t,"SF",0);
   if(pc==0x1444517L){oracle(t,"CF",0);oracle(t,"ZF",0);}
  }
  boolean stack(long a,int n){return n>0&&a>=STACK_LOW&&a<STACK_HIGH&&n<=STACK_HIGH-a;}
  long reg(PcodeThread<byte[]> t,String n){return t.getState().inspectRegisterValue(currentProgram.getRegister(n)).getUnsignedValue().longValue();}
  void reg(PcodeThread<byte[]> t,String n,long v){t.getState().setRegisterValue(new RegisterValue(currentProgram.getRegister(n),new BigInteger(Long.toUnsignedString(v))));}
  void opaqueReadGuard(AddressSpace space,long a,int n){if(active&&space.isMemorySpace())for(int k=0;k<n;k++)if(opaque.containsKey(a+k))halt("OPAQUE_VALUE_READ","opaque:"+Long.toHexString(opaque.get(a+k)),a+k,1);}
  void clearOpaque(AddressSpace space,long a,int n){if(space.isMemorySpace())for(int k=0;k<n;k++)opaque.remove(a+k);}
  byte[] peek(PcodeThread<byte[]> t,long a){
   if(opaque.containsKey(a))return null;inspecting=true;inspectMissing=false;
   try{return t.getState().getVar(toAddr(a),1,false,Reason.INSPECT);}
   catch(RuntimeException e){if(inspectMissing)return null;throw e;}
   finally{inspecting=false;}
  }
  // Exact F3 A4 semantics, one byte per instruction step; unknown bytes stay out of concrete state.
  void modelCopy(PcodeThread<byte[]> t){
   checkTime();if(ops>=opLimit)halt("PCODE_BUDGET","before_opaque_model",pc,0);
   long count=reg(t,"RCX");if(count==0){t.overrideCounter(toAddr(pc+2));completed++;modeledCopies++;throw new ModeledStep();}
   long src=reg(t,"RSI"),dst=reg(t,"RDI"),df=reg(t,"DF");
   if(df!=0&&df!=1)halt("INVALID_DIRECTION_FLAG","opaque_copy",pc,0);
   if(!stack(src,1))halt("OPAQUE_COPY_SOURCE_OUTSIDE_STACK","opaque_copy",src,1);
   writeGuard(toAddr(dst).getAddressSpace(),dst,1,"opaque_copy");
   byte[] value=peek(t,src);
   if(value==null){opaque.put(dst,opaque.getOrDefault(src,src));opaqueCopies++;out.println("OPAQUE_COPY\t"+Long.toHexString(src)+"\t"+Long.toHexString(dst)+"\torigin="+Long.toHexString(opaque.get(dst)));}
   else {t.getState().setVar(toAddr(dst),1,false,value);opaque.remove(dst);}
   reg(t,"RCX",count-1);reg(t,"RSI",src+(df==0?1:-1));reg(t,"RDI",dst+(df==0?1:-1));
   t.overrideCounter(toAddr(pc));completed++;modeledCopies++;throw new ModeledStep();
  }
  void checkTime(){if(System.nanoTime()>deadline)halt("TIME_BUDGET","clock",pc,0);}
  void writeGuard(AddressSpace space,long addr,int n,String route){if(active&&space.isMemorySpace()&&!stack(addr,n))halt("NON_STACK_WRITE",route,addr,n);}
  void targetGuard(Address target,String route){if(target.getOffset()<0x1000||!code.contains(target))halt("EXTERNAL_OR_NULL_TARGET",route,target.getOffset(),0);}
  public void beforeDecodeInstruction(PcodeThread<byte[]> t,Address a,RegisterValue ctx){if(active){pc=a.getOffset();checkTime();targetGuard(a,"decode");}}
  public void beforeExecuteInstruction(PcodeThread<byte[]> t,Instruction i,PcodeProgram p){
   if(!active)return;pc=i.getAddress().getOffset();checkTime();
   if(attempted>=limit)halt("INSTRUCTION_BUDGET","instruction",pc,0);
   String m=i.getMnemonicString().toUpperCase(Locale.ROOT);mnemonic=m;
   if(Set.of("SYSCALL","SYSENTER","INT","INT3","HLT","SYSRET","IRET","IRETQ").contains(m))halt("OS_OR_PRIVILEGED_INSTRUCTION","instruction",pc,0);
   if(i.toString().contains("FS:")||i.toString().contains("GS:"))halt("SEGMENTED_CONTEXT_UNSUPPORTED","instruction",pc,0);
   if(!code.contains(i.getMinAddress(),i.getMaxAddress()))halt("OUTSIDE_CODE_RANGE","instruction",pc,i.getLength());
   checkOracle(t);attempted++;try {out.println("INS\t"+Long.toHexString(pc)+"\t"+HexFormat.of().formatHex(i.getBytes())+"\t"+i.toString());} catch(MemoryAccessException e){halt("DECODE_BYTES_UNAVAILABLE","instruction",pc,i.getLength());}
   if(opaqueCopy){try{if(Arrays.equals(i.getBytes(),hex("f3a4"))){if(!m.startsWith("MOVSB"))halt("COPY_DECODE_MISMATCH","opaque_copy",pc,0);modelCopy(t);}}catch(MemoryAccessException e){halt("DECODE_BYTES_UNAVAILABLE","opaque_copy",pc,i.getLength());}}
  }
  public void afterExecuteInstruction(PcodeThread<byte[]> t,Instruction i){if(active){if(locked)halt("UNPAIRED_ATOMIC_MARKER","instruction",pc,0);completed++;}}
  public void beforeStepOp(PcodeThread<byte[]> t,PcodeOp op,PcodeFrame frame){
   if(!active)return;checkTime();if(ops>=opLimit)halt("PCODE_BUDGET","pcode",pc,0);ops++;
   if(op.getOpcode()==PcodeOp.CALLOTHER){
    int id=(int)op.getInput(0).getOffset();String name=currentProgram.getLanguage().getUserDefinedOpName(id);
    if(!Set.of("LOCK","UNLOCK").contains(name)||!mnemonic.startsWith("XCHG")||op.getNumInputs()!=1||op.getOutput()!=null)halt("USEROP_NOT_ALLOWED", "pcode:"+name,pc,0);
    if(name.equals("LOCK")){if(locked)halt("UNPAIRED_ATOMIC_MARKER","nested",pc,0);locked=true;}
    else {if(!locked)halt("UNPAIRED_ATOMIC_MARKER","unlock",pc,0);locked=false;atomicPairs++;}
   }
   for(Varnode v:op.getInputs())if(v.isAddress())opaqueReadGuard(v.getAddress().getAddressSpace(),v.getOffset(),v.getSize());
   Varnode dest=op.getOutput();if(dest!=null)writeGuard(dest.getAddress().getAddressSpace(),dest.getOffset(),dest.getSize(),"direct_output");
   if(op.getOpcode()==PcodeOp.CALL||op.getOpcode()==PcodeOp.BRANCH){Varnode v=op.getInput(0);if(v.isAddress())targetGuard(v.getAddress(),"direct_transfer");}
   if(op.getOpcode()==PcodeOp.CALLIND||op.getOpcode()==PcodeOp.BRANCHIND||op.getOpcode()==PcodeOp.RETURN){
    byte[] v=t.getState().getVar(op.getInput(0),Reason.INSPECT);long addr=t.getArithmetic().toLong(v,Purpose.BRANCH);targetGuard(toAddr(addr),"computed_transfer");
   }
  }
  public void beforeLoad(PcodeThread<byte[]> t,PcodeOp op,AddressSpace space,byte[] offset,int n){if(active)opaqueReadGuard(space,t.getArithmetic().toLong(offset,Purpose.LOAD),n);}
  public void afterStore(PcodeThread<byte[]> t,PcodeOp op,AddressSpace space,byte[] offset,int n,byte[] value){if(active)clearOpaque(space,t.getArithmetic().toLong(offset,Purpose.STORE),n);}
  public void afterStepOp(PcodeThread<byte[]> t,PcodeOp op,PcodeFrame frame){if(active){Varnode v=op.getOutput();if(v!=null)clearOpaque(v.getAddress().getAddressSpace(),v.getOffset(),v.getSize());}}
  public void beforeStore(PcodeThread<byte[]> t,PcodeOp op,AddressSpace space,byte[] offset,int n,byte[] value){if(active)writeGuard(space,t.getArithmetic().toLong(offset,Purpose.STORE),n,"store");}
  public <A,U> AddressSetView readUninitialized(PcodeThread<byte[]> t,PcodeExecutorStatePiece<A,U> p,AddressSetView set,Reason reason){if(inspecting){inspectMissing=true;throw new Halt("UNKNOWN_INSPECTION");}if(active)halt("UNINITIALIZED_READ","state",set.getMinAddress().getOffset(),(int)Math.min(set.getNumAddresses(),Integer.MAX_VALUE));return set;}
  public <A,U> int readUninitialized(PcodeThread<byte[]> t,PcodeExecutorStatePiece<A,U> p,AddressSpace space,A offset,int n,Reason reason){if(inspecting){inspectMissing=true;throw new Halt("UNKNOWN_INSPECTION");}if(active)halt("UNINITIALIZED_READ","state",p.getAddressArithmetic().toLong(offset,Purpose.LOAD),n);return 0;}
 }
 class Trial {
  PcodeEmulator emu;PcodeThread<byte[]> thread;Guard guard;
  Trial(AddressSet code,PrintWriter out,int n,long opN){guard=new Guard(code,out,n,opN);emu=new PcodeEmulator(currentProgram.getLanguage(),guard){ protected PcodeUseropLibrary<byte[]> createUseropLibrary(){return new AtomicMarkers();} };thread=emu.newThread();}
  void initialize(long start){
   for(Register r:currentProgram.getLanguage().getRegisters())if(r.isBaseRegister()&&!r.isProcessorContext())thread.getState().setRegisterValue(new RegisterValue(r,BigInteger.ZERO));
   EmulatorUtilities.initializeRegisters(thread,currentProgram,toAddr(start));
   thread.getState().setRegisterValue(new RegisterValue(currentProgram.getRegister("RSP"),BigInteger.valueOf(SP)));
   Register iff=currentProgram.getRegister("IF");if(iff!=null)thread.getState().setRegisterValue(new RegisterValue(iff,BigInteger.ONE));
   thread.getState().setVar(toAddr(SP),8,false,thread.getArithmetic().fromConst(0x7fff00000000L,8));
  }
  byte[] inspectMemory(long address,int size){
   for(int k=0;k<size;k++)if(guard.opaque.containsKey(address+k))return null;
   guard.inspecting=true;guard.inspectMissing=false;
   try{return thread.getState().getVar(toAddr(address),size,false,Reason.INSPECT);}
   catch(RuntimeException e){if(guard.inspectMissing)return null;throw e;}
   finally{guard.inspecting=false;}
  }
  void run(){
   guard.active=true;guard.deadline=System.nanoTime()+guard.timeBudgetNanos;
   try{while(true){monitor.checkCancelled();try{thread.stepInstruction();}catch(ModeledStep e){/* Exact copy semantics completed; no engine frame was entered. */}}}
   catch(Throwable e){if(guard.stop==null){guard.stop="UNEXPECTED_ENGINE_ERROR";guard.via=e.getClass().getName();guard.out.println("ENGINE_ERROR\t"+e);}}
   finally{guard.active=false;for(String name:List.of("RAX","RBX","RCX","RDX","RSI","RDI","RBP","RSP","R8","R9","R10","R11","R12","R13","R14","R15","CF","ZF","SF","OF","PF","AF","DF")){Register r=currentProgram.getRegister(name);guard.out.println("STOP_REGISTER\t"+name+"\t"+thread.getState().inspectRegisterValue(r).getUnsignedValue().toString(16));}guard.out.println("COUNTS\tattempted="+guard.attempted+"\tcompleted="+guard.completed+"\tpcode="+guard.ops+"\tatomic_pairs="+guard.atomicPairs+"\tmodeled_copy_steps="+guard.modeledCopies+"\topaque_byte_copies="+guard.opaqueCopies);}
  }
 }
 byte[] hex(String s){return HexFormat.of().parseHex(s);}
 void require(boolean b,String s){if(!b)throw new IllegalStateException(s);}
 Trial toy(PrintWriter out,String name,byte[] bytes,int limit,long opLimit){
  out.println("CASE\t"+name);AddressSet code=new AddressSet(toAddr(TOY),toAddr(TOY+bytes.length-1));Trial t=new Trial(code,out,limit,opLimit);
  byte[] decodeBuffer=Arrays.copyOf(bytes,bytes.length+32);Arrays.fill(decodeBuffer,bytes.length,decodeBuffer.length,(byte)0x90);
  t.emu.getSharedState().setVar(toAddr(TOY),decodeBuffer.length,false,decodeBuffer);
  t.emu.getSharedState().setVar(toAddr(0x2000),8,false,new byte[8]);t.initialize(TOY);return t;
 }
 void selfTest(PrintWriter out){
  int passed=0;
  Trial a=toy(out,"private_stack",hex("48b88877665544332211505b90"),20,1000);a.run();require(a.guard.stop.equals("EXTERNAL_OR_NULL_TARGET"),"stack case stop");require(a.thread.getState().inspectRegisterValue(currentProgram.getRegister("RBX")).getUnsignedValue().longValue()==0x1122334455667788L,"stack value");passed++;
  Trial b=toy(out,"computed_write",hex("48b8887766554433221148bb0020000000000000488903"),20,1000);b.run();require(b.guard.stop.equals("NON_STACK_WRITE")&&b.guard.via.equals("store")&&b.guard.stopAddress==0x2000,"computed guard");require(Arrays.equals(b.emu.getSharedState().getVar(toAddr(0x2000),8,false,Reason.INSPECT),new byte[8]),"computed write applied");passed++;
  Trial c=toy(out,"direct_write",hex("48b88877665544332211488905ef1ff0ff"),20,1000);c.run();require(c.guard.stop.equals("NON_STACK_WRITE")&&c.guard.via.equals("direct_output")&&c.guard.stopAddress==0x2000,"direct guard");require(Arrays.equals(c.emu.getSharedState().getVar(toAddr(0x2000),8,false,Reason.INSPECT),new byte[8]),"direct write applied");passed++;
  Trial d=toy(out,"unknown_stack_read",hex("488b442420"),20,1000);d.run();require(d.guard.stop.equals("UNINITIALIZED_READ"),"unknown read was defaulted");passed++;
  Trial e=toy(out,"syscall",hex("0f05"),20,1000);e.run();require(e.guard.stop.equals("OS_OR_PRIVILEGED_INSTRUCTION")&&e.guard.completed==0,"syscall guard");passed++;
  Trial f=toy(out,"userop",hex("0fa2"),20,1000);f.run();require(f.guard.stop.equals("USEROP_NOT_ALLOWED"),"userop guard");passed++;
  Trial g=toy(out,"instruction_limit",hex("ebfe"),3,1000);g.run();require(g.guard.stop.equals("INSTRUCTION_BUDGET")&&g.guard.completed==3,"instruction bound");passed++;
  Trial h=toy(out,"pcode_limit",hex("48b80100000000000000"),20,0);h.run();require(h.guard.stop.equals("PCODE_BUDGET")&&h.guard.completed==0,"pcode bound");passed++;
  Trial j=toy(out,"external_direct_call",hex("e8fbefffff"),20,1000);j.run();require(j.guard.stop.equals("EXTERNAL_OR_NULL_TARGET"),"external direct call");passed++;
  Trial k=toy(out,"external_computed_call",hex("48b8efbeadde00000000ffd0"),20,1000);k.run();require(k.guard.stop.equals("EXTERNAL_OR_NULL_TARGET"),"external computed call");passed++;
  Trial l=toy(out,"stack_boundary",hex("48b8010000000000000048bb"+HexFormat.of().formatHex(ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN).putLong(STACK_HIGH-4).array())+"488903"),20,1000);l.run();require(l.guard.stop.equals("NON_STACK_WRITE")&&l.guard.stopAddress==STACK_HIGH-4,"stack boundary guard");passed++;
  Trial q=toy(out,"time_limit",hex("90"),20,1000);q.guard.timeBudgetNanos=0;q.run();require(q.guard.stop.equals("TIME_BUDGET")&&q.guard.completed==0,"time guard");passed++;
  Trial atomic=toy(out,"stack_atomic_exchange",hex("6a1148c7c32200000048871c2458"),20,1000);atomic.run();require(atomic.guard.stop.equals("EXTERNAL_OR_NULL_TARGET")&&atomic.guard.atomicPairs==1,"atomic pairing");require(atomic.thread.getState().inspectRegisterValue(currentProgram.getRegister("RBX")).getUnsignedValue().longValue()==0x11&&atomic.thread.getState().inspectRegisterValue(currentProgram.getRegister("RAX")).getUnsignedValue().longValue()==0x22,"atomic exchange values");passed++;
  Trial atomicBad=toy(out,"nonstack_atomic_exchange",hex("48c7c300200000488703"),20,1000);atomicBad.run();require(atomicBad.guard.stop.equals("NON_STACK_WRITE"),"atomic write guard");require(Arrays.equals(atomicBad.emu.getSharedState().getVar(toAddr(0x2000),8,false,Reason.INSPECT),new byte[8]),"atomic nonstack applied");passed++;
  String stopBefore=a.guard.stop;byte[] known=a.inspectMemory(SP-8,8);require(known!=null&&HexFormat.of().formatHex(known).equals("8877665544332211"),"known inspection");passed++;
  require(a.inspectMemory(SP+32,1)==null&&a.guard.stop.equals(stopBefore),"unknown inspection preserves stop");passed++;
  out.println("SELF_TEST_PASS\t"+passed+"\tysm_target_simulated=false");println("GUARDED_SIMULATION_SELF_TEST_PASS "+passed);
 }
 void configureCopy(Trial t,long src,long dst,long count,int df){t.guard.opaqueCopy=true;t.guard.reg(t.thread,"RSI",src);t.guard.reg(t.thread,"RDI",dst);t.guard.reg(t.thread,"RCX",count);t.guard.reg(t.thread,"DF",df);t.guard.reg(t.thread,"RDX",dst);}
 void put(Trial t,long a,int... bytes){byte[] v=new byte[bytes.length];for(int i=0;i<v.length;i++)v[i]=(byte)bytes[i];t.thread.getState().setVar(toAddr(a),v.length,false,v);}
 void opaqueTests(PrintWriter out){
  int passed=0;long src=SP+32,dst=SP-64;
  Trial a=toy(out,"opaque_copy_then_read",hex("f3a48a02"),20,1000);configureCopy(a,src,dst,1,0);a.run();require(a.guard.stop.equals("OPAQUE_VALUE_READ")&&a.guard.opaque.get(dst)==src,"opaque consumer guard");passed++;
  Trial b=toy(out,"opaque_overwrites_stale_known",hex("f3a48a02"),20,1000);configureCopy(b,src,dst,1,0);put(b,dst,99);b.run();require(b.guard.stop.equals("OPAQUE_VALUE_READ")&&b.inspectMemory(dst,1)==null,"stale byte leaked");passed++;
  Trial c=toy(out,"known_copy",hex("f3a48a02"),20,1000);configureCopy(c,src,dst,1,0);put(c,src,0x42);c.run();require(c.guard.stop.equals("EXTERNAL_OR_NULL_TARGET")&&c.guard.reg(c.thread,"AL")==0x42&&c.guard.opaque.isEmpty(),"known copy value");passed++;
  Trial d=toy(out,"opaque_overwritten_by_known_store",hex("f3a4c602558a02"),20,1000);configureCopy(d,src,dst,1,0);d.run();require(d.guard.stop.equals("EXTERNAL_OR_NULL_TARGET")&&d.guard.reg(d.thread,"AL")==0x55&&d.guard.opaque.isEmpty(),"known store clears shadow");passed++;
  Trial e=toy(out,"opaque_nonstack_destination",hex("f3a4"),20,1000);configureCopy(e,src,0x2000,1,0);e.run();require(e.guard.stop.equals("NON_STACK_WRITE")&&e.guard.opaque.isEmpty()&&e.guard.reg(e.thread,"RCX")==1,"nonstack guard unchanged");passed++;
  Trial f=toy(out,"opaque_nonstack_source",hex("f3a4"),20,1000);configureCopy(f,0x2000,dst,1,0);f.run();require(f.guard.stop.equals("OPAQUE_COPY_SOURCE_OUTSIDE_STACK"),"source scope");passed++;
  Trial g=toy(out,"opaque_zero_count",hex("f3a4"),20,1000);configureCopy(g,0xdead,0xbeef,0,0);g.run();require(g.guard.stop.equals("EXTERNAL_OR_NULL_TARGET")&&g.guard.opaque.isEmpty(),"zero count access");passed++;
  Trial h=toy(out,"opaque_reverse_copy",hex("f3a4"),20,1000);configureCopy(h,src+1,dst+1,2,1);put(h,src,11,22);h.run();require(Arrays.equals(h.inspectMemory(dst,2),new byte[]{11,22})&&h.guard.reg(h.thread,"DF")==1,"reverse copy");passed++;
  Trial j=toy(out,"opaque_instruction_budget",hex("f3a4"),2,1000);configureCopy(j,src,dst,3,0);j.run();require(j.guard.stop.equals("INSTRUCTION_BUDGET")&&j.guard.completed==2&&j.guard.reg(j.thread,"RCX")==1,"modeled instruction accounting");passed++;
  Trial k=toy(out,"opaque_overlap_forward",hex("f3a4"),20,1000);configureCopy(k,src,src-1,3,0);put(k,src,10,20,30);k.run();require(Arrays.equals(k.inspectMemory(src-1,3),new byte[]{10,20,30}),"forward overlap");passed++;
  Trial l=toy(out,"opaque_direct_read",hex("f3a4a0"+HexFormat.of().formatHex(ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN).putLong(dst).array())),20,1000);configureCopy(l,src,dst,1,0);put(l,dst,99);l.run();require(l.guard.stop.equals("OPAQUE_VALUE_READ"),"direct input guard");passed++;
  Trial chain=toy(out,"opaque_overlap_identity",hex("f3a4"),20,1000);configureCopy(chain,src,src+1,3,0);chain.run();require(chain.guard.opaque.get(src+3)==src&&chain.guard.opaqueCopies==3,"opaque identity lost on overlap");passed++;
  Trial direct=toy(out,"opaque_direct_known_overwrite",hex("f3a448b8776655443322110048a3"+HexFormat.of().formatHex(ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN).putLong(dst).array())+"8a02"),20,1000);configureCopy(direct,src,dst,1,0);direct.run();require(direct.guard.stop.equals("EXTERNAL_OR_NULL_TARGET")&&direct.guard.reg(direct.thread,"AL")==0x77&&direct.guard.opaque.isEmpty(),"direct known output did not clear shadow");passed++;
  Trial budget=toy(out,"opaque_pcode_budget",hex("f3a4"),20,0);configureCopy(budget,src,dst,1,0);budget.run();require(budget.guard.stop.equals("PCODE_BUDGET")&&budget.guard.completed==0,"pcode bound before model");passed++;
  for(int direction=0;direction<=1;direction++)for(int count:new int[]{0,1,2,16,31}){
   Trial reference=toy(out,"copy_reference_"+direction+"_"+count,hex("f3a4"),100,10000),model=toy(out,"copy_model_"+direction+"_"+count,hex("f3a4"),100,10000);
   for(Trial trial:List.of(reference,model)){configureCopy(trial,SP+128+(direction==1?count-1:0),SP-512+(direction==1?count-1:0),count,direction);int[] data=new int[64];for(int k2=0;k2<64;k2++)data[k2]=(k2*37+11)&255;put(trial,SP+128,data);put(trial,SP-512,new int[64]);for(String flag:List.of("CF","ZF","SF","OF","PF","AF"))trial.guard.reg(trial.thread,flag,1);}
   reference.guard.opaqueCopy=false;reference.run();model.run();require(reference.guard.stop.equals("EXTERNAL_OR_NULL_TARGET")&&model.guard.stop.equals(reference.guard.stop),"differential stop");
   require(reference.guard.completed==model.guard.completed&&Arrays.equals(reference.inspectMemory(SP-512,64),model.inspectMemory(SP-512,64)),"differential copy/count");
   for(String n:List.of("RSI","RDI","RCX","RSP","RAX","RDX","CF","ZF","SF","OF","PF","AF","DF"))require(reference.guard.reg(reference.thread,n)==model.guard.reg(model.thread,n),"differential register "+n);passed++;
  }
  out.println("OPAQUE_COPY_SELF_TEST_PASS\t"+passed+"\tysm_target_simulated=false");println("OPAQUE_COPY_SELF_TEST_PASS "+passed);
 }
 void verifyMemory(String manifest) throws Exception {
  java.util.List<String> rows=Files.readAllLines(Path.of(manifest));require(rows.size()==7,"Expected seven load segments");
  for(String line:rows){String[] f=line.split("\t");long a=Long.parseUnsignedLong(f[0],16);int n=Integer.parseInt(f[1]);require(n>0&&n<26000000,"Invalid segment size");byte[] bytes=new byte[n];require(currentProgram.getMemory().getBytes(toAddr(a),bytes)==n,"Short memory read");require(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)).equals(f[2]),"Memory hash mismatch");}
 }
 public void run() throws Exception {
  String[] args=getScriptArgs();require(args.length>=2,"mode output [memory-manifest image] required");
  require(currentProgram.getLanguageID().toString().equals("x86:LE:64:default"),"Wrong language");
  try(PrintWriter out=new PrintWriter(Files.newBufferedWriter(Path.of(args[1])))){
   if(args[0].equals("self-test")){selfTest(out);return;}
   if(args[0].equals("self-test-opaque-copy")){selfTest(out);opaqueTests(out);return;}
   require((args[0].equals("run-approved-ysm-init")||args[0].equals("run-approved-opaque-copy-init"))&&args.length==4,"Explicit bounded YSM mode required");
   String fileHash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(args[3]))));require(fileHash.equals(IMAGE_SHA),"Wrong native image");
   require(currentProgram.getImageBase().getOffset()==0,"Expected analysis base zero");
   verifyMemory(args[2]);
   AddressSet code=new AddressSet();for(MemoryBlock b:currentProgram.getMemory().getBlocks())if(b.isInitialized()&&b.isExecute())code.addRange(b.getStart(),b.getEnd());
   Trial t=new Trial(code,out,10000,1000000);t.guard.opaqueCopy=args[0].equals("run-approved-opaque-copy-init");EmulatorUtilities.loadProgram(t.emu,currentProgram);t.initialize(0x152eb19);
   out.println("MODEL\topaque_stack_copy="+t.guard.opaqueCopy);
   out.println("CONFIG\tDT_INIT=152eb19\timagebase=0\tregister_inputs=synthetic_zero_except_rsp_pc_if\tstack_uninitialized_except_return\tmax_instructions=10000\tmax_pcode=1000000\tmax_seconds=60\thost_native_execution=false");
   t.run();require(!t.guard.stop.equals("UNEXPECTED_ENGINE_ERROR"),"Unexpected engine error; do not claim a valid target result");
   verifyMemory(args[2]);require(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(args[3])))).equals(fileHash),"Original file changed");
   if(t.guard.pc==0x143beaeL&&t.guard.stop.equals("UNINITIALIZED_READ")){
    long src=t.thread.getState().inspectRegisterValue(currentProgram.getRegister("R10")).getUnsignedValue().longValue();
    require(t.guard.stack(src,328),"Diagnostic range must remain inside private stack");
    for(int k=0;k<328;k++){byte[] v=t.inspectMemory(src+k,1);out.println("SOURCE_BYTE\t"+Long.toHexString(src+k)+"\t"+(v==null?"UNKNOWN":HexFormat.of().formatHex(v)));}
   }
   out.println("PRESERVATION\tfile_and_seven_program_segments_unchanged=true");
   out.println("BOUNDED_RESULT\t"+t.guard.stop+"\toriginal_image_sha256="+fileHash+"\thost_native_execution=false\tnon_stack_write_applied=false");println("BOUNDED_DT_INIT_STOP "+t.guard.stop);
  }
 }
}
