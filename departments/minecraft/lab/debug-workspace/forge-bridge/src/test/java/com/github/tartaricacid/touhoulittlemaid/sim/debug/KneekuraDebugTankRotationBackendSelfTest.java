package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import java.util.*;

/** Actual compiled API/call boundaries only; this is explicitly not native world acceptance. */
public final class KneekuraDebugTankRotationBackendSelfTest {
 static int checks;
 static void check(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
 static int calls(MethodNode m,String ownerSuffix,String name){int n=0;for(var i:m.instructions)if(i instanceof MethodInsnNode c && c.owner.endsWith(ownerSuffix) && c.name.equals(name))n++;return n;}
 static MethodNode method(ClassNode c,String name){return c.methods.stream().filter(m->m.name.equals(name)).findFirst().orElseThrow();}
 public static void main(String[] args)throws Exception{
  ClassNode c=new ClassNode();try(var stream=KneekuraDebugForgeTankRotationBackend.class.getResourceAsStream("KneekuraDebugForgeTankRotationBackend.class")){new ClassReader(stream).accept(c,0);}
  int writes=0;for(MethodNode m:c.methods)writes+=calls(m,"/ServerLevel","setBlock");
  check(writes==1,"one fixed native shell setBlock call site");
  check(method(c,"<init>").desc.contains("KneekuraDebugScopedOwnerGate;"),"only concrete source owner gate admitted");
  check(c.fields.stream().anyMatch(f->f.name.equals("gate") && (f.access&Opcodes.ACC_FINAL)!=0),"source gate cannot be replaced by request");
  MethodNode read=method(c,"stateAt");check(calls(read,"/ServerLevel","hasChunkAt")==1 && calls(read,"/ServerLevel","getBlockState")==1 && calls(read,"/ServerLevel","getBlockEntity")==1,"bounded original loaded-cell query sites");
  check(calls(method(c,"guard"),"/KneekuraDebugScopedOwnerGate","requireAuthorized")==1,"native owner guard retained");
  check(calls(method(c,"reserve"),"/KneekuraDebugOwnerFiles","writeNew")==1 && calls(method(c,"reserve"),"/KneekuraDebugOwnerFiles","replaceExpected")==1,"durable reservation and unknown owner marker before generation");
  check(calls(method(c,"publishVerified"),"/MinecraftServer","saveEverything")==1,"actual world save return remains checked");
  check(calls(method(c,"publishVerified"),"/KneekuraDebugOwnerFiles","replaceExpected")==1,"verified owner publication remains atomic");
  check(calls(method(c,"requireQuiet"),"/ServerLevel","getEntitiesOfClass")==0 && calls(method(c,"requireQuiet"),"/ServerLevel","getEntities")==1,"quiet query uses finite native result allocation instead of an unbounded entity list");
  ClassNode session=new ClassNode();try(var stream=KneekuraDebugOwnerConnection.class.getResourceAsStream("KneekuraDebugOwnerConnection$Session.class")){new ClassReader(stream).accept(session,0);}
  check(calls(method(session,"tick"),"/KneekuraDebugTankRotationController","onTick")==1,"finite maintenance tick connected before ordinary owner dispatch");
  check(calls(method(session,"tick"),"/KneekuraDebugForgeTankRotationBackend","bindInstallationReceipt")==1,"actual installed receipt bound before maintenance ticks");
  check(calls(method(c,"bindInstallationReceipt"),"/KneekuraDebugTankRotationPlan","installationReceiptHash")==1 && calls(method(c,"guard"),"/KneekuraDebugOwnerFiles","read")==2,"installed receipt identity and byte closure remain checked");
  check(calls(method(session,"close"),"/KneekuraDebugTankRotationController","revoke")==1,"shutdown revokes unfinished maintenance before owner detach");
  check(calls(method(session,"install"),"/KneekuraDebugTankRotationPlan$Validated","controllerPlan")==1 && calls(method(session,"install"),"/KneekuraDebugArenaRuntime","presentationLeaseOwner")==1,"maintenance consumes original owner lease without renewal");
  ClassNode presentation=new ClassNode();try(var stream=KneekuraDebugTankPresentation.class.getResourceAsStream("KneekuraDebugTankPresentation.class")){new ClassReader(stream).accept(presentation,0);}
  MethodNode update=method(presentation,"update");boolean maintenanceVeto=false;
  for(var instruction:update.instructions)if(instruction instanceof LdcInsnNode literal && "tankRotationHash".equals(literal.cst)){
   var next=instruction.getNext();while(next!=null && next.getOpcode()<0)next=next.getNext();
   if(!(next instanceof MethodInsnNode call) || !call.owner.equals("com/google/gson/JsonObject") || !call.name.equals("has"))continue;
   next=next.getNext();while(next!=null && next.getOpcode()<0)next=next.getNext();
   if(!(next instanceof JumpInsnNode branch) || branch.getOpcode()!=Opcodes.IFEQ)continue;
   next=next.getNext();while(next!=null && next.getOpcode()<0)next=next.getNext();maintenanceVeto=next!=null && next.getOpcode()==Opcodes.RETURN;
  }
  check(maintenanceVeto,"sealed maintenance envelope exits before resource presentation can reactivate");
  for(MethodNode m:c.methods)for(var i:m.instructions)if(i instanceof MethodInsnNode call){
   check(!Set.of("getChunk","getChunkSource","setForced","setDifficulty","setDayTime","setWeatherParameters","getGameRules","teleportTo","setGameMode","performPrefixedCommand","addFreshEntity","remove","discard").contains(call.name),"no chunk load/global environment/player/entity command: "+call.name);
  }
  System.out.println("Genuine compiled Tank backend API boundaries passed: "+checks+"; native generation NOT_RUN by this test");
 }
}
