// Static lifting only. No target execution, emulator, or automatic analysis.
import ghidra.app.script.GhidraScript;
import ghidra.app.util.PseudoDisassembler;
import ghidra.app.util.PseudoInstruction;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.lang.Register;
import ghidra.program.model.pcode.PcodeOp;
import java.nio.file.*;
import java.io.*;
import java.security.MessageDigest;
import java.util.HexFormat;
public class YsmScopedLift extends GhidraScript {
 public void run() throws Exception {
  String[] args=getScriptArgs();
  if(args.length!=3)throw new IllegalArgumentException("manifest.tsv output.tsv memory.tsv required");
  if(currentProgram.getImageBase().getOffset()!=0)throw new IllegalStateException("Expected image base zero");
  PseudoDisassembler decoder=new PseudoDisassembler(currentProgram);
  try(PrintWriter out=new PrintWriter(Files.newBufferedWriter(Path.of(args[1])))){
   out.println("PROGRAM\t"+currentProgram.getName()+"\t"+currentProgram.getLanguageID()+"\t"+currentProgram.getImageBase());
   for(MemoryBlock b:currentProgram.getMemory().getBlocks())out.println("BLOCK\t"+b.getName()+"\t"+b.getStart()+"\t"+b.getEnd()+"\t"+b.isInitialized()+"\t"+b.isRead()+"\t"+b.isWrite()+"\t"+b.isExecute());
   for(Register r:currentProgram.getLanguage().getRegisters())out.println("REG\t"+r.getName()+"\t"+r.getAddress()+"\t"+r.getBitLength());
   for(String line:Files.readAllLines(Path.of(args[2]))){
    String[] f=line.split("\t");long start=Long.parseUnsignedLong(f[0],16);int size=Integer.parseInt(f[1]);
    byte[] bytes=new byte[size];if(currentProgram.getMemory().getBytes(toAddr(start),bytes)!=size)throw new IllegalStateException("Short segment read");
    String sha=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    if(!sha.equals(f[2]))throw new IllegalStateException("PT_LOAD bytes mismatch "+f[0]);
    out.println("LOAD_MATCH\t"+f[0]+"\t"+size+"\t"+sha+"\t"+f[3]);
   }
   int ranges=0,instructions=0;
   for(String line:Files.readAllLines(Path.of(args[0]))){
    if(line.isBlank()||line.startsWith("#"))continue;
    String[] f=line.split("\t");long start=Long.parseUnsignedLong(f[0],16);int size=Integer.parseInt(f[1]);Address a=toAddr(start);byte[] bytes=new byte[size];
    if(currentProgram.getMemory().getBytes(a,bytes)!=size)throw new IllegalStateException("Short range read");
    String sha=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    if(!sha.equals(f[2]))throw new IllegalStateException("Imported bytes mismatch "+f[0]);
    int offset=0,count=0;
    while(offset<size){
     monitor.checkCancelled();PseudoInstruction ins=decoder.disassemble(a.add(offset));
     if(ins==null||ins.getLength()<=0||offset+ins.getLength()>size)throw new IllegalStateException("Instruction boundary mismatch "+f[0]+"+"+offset);
     out.println("INS\t"+ins.getAddress()+"\t"+ins.getLength()+"\t"+HexFormat.of().formatHex(ins.getBytes())+"\t"+ins.toString());
     for(PcodeOp op:ins.getPcode())out.println("PCODE\t"+ins.getAddress()+"\t"+op.toString());
     offset+=ins.getLength();count++;
    }
    out.println("RANGE\t"+f[0]+"\t"+size+"\t"+sha+"\t"+count+"\t"+f[3]);ranges++;instructions+=count;
   }
   for(long addr:new long[]{0xd2cd48L,0xd2cd4cL}){byte[] bytes=new byte[4];currentProgram.getMemory().getBytes(toAddr(addr),bytes);out.println("DATA\t"+Long.toHexString(addr)+"\t"+HexFormat.of().formatHex(bytes));}
   out.println("COMPLETE\t"+ranges+"\t"+instructions+"\ttarget_executed=false\tautomatic_analysis=false");
   println("YSM_SCOPED_LIFT_COMPLETE ranges="+ranges+" instructions="+instructions);
  }
 }
}
