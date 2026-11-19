package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.HashSet;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/** Pure-Java original-IA wind contracts. SOURCE tests, never runtime parity. */
public final class PinnedIa133WindSelfTest {
    private static int checks;
    private PinnedIa133WindSelfTest() {}

    private static void yes(boolean condition, String explanation) {
        checks++;
        if (!condition) throw new AssertionError(explanation);
    }

    private static void near(double actual, double expected, double tolerance, String explanation) {
        yes(Double.isFinite(actual) && Math.abs(actual - expected) <= tolerance,
                explanation + " actual=" + actual + " expected=" + expected);
    }

    private static State start() {
        return new State(0,new Vec3(0,200,0),new Vec3(0,0,.7),
                0,0,0,0,0,0,0,0,0,1,0,1,0,false,false);
    }

    public static void main(String[] args) throws Exception {
        if (args.length!=1) throw new IllegalArgumentException("Usage: PinnedIa133WindSelfTest EXACT_SOURCE_ANCHOR");
        near(PinnedIa133WindWorld.cosNoise(0),5,0,"Pinned Utils.cosNoise(0) 5 harmonics");
        double argument=1.25;
        double explicit=0;
        for(int i=0;i<5;i++) {explicit+=Math.cos(argument);argument*=1.3;}
        near(PinnedIa133WindWorld.cosNoise(1.25),explicit,0,"Bytecode five harmonic sum");

        var world=PinnedIa133WindWorld.calmAirCalibration();
        var b17=AircraftAtlasMain.load(Path.of(args[0])).stream()
                .filter(e->e.aircraftId().equals("warfare_wings:b17")).findFirst().orElseThrow().model();
        Wind wind=world.windAfterFriction(b17,start(),new Vec3(0,0,.669));
        yes(wind.pitchDeltaDeg()>0.020 && wind.yawDeltaDeg()>0.020,
                "zero WEATHER wind does not suppress original aircraft-speed wind");
        State realSourceStep=tickWithReaction(b17,start(),Control.neutral(1),world,
                WarfareWingsEngineReaction.ticks(b17.id()));
        near(realSourceStep.yawDeg(),0.02006419003,1e-5,
                "Pinned B17 original-Forge first step yaw sample (independent measured reference)");
        near(realSourceStep.pitchDeg(),0.020064163953,1e-5,
                "Pinned B17 original-Forge first step pitch sample (independent measured reference)");
        State legacy=tickWithReaction(b17,start(),Control.neutral(1),new FlatWorld(0),150);
        yes(Math.abs(legacy.yawDeg())<1e-12 && realSourceStep.yawDeg()>0,
                "legacy FlatWorld must not silently change or claim original wind");
        var roster=AircraftAtlasMain.load(Path.of(args[0]));
        yes(roster.size()==24,"exact source anchor all 24 airframes");
        var ids=new HashSet<String>();
        for(var plane:roster) {
            yes(ids.add(plane.aircraftId()),"unique exact 24 aircraft");
            State first=start();
            State second=start();
            int reaction=WarfareWingsEngineReaction.ticks(plane.aircraftId());
            for(int tick=0;tick<80;tick++) {
                first=tickWithReaction(plane.model(),first,Control.neutral(1),world,reaction);
                second=tickWithReaction(plane.model(),second,Control.neutral(1),world,reaction);
            }
            yes(first.equals(second),"same original 80-step physics is deterministic " + plane.aircraftId());
            yes(Double.isFinite(first.position().x()) && Double.isFinite(first.position().y())
                    && Double.isFinite(first.position().z()) && first.tick()==80,
                    "finite 20Hz source orbit " + plane.aircraftId());
            yes(Math.abs(first.yawDeg())>1e-5 && Math.abs(first.pitchDeg())>1e-5,
                    "speed-sourced wind actually advances original attitude " + plane.aircraftId());
        }
        boolean rejected=false;
        try {new PinnedIa133WindWorld(0,0,0,0,Float.NaN,0);} catch(IllegalArgumentException expected) {rejected=true;}
        yes(rejected,"reject unbounded weather noise instead of silently corrupting numerical physics");
        System.out.println("PinnedIa133WindSelfTest SOURCE_ONLY passed " + checks +
                " checks / 24 bytecode-owned aircraft / real B17 first-tick cross-reference. " +
                "VOXELS, WEAPONS, REAL_FORGE_PARITY: NOT_RUN");
    }
}
