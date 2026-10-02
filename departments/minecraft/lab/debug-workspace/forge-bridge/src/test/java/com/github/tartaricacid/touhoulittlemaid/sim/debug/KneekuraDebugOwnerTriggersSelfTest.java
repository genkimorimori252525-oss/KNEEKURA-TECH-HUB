package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.util.*;
public final class KneekuraDebugOwnerTriggersSelfTest {
 public static void main(String[] args)throws Exception {
  var bounds=new KneekuraDebugArenaController.Bounds(0,0,0,8,8,8);
  var detector=new KneekuraDebugOwnerTriggers.ExitDetector(bounds,2,1000);
  if(detector.sample("subject",List.of(9.0,1.0,1.0),0)!=null)throw new AssertionError("first outside is not an exit");
  detector.sample("subject",List.of(1.0,1.0,1.0),1);
  var event=detector.sample("subject",List.of(9.0,1.0,1.0),2);
  if(event==null||!event.get("transition").getAsString().equals("INSIDE_TO_OUTSIDE"))throw new AssertionError("observed exit missing");
  if(detector.sample("subject",List.of(10.0,1.0,1.0),3)!=null)throw new AssertionError("duplicate outside");
  detector.sample("subject",List.of(1.0,1.0,1.0),4);detector.missing("subject");
  if(detector.sample("subject",List.of(9.0,1.0,1.0),1005)!=null)throw new AssertionError("missing interval inferred exit");
  detector.sample("subject",List.of(1.0,1.0,1.0),1006);
  if(detector.sample("subject",List.of(9.0,1.0,1.0),1007)==null)throw new AssertionError("second real exit missing");
  detector.sample("subject",List.of(1.0,1.0,1.0),2008);
  if(detector.sample("subject",List.of(9.0,1.0,1.0),2009)!=null)throw new AssertionError("event budget exceeded");
  if(KneekuraDebugOwnerTriggers.remainingMillis(1500,1000,5000)!=500)throw new AssertionError("absolute deadline");
  if(KneekuraDebugOwnerTriggers.remainingMillis(999,1000,5000)!=0)throw new AssertionError("expired dispatch");
  System.out.println("bounded actual point transition and absolute trigger deadline checks passed; Minecraft NOT_RUN");
 }
}
