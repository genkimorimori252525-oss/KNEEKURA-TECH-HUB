package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

public final class CombatSimulationSelfTest {
    private static int checks;
    private static final World FLAT = new FlatWorld(0);
    private static final Vec3 GOAL = new Vec3(0,170,280);
    private static final Vec3 HOME = new Vec3(0,170,-220);
    private CombatSimulationSelfTest() {}
    private static void yes(boolean condition,String reason) {
        checks++;if (!condition)throw new AssertionError(reason);
    }
    private static SquadronCommand.AircraftSpec plane(String id,String type,String team,
            String flight,int slot,TacticalAirAI.Mission mission,String escort,
            double x,double y,double z,double yaw,double speed,double fuel) {
        return new SquadronCommand.AircraftSpec(id,"warfare_wings:"+type,team,
                flight,slot,mission,escort,null,new Vec3(x,y,z),
                forward(yaw,0).scale(speed),yaw,GOAL,HOME,fuel,1,1.6);
    }
    private static CombatSimulation.Report run(Path csv,String name,int ticks,
            Map<String,String> escort,List<SquadronCommand.AircraftSpec> members) throws Exception {
        return CombatSimulation.run(csv,new CombatSimulation.Scenario(name,members,ticks,
                50,95,escort,FLAT,SquadronCommand.Sensors.DEFAULT));
    }
    private static void oneVsOne(Path csv) throws Exception {
        var a=plane("alpha","a6m","a","first",0,TacticalAirAI.Mission.INTERCEPT,
                null,0,160,0,0,1.3,1);
        var b=plane("bravo","p47n","b","first",0,TacticalAirAI.Mission.INTERCEPT,
                null,0,160,90,180,1.1,1);
        var report=run(csv,"one-v-one",150,Map.of(),List.of(a,b));
        System.out.println("Combat 1v1: "+report.pairs().get(new CombatSimulation.PairKey("alpha","bravo")));
        yes(report.simulatedTicks()==150 && report.timedOut(),"fixed source horizon explicitly times out");
        var pair=report.pairs().get(new CombatSimulation.PairKey("alpha","bravo"));
        yes(pair!=null && pair.closestApproachBlocks()<pair.initialSeparation(),
                "closing maneuver improves closest approach from initial geometry");
        yes(pair.closestTick()>0,"closest approach sampled after start");
        yes(report.units().get("alpha").assignedTicks()>0
                && report.units().get("bravo").assignedTicks()>0,"both locally assign opponent");
        yes(report.units().get("alpha").pathBlocks()>40,"A6M has actual physical movement");
        yes(report.units().get("alpha").groundedTicks()==0,"air fight avoids touchdown");
    }
    private static void twoVsTwo(Path csv) throws Exception {
        var members=List.of(
                plane("a1","a6m","a","patrol",0,TacticalAirAI.Mission.INTERCEPT,
                        null,-35,170,0,0,1.2,1),
                plane("a2","f4u","a","patrol",1,TacticalAirAI.Mission.INTERCEPT,
                        null,35,170,0,0,1.2,1),
                plane("b1","bf109","b","patrol",0,TacticalAirAI.Mission.INTERCEPT,
                        null,-35,170,105,180,1.2,1),
                plane("b2","p47n","b","patrol",1,TacticalAirAI.Mission.INTERCEPT,
                        null,35,170,105,180,1.2,1));
        var baseline=run(csv,"two-v-two",160,Map.of(),members);
        var permuted=new ArrayList<>(members);Collections.reverse(permuted);
        var repeat=run(csv,"two-v-two",160,Map.of(),permuted);
        yes(baseline.equals(repeat),"fully deterministic results under roster reorder");
        yes(baseline.pairs().size()==6,"all 2v2 pairs have separation telemetry");
        yes(baseline.pairs().get(new CombatSimulation.PairKey("a1","a2")).closestApproachBlocks()>6,
                "same-side teammates remain physically distinct");
        yes(baseline.pairs().get(new CombatSimulation.PairKey("a1","b1")).dangerouslyCloseTicks()==0,
                "2v2 head-on aircraft must avoid <6 block body proximity");
        for (var pair : baseline.pairs().values()) {
            yes(pair.closestApproachBlocks() >= 6.0 && pair.dangerouslyCloseTicks() == 0,
                    "ALL 2v2 aircraft pairs must stay >=6 blocks: "+pair);
        }
        yes(baseline.passesSafetyGates() && baseline.failedOperationalGates().isEmpty(),
                "strict 2v2 geometry, separation and terrain safety gates pass");
        yes(baseline.units().get("a1").hostileContactTicks()>0
                && baseline.units().get("b1").hostileContactTicks()>0,
                "each side independently senses a hostile");
        yes(baseline.units().get("a1").groundedTicks()==0,
                "2v2 fighter remains airborne");
        System.out.println("Combat 2v2: a1/b1 "+baseline.pairs().get(new CombatSimulation.PairKey("a1","b1"))
                +", a1/a2 "+baseline.pairs().get(new CombatSimulation.PairKey("a1","a2")));
    }
    private static void escortAndRetreat(Path csv) throws Exception {
        var members=List.of(
                plane("cargo","b17","blue","bomb",0,TacticalAirAI.Mission.LEVEL_BOMB,
                        null,0,170,0,0,0.8,1),
                plane("cover1","f4u","blue","cover",0,TacticalAirAI.Mission.ESCORT,
                        "cargo",-65,190,-20,0,1.0,1),
                plane("cover2","p47n","blue","cover",1,TacticalAirAI.Mission.ESCORT,
                        "cargo",65,190,-20,0,1.0,1),
                plane("raid","a6m","red","raid",0,TacticalAirAI.Mission.INTERCEPT,
                        null,0,170,170,180,1.3,1));
        var result=run(csv,"escort-raid",190,
                Map.of("cover1","cargo","cover2","cargo"),members);
        var asset=result.assets().get("cargo");
        System.out.println("Combat mixed escort: "+asset);
        System.out.println("Combat B17 defensive aborts: "
                +result.units().get("cargo").defensiveAbortTicks());
        yes(asset!=null && Double.isFinite(asset.closestThreatBlocks()),
                "mixed strike/escort tracks enemy proximity to protected bomber");
        yes(asset.escortThreatAssignedTicks()>0,"escort assigned to threat over time");
        yes(asset.corridorBreached() && asset.threatWithinCorridorTicks()>0,
                "intrusion is a measured escort protection failure, even while pilots assign targets");
        yes(asset.threatWithinCorridorTicks()<136 && asset.closestThreatBlocks()>14.46,
                "observed-threat bomber break improves both hostile exposure and closest approach versus pinned earlier source");
        yes(asset.firstEscortAssignmentTick()>0
                && asset.firstEscortAssignmentTick()<asset.firstThreatEntryTick(),
                "assignment starts before perimeter breach; assignment alone cannot guarantee interception");
        yes(result.units().get("cargo").defensiveAbortTicks()>50,
                "early defensive diversion is measured explicitly rather than silently credited as bombing completion");
        yes(!result.passesSafetyGates()
                && result.failedOperationalGates().stream().anyMatch(
                    code -> code.startsWith("ESCORT_PROTECTION_BREACHED:cargo:")),
                "escorted bomber threat inside protection radius remains an explicit FAILED gate");
        yes(result.units().get("cargo").pathBlocks()>30,"bomber travels on mission");
        yes(result.units().get("cargo").finalDistanceToObjective()
                <Math.hypot(280,0),"bomber closes target waypoint distance");
        yes(result.pairs().get(new CombatSimulation.PairKey("cover1","cover2")).closestApproachBlocks()>6,
                "escorts do not occupy same physical location");
        var preparedCover = run(csv,"escort-prepositioned",190,
                Map.of("cover1","cargo","cover2","cargo"),List.of(
                    members.get(0),
                    plane("cover1","f4u","blue","cover",0,TacticalAirAI.Mission.ESCORT,
                            "cargo",-27,190,115,0,1.0,1),
                    plane("cover2","p47n","blue","cover",1,TacticalAirAI.Mission.ESCORT,
                            "cargo",27,190,115,0,1.0,1),
                    members.get(3)));
        var prepared=preparedCover.assets().get("cargo");
        System.out.println("Prepared escort: "+prepared);
        System.out.printf(java.util.Locale.ROOT,
                "ESCORT_ENERGY_SOURCE aft F4U=%.3f P47N=%.3f blocks/s; prepared F4U=%.3f P47N=%.3f blocks/s; guard-pair closest aft=%.3f prepared=%.3f blocks%n",
                result.units().get("cover1").finalSpeedBps(),
                result.units().get("cover2").finalSpeedBps(),
                preparedCover.units().get("cover1").finalSpeedBps(),
                preparedCover.units().get("cover2").finalSpeedBps(),
                result.pairs().get(new CombatSimulation.PairKey("cover1","cover2")).closestApproachBlocks(),
                preparedCover.pairs().get(new CombatSimulation.PairKey("cover1","cover2")).closestApproachBlocks());
        yes(preparedCover.passesSafetyGates() && !prepared.corridorBreached(),
                "advanced fighter screen actually protects the 95-block corridor for the entire scenario");
        yes(prepared.threatWithinCorridorTicks()==0 && prepared.firstThreatEntryTick()==-1
                && prepared.closestThreatBlocks()>95,
                "prepared guards physically hold enemy outside unchanged 95-block perimeter");
        for (var pair : preparedCover.pairs().values())
            yes(pair.closestApproachBlocks()>=6.0 && pair.dangerouslyCloseTicks()==0,
                    "prepared screen does not buy protection through forbidden <6-block body proximity");
        yes(preparedCover.units().get("cargo").groundedTicks()==0
                && preparedCover.units().get("cargo").finalDistanceToObjective()<280,
                "prepared protection preserves actual flight and measurable bomber objective progress");
        yes(preparedCover.units().get("cargo").finalDistanceToObjective()
                    < result.units().get("cargo").finalDistanceToObjective(),
                "prepared interception preserves more mission progress than aft deployment under the same threat");
        var retreat=run(csv,"fuel-withdrawal",50,Map.of(),List.of(
                plane("tired","p47n","blue","solo",0,TacticalAirAI.Mission.INTERCEPT,
                        null,0,160,0,0,1,0.03),
                plane("enemy","a6m","red","solo",0,TacticalAirAI.Mission.INTERCEPT,
                        null,0,160,55,180,1,1)));
        System.out.println("Retreat diagnostics: "+retreat.units().get("tired"));
        yes(retreat.units().get("tired").pathBlocks()>0,"low-fuel aircraft continues physical motion");
        yes(retreat.units().get("tired").withdrawalTicks()>35,
                "measured low-fuel retreat orders persist across actual physical ticks");
        yes(retreat.units().get("tired").groundedTicks()==0,
                "low-fuel pilot attempts airborne withdrawal without touchdown");
        yes(retreat.units().get("tired").assignedTicks()>0,
                "withdrawal doesn't silently delete sensed hostiles");
    }
    private static void invalid(Path csv) throws Exception {
        boolean rejected=false;
        try {
            run(csv,"bad",40,Map.of("fighter","missing"),List.of(
                    plane("fighter","a6m","blue","solo",0,TacticalAirAI.Mission.INTERCEPT,
                            null,0,120,0,0,1,1)));
        } catch (IllegalArgumentException ex){rejected=true;}
        yes(rejected,"invalid protective pair fails closed");
    }
    private static void observedEnemySafety(Path csv) throws Exception {
        var observer=plane("observer","a6m","blue","one",0,
                TacticalAirAI.Mission.INTERCEPT,null,0,160,0,0,1.2,1);
        var hidden=plane("hostile","bf109","red","one",0,
                TacticalAirAI.Mission.INTERCEPT,null,0,160,75,180,1.0,1);
        var blind=SquadronCommand.load(csv,List.of(observer,hidden),FLAT,
                new SquadronCommand.Sensors(45,75,3,9));
        var unseen=blind.advance(blind.start()).commands().get("observer");
        yes(!unseen.observedTargetThisTick() && unseen.threatContactId()==null,
                "out-of-range hostile is not delivered by omniscient world query");
        yes(unseen.safetyClearance().reason()==FlightSafetyPlanner.Reason.CLEAR,
                "unobserved hostile cannot enter source collision avoidance channel");

        var visible=SquadronCommand.load(csv,List.of(observer,hidden),FLAT,
                new SquadronCommand.Sensors(190,150,3,9));
        var detected=visible.advance(visible.start()).commands().get("observer");
        yes(detected.observedTargetThisTick()
                && "hostile".equals(detected.threatContactId()),
                "observed approaching aircraft supplies a real local track");
        yes(detected.safetyClearance().reason()
                        == FlightSafetyPlanner.Reason.MOVING_COLLISION_RISK
                && "hostile".equals(detected.safetyClearance().obstacleId()),
                "visible closing aircraft triggers predictive collision avoidance");
        yes(!detected.decision().firingWindowCandidate(),
                "imminent aircraft collision suppresses advisory fire");

        var entry=AircraftAtlasMain.load(csv).stream()
                .filter(type->type.aircraftId().equals("warfare_wings:a6m"))
                .findFirst().orElseThrow();
        var profile=TacticalAirAI.Profile.fromAtlas(AircraftAtlasMain.evaluate(entry));
        var state=State.airborne(new Vec3(0,160,0),new Vec3(0,0,1));
        var frame=new TacticalAirAI.Frame(profile,entry.model(),state,
                TacticalAirAI.Mission.INTERCEPT,GOAL,HOME,null,null,null,
                1,1,0,false,0);
        var guard=FlightSafetyPlanner.guard(frame,GOAL,
                new FlightSafetyPlanner.Environment((x,z)->0,List.of(
                    new FlightSafetyPlanner.MovingObstacle(
                            "ally",new Vec3(0,165,0),new Vec3(0,0,1),4),
                    new FlightSafetyPlanner.MovingObstacle(
                            "observed-threat",new Vec3(17,160,45),new Vec3(0,0,-1),4,true)),4));
        yes(guard.reason()==FlightSafetyPlanner.Reason.MOVING_COLLISION_RISK
                        && "observed-threat".equals(guard.obstacleId()),
                "mixed ally and observed-hostile risk ranking selects deeper predicted safety breach");

        var bomber=AircraftAtlasMain.load(csv).stream()
                .filter(type->type.aircraftId().equals("warfare_wings:b17"))
                .findFirst().orElseThrow();
        var bomberProfile=TacticalAirAI.Profile.fromAtlas(AircraftAtlasMain.evaluate(bomber));
        var bomberState=State.airborne(new Vec3(0,170,0),new Vec3(0,0,0.8));
        var inbound=new TacticalAirAI.Contact("visible-inbound",new Vec3(0,170,160),
                new Vec3(0,0,-1.3),true);
        var inert=new TacticalAirAI.Contact("visible-but-not-closing",
                inbound.position(),Vec3.ZERO,true);
        var staticThreat=new TacticalAirAI.Frame(bomberProfile,bomber.model(),bomberState,
                TacticalAirAI.Mission.LEVEL_BOMB,GOAL,HOME,inert,null,null,
                1,1,0,false,0);
        var urgentThreat=new TacticalAirAI.Frame(bomberProfile,bomber.model(),bomberState,
                TacticalAirAI.Mission.LEVEL_BOMB,GOAL,HOME,inbound,null,null,
                1,1,0,false,0);
        yes(TacticalAirAI.decide(staticThreat,TacticalAirAI.Memory.INITIAL).maneuver()
                ==TacticalAirAI.Maneuver.LEVEL_BOMB_RUN,
                "stationary contact alone cannot invent an imminent inbound emergency");
        yes(TacticalAirAI.decide(urgentThreat,TacticalAirAI.Memory.INITIAL).maneuver()
                ==TacticalAirAI.Maneuver.DEFENSIVE_BREAK,
                "personally observed, rapidly closing enemy induces a real early bombing abort");
        var depleted=new TacticalAirAI.Frame(bomberProfile,bomber.model(),bomberState,
                TacticalAirAI.Mission.LEVEL_BOMB,GOAL,HOME,inbound,null,null,
                0.04,1,0,false,0);
        yes(TacticalAirAI.decide(depleted,TacticalAirAI.Memory.INITIAL).maneuver()
                ==TacticalAirAI.Maneuver.RETURN_HOME,
                "critical fuel reserve still outranks discretionary observed-threat maneuver");
    }
    private static void everyAtlasAirframe(Path csv) throws Exception {
        var roster=AircraftAtlasMain.load(csv);
        yes(roster.size()==24,"exact source Atlas type count");
        List<SquadronCommand.AircraftSpec> all=new ArrayList<>();
        for (int i=0;i<roster.size();i++) {
            var item=roster.get(i);
            TacticalAirAI.Mission mission=switch(item.role()) {
                case "bomber" -> TacticalAirAI.Mission.LEVEL_BOMB;
                case "torpedo_bomber" -> TacticalAirAI.Mission.TORPEDO;
                case "attacker" -> TacticalAirAI.Mission.STRAFE;
                default -> TacticalAirAI.Mission.PATROL;
            };
            all.add(plane("airframe"+i,item.baseId(),"source","flight"+i,0,
                    mission,null,i*220.0,225,0,0,0.8,1));
        }
        var report=run(csv,"all-24-Atlas-types",55,Map.of(),all);
        yes(report.units().size()==24,"every source aircraft has one diagnostic record");
        yes(report.pairs().size()==276,"24 aircraft have 276 unique separation pairs");
        for (var item : report.units().values()) {
            yes(item.pathBlocks()>3,"real controlled movement for "+item.id());
            yes(item.groundedTicks()==0,"source aircraft airborne "+item.id());
            yes(item.minTerrainClearance()>100,"high-altitude safe clearance "+item.id());
        }
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=1)throw new IllegalArgumentException("anchor CSV required");
        Path csv=Path.of(args[0]);
        oneVsOne(csv);twoVsTwo(csv);escortAndRetreat(csv);invalid(csv);
        observedEnemySafety(csv);
        everyAtlasAirframe(csv);
        System.out.println("CombatSimulationSelfTest PASS: "+checks
                +" assertions, source-only 1v1/2v2/mixed escort/retreat; NO_HITS_NO_KILLS");
    }
}
