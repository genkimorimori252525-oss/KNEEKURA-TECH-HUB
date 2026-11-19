package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.List;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

public final class TacticalAirAISelfTest {
    private static int checks;
    private static final World FLAT = new FlatWorld(0);

    private static Frame frame(Profile profile, Model model, State state, Mission mission,
                               Contact contact, Vec3 formationAnchor,
                               double fuel, double health) {
        return new Frame(profile, model, state, mission,
                new Vec3(200, 80, 300), new Vec3(-150, 100, -200),
                contact, formationAnchor, null, fuel, health, 0, true, 1.5);
    }

    private static State state(double altitude, double speed) {
        return State.airborne(new Vec3(0, altitude, 0), new Vec3(0, 0, speed));
    }

    private static void assertTrue(boolean condition, String why) {
        checks++;
        if (!condition) throw new AssertionError(why);
    }

    private static void expect(Maneuver expected, Decision actual, String label) {
        assertTrue(actual.maneuver() == expected,
                label + ": expected " + expected + " got " + TacticalAirAI.debug(actual));
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Usage: TacticalAirAISelfTest ANCHOR_CSV");
        List<AircraftAtlasMain.Entry> roster = AircraftAtlasMain.load(Path.of(args[0]));
        assertTrue(roster.size() == 24, "exact 24-aircraft roster");
        AircraftAtlasMain.Entry zero = find(roster, "a6m");
        AircraftAtlasMain.Entry thunderbolt = find(roster, "p47n");
        AircraftAtlasMain.Entry bomber = find(roster, "b17");
        AircraftAtlasMain.Entry stuka = find(roster, "ju87");
        AircraftAtlasMain.Entry torpedo = find(roster, "g4m");
        AircraftAtlasMain.Entry attacker = find(roster, "il2");

        Profile a6m = Profile.fromAtlas(AircraftAtlasMain.evaluate(zero));
        Profile p47n = Profile.fromAtlas(AircraftAtlasMain.evaluate(thunderbolt));
        Profile b17 = Profile.fromAtlas(AircraftAtlasMain.evaluate(bomber));
        Profile ju87 = Profile.fromAtlas(AircraftAtlasMain.evaluate(stuka));
        Profile g4m = Profile.fromAtlas(AircraftAtlasMain.evaluate(torpedo));
        Profile il2 = Profile.fromAtlas(AircraftAtlasMain.evaluate(attacker));
        Contact bandit = new Contact("bandit", new Vec3(0, 100, 35), Vec3.ZERO, true);
        Contact harmless = new Contact("neutral", new Vec3(0, 100, 35), Vec3.ZERO, false);

        expect(Maneuver.TURN_PURSUIT,
                decide(frame(a6m, zero.model(), state(100, 1.4), Mission.INTERCEPT,
                        bandit, null, 1, 1), Memory.INITIAL), "A6M high-authority pursuit");
        expect(Maneuver.EXTEND_AND_REENTER,
                decide(frame(p47n, thunderbolt.model(), state(100, 0.35), Mission.INTERCEPT,
                        bandit, null, 1, 1), Memory.INITIAL), "P-47N speed recovery");
        expect(Maneuver.HIGH_SIDE_PASS,
                decide(frame(p47n, thunderbolt.model(), state(150, 2.3), Mission.INTERCEPT,
                        bandit, null, 1, 1), Memory.INITIAL), "P-47N altitude advantage");
        expect(Maneuver.LEVEL_BOMB_RUN,
                decide(frame(b17, bomber.model(), state(150, 1.1), Mission.LEVEL_BOMB,
                        bandit, null, 1, 1), Memory.INITIAL), "B-17 stays on bombing mission");
        expect(Maneuver.DIVE_ATTACK,
                decide(frame(ju87, stuka.model(), state(130, 1.1), Mission.DIVE_BOMB,
                        bandit, null, 1, 1), Memory.INITIAL), "Ju 87 dive mission");
        expect(Maneuver.TORPEDO_APPROACH,
                decide(frame(g4m, torpedo.model(), state(60, 1.0), Mission.TORPEDO,
                        bandit, null, 1, 1), Memory.INITIAL), "G4M role overrides old escort label");
        expect(Maneuver.STRAFING_RUN,
                decide(frame(il2, attacker.model(), state(60, 1.0), Mission.STRAFE,
                        bandit, null, 1, 1), Memory.INITIAL), "IL-2 ground attack");
        expect(Maneuver.DEFENSIVE_BREAK,
                decide(frame(b17, bomber.model(), state(120, 0.9), Mission.INTERCEPT,
                        bandit, null, 1, 1), Memory.INITIAL), "non-fighter must not chase");
        expect(Maneuver.TERRAIN_RECOVERY,
                decide(frame(a6m, zero.model(), state(5, 0.9), Mission.INTERCEPT,
                        bandit, null, 0.01, 0.1), Memory.INITIAL), "terrain beats withdrawal");
        expect(Maneuver.COLLISION_AVOID,
                decide(new Frame(a6m, zero.model(), state(90, 0.9), Mission.ESCORT,
                        new Vec3(200, 80, 300), new Vec3(-150, 100, -200),
                        bandit, new Vec3(60, 90, 0), new Vec3(1, 90, 0),
                        0.01, 0.1, 0, true, 1.5), Memory.INITIAL), "friendly separation");
        expect(Maneuver.RETURN_HOME,
                decide(frame(a6m, zero.model(), state(90, 0.9), Mission.INTERCEPT,
                        bandit, null, 0.01, 1), Memory.INITIAL), "fuel withdrawal");
        expect(Maneuver.PATROL_ROUTE,
                decide(frame(a6m, zero.model(), state(100, 1.0), Mission.PATROL,
                        harmless, null, 1, 1), Memory.INITIAL), "neutral contact not hostile");
        Contact headOn = new Contact("oncoming", new Vec3(0, 100, 30), new Vec3(0, 0, -1), true);
        expect(Maneuver.TURN_PURSUIT,
                decide(frame(a6m, zero.model(), state(100, 1.4), Mission.INTERCEPT,
                        headOn, null, 1, 1), Memory.INITIAL), "head-on is not tail threat");
        Contact tailPursuer = new Contact("tail", new Vec3(0, 100, -30), new Vec3(0, 0, 1), true);
        expect(Maneuver.DEFENSIVE_BREAK,
                decide(frame(a6m, zero.model(), state(100, 1.4), Mission.INTERCEPT,
                        tailPursuer, null, 1, 1), Memory.INITIAL), "real tail threat");
        expect(Maneuver.DEFENSIVE_BREAK,
                decide(frame(b17, bomber.model(), state(100, 1.1), Mission.LEVEL_BOMB,
                        tailPursuer, null, 1, 1), Memory.INITIAL), "bomber rear attack abort");
        Frame escortOutOfLeash = new Frame(p47n, thunderbolt.model(), state(120, 2.2),
                Mission.ESCORT, new Vec3(200, 80, 300), new Vec3(-150, 100, -200),
                new Contact("distant", new Vec3(400, 120, 50), Vec3.ZERO, true),
                new Vec3(20, 120, 40), null, 1, 1, 0, false, 0);
        expect(Maneuver.ESCORT_SCREEN,
                decide(escortOutOfLeash, Memory.INITIAL), "escorted asset leash");

        // Changing a metadata faction cannot secretly change the tactical branch.
        Profile otherFaction = new Profile(a6m.aircraftId(), a6m.role(), "alternate",
                a6m.atlasDoctrine(), a6m.predictedTopSpeedBps(), a6m.yawChange20TicksDeg(),
                a6m.ticksTo90Yaw(), a6m.equalAngle90SpeedRetention());
        Decision original = decide(frame(a6m, zero.model(), state(100, 1.4),
                Mission.INTERCEPT, bandit, null, 1, 1), Memory.INITIAL);
        Decision renamed = decide(frame(otherFaction, zero.model(), state(100, 1.4),
                Mission.INTERCEPT, bandit, null, 1, 1), Memory.INITIAL);
        assertTrue(original.maneuver() == renamed.maneuver()
                && original.controls().equals(renamed.controls()), "faction metadata is not a hard-coded tactic");

        // Steering polarity must match the IA controller: positive X reduces yaw.
        Frame east = frame(a6m, zero.model(), state(100, 1), Mission.PATROL, null, null, 1, 1);
        assertTrue(steer(east, new Vec3(100, 100, 0), 1).x() > 0, "right-turn X polarity");
        assertTrue(steer(east, new Vec3(0, 200, 100), 1).z() < 0, "nose-up Z polarity");
        State dive = new State(0, new Vec3(0, 5, 0), new Vec3(0, -0.3, 0.8),
                0, 90, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, false, false);
        Decision recovery = decide(frame(a6m, zero.model(), dive,
                Mission.PATROL, null, null, 1, 1), Memory.INITIAL);
        assertTrue(recovery.steeringPoint().y() > dive.position().y(),
                "terrain recovery cannot request descending waypoints at steep pitch");

        // All 24 have valid performance fingerprints and can run for 80 deterministic steps.
        for (AircraftAtlasMain.Entry entry : roster) {
            Profile profile = Profile.fromAtlas(AircraftAtlasMain.evaluate(entry));
            assertTrue(profile.aircraftId().equals(entry.model().id()), "Atlas binds model ID");
            double canonical = flightSignature(entry, profile);
            double replay = flightSignature(entry, profile);
            assertTrue(Double.doubleToLongBits(canonical) == Double.doubleToLongBits(replay),
                    "deterministic tactical replay: " + entry.aircraftId());
        }

        // Flight gun permission is only an advisory candidate and respects visibility.
        Decision permitted = decide(frame(a6m, zero.model(), state(100, 1.4),
                Mission.INTERCEPT, bandit, null, 1, 1), Memory.INITIAL);
        assertTrue(permitted.firingWindowCandidate(), "aligned fighter fire window");
        Frame blocked = new Frame(a6m, zero.model(), state(100, 1.4), Mission.INTERCEPT,
                new Vec3(200, 80, 300), new Vec3(-150, 100, -200),
                bandit, null, null, 1, 1, 0, false, 1.5);
        assertTrue(!decide(blocked, Memory.INITIAL).firingWindowCandidate(),
                "line-of-fire permission gates fire candidate");
        Frame tooSlowProjectile = new Frame(a6m, zero.model(), state(100, 1.4), Mission.INTERCEPT,
                new Vec3(200, 80, 300), new Vec3(-150, 100, -200),
                new Contact("fast-lateral", new Vec3(0, 100, 35), new Vec3(2, 0, 0), true),
                null, null, 1, 1, 0, true, 0.3);
        assertTrue(!decide(tooSlowProjectile, Memory.INITIAL).firingWindowCandidate(),
                "projectile must have reachable target intercept");
        boolean identityRejected = false;
        try {
            Profile fake = new Profile(b17.aircraftId(), "fighter", b17.faction(),
                    b17.atlasDoctrine(), b17.predictedTopSpeedBps(),
                    b17.yawChange20TicksDeg(), b17.ticksTo90Yaw(), b17.equalAngle90SpeedRetention());
            frame(fake, bomber.model(), state(100, 1), Mission.INTERCEPT, bandit, null, 1, 1);
        } catch (IllegalArgumentException expected) {
            identityRejected = true;
        }
        assertTrue(identityRejected, "role data cannot be silently forged");

        System.out.println("TacticalAirAISelfTest passed: " + checks
                + " checks / 24 aircraft; exact Minecraft combat parity NOT_RUN");
    }

    private static double flightSignature(AircraftAtlasMain.Entry entry, Profile profile) {
        State state = state(250, 0.8);
        Memory memory = Memory.INITIAL;
        double signature = 0;
        for (int i = 0; i < 80; i++) {
            Mission mission = switch (entry.role()) {
                case "bomber" -> Mission.LEVEL_BOMB;
                case "torpedo_bomber" -> Mission.TORPEDO;
                case "attacker" -> Mission.STRAFE;
                default -> Mission.INTERCEPT;
            };
            Frame f = frame(profile, entry.model(), state, mission,
                    new Contact("target", new Vec3(35, 195, 120), Vec3.ZERO, true),
                    null, 1, 1);
            Decision action = decide(f, memory);
            state = tick(entry.model(), state, action.controls(), FLAT);
            memory = action.nextMemory();
            assertTrue(Double.isFinite(state.position().x())
                    && Double.isFinite(state.position().y())
                    && Double.isFinite(state.position().z()), "finite flight state");
            signature += action.maneuver().ordinal() + state.yawDeg() * 0.001
                    + state.position().x() * 0.00001;
        }
        return signature;
    }

    private static AircraftAtlasMain.Entry find(List<AircraftAtlasMain.Entry> entries, String baseId) {
        return entries.stream().filter(r -> r.baseId().equals(baseId)).findFirst().orElseThrow();
    }
}
