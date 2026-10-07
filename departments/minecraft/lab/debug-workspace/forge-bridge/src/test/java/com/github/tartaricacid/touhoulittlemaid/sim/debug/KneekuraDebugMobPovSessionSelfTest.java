package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.util.UUID;
public final class KneekuraDebugMobPovSessionSelfTest {
 private static int checks;
 private static void check(boolean value,String reason){checks++;if(!value)throw new AssertionError(reason);}
 public static void main(String[] args){
  Object cardinal=new Object(),pov=new Object();
  check(KneekuraDebugCameraOwnership.claim(cardinal),"first owner claims");
  check(!KneekuraDebugCameraOwnership.claim(pov),"second owner cannot overlap");
  KneekuraDebugCameraOwnership.release(pov);check(KneekuraDebugCameraOwnership.owns(cardinal),"foreign release cannot clear camera");
  KneekuraDebugCameraOwnership.release(cardinal);check(KneekuraDebugCameraOwnership.claim(pov),"actual release allows next view");
  KneekuraDebugCameraOwnership.release(pov);
  UUID subject=UUID.fromString("00000000-0000-0000-0000-000000000001");
  var session=new KneekuraDebugMobPovSession(subject,100,1100);
  check(session.poll(1099,true,true,true,true,true)==null,"live view until deadline");
  check(session.poll(1100,true,true,true,true,true).equals("EXPIRED"),"deadline closes view");
  check(session.poll(1101,true,true,true,true,true).equals("EXPIRED"),"closed view never reactivates");
  String[] errors={"OWNER_LOST","WORLD_CHANGED","TARGET_UNLOADED","TARGET_DEAD","CAMERA_REPLACED"};
  for(int i=0;i<errors.length;i++){
   session=new KneekuraDebugMobPovSession(subject,100,1100);boolean[] state={true,true,true,true,true};state[i]=false;
   check(session.poll(101,state[0],state[1],state[2],state[3],state[4]).equals(errors[i]),errors[i]);
  }
  session=new KneekuraDebugMobPovSession(subject,100,1100);
  check(session.poll(99,true,true,true,true,true).equals("CLOCK_CHANGED"),"backward monotonic time closes");
  try{new KneekuraDebugMobPovSession(subject,100,100);throw new AssertionError("zero duration");}catch(IllegalArgumentException expected){checks++;}
  System.out.println("mob POV lifecycle/ownership checks="+checks);
 }
}
