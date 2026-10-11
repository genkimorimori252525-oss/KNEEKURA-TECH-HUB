package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
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
        // Source V3 exact engine-response 2v2 is a distinct physical model,
        // with the identical roster, start velocities and unmodified 6-block
        // body safety gate. Do not claim a kill or actual Minecraft battle.
        var reaction2v2 = CombatSimulation.runWithExactReaction(csv,
                new CombatSimulation.Scenario("two-v-two-original-reaction",
                        members,160,50,95,Map.of(),FLAT,SquadronCommand.Sensors.DEFAULT));
        var repeatReaction2v2 = CombatSimulation.runWithExactReaction(csv,
                new CombatSimulation.Scenario("two-v-two-original-reaction",
                        permuted,160,50,95,Map.of(),FLAT,SquadronCommand.Sensors.DEFAULT));
        yes(reaction2v2.equals(repeatReaction2v2),
                "exact-response 2v2 still deterministic under inverted roster");
        for(var pair: reaction2v2.pairs().values())
            yes(pair.closestApproachBlocks()>=6.0 && pair.dangerouslyCloseTicks()==0,
                    "EXACT ENGINE SOURCE MODE 2v2 <6-block danger FAILED: "+pair);
        yes(reaction2v2.passesSafetyGates(),
                "exact-response 2v2 strict operational airframe separation");
        double minExactPair = reaction2v2.pairs().values().stream()
                .mapToDouble(CombatSimulation.PairMetric::closestApproachBlocks)
                .min().orElseThrow();
        System.out.printf(java.util.Locale.ROOT,
                "EXACT_REACTION_2V2_ALL_PAIR_MIN=%.9f blocks / 6 pairs / <6: zero%n",
                minExactPair);
        System.out.println("Exact-reaction SOURCE 2v2: "
                +reaction2v2.pairs().get(new CombatSimulation.PairKey("a1","b1")));
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
        var reactionEscort = CombatSimulation.runWithExactReaction(csv,
                new CombatSimulation.Scenario("escort-raid-reaction-v3",
                        members,190,50,95,Map.of("cover1","cargo","cover2","cargo"),
                        FLAT,SquadronCommand.Sensors.DEFAULT));
        var responseAsset=reactionEscort.assets().get("cargo");
        yes(responseAsset != null
                        && (responseAsset.threatWithinCorridorTicks()>0)==responseAsset.corridorBreached(),
                "original-reaction source escort objective is evaluated by unchanged 95-block radius");
        yes(responseAsset.corridorBreached()==
                        reactionEscort.failedOperationalGates().stream().anyMatch(
                            s -> s.startsWith("ESCORT_PROTECTION_BREACHED:cargo:")),
                "exact-response failed escort is NEVER disguised as a source PASS");
        yes(!reactionEscort.passesSafetyGates() && responseAsset.threatWithinCorridorTicks()>0,
                "original aft start MUST remain operationally FAILED while any attacker enters 95b");
        yes(responseAsset.threatWithinCorridorTicks()<92
                        && responseAsset.closestThreatBlocks()>40.913,
                "unchanged original exact-response physical setup improves both exposure and distance vs HEAD 0cd4aaa");
        yes(responseAsset.threatWithinCorridorTicks()<=54
                        && responseAsset.closestThreatBlocks()>81.90,
                "new observed-only escort diversion improves original unchanged rear V3 55tick/81.231b failure without disguising the breach");
        for(var pair:reactionEscort.pairs().values())
            yes(pair.closestApproachBlocks()>=6.0 && pair.dangerouslyCloseTicks()==0,
                    "improved aft escort never trades 6b body separation for protection: "+pair);
        System.out.println("Exact-reaction SOURCE B17 escort: "+responseAsset
                +" operationalFailed="+!reactionEscort.passesSafetyGates());
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
        var reactionPrepared = CombatSimulation.runWithExactReaction(csv,
                new CombatSimulation.Scenario("escort-prepositioned-exact-reaction",
                        List.of(members.get(0),
                            plane("cover1","f4u","blue","cover",0,TacticalAirAI.Mission.ESCORT,
                                    "cargo",-27,190,115,0,1.0,1),
                            plane("cover2","p47n","blue","cover",1,TacticalAirAI.Mission.ESCORT,
                                    "cargo",27,190,115,0,1.0,1),
                            members.get(3)),
                        190,50,95,Map.of("cover1","cargo","cover2","cargo"),
                        FLAT,SquadronCommand.Sensors.DEFAULT));
        var reactionPreparedAsset = reactionPrepared.assets().get("cargo");
        yes(reactionPreparedAsset!=null && reactionPreparedAsset.corridorBreached()
                == (reactionPreparedAsset.threatWithinCorridorTicks()>0),
                "exact-reaction prepared screen must report unchanged 95-block violation honestly");
        yes(reactionPrepared.passesSafetyGates()
                        && reactionPrepared.failedOperationalGates().isEmpty(),
                "forward V3 source physically protects original 95b perimeter without reducing safety gate");
        yes(reactionPreparedAsset.threatWithinCorridorTicks()==0
                        && reactionPreparedAsset.firstThreatEntryTick()==-1
                        && reactionPreparedAsset.closestThreatBlocks()>95.0,
                "forward V3 reaches original protection requirement by real climb and lateral flight");
        yes(reactionPreparedAsset.closestThreatBlocks()>98.570,
                "original prepared 0/190 protection retains the previous 98.570b closest-threat margin");
        yes(reactionPrepared.units().get("cargo").groundedTicks()==0
                        && reactionPrepared.units().get("cargo").pathBlocks()>20
                        && reactionPrepared.units().get("cargo").finalDistanceToObjective()<280,
                "successful V3 forward cover is achieved by physically flying a progressing B17, not freezing it");
        yes(reactionPrepared.units().get("cargo").defensiveAbortTicks()>20,
                "forward V3 physical protection involves actual observed-threat evasive decisions");
        for (var pair : reactionPrepared.pairs().values())
            yes(pair.closestApproachBlocks() >= 6.0 && pair.dangerouslyCloseTicks() == 0,
                    "exact-reaction prepared screen cannot trade real body safety for protection");
        System.out.println("EXACT_REACTION_PREPARED_ESCORT "
                +reactionPreparedAsset+" failedGates="+reactionPrepared.failedOperationalGates());
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
        var patrolUrgent=new TacticalAirAI.Frame(bomberProfile,bomber.model(),bomberState,
                TacticalAirAI.Mission.PATROL,GOAL,HOME,inbound,null,null,
                1,1,0,false,0);
        var patrolIdle=new TacticalAirAI.Frame(bomberProfile,bomber.model(),bomberState,
                TacticalAirAI.Mission.PATROL,GOAL,HOME,inert,null,null,
                1,1,0,false,0);
        yes(TacticalAirAI.decide(patrolUrgent,TacticalAirAI.Memory.INITIAL).maneuver()
                ==TacticalAirAI.Maneuver.DEFENSIVE_BREAK,
                "real Forge B17 PATROL mission defends itself against individually observed inbound aircraft");
        yes(!TacticalAirAI.decide(patrolIdle,TacticalAirAI.Memory.INITIAL).reasonCode()
                    .equals("BOMBER_OBSERVED_INBOUND_ABORT"),
                "inert observed contact cannot trigger the new imminent-attack maneuver");
        var patrolUnseen=new TacticalAirAI.Frame(bomberProfile,bomber.model(),bomberState,
                TacticalAirAI.Mission.PATROL,GOAL,HOME,null,null,null,
                1,1,0,false,0);
        yes(TacticalAirAI.decide(patrolUnseen,TacticalAirAI.Memory.INITIAL).maneuver()
                ==TacticalAirAI.Maneuver.PATROL_ROUTE,
                "unobserved opponent cannot provoke the B17 into omniscient evasion");
        var patrolFuelCritical=new TacticalAirAI.Frame(bomberProfile,bomber.model(),bomberState,
                TacticalAirAI.Mission.PATROL,GOAL,HOME,inbound,null,null,
                0.04,1,0,false,0);
        yes(TacticalAirAI.decide(patrolFuelCritical,TacticalAirAI.Memory.INITIAL).maneuver()
                ==TacticalAirAI.Maneuver.RETURN_HOME,
                "patrol bomber observed defense never defeats critical-fuel withdrawal");

        // Future protectee position is extrapolated exclusively from an allied
        // aircraft's measured velocity, not from global unseen enemy state.
        var fighter=AircraftAtlasMain.load(csv).stream()
                .filter(type->type.aircraftId().equals("warfare_wings:f4u"))
                .findFirst().orElseThrow();
        var fighterProfile=TacticalAirAI.Profile.fromAtlas(AircraftAtlasMain.evaluate(fighter));
        var fighterState=State.airborne(new Vec3(-40,190,0),new Vec3(0,0,0.8));
        var contact=new TacticalAirAI.Contact("personally-sensed-raid",
                new Vec3(0,170,150),new Vec3(0,0,-1),true);
        var assetPosition=new Vec3(0,170,0);
        var stationaryAsset=new TacticalAirAI.Frame(fighterProfile,fighter.model(),
                fighterState,TacticalAirAI.Mission.ESCORT,GOAL,HOME,contact,
                assetPosition,null,1,1,0,false,0);
        var advancingAsset=new TacticalAirAI.Frame(fighterProfile,fighter.model(),
                fighterState,TacticalAirAI.Mission.ESCORT,GOAL,HOME,contact,
                assetPosition,null,1,1,0,false,0,new Vec3(0,0,0.4));
        var wait=TacticalAirAI.decide(stationaryAsset,TacticalAirAI.Memory.INITIAL);
        var lead=TacticalAirAI.decide(advancingAsset,TacticalAirAI.Memory.INITIAL);
        yes(wait.maneuver()==TacticalAirAI.Maneuver.ESCORT_SCREEN
                    && lead.maneuver()==TacticalAirAI.Maneuver.ESCORT_SCREEN,
                "future allied velocity only changes a valid escort waypoint, not the fighter role");
        yes(lead.steeringPoint().add(wait.steeringPoint().scale(-1)).length()>8.0,
                "observed protectee motion materially shifts the physically commanded defense point");
        yes(lead.steeringPoint().z()>wait.steeringPoint().z(),
                "advancing protected aircraft requires a correspondingly forward predictive screen");
    }
    private static void observedCrossingIntercept(Path csv) throws Exception {
        var fighter=AircraftAtlasMain.load(csv).stream()
                .filter(type->type.aircraftId().equals("warfare_wings:spitfire"))
                .findFirst().orElseThrow();
        var profile=TacticalAirAI.Profile.fromAtlas(AircraftAtlasMain.evaluateReaction(fighter));
        var current=State.airborne(new Vec3(0,170,0),new Vec3(0,0,2.0));
        var crossing=new TacticalAirAI.Contact("crossing-observed-only",
                new Vec3(30,170,0),new Vec3(0,0,.5),true);
        var frame=new TacticalAirAI.Frame(profile,fighter.model(),current,
                TacticalAirAI.Mission.INTERCEPT,GOAL,HOME,crossing,null,null,
                1,1,0,false,0);
        var predicted=TacticalAirAI.leadPoint(frame,crossing,2.0);
        double crossingTime=30.0/Math.sqrt(2.0*2.0-.5*.5);
        yes(Math.abs(predicted.x()-30.0)<1e-9
                        && Math.abs(predicted.z()-.5*crossingTime)<1e-9,
                "crossing pursuit uses the real relative quadratic intercept, not range/sum-of-speeds");
        yes(Math.abs(predicted.z()-.5*(30.0/(2.0+.5)))>1.5,
                "crossing intercept materially differs from the old straight-line closure heuristic");
        var uncatchable=new TacticalAirAI.Contact("observed-faster-departing",
                new Vec3(0,170,50),new Vec3(0,0,3),true);
        var fallback=TacticalAirAI.leadPoint(frame,uncatchable,1.0);
        yes(Math.abs(fallback.z()-87.5)<1e-9,
                "unreachable faster target uses finite bounded pursuit lead rather than a false root");
        var farCrossing=new TacticalAirAI.Contact("observed-distant-crossing",
                new Vec3(120,170,0),new Vec3(0,0,1),true);
        var bounded=TacticalAirAI.leadPoint(frame,farCrossing,2.0);
        yes(bounded.z()==30.0,
                "observed-track crossing extrapolation is capped at thirty physics ticks");
        var coincident=new TacticalAirAI.Contact("observed-coincident",current.position(),
                new Vec3(0,0,2),true);
        yes(TacticalAirAI.leadPoint(frame,coincident,2.0).equals(current.position()),
                "zero-range observed track avoids a degenerate quadratic and has a finite steering point");
        var unseen=new TacticalAirAI.Frame(profile,fighter.model(),current,
                TacticalAirAI.Mission.PATROL,GOAL,HOME,null,null,null,
                1,1,0,false,0);
        yes(TacticalAirAI.decide(unseen,TacticalAirAI.Memory.INITIAL).maneuver()
                        == TacticalAirAI.Maneuver.PATROL_ROUTE,
                "intercept prediction cannot steer toward an opponent missing from the local sensor track");
    }
    private static void observedEscortDrag(Path csv) throws Exception {
        var fighter=AircraftAtlasMain.load(csv).stream()
                .filter(type->type.aircraftId().equals("warfare_wings:p47n"))
                .findFirst().orElseThrow();
        var profile=TacticalAirAI.Profile.fromAtlas(AircraftAtlasMain.evaluateReaction(fighter));
        Vec3 escortPosition=new Vec3(-35,195,60), protecteePosition=new Vec3(0,170,0);
        var state=State.airborne(escortPosition,new Vec3(0,0,.8));
        var incoming=new TacticalAirAI.Contact("individually-observed-inbound",
                new Vec3(-35,195,100),new Vec3(0,0,-1),true);
        var frame=new TacticalAirAI.Frame(profile,fighter.model(),state,
                TacticalAirAI.Mission.ESCORT,GOAL,HOME,incoming,protecteePosition,
                null,1,1,0,false,0,new Vec3(0,0,.4));
        var decision=TacticalAirAI.decide(frame,TacticalAirAI.Memory.INITIAL);
        yes(decision.maneuver()==TacticalAirAI.Maneuver.ESCORT_SCREEN
                        && decision.reasonCode().equals("ESCORT_OBSERVED_CONTACT_OUTBOUND_DRAG"),
                "escort diverts only when its own observed enemy track is close and closing");
        Vec3 vector=decision.steeringPoint().add(escortPosition.scale(-1));
        Vec3 outbound=escortPosition.add(protecteePosition.scale(-1)).normalize();
        yes(vector.dot(outbound)>0,
                "contact-avoidance tangent must have outward component from actual allied protectee");
        yes(Math.abs(vector.length()-155)<1e-9,
                "escape waypoint remains a bounded 155-block navigation request, not physical displacement");
        yes(!decision.firingWindowCandidate()
                        && Double.isFinite(decision.controls().x())
                        && Double.isFinite(decision.controls().z()),
                "tangential escort only produces finite IA steering inputs, never fired weapons");

        var departing=new TacticalAirAI.Contact("observed-departing",incoming.position(),
                new Vec3(0,0,1.2),true);
        var outgoingFrame=new TacticalAirAI.Frame(profile,fighter.model(),state,
                TacticalAirAI.Mission.ESCORT,GOAL,HOME,departing,protecteePosition,
                null,1,1,0,false,0,new Vec3(0,0,.4));
        yes(!TacticalAirAI.decide(outgoingFrame,TacticalAirAI.Memory.INITIAL)
                        .reasonCode().equals("ESCORT_OBSERVED_CONTACT_OUTBOUND_DRAG"),
                "an individually observed enemy moving away cannot falsely trigger inbound defensive drag");
        var edge=new TacticalAirAI.Contact("exact-contact-limit",
                new Vec3(-35,195,108),incoming.velocity(),true);
        var limit=new TacticalAirAI.Frame(profile,fighter.model(),state,
                TacticalAirAI.Mission.ESCORT,GOAL,HOME,edge,protecteePosition,
                null,1,1,0,false,0,new Vec3(0,0,.4));
        yes(!TacticalAirAI.decide(limit,TacticalAirAI.Memory.INITIAL)
                        .reasonCode().equals("ESCORT_OBSERVED_CONTACT_OUTBOUND_DRAG"),
                "farther contacts retain the outward predictive screen without premature evasive break");
        var unseen=new TacticalAirAI.Frame(profile,fighter.model(),state,
                TacticalAirAI.Mission.ESCORT,GOAL,HOME,null,protecteePosition,
                null,1,1,0,false,0,new Vec3(0,0,.4));
        yes(!TacticalAirAI.decide(unseen,TacticalAirAI.Memory.INITIAL)
                        .reasonCode().equals("ESCORT_OBSERVED_CONTACT_OUTBOUND_DRAG"),
                "no detected enemy cannot trigger an omniscient escort-contact drag");
        var fuelEmergency=new TacticalAirAI.Frame(profile,fighter.model(),state,
                TacticalAirAI.Mission.ESCORT,GOAL,HOME,incoming,protecteePosition,
                null,.02,1,0,false,0,new Vec3(0,0,.4));
        yes(TacticalAirAI.decide(fuelEmergency,TacticalAirAI.Memory.INITIAL).maneuver()
                        ==TacticalAirAI.Maneuver.RETURN_HOME,
                "critical fuel withdrawal outranks even an imminent escort-contact diversion");

        var distant=new TacticalAirAI.Contact("observed-not-imminent",
                new Vec3(-35,195,150),new Vec3(0,0,-1),true);
        var spoolingFrame=new TacticalAirAI.Frame(profile,fighter.model(),state,
                TacticalAirAI.Mission.ESCORT,GOAL,HOME,distant,protecteePosition,
                null,1,1,0,false,0,new Vec3(0,0,.4));
        var upToPower=new State(0,state.position(),state.velocity(),0,0,0,
                0,0,0,0,0,0,1,.4,1,0,false,false);
        var powerReadyFrame=new TacticalAirAI.Frame(profile,fighter.model(),upToPower,
                TacticalAirAI.Mission.ESCORT,GOAL,HOME,distant,protecteePosition,
                null,1,1,0,false,0,new Vec3(0,0,.4));
        var spooling=TacticalAirAI.decide(spoolingFrame,TacticalAirAI.Memory.INITIAL);
        var powered=TacticalAirAI.decide(powerReadyFrame,TacticalAirAI.Memory.INITIAL);
        yes(spooling.reasonCode().equals("ESCORT_PREDICTIVE_SCREEN")
                        && powered.reasonCode().equals("ESCORT_PREDICTIVE_SCREEN"),
                "known hostile outside the diversion window retains normal escort protection");
        yes(Math.abs(powered.steeringPoint().y()-spooling.steeringPoint().y()-50)<1e-9,
                "observed source-engine spool controls the bounded early descending screen only");
    }
    private static void everyAtlasAirframe(Path csv) throws Exception {
        var roster=AircraftAtlasMain.load(csv);
        yes(roster.size()==24,"exact source Atlas type count");
        Set<String> airframeTypes=new HashSet<>();
        List<SquadronCommand.AircraftSpec> all=new ArrayList<>();
        for (int i=0;i<roster.size();i++) {
            var item=roster.get(i);
            yes(airframeTypes.add(item.aircraftId()),"all 24 aircraft keep distinct Atlas identities");
            TacticalAirAI.Mission mission=switch(item.role()) {
                case "bomber" -> TacticalAirAI.Mission.LEVEL_BOMB;
                case "torpedo_bomber" -> TacticalAirAI.Mission.TORPEDO;
                case "attacker" -> TacticalAirAI.Mission.STRAFE;
                default -> TacticalAirAI.Mission.PATROL;
            };
            all.add(plane("airframe"+i,item.baseId(),"source","flight"+i,0,
                    mission,null,i*220.0,225,0,0,0.8,1));
        }
        for (String key : List.of("a6m","p47n","spitfire","il2","b17"))
            yes(airframeTypes.contains("warfare_wings:"+key),
                    "essential historical fighter, attack and bomber roles remain in the Atlas: "+key);
        var report=run(csv,"all-24-Atlas-types",55,Map.of(),all);
        yes(report.units().size()==24,"every source aircraft has one diagnostic record");
        yes(report.pairs().size()==276,"24 aircraft have 276 unique separation pairs");
        for (var item : report.units().values()) {
            yes(item.pathBlocks()>3,"real controlled movement for "+item.id());
            yes(item.groundedTicks()==0,"source aircraft airborne "+item.id());
            yes(item.minTerrainClearance()>100,"high-altitude safe clearance "+item.id());
        }
        var exact=CombatSimulation.runWithExactReaction(csv,
                new CombatSimulation.Scenario("exact-engine-all-24-aircraft",
                        all,55,50,95,Map.of(),FLAT,SquadronCommand.Sensors.DEFAULT));
        yes(exact.units().size()==24 && exact.pairs().size()==276,
                "every Atlas airframe runs the exact-WW source engine response with all 276 pairs");
        yes(exact.passesSafetyGates(),
                "spaced 24-plane exact-response mission has no source body or ground failures");
        for(var item:exact.units().values()) {
            yes(item.pathBlocks()>3,"V3 controls truly advance "+item.id());
            yes(item.groundedTicks()==0 && item.minTerrainClearance()>100,
                    "V3 all-airframe physical terrain clearance "+item.id());
        }
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=1)throw new IllegalArgumentException("anchor CSV required");
        Path csv=Path.of(args[0]);
        oneVsOne(csv);twoVsTwo(csv);escortAndRetreat(csv);invalid(csv);
        observedEnemySafety(csv);
        observedCrossingIntercept(csv);
        observedEscortDrag(csv);
        everyAtlasAirframe(csv);
        System.out.println("CombatSimulationSelfTest PASS: "+checks
                +" assertions, source-only 1v1/2v2/mixed escort/retreat; NO_HITS_NO_KILLS");
    }
}
