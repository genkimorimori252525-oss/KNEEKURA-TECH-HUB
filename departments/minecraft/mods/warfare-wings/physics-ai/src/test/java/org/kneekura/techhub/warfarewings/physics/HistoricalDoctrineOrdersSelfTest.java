package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.List;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;
import static org.kneekura.techhub.warfarewings.physics.HistoricalDoctrineOrders.*;

public final class HistoricalDoctrineOrdersSelfTest {
    private static int checks;
    private static void require(boolean ok, String reason) {
        checks++;
        if (!ok) throw new AssertionError(reason);
    }
    private static AircraftAtlasMain.Entry get(List<AircraftAtlasMain.Entry> entries, String id) {
        return entries.stream().filter(e -> e.baseId().equals(id)).findFirst().orElseThrow();
    }
    private static Frame frame(AircraftAtlasMain.Entry e, Mission mission, Contact contact,
                               Vec3 anchor, double fuel, double y) {
        State s = State.airborne(new Vec3(0, y, 0), new Vec3(0, 0, 1));
        return new Frame(Profile.fromAtlas(AircraftAtlasMain.evaluate(e)), e.model(), s,
                mission, new Vec3(100, 125, 200), new Vec3(-100, 125, -200),
                contact, anchor, null, fuel, 1, 0, false, 0);
    }
    public static void main(String[] args) throws Exception {
        List<AircraftAtlasMain.Entry> entries = AircraftAtlasMain.load(Path.of(args[0]));
        AircraftAtlasMain.Entry spitfire = get(entries, "spitfire");
        AircraftAtlasMain.Entry f6f = get(entries, "f6f");
        AircraftAtlasMain.Entry b17 = get(entries, "b17");
        AircraftAtlasMain.Entry p47 = get(entries, "p47n");
        Vec3 leader = new Vec3(100, 140, 50);
        for (int i = 0; i < 4; i++) {
            Decision d = decide(frame(spitfire, Mission.ESCORT, null, leader, 1, 140),
                    Memory.INITIAL, new Order(Pattern.RAF_FINGER_FOUR_1940, i, 0, 1940));
            require(d.maneuver() == Maneuver.FINGER_FOUR_HOLD, "finger-four slot " + i);
            require(d.performanceEvidence().contains("GAME_HEURISTIC"), "evidence status");
            for (int j = 0; j < i; j++) {
                Vec3 prev = decide(frame(spitfire, Mission.ESCORT, null, leader, 1, 140),
                        Memory.INITIAL, new Order(Pattern.RAF_FINGER_FOUR_1940, j, 0, 1940)).steeringPoint();
                require(d.steeringPoint().add(prev.scale(-1)).length() > 8, "formation spacing");
            }
        }
        for (int i = 0; i < 6; i++) {
            Decision d = decide(frame(b17, Mission.LEVEL_BOMB, null, leader, 1, 140),
                    Memory.INITIAL, new Order(Pattern.USAAF_COMBAT_BOX_1943, i, 0, 1943));
            require(d.maneuver() == Maneuver.COMBAT_BOX_HOLD, "combat box station " + i);
        }
        for (int i = 0; i < 4; i++) {
            Decision d = decide(frame(p47, Mission.ESCORT, null, leader, 1, 140),
                    Memory.INITIAL, new Order(Pattern.USAAF_ESCORT_COVER_1944, i, 0, 1944));
            require(d.maneuver() == Maneuver.ESCORT_SCREEN, "escort station " + i);
        }
        Contact rear = new Contact("rear-contact", new Vec3(0, 140, -40), new Vec3(0, 0, 1), true);
        Vec3[] pair = new Vec3[2];
        for (int i = 0; i < 2; i++) {
            Decision d = decide(frame(f6f, Mission.INTERCEPT, rear, leader, 1, 140),
                    Memory.INITIAL, new Order(Pattern.USN_MUTUAL_SUPPORT_1942, i, 0, 1944));
            require(d.maneuver() == Maneuver.MUTUAL_SUPPORT_WEAVE, "paired mutual support");
            pair[i] = d.steeringPoint();
        }
        require(pair[0].add(pair[1].scale(-1)).length() > 20, "paired cross-over separation");
        Decision rescue = decide(frame(spitfire, Mission.ESCORT, null, leader, 0.03, 140),
                Memory.INITIAL, new Order(Pattern.RAF_FINGER_FOUR_1940, 1, 0, 1940));
        require(rescue.maneuver() == Maneuver.RETURN_HOME, "safety overrides historical formation");
        Decision baseline = TacticalAirAI.decide(frame(p47, Mission.ESCORT, null, leader, 1, 140),
                Memory.INITIAL);
        Decision none = decide(frame(p47, Mission.ESCORT, null, leader, 1, 140),
                Memory.INITIAL, new Order(Pattern.NONE, 0, 0, 1944));
        require(baseline.equals(none), "no pattern gives same generic decision");
        Decision pairFormation = decide(frame(f6f, Mission.ESCORT, null, leader, 1, 140),
                Memory.INITIAL, new Order(Pattern.USN_MUTUAL_SUPPORT_1942, 1, 0, 1944));
        require(pairFormation.maneuver() == Maneuver.PAIRED_FORMATION_HOLD, "pair is not finger-four");
        boolean eraBlocked = false;
        try {
            decide(frame(f6f, Mission.ESCORT, null, leader, 1, 140),
                    Memory.INITIAL, new Order(Pattern.USN_MUTUAL_SUPPORT_1942, 1, 0, 1942));
        } catch (IllegalArgumentException expected) {
            eraBlocked = true;
        }
        require(eraBlocked, "F6F 1942 anachronism must be rejected");
        require(Pattern.values().length == 5, "documented historical pattern roster");
        System.out.println("HistoricalDoctrineOrdersSelfTest passed: " + checks + " checks");
    }
}
