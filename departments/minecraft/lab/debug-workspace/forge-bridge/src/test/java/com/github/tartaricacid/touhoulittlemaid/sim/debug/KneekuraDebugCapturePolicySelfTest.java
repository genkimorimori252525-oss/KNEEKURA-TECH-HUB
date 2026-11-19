package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.util.List;
import java.util.Set;
import java.util.UUID;
public final class KneekuraDebugCapturePolicySelfTest {
 static KneekuraDebugCaptureSession.Request request(double fov,int width) {
  var id=new KneekuraDebugCaptureSession.Identity("s","r","snap",1,"e",1,"a".repeat(64),"arena",0,0,"b".repeat(64));
  return new KneekuraDebugCaptureSession.Request("capture",id,List.of(UUID.fromString("00000000-0000-0000-0000-000000000001")),List.of("behavior"),List.of(0,0,0),List.of(8,8,8),fov,width,480,1000,2000,true,true);
 }
 static void reject(Runnable r){try{r.run();throw new AssertionError("unapproved capture allowed");}catch(IllegalArgumentException expected){}}
 public static void main(String[] args){
  var policy=new KneekuraDebugCapturePolicy("a".repeat(64),1,70,640,480,2000,true,true,Set.of("behavior"));
  policy.validate(request(70,640));reject(()->policy.validate(request(71,640)));reject(()->policy.validate(request(70,641)));
  var denied=new KneekuraDebugCapturePolicy("a".repeat(64),1,70,640,480,2000,false,false,Set.of("behavior"));
  reject(()->denied.validate(request(70,640)));
  System.out.println("capture policy checks=4");
 }
}
