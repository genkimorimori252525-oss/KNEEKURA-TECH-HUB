// Bounded static constant-propagation experiment; no target execution or CPU emulation.
import ghidra.app.script.GhidraScript;
import ghidra.app.util.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.pcode.*;
import ghidra.program.util.*;
import java.nio.file.*;
import java.util.*;
import java.io.*;
public class YsmStaticPropagationProbe extends GhidraScript {
 public void run() throws Exception {
  String[] args=getScriptArgs();if(args.length!=2)throw new IllegalArgumentException("manifest output required");
  AddressSet allowed=new AddressSet();
  for(String line:Files.readAllLines(Path.of(args[0]))){String[] f=line.split("\t");long a=Long.parseUnsignedLong(f[0],16);int n=Integer.parseInt(f[1]);allowed.addRange(toAddr(a),toAddr(a+n-1));}
  PseudoDisassembler decoder=new PseudoDisassembler(currentProgram);Map<Address,PseudoInstruction> cache=new HashMap<>();
  try(PrintWriter out=new PrintWriter(Files.newBufferedWriter(Path.of(args[1])))){
   SymbolicPropogator prop=new SymbolicPropogator(currentProgram,true){
    public Instruction getInstructionAt(Address a){
     if(!allowed.contains(a))return null;
     try{return cache.computeIfAbsent(a,x->{try{PseudoInstruction i=decoder.disassemble(x);if(i.getFlowType().isCall())i.setFlowOverride(FlowOverride.BRANCH);return i;}catch(Exception e){throw new RuntimeException(e);}});}catch(Exception e){out.println("DECODE_ERROR\t"+a+"\t"+e);return null;}
    }
    public Function getFunctionAt(Address a){return null;}
    public PcodeOp[] getInstructionPcode(Instruction i){
     PcodeOp[] old=i.getPcode(false);PcodeOp[] result=old.clone();
     for(int j=0;j<old.length;j++)if(old[j].getOpcode()==PcodeOp.CALL)result[j]=new PcodeOp(old[j].getSeqnum(),PcodeOp.BRANCH,old[j].getInputs(),old[j].getOutput());
     return result;
    }
   };
   prop.setParamRefCheck(false);prop.setReturnRefCheck(false);prop.setStoredRefCheck(false);
   prop.setRegister(toAddr(0x152eb19),currentProgram.getRegister("RSP"));
   ContextEvaluatorAdapter eval=new ContextEvaluatorAdapter(){
    int count=0;
    public boolean evaluateContextBefore(VarnodeContext c,Instruction i){
     count++;out.print("BEFORE\t"+i.getAddress()+"\t"+i.toString());
     for(String name:new String[]{"RSP","RBP","RCX","R11","R10","RSI","CF","ZF","SF"})out.print("\t"+name+"="+c.getRegisterVarnodeValue(currentProgram.getRegister(name)));
     out.println();
     if(count>1000){out.println("STOP_BUDGET");return true;}
     String m=i.getMnemonicString();
     if(m.equals("RET")){out.println("STOP_RETURN\t"+i.getAddress());return true;}
     if(i.getFlowType().isConditional()){
      String flag;
      if(m.equals("JNZ")||m.equals("JNE")||m.equals("JZ")||m.equals("JE"))flag="ZF";
      else if(m.equals("JNC")||m.equals("JAE")||m.equals("JC")||m.equals("JB"))flag="CF";
      else {out.println("STOP_UNSUPPORTED_PREDICATE\t"+i.getAddress()+"\t"+m);return true;}
      Varnode value=c.getRegisterVarnodeValue(currentProgram.getRegister(flag));
      if(value==null||!c.isConstant(value)){out.println("STOP_UNKNOWN_FLAG\t"+flag+"\t"+i.getAddress());return true;}
      if(value.getOffset()!=0){out.println("STOP_ORACLE_DISAGREEMENT\t"+i.getAddress()+"\t"+value);return true;}
      out.println("ORACLE_MATCH\t"+i.getAddress()+"\t"+flag+"=0\t"+value.getAddress().getAddressSpace().getName());
     }
     return false;
    }
    public boolean followFalseConditionalBranches(){return false;}
    public boolean allowAccess(VarnodeContext c,Address a){return a.getOffset()>=0x14c9bd5L&&a.getOffset()<0x14c9bd9L;}
   };
   AddressSet visited=prop.flowConstants(toAddr(0x152eb19),allowed,eval,false,monitor);
   out.println("FINISHED\tvisited_bytes="+visited.getNumAddresses());
   println("STATIC_PROPAGATION_PROBE_FINISHED bytes="+visited.getNumAddresses());
  }
 }
}
