package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import net.minecraft.util.profiling.InactiveProfiler;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import java.util.*;
/** Genuine bounded allocator / production Gson shape, not native Brain/Sensor invocation acceptance. */
public final class KneekuraDebugDecisionIdentityInterop {
 private static final class OriginalGoal extends Goal {
  int calls;
  @Override public boolean canUse(){calls++;return true;}
 }
 public static void main(String[] args)throws Exception {
  var snapshot=new KneekuraDebugDecisionSnapshot();snapshot.reset(7);
  for(int i=0;i<256;i++)if(snapshot.identity(new Object())==null)throw new AssertionError("premature Goal identity limit");
  if(snapshot.identity(new Object())!=null)throw new AssertionError("unbounded Goal identities");
  var selector=new GoalSelector(()->InactiveProfiler.INSTANCE);var goal=new OriginalGoal();selector.addGoal(1,goal);
  var context=new KneekuraDebugDecisionBurstBudget.Context("s","r","snap",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld");
  var payloads=new ArrayList<JsonObject>();
  var session=new KneekuraDebugDecisionHooks.Session(null,selector,new GoalSelector(()->InactiveProfiler.INSTANCE),snapshot,
   new KneekuraDebugDecisionBurstBudget(context,100,10,8,65536),8,Set.of("goal","brain"),()->context,()->100L,(method,row)->payloads.add(row));
  var wrapper=selector.getAvailableGoals().iterator().next();session.goalReturn(wrapper,false,wrapper.canUse());
  if(goal.calls!=1||payloads.size()!=1)throw new AssertionError("original callback replay/loss");
  var allocator=KneekuraDebugDecisionHooks.Session.class.getDeclaredMethod("token",Object.class);allocator.setAccessible(true);
  for(int i=0;i<128;i++)if(allocator.invoke(session,new Object())==null)throw new AssertionError("premature component limit");
  String unknown=(String)allocator.invoke(session,new Object());if(unknown!=null)throw new AssertionError("unbounded component identities");
  for(String kind:List.of("BRAIN_TICK_RETURN","BEHAVIOR_TRY_START_RETURN","SENSOR_SCAN_RETURN")){
   var p=payloads.get(0).deepCopy();p.addProperty("kind",kind);var d=new JsonObject();d.addProperty("instanceIdentity",unknown);
   if(kind.equals("BRAIN_TICK_RETURN")){d.addProperty("brainClass","fixture.Brain");d.addProperty("storedBrainMatch",true);}
   else {d.addProperty("className","fixture.Component");if(kind.startsWith("BEHAVIOR_")){
     d.addProperty("cachedStatus","RUNNING");d.addProperty("result",true);d.addProperty("reasonStatus","NOT_EXPOSED");
    }else d.addProperty("candidatePopulationStatus","NOT_EXPOSED");}
   p.add("data",d);payloads.add(p);
  }
  var rows=new JsonArray();var gson=new Gson();for(var p:payloads){
   var serialized=JsonParser.parseString(gson.toJson(p)).getAsJsonObject();
   if(serialized.getAsJsonObject("data").has("instanceIdentity"))throw new AssertionError("production Gson fixture must omit null");rows.add(serialized);
  }
  System.out.println("INTEROP:"+rows);
 }
}
