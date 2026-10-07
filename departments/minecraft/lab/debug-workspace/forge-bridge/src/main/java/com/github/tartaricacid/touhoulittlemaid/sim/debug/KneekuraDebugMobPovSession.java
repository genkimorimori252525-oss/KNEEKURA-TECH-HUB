package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.util.Objects;
import java.util.UUID;
/** Monotonic live-view termination; polling has no persistence or entity effects. */
final class KneekuraDebugMobPovSession {
 final UUID subject;
 private final long started,deadline;
 private String ended;
 KneekuraDebugMobPovSession(UUID subject,long started,long deadline){
  this.subject=Objects.requireNonNull(subject);this.started=started;this.deadline=deadline;
  if(deadline-started<=0||deadline-started>120_000_000_000L)throw new IllegalArgumentException("MOB_POV_DURATION_BOUND");
 }
 String poll(long now,boolean owner,boolean world,boolean loaded,boolean alive,boolean camera){
  if(ended!=null)return ended;
  if(now-started<0)ended="CLOCK_CHANGED";
  else if(now-started>=deadline-started)ended="EXPIRED";
  else if(!owner)ended="OWNER_LOST";
  else if(!world)ended="WORLD_CHANGED";
  else if(!loaded)ended="TARGET_UNLOADED";
  else if(!alive)ended="TARGET_DEAD";
  else if(!camera)ended="CAMERA_REPLACED";
  return ended;
 }
}
