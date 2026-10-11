package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
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
    public static void main(String[] args) throws Exception {
        if(args.length!=1)throw new IllegalArgumentException("anchor CSV required");
        Path atlas=Path.of(args[0]);
        bombing(atlas);torpedo(atlas);dive(atlas);boundedTimeout(atlas);
        System.out.println("StrikeSimulationSelfTest PASS: "+checks+" assertions, geometric phases only");
    }
}
