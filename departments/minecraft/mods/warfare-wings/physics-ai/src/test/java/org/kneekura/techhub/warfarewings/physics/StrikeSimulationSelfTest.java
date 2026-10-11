package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

public final class StrikeSimulationSelfTest {
    private static int checks;
    private StrikeSimulationSelfTest() {}
    private static void yes(boolean condition,String detail) {
        checks++;if(!condition)throw new AssertionError(detail);
    }
    private static StrikeSimulation.Report fly(Path atlas,String id,String type,
            TacticalAirAI.Mission mission,double altitude,double distance,
            double speed,int ticks) throws Exception {
        return StrikeSimulation.run(atlas,new StrikeSimulation.Plan(id,
                "warfare_wings:"+type,mission,
                new Vec3(0,altitude,0),new Vec3(0,0,speed),0,
                new Vec3(0,mission==TacticalAirAI.Mission.TORPEDO?0:0,distance),
                new Vec3(0,altitude,-200),0,new FlatWorld(0),ticks,
                StrikeSimulation.Geometry.LAB));
    }
    private static void bombing(Path atlas) throws Exception {
        var result=fly(atlas,"b17-level","b17",TacticalAirAI.Mission.LEVEL_BOMB,170,145,.9,680);
        System.out.println("Strike B17: window="+result.firstWindowTick()
                +" crossing="+result.crossedTargetPlaneTick()
                +" minAGL="+result.minTerrainClearance()+" phase="+result.terminalPhase()
                +" phases="+result.phaseTicks());
        yes(result.ticks()>10,"bomber advances clock");
        yes(result.minTerrainClearance()>0,"level bombing stays above ground");
        yes(result.closestHorizontalToStrike()<145,"actual bomber closes horizontal target distance");
        yes(result.windowTicks()>0 && result.firstWindowTick()>0,
                "level bomber has source-geometric attack approach window");
        yes(result.crossedTargetPlaneTick()>result.firstWindowTick(),
                "actual aircraft crosses geometric target plane after entering approach window");
        yes(result.lateralAtCrossing()<=StrikeSimulation.Geometry.LAB.lateralRadius(),
                "level bomber crosses target plane within horizontal track corridor");
        yes(result.phaseTicks().getOrDefault(StrikeSimulation.Phase.EGRESS,0)>0
                && result.phaseTicks().getOrDefault(StrikeSimulation.Phase.RETURN_HOME,0)>0,
                "level bomber leaves window and receives a homeward navigation phase");
        yes(result.timedOut() && result.firstHomeTick()==-1,
                "uncompleted long return is explicitly timed out, not declared success");
        yes(result.groundTouchTicks()==0,"level bomber avoids touchdown");
        yes(result.evidence().contains("NO_RELEASE_NO_HITS"),"no claimed simulated weapon damage");
    }
    private static void torpedo(Path atlas) throws Exception {
        var result=fly(atlas,"g4m-sea","g4m",TacticalAirAI.Mission.TORPEDO,30,160,.9,680);
        System.out.println("Strike G4M: window="+result.firstWindowTick()
                +" minSea="+result.minSeaSurfaceClearance()
                +" minHorizontal="+result.closestHorizontalToStrike()+" phases="+result.phaseTicks());
        yes(result.minTerrainClearance()>0,"sea level protection, no forced water collision");
        yes(result.minSeaSurfaceClearance()>0,"water clearance is observed separately");
        yes(result.closestHorizontalToStrike()<160,"torpedo craft reaches closer approach");
        yes(result.windowTicks()>0,"torpedo window valid in experimental above-sea band");
        yes(result.crossedTargetPlaneTick()>0
                && result.lateralAtCrossing()<=StrikeSimulation.Geometry.LAB.lateralRadius(),
                "torpedo craft crosses intended waypoint corridor with measured lateral error");
        yes(result.phaseTicks().getOrDefault(StrikeSimulation.Phase.RETURN_HOME,0)>0,
                "torpedo pilot receives return-to-home control after crossing");
        yes(result.timedOut() && result.firstHomeTick()==-1,
                "torpedo flight does not mislabel incomplete return as mission accomplished");
    }
    private static void dive(Path atlas) throws Exception {
        var result=fly(atlas,"ju87-dive","ju87",TacticalAirAI.Mission.DIVE_BOMB,150,150,.9,520);
        System.out.println("Strike Ju87: pullout="+result.firstPullOutTick()
                +" recovered="+result.recoveredPullOutTick()
                +" minAGL="+result.minTerrainClearance()+" phase="+result.terminalPhase());
        yes(result.firstPullOutTick()>0,"dive must enter controlled pull-out phase");
        yes(result.groundTouchTicks()==0,"Ju87 avoids touchdown during pull-out window");
        yes(result.minTerrainClearance()>40,"dive pull-out maintains measured margin above 40 blocks");
        yes(result.recoveredPullOutTick()>result.firstPullOutTick(),
                "actual climbing recovery measured after dive pull-out");
        yes(result.finalState().position().y()>StrikeSimulation.Geometry.LAB.divePullOutAgl(),
                "actual final altitude clears pullout engineering margin");
        yes(result.firstWindowTick()==-1,
                "early dive abort does not fabricate a weapon approach window");
    }
    private static void boundedTimeout(Path atlas) throws Exception {
        var shortRun=fly(atlas,"timeout","b17",TacticalAirAI.Mission.LEVEL_BOMB,160,650,.9,12);
        yes(shortRun.timedOut() && shortRun.terminalPhase()==StrikeSimulation.Phase.TIMEOUT,
                "short horizon is a timeout, not fictional mission victory");
        yes(shortRun.firstWindowTick()==-1,"distant target does not earn attack window");
        yes(shortRun.crossedTargetPlaneTick()==-1,"cannot cross target plane after only 12 ticks");
    }
    private static void longReturnDiagnostic(Path atlas) throws Exception {
        var b17=fly(atlas,"b17-extended","b17",TacticalAirAI.Mission.LEVEL_BOMB,170,145,.9,2400);
        var g4m=fly(atlas,"g4m-extended","g4m",TacticalAirAI.Mission.TORPEDO,30,160,.9,2400);
        System.out.println("STRIKE_LONG_RTB B17: phase="+b17.terminalPhase()
                +" tick="+b17.ticks()+" homeTick="+b17.firstHomeTick()
                +" finalDistance="+b17.distanceToHome()+" terrainTouch="+b17.groundTouchTicks());
        System.out.println("STRIKE_LONG_RTB G4M: phase="+g4m.terminalPhase()
                +" tick="+g4m.ticks()+" homeTick="+g4m.firstHomeTick()
                +" finalDistance="+g4m.distanceToHome()+" terrainTouch="+g4m.groundTouchTicks());
        yes(b17.terminalPhase()==StrikeSimulation.Phase.COMPLETE
                && g4m.terminalPhase()==StrikeSimulation.Phase.COMPLETE
                && !b17.timedOut() && !g4m.timedOut(),
                "extended duration produces actual observed home arrival for both strike types");
        yes(b17.firstHomeTick()==b17.ticks() && g4m.firstHomeTick()==g4m.ticks(),
                "home arrival event is recorded on the actual physical tick");
        yes(b17.distanceToHome()<=StrikeSimulation.Geometry.LAB.homeRadius()
                && g4m.distanceToHome()<=StrikeSimulation.Geometry.LAB.homeRadius(),
                "both aircraft physically enter unmodified configured 45-block home radius");
        yes(b17.groundTouchTicks()==0 && g4m.groundTouchTicks()==0,
                "extended attack-to-return flight has no ground contact");
        yes(b17.phaseTicks().containsKey(StrikeSimulation.Phase.EGRESS)
                && g4m.phaseTicks().containsKey(StrikeSimulation.Phase.EGRESS)
                && b17.phaseTicks().containsKey(StrikeSimulation.Phase.RETURN_HOME)
                && g4m.phaseTicks().containsKey(StrikeSimulation.Phase.RETURN_HOME),
                "real source ticks include the outbound egress and actual homeward flight phases");
    }
    private static void integratedSquadronReturn(Path atlas) throws Exception {
        World sameWorld = new FlatWorld(0);
        Vec3 takeoff=new Vec3(0,170,0), goal=new Vec3(0,0,145);
        Vec3 home=new Vec3(0,170,-200);
        Vec3 velocity=new Vec3(0,0,0.9);
        var bomber=new SquadronCommand.AircraftSpec("bomber",
                "warfare_wings:b17","blue","bombers",0,
                TacticalAirAI.Mission.LEVEL_BOMB,null,null,
                takeoff,velocity,0,goal,home,1,1,0);
        var escortA=new SquadronCommand.AircraftSpec("escortA",
                "warfare_wings:f4u","blue","guards",0,
                TacticalAirAI.Mission.ESCORT,"bomber",null,
                new Vec3(-65,190,45),new Vec3(0,0,1),0,goal,home,1,1,0);
        var escortB=new SquadronCommand.AircraftSpec("escortB",
                "warfare_wings:p47n","blue","guards",1,
                TacticalAirAI.Mission.ESCORT,"bomber",null,
                new Vec3(65,190,45),new Vec3(0,0,1),0,goal,home,1,1,0);
        var scenario=new CombatSimulation.Scenario("actual-squadron-strike",
                List.of(bomber,escortA,escortB),1600,50,95,
                Map.of("escortA","bomber","escortB","bomber"),
                sameWorld,SquadronCommand.Sensors.DEFAULT);
        var plan=new StrikeSimulation.Plan("inside-squadron",
                bomber.aircraftTypeId(),bomber.mission(),takeoff,velocity,0,
                goal,home,0,sameWorld,1600,StrikeSimulation.Geometry.LAB);
        var outcome=CombatSimulation.runWithStrikePlans(atlas,scenario,Map.of("bomber",plan));
        var phase=outcome.strikeStates().get("bomber");
        System.out.println("STRIKE_SQUADRON phase="+phase.phase()
                +" window="+phase.firstWindowTick()
                +" crossing="+phase.crossedTargetTick()
                +" RTB="+phase.reachedHomeTick()
                +" stages="+phase.phaseTicks()
                +" safety="+outcome.combat().failedOperationalGates());
        yes(outcome.combat().simulatedTicks()==1600
                && outcome.combat().units().size()==3,
                "strike bomber and both guards share one 1600-tick physical snapshot");
        yes(phase.firstWindowTick()>0 && phase.crossedTargetTick()>phase.firstWindowTick(),
                "shared-source bomber detects a physically crossed attack waypoint");
        yes(phase.phaseTicks().getOrDefault(StrikeSimulation.Phase.EGRESS,0)>0
                && phase.phaseTicks().getOrDefault(StrikeSimulation.Phase.RETURN_HOME,0)>0,
                "shared mission controller issues real egress and homeward pilot commands");
        yes(phase.phase()==StrikeSimulation.Phase.COMPLETE
                    && phase.reachedHomeTick()>phase.crossedTargetTick()
                    && phase.reachedHomeTick()<1600,
                "same physically flown escorted bomber reaches home after attack crossing");
        yes(outcome.combat().units().get("bomber").groundedTicks()==0,
                "joined bomber remains airborne throughout measured integration");
        yes(outcome.combat().passesSafetyGates()
                    && outcome.combat().failedOperationalGates().isEmpty(),
                "no hostile plus two actual physical escorts maintain unchanged body-safety gates");
        for (var pair : outcome.combat().pairs().values())
            yes(pair.closestApproachBlocks()>=6 && pair.dangerouslyCloseTicks()==0,
                    "joined bomber and escorts never occupy the same six-block collision envelope");
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=1)throw new IllegalArgumentException("anchor CSV required");
        Path atlas=Path.of(args[0]);
        bombing(atlas);torpedo(atlas);dive(atlas);boundedTimeout(atlas);longReturnDiagnostic(atlas);
        integratedSquadronReturn(atlas);
        System.out.println("StrikeSimulationSelfTest PASS: "+checks+" assertions, geometric phases only");
    }
}
