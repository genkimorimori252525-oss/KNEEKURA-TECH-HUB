package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.common.collect.ImmutableList;
import com.google.gson.JsonObject;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.schedule.Activity;
import net.minecraft.world.entity.schedule.Schedule;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import com.mojang.datafixers.util.Pair;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import org.objectweb.asm.*;

/** Genuine untransformed originals; installed inner callbacks require separate native proof. */
public final class KneekuraDebugBrainActivitySelfTest {
    private static Method update;
    private static Method queryReturn,requirementsReturn,setReturn;
    private static final class ProbeBrain extends Brain<Mob> {
        Runnable body=()->{};int updates;
        ProbeBrain(){super(List.of(),List.of(),ImmutableList.of(),()->null);}
        @Override public void updateActivityFromSchedule(long day,long game){updates++;body.run();}
        @Override public Schedule getSchedule(){throw new AssertionError("OBSERVER_SCHEDULE_GETTER");}
        @Override public Set<Activity> getActiveActivities(){throw new AssertionError("OBSERVER_ACTIVE_GETTER");}
        @Override public String toString(){throw new AssertionError("OBSERVER_BRAIN_STRING");}
    }
    private static final class Subject extends Mob {
        private Subject(){super(null,null);}
        @Override public Brain<?> getBrain(){throw new AssertionError("OBSERVER_BRAIN_GETTER");}
        @Override public String toString(){throw new AssertionError("OBSERVER_ENTITY_STRING");}
    }
    private static final class Query extends Schedule {
        int calls;Activity activity=Activity.REST;RuntimeException failure;
        @Override public Activity getActivityAt(int tick){calls++;if(failure!=null)throw failure;return activity;}
        @Override public String toString(){throw new AssertionError("OBSERVER_SCHEDULE_STRING");}
    }
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static void field(Object owner,Class<?> base,String name,Object value)throws Exception {
        var f=base.getDeclaredField(name);f.setAccessible(true);f.set(owner,value);
    }
    private static void invoke(Brain<?> brain,long day,long game)throws Exception {
        try{update.invoke(null,brain,day,game);}
        catch(InvocationTargetException error){if(error.getCause() instanceof RuntimeException original)throw original;if(error.getCause() instanceof Error original)throw original;throw error;}
    }
    private static Object call(Method method,Object... args) {
        try{return method.invoke(null,args);}
        catch(InvocationTargetException error){if(error.getCause() instanceof RuntimeException original)throw original;if(error.getCause() instanceof Error original)throw original;throw new AssertionError(error);}
        catch(ReflectiveOperationException error){throw new AssertionError(error);}
    }
    private static Object original(Method method,Brain<?> brain,Object... args) {
        try{return method.invoke(brain,args);}catch(ReflectiveOperationException error){throw new AssertionError(error);}
    }
    private static void compiledHandlers()throws Exception {
        String pkg="com/github/tartaricacid/touhoulittlemaid/sim/debug/decisionmixin/";
        var expected=Map.of("kneekura$originalUpdate",new String[]{"Redirect","lambda$create$0(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/LivingEntity;J)Z","INVOKE","Lnet/minecraft/world/entity/ai/Brain;updateActivityFromSchedule(JJ)V","originalActivityUpdate"},
            "kneekura$originalActivityQuery",new String[]{"Redirect","updateActivityFromSchedule(JJ)V","INVOKE","Lnet/minecraft/world/entity/schedule/Schedule;getActivityAt(I)Lnet/minecraft/world/entity/schedule/Activity;","originalActivityQuery"},
            "kneekura$activityRequirements",new String[]{"Inject","activityRequirementsAreMet(Lnet/minecraft/world/entity/schedule/Activity;)Z","RETURN","","activityRequirementsReturn"},
            "kneekura$activeActivity",new String[]{"Inject","setActiveActivity(Lnet/minecraft/world/entity/schedule/Activity;)V","RETURN","","activeActivityReturn"});
        var found=new HashSet<String>();
        for(String owner:List.of("KneekuraDebugBrainDecisionMixin","KneekuraDebugScheduledActivityMixin"))try(var stream=KneekuraDebugBrainActivitySelfTest.class.getClassLoader().getResourceAsStream(pkg+owner+".class")){
            require(stream!=null,"compiled original activity handler required");
            new ClassReader(stream).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
                    var spec=expected.get(name);if(spec==null)return null;found.add(name);int[] captures={0},required={0},methods={0},ats={0},targets={0};
                    return new MethodVisitor(Opcodes.ASM9){
                        private AnnotationVisitor annotation(){return new AnnotationVisitor(Opcodes.ASM9){
                            @Override public void visit(String key,Object value){
                                if(key.equals("require"))required[0]=(Integer)value;
                                if(key.equals("cancellable"))require(Boolean.FALSE.equals(value),"cannot cancel original");
                                if(key.equals("value")&&value.equals(spec[2]))ats[0]++;
                                if(key.equals("target")){require(value.equals(spec[3]),"exact original invocation target");targets[0]++;}
                            }
                            @Override public AnnotationVisitor visitArray(String key){
                                if(key.equals("method"))return new AnnotationVisitor(Opcodes.ASM9){@Override public void visit(String ignored,Object value){require(value.equals(spec[1]),"exact original erased method descriptor");methods[0]++;}};
                                return annotation();
                            }
                            @Override public AnnotationVisitor visitAnnotation(String key,String desc){return annotation();}
                        };}
                        @Override public AnnotationVisitor visitAnnotation(String desc,boolean visible){require(desc.endsWith("/"+spec[0]+";"),"expected original boundary annotation");return annotation();}
                        @Override public void visitMethodInsn(int opcode,String owner,String call,String desc,boolean itf){
                            if(owner.endsWith("/KneekuraDebugDecisionHooks")){require(call.equals(spec[4])&&opcode==Opcodes.INVOKESTATIC,"one observer delegate");captures[0]++;}
                            else require((owner.endsWith("/CallbackInfoReturnable")&&call.equals("getReturnValue"))||
                                (name.equals("kneekura$activityRequirements")&&owner.equals("java/lang/Boolean")&&call.equals("booleanValue")&&desc.equals("()Z")),"handler cannot replay AI/query or change return");
                        }
                        @Override public void visitEnd(){require(captures[0]==1&&required[0]==1&&methods[0]==1&&ats[0]==1&&targets[0]==(spec[0].equals("Redirect")?1:0),"required exact noncancelling original boundary");}
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }require(found.equals(expected.keySet()),"all four original activity handlers compiled");
    }
    private static KneekuraDebugDecisionHooks.Session install(Subject subject,Set<String> channels,int events,int bytes,
            AtomicReference<KneekuraDebugDecisionBurstBudget.Context> context,AtomicLong tick,List<JsonObject> rows)throws Exception {
        var session=new KneekuraDebugDecisionHooks.Session(subject,null,null,new KneekuraDebugDecisionSnapshot(),
            new KneekuraDebugDecisionBurstBudget(context.get(),100,100,events,bytes),8,channels,context::get,tick::get,
            (method,row)->rows.add(row));KneekuraDebugDecisionHooks.install(session);return session;
    }
    public static void main(String[] args)throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        var uf=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");uf.setAccessible(true);var unsafe=(sun.misc.Unsafe)uf.get(null);
        var subject=(Subject)unsafe.allocateInstance(Subject.class);
        var brain=new Brain<>(List.of(),List.of(),ImmutableList.of(),()->null);var query=new Query();
        brain.setSchedule(query);brain.setCoreActivities(Set.of(Activity.CORE));brain.setDefaultActivity(Activity.IDLE);
        brain.addActivity(Activity.REST,0,ImmutableList.of());brain.addActivity(Activity.IDLE,0,ImmutableList.of());
        brain.setActiveActivityIfPossible(Activity.IDLE);field(subject,net.minecraft.world.entity.LivingEntity.class,"brain",brain);
        brain.updateActivityFromSchedule(12000,100);require(query.calls==1&&brain.isActive(Activity.REST),"genuine original query and activity transition");
        brain.updateActivityFromSchedule(12000,120);require(query.calls==1,"original >20 schedule guard");
        try{update=KneekuraDebugDecisionHooks.class.getMethod("originalActivityUpdate",Brain.class,long.class,long.class);}
        catch(NoSuchMethodException error){throw new AssertionError("original activity call scope observation missing",error);}
        queryReturn=KneekuraDebugDecisionHooks.class.getMethod("originalActivityQuery",Brain.class,Schedule.class,int.class);
        requirementsReturn=KneekuraDebugDecisionHooks.class.getMethod("activityRequirementsReturn",Brain.class,Activity.class,boolean.class);
        setReturn=KneekuraDebugDecisionHooks.class.getMethod("activeActivityReturn",Brain.class,Activity.class);
        var context=new AtomicReference<>(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"11111111-2222-3333-4444-555555555555","minecraft:overworld"));
        var tick=new AtomicLong(100);var rows=new ArrayList<JsonObject>();
        KneekuraDebugDecisionHooks.clear("OFF");invoke(brain,12000,121);require(query.calls==2&&rows.isEmpty(),"OFF original query once");
        brain.setActiveActivityIfPossible(Activity.IDLE);install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);
        invoke(brain,12000,142);require(query.calls==3&&rows.size()==1&&brain.isActive(Activity.REST),"wrapper preserves actual query and switch once");
        var before=rows.get(0).deepCopy();brain.setActiveActivityIfPossible(Activity.IDLE);require(rows.get(0).equals(before),"detached cached state across later activity changes");
        invoke(brain,12000,162);require(query.calls==3&&rows.size()==2,"guarded normal return does not replay stateful query");
        int count=rows.size();var failure=new IllegalStateException("original query failed");query.failure=failure;
        try{invoke(brain,12000,163);throw new AssertionError("original exception lost");}catch(IllegalStateException error){require(error==failure,"original exception identity");}
        require(query.calls==4&&rows.size()==count,"no normal return from throwing original");query.failure=null;
        invoke(brain,12000,184);require(query.calls==5&&rows.size()==count+1,"throw cleanup allows next distinct invocation");
        var interop=new ArrayList<>(rows);
        install(subject,Set.of("brain"),256,524288,context,tick,rows);count=rows.size();invoke(brain,12000,205);require(query.calls==6&&rows.size()==count,"dedicated channel does not arm through generic brain");
        install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);
        var foreign=new Brain<>(List.of(),List.of(),ImmutableList.of(),()->null);foreign.setSchedule(new Query());invoke(foreign,12000,100);require(rows.size()==count,"stored selected Brain reference fence");
        var workerFailure=new AtomicReference<Throwable>();Thread worker=new Thread(()->{try{invoke(brain,12000,226);}catch(Throwable error){workerFailure.set(error);}});worker.start();worker.join();require(workerFailure.get()==null&&rows.size()==count&&query.calls==7,"wrong thread preserves original but does not observe");
        install(subject,Set.of("brain_activity"),1,524288,context,tick,rows);invoke(brain,12000,247);invoke(brain,12000,268);require(rows.size()==count+1&&query.calls==9,"event fence cannot suppress originals");
        install(subject,Set.of("brain_activity"),256,1,context,tick,rows);count=rows.size();invoke(brain,12000,289);require(rows.size()==count&&query.calls==10,"byte fence cannot suppress original");
        install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);tick.set(200);invoke(brain,12000,310);require(rows.size()==count&&query.calls==11,"time fence cannot suppress original");
        tick.set(100);install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);
        context.set(new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,context.get().subjectUuid(),context.get().dimension()));invoke(brain,12000,331);require(rows.size()==count&&query.calls==12,"selection revision fence preserves original");
        // Explicit compiled-fixture callbacks execute genuine private originals once. They are not installed proof.
        var probe=new ProbeBrain();var scopedQuery=new Query();probe.setSchedule(scopedQuery);probe.setCoreActivities(Set.of(Activity.CORE));
        probe.addActivity(Activity.REST,0,ImmutableList.of());probe.addActivity(Activity.IDLE,0,ImmutableList.of());probe.setActiveActivityIfPossible(Activity.IDLE);
        field(subject,net.minecraft.world.entity.LivingEntity.class,"brain",probe);
        var requirements=Brain.class.getDeclaredMethod("activityRequirementsAreMet",Activity.class);requirements.setAccessible(true);
        var setter=Brain.class.getDeclaredMethod("setActiveActivity",Activity.class);setter.setAccessible(true);
        rows.clear();install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);
        probe.body=()->{
            Activity value=(Activity)call(queryReturn,probe,scopedQuery,12000);
            boolean result=(Boolean)original(requirements,probe,value);call(requirementsReturn,probe,value,result);
            original(setter,probe,value);call(setReturn,probe,value);
        };
        invoke(probe,12000,100);require(scopedQuery.calls==1&&probe.updates==1&&rows.size()==4,"original query/private condition/private setter inside actual virtual update scope");
        String id=rows.get(0).getAsJsonObject("data").get("activityInvocationId").getAsString();
        require(rows.stream().allMatch(r->r.getAsJsonObject("data").get("activityInvocationId").getAsString().equals(id)),"exact call scope link, not tick adjacency");interop.addAll(rows);
        count=rows.size();call(queryReturn,probe,scopedQuery,-1);call(requirementsReturn,probe,Activity.REST,false);call(setReturn,probe,Activity.REST);
        require(scopedQuery.calls==2&&rows.size()==count,"outside original update frame only original query executes");
        probe.addActivityWithConditions(Activity.REST,ImmutableList.of(),Set.of(Pair.of(MemoryModuleType.WALK_TARGET,MemoryStatus.VALUE_PRESENT)));
        rows.clear();install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);
        probe.body=()->{
            Activity value=(Activity)call(queryReturn,probe,scopedQuery,12000);
            boolean result=(Boolean)original(requirements,probe,value);require(!result,"genuine missing memory condition fails");
            call(requirementsReturn,probe,value,result);original(setter,probe,Activity.IDLE);call(setReturn,probe,Activity.IDLE);
        };
        invoke(probe,12000,100);require(rows.size()==4&&probe.isActive(Activity.IDLE)&&!rows.get(1).getAsJsonObject("data").get("result").getAsBoolean(),"actual false requirements, distinct fallback activity, no false switch-success interpretation");interop.addAll(rows);
        // Unsupported cached sets must not execute custom size/iterator/toString.
        var custom=new AbstractSet<Activity>(){
            @Override public Iterator<Activity> iterator(){throw new AssertionError("CUSTOM_ITERATOR");}
            @Override public int size(){throw new AssertionError("CUSTOM_SIZE");}
            @Override public String toString(){throw new AssertionError("CUSTOM_SET_STRING");}
        };
        field(probe,Brain.class,"coreActivities",custom);probe.body=()->{};rows.clear();install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);
        invoke(probe,Long.MIN_VALUE,Long.MAX_VALUE);require(rows.size()==1&&rows.get(0).getAsJsonObject("data").getAsJsonObject("before").getAsJsonObject("coreActivities").get("detail").getAsString().equals("CUSTOM_ACTIVITY_SET"),"custom set unavailable, exact signed long arguments");interop.add(rows.get(0));
        field(probe,Brain.class,"coreActivities",Set.of(Activity.CORE));
        var many=new HashSet<Activity>();for(var f:Activity.class.getFields())if(f.getType()==Activity.class)many.add((Activity)f.get(null));
        require(many.size()>16,"genuine registered activities exceed observation prefix");field(probe,Brain.class,"activeActivities",many);
        rows.clear();install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);invoke(probe,12000,100);
        require(rows.get(0).getAsJsonObject("data").getAsJsonObject("before").getAsJsonObject("activeActivities").getAsJsonArray("values").size()==16,"bounded16 cached activities, not complete population");interop.add(rows.get(0));
        field(probe,Brain.class,"activeActivities",new HashSet<>(Set.of(Activity.CORE,Activity.IDLE)));
        // Depth9+ remain suppressed even when frame8 is null; original virtual calls still execute.
        var depth=new int[]{0};rows.clear();install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);int calls=scopedQuery.calls;
        probe.body=()->{depth[0]++;if(depth[0]<10)call(update,probe,12000L,100L);call(queryReturn,probe,scopedQuery,12000);depth[0]--;};
        invoke(probe,12000,100);require(scopedQuery.calls==calls+10&&rows.size()==16,"eight-frame cap does not reset below a suppressed ninth invocation");
        require(rows.stream().map(r->r.getAsJsonObject("data").get("activityInvocationId").getAsString()).distinct().count()==8,"no overflow frame or caller misattribution");
        // Original exception after query has query-return evidence, no void normal-return; finally removes frame.
        rows.clear();install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);
        probe.body=()->{call(queryReturn,probe,scopedQuery,12000);throw failure;};
        try{invoke(probe,12000,100);throw new AssertionError("original override exception lost");}catch(IllegalStateException error){require(error==failure,"same original override exception");}
        require(rows.size()==1&&rows.get(0).get("kind").getAsString().equals("BRAIN_ACTIVITY_QUERY_RETURN"),"inner normal return survives outer throw");
        count=rows.size();call(queryReturn,probe,scopedQuery,12000);require(rows.size()==count,"throwing frame cannot leak into subsequent query");
        probe.body=()->{};invoke(probe,12000,100);require(rows.size()==2&&!rows.get(0).getAsJsonObject("data").get("activityInvocationId").equals(rows.get(1).getAsJsonObject("data").get("activityInvocationId")),"next update gets distinct invocation after throw");
        // Shared128 component cap is independent of bounded256 call IDs.
        rows.clear();install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);
        probe.body=()->{for(int i=0;i<130;i++)call(queryReturn,probe,new Query(),12000);};invoke(probe,12000,100);
        require(rows.size()==131&&rows.get(129).getAsJsonObject("data").get("scheduleInstanceIdentity").isJsonNull(),"capped schedule reference remains unknown without eviction");interop.add(rows.get(129));
        rows.clear();install(subject,Set.of("brain_activity"),256,524288,context,tick,rows);probe.body=()->{throw failure;};int prior=probe.updates;
        for(int i=0;i<257;i++)try{invoke(probe,12000,100);}catch(IllegalStateException error){require(error==failure,"original identity beyond call-ID cap");}
        probe.body=()->{};invoke(probe,12000,100);require(rows.isEmpty()&&probe.updates==prior+258,"bounded256 invocation IDs do not suppress original calls or reuse IDs");
        KneekuraDebugDecisionHooks.clear("TEST_COMPLETE");
        compiledHandlers();
        for(var row:interop)System.out.println("BRAIN_ACTIVITY_INTEROP:"+new com.google.gson.Gson().toJson(row));
        System.out.println("Genuine Brain original query/time guard/transition/exception identity, dedicated opt-in and context fences; untransformed inner callbacks are not native proof");
    }
}
