package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.SquadronCommand.*;

/**
 * Self-contained source-only 20 Hz regression with actual multi-unit state.
 * Assertions cover command decisions and telemetry; no synthetic kills or
 * claimed aircraft-vs-aircraft victories.
 */
public final class MissionScenarioSelfTest {
    private static int checks;
    private static final World FLAT = new FlatWorld(0);
    private static final Vec3 GOAL = new Vec3(0, 120, 350);
    private static final Vec3 HOME = new Vec3(0, 150, -400);

    private MissionScenarioSelfTest() {}

    private static AircraftSpec craft(String id, String type, String team, String squadron,
                                      int slot, TacticalAirAI.Mission mission,
                                      String escorted, HistoricalDoctrineOrders.Order pattern,
                                      double x, double y, double z, double yaw, double speed) {
        return new AircraftSpec(id, "warfare_wings:" + type, team, squadron,
                slot, mission, escorted, pattern,
                new Vec3(x, y, z), forward(yaw, 0).scale(speed),
                yaw, GOAL, HOME, 1, 1, 1.6);
    }

    private static SquadronCommand scenario(Path csv, Sensors sensors, AircraftSpec... aircraft) throws Exception {
        return SquadronCommand.load(csv, List.of(aircraft), FLAT, sensors);
    }

    private static void require(boolean success, String what) {
        checks++;
        if (!success) throw new AssertionError("MissionScenarioSelfTest: " + what);
    }

    private static void close(Vec3 actual, Vec3 expected, double epsilon, String why) {
        require(actual.add(expected.scale(-1)).length() <= epsilon,
                why + " actual=" + actual + " expected=" + expected);
    }

    private interface Throwing { void run() throws Exception; }
    private static void rejects(Throwing action, String why) throws Exception {
        boolean rejected = false;
        try { action.run(); }
        catch (IllegalArgumentException expected) { rejected = true; }
        require(rejected, why);
    }

    private static void oneVsOne(Path csv) throws Exception {
        SquadronCommand command = scenario(csv, Sensors.DEFAULT,
                craft("blue", "a6m", "blue", "alpha", 0,
                        TacticalAirAI.Mission.INTERCEPT, null, null, 0, 150, 0, 0, 0.9),
                craft("red", "p47n", "red", "alpha", 0,
                        TacticalAirAI.Mission.INTERCEPT, null, null, 0, 150, 55, 180, 0.9));
        require(command.supportedAircraftTypes() == 24, "all 24 types loaded");
        Snapshot start = command.start();
        Step first = command.advance(start);
        require(first.commands().get("blue").assignedTargetId().equals("red"), "1v1 blue tracks red");
        require(first.commands().get("red").assignedTargetId().equals("blue"), "1v1 red tracks blue");
        require(first.next().units().get("blue").tracks().size() == 1, "blue local track");
        require(first.next().units().get("red").tracks().size() == 1, "red local track");
        require(start.tick() == 0 && start.units().get("blue").aircraft().tick() == 0,
                "input snapshot must not mutate");
        require(first.next().tick() == 1, "one tick equals 50ms in a 20Hz timeline");

        Snapshot current = first.next();
        for (int i = 1; i < 80; i++) current = command.advance(current).next();
        require(current.tick() == 80, "80 synchronous ticks");
        require(current.units().get("red").aircraft().tick() == 80, "red advances once per tick");
        require(current.units().get("blue").aircraft().tick() == 80, "blue advances once per tick");
        require(!current.units().get("red").aircraft().position()
                .equals(current.units().get("blue").aircraft().position()), "physical aircraft remain separate");
    }

    private static void twoVsTwo(Path csv) throws Exception {
        AircraftSpec b1 = craft("b1", "a6m", "blue", "fighters", 0,
                TacticalAirAI.Mission.INTERCEPT, null, null, -25, 160, 0, 0, 1);
        AircraftSpec b2 = craft("b2", "p47n", "blue", "fighters", 1,
                TacticalAirAI.Mission.INTERCEPT, null, null, 25, 160, 0, 0, 1);
        AircraftSpec r1 = craft("r1", "bf109", "red", "fighters", 0,
                TacticalAirAI.Mission.INTERCEPT, null, null, -25, 160, 92, 180, 1);
        AircraftSpec r2 = craft("r2", "a6m", "red", "fighters", 1,
                TacticalAirAI.Mission.INTERCEPT, null, null, 25, 160, 92, 180, 1);
        SquadronCommand command = scenario(csv, Sensors.DEFAULT, b1, b2, r1, r2);
        Step first = command.advance(command.start());
        require("r1".equals(first.commands().get("b1").assignedTargetId()), "left fighter owns left bandit");
        require("r2".equals(first.commands().get("b2").assignedTargetId()), "load balancer spreads blue 2v2 targets");
        require(!first.next().units().get("b1").tracks().containsKey("b2"),
                "friendly may never appear in hostile sensor tracks");
        require(first.next().units().get("b1").tracks().size() == 2
                && first.next().units().get("b2").tracks().size() == 2,
                "per-pilot 2v2 hostile sightings");

        List<AircraftSpec> reverse = new ArrayList<>(List.of(b1,b2,r1,r2));
        Collections.reverse(reverse);
        SquadronCommand reversed = SquadronCommand.load(csv, reverse, FLAT, Sensors.DEFAULT);
        Snapshot a = command.start(), b = reversed.start();
        double minBlueSpacing = Double.POSITIVE_INFINITY;
        for (int step = 0; step < 80; step++) {
            a = command.advance(a).next();
            b = reversed.advance(b).next();
            require(a.equals(b), "roster insertion order cannot affect tick " + step);
            double blueSpacing = a.units().get("b1").aircraft().position()
                    .add(a.units().get("b2").aircraft().position().scale(-1)).length();
            minBlueSpacing = Math.min(minBlueSpacing, blueSpacing);
        }
        require(minBlueSpacing > 6, "2v2 wingmen retain physical separation in this source scenario");
        require(a.units().get("b1").aircraft().position().add(b1.startPosition().scale(-1)).length() > 12,
                "2v2 fighter changes position across 80 controlled physics ticks");
    }

    private static void escortIntercept(Path csv) throws Exception {
        AircraftSpec bomber = craft("cargo", "b17", "blue", "bombers", 0,
                TacticalAirAI.Mission.LEVEL_BOMB, null, null, 0, 170, 0, 0, 0.8);
        AircraftSpec escortLeft = craft("escort-left", "p47n", "blue", "cover", 0,
                TacticalAirAI.Mission.ESCORT, "cargo", null, -72, 186, -25, 0, 1.0);
        AircraftSpec escortRight = craft("escort-right", "f4u", "blue", "cover", 1,
                TacticalAirAI.Mission.ESCORT, "cargo", null, 72, 186, -25, 0, 1.0);
        AircraftSpec bandit = craft("interceptor", "a6m", "red", "interceptors", 0,
                TacticalAirAI.Mission.INTERCEPT, null, null, 0, 170, 100, 180, 0.9);
        SquadronCommand command = scenario(csv, Sensors.DEFAULT, bomber, escortLeft, escortRight, bandit);
        Step first = command.advance(command.start());
        require(first.commands().get("cargo").assignedTargetId() == null,
                "bomber keeps ground mission and receives no fighter target");
        require(first.commands().get("cargo").decision().maneuver()
                == TacticalAirAI.Maneuver.LEVEL_BOMB_RUN, "bomber continues level-bomb approach");
        require("interceptor".equals(first.commands().get("escort-left").assignedTargetId()),
                "escort prioritizes threat to escorted bomber");
        require("interceptor".equals(first.commands().get("escort-right").assignedTargetId()),
                "both escort pilots can defend the same threatened asset");
        require(!first.commands().get("escort-left").formationAnchor().equals(
                first.commands().get("escort-right").formationAnchor()), "distinct cover stations");
        require(first.commands().get("cargo").threatContactId() != null,
                "bomber independently observes danger for defensive behavior");

        Snapshot follow = first.next();
        double initialDistanceToObjective = bomber.startPosition().add(GOAL.scale(-1)).length();
        double minEscortSeparation = Double.POSITIVE_INFINITY;
        for (int tick = 1; tick < 110; tick++) {
            follow = command.advance(follow).next();
            Vec3 left = follow.units().get("escort-left").aircraft().position();
            Vec3 right = follow.units().get("escort-right").aircraft().position();
            minEscortSeparation = Math.min(minEscortSeparation,
                    left.add(right.scale(-1)).length());
        }
        require(follow.tick() == 110, "escort package advances synchronously for 110 ticks");
        require(follow.units().get("cargo").aircraft().position().add(GOAL.scale(-1)).length()
                        < initialDistanceToObjective,
                "escorted bomber closes distance to ground objective during actual flight");
        require(minEscortSeparation > 6,
                "cover wingmen maintain separate physical trajectories in source scenario");
    }

    private static void formationAndHeading(Path csv) throws Exception {
        HistoricalDoctrineOrders.Order order = new HistoricalDoctrineOrders.Order(
                HistoricalDoctrineOrders.Pattern.RAF_FINGER_FOUR_1940, 1, 90, 1940);
        AircraftSpec lead = craft("leader", "spitfire", "blue", "raf", 0,
                TacticalAirAI.Mission.PATROL, null, null, 0, 180, 0, 90, 0.8);
        AircraftSpec wing = craft("wing", "spitfire", "blue", "raf", 1,
                TacticalAirAI.Mission.PATROL, null, order, -50, 185, -50, 90, 0.8);
        SquadronCommand command = scenario(csv, Sensors.DEFAULT, lead, wing);
        Step first = command.advance(command.start());
        require(first.commands().get("wing").decision().maneuver()
                == TacticalAirAI.Maneuver.FINGER_FOUR_HOLD,
                "explicit RAF 1940 pattern acts on wingman's station");
        Vec3 expected = HistoricalDoctrineOrders.station(
                lead.startPosition(), lead.startYawDeg(), new Vec3(-20, 3, -18));
        close(first.commands().get("wing").decision().steeringPoint(), expected, 1e-8,
                "heading-rotated historical station");
        require(first.commands().get("leader").decision().maneuver()
                == TacticalAirAI.Maneuver.PATROL_ROUTE,
                "formation leader keeps mission route and does not chase itself");

        Snapshot movement = first.next();
        for (int i = 0; i < 20; i++) movement = command.advance(movement).next();
        Step turned = command.advance(movement);
        double actualLeaderYaw = movement.units().get("leader").aircraft().yawDeg();
        Vec3 movingSlot = HistoricalDoctrineOrders.station(
                movement.units().get("leader").aircraft().position(),
                actualLeaderYaw, new Vec3(-20, 3, -18));
        close(turned.commands().get("wing").decision().steeringPoint(), movingSlot, 1e-7,
                "historical station must use leader's updated heading each tick");

        SquadronCommand generic = scenario(csv, Sensors.DEFAULT, lead,
                craft("wing", "spitfire", "blue", "raf", 1,
                        TacticalAirAI.Mission.PATROL, null, null, -50, 185, -50, 90, 0.8));
        Step genericStep = generic.advance(generic.start());
        Vec3 desired = HistoricalDoctrineOrders.station(
                lead.startPosition(), lead.startYawDeg(), new Vec3(-26, 5, -24));
        require(genericStep.commands().get("wing").decision().maneuver()
                == TacticalAirAI.Maneuver.FORMATION_HOLD, "generic wing station requested");
        close(genericStep.commands().get("wing").decision().steeringPoint(), desired, 1e-8,
                "nonzero heading station not displaced by world-axis TacticalAirAI compensation");

        HistoricalDoctrineOrders.Order box = new HistoricalDoctrineOrders.Order(
                HistoricalDoctrineOrders.Pattern.USAAF_COMBAT_BOX_1943, 1, 25, 1943);
        SquadronCommand combatBox = scenario(csv, Sensors.DEFAULT,
                craft("box-lead", "b17", "blue", "bomberBox", 0,
                        TacticalAirAI.Mission.LEVEL_BOMB, null, null, 0, 220, 0, 25, 0.8),
                craft("box-wing", "b29", "blue", "bomberBox", 1,
                        TacticalAirAI.Mission.LEVEL_BOMB, null, box, -60, 230, -75, 25, 0.8));
        Step bomberBox = combatBox.advance(combatBox.start());
        require(bomberBox.commands().get("box-wing").decision().maneuver()
                == TacticalAirAI.Maneuver.COMBAT_BOX_HOLD, "bomber box preserved as explicit order");
    }

    private static void strikeRoles(Path csv) throws Exception {
        SquadronCommand command = scenario(csv, Sensors.DEFAULT,
                craft("level", "b17", "blue", "bomb", 0,
                        TacticalAirAI.Mission.LEVEL_BOMB, null, null, 0, 190, 0, 0, 0.85),
                craft("torpedo", "g4m", "blue", "torpedo", 0,
                        TacticalAirAI.Mission.TORPEDO, null, null, 200, 75, 0, 0, 0.85),
                craft("dive", "ju87", "blue", "dive", 0,
                        TacticalAirAI.Mission.DIVE_BOMB, null, null, 400, 200, 0, 0, 0.85),
                craft("strafe", "il2", "blue", "strafe", 0,
                        TacticalAirAI.Mission.STRAFE, null, null, 600, 100, 0, 0, 0.85));
        Step first = command.advance(command.start());
        require(first.commands().get("level").decision().maneuver()
                == TacticalAirAI.Maneuver.LEVEL_BOMB_RUN, "level bombing role");
        require(first.commands().get("torpedo").decision().maneuver()
                == TacticalAirAI.Maneuver.TORPEDO_APPROACH, "torpedo approach role");
        require(first.commands().get("dive").decision().maneuver()
                == TacticalAirAI.Maneuver.DIVE_ATTACK, "dive attack role");
        require(first.commands().get("strafe").decision().maneuver()
                == TacticalAirAI.Maneuver.STRAFING_RUN, "strafing role");
        Snapshot current = first.next();
        for (int i = 1; i < 100; i++) current = command.advance(current).next();
        for (Local local : current.units().values()) {
            require(Double.isFinite(local.aircraft().position().y()),
                    "all ground-attack roles retain finite dynamic state");
            require(local.aircraft().tick() == 100, "ground attack role ticks exactly");
        }
    }

    private static void safetyAndIsolation(Path csv) throws Exception {
        AircraftSpec shooter = craft("shooter", "a6m", "blue", "one", 0,
                TacticalAirAI.Mission.INTERCEPT, null, null, 0, 160, 0, 0, 1.4);
        AircraftSpec allyInFireLane = craft("friend", "p47n", "blue", "two", 0,
                TacticalAirAI.Mission.PATROL, null, null, 0, 160, 22, 0, 1.4);
        AircraftSpec target = craft("bandit", "bf109", "red", "one", 0,
                TacticalAirAI.Mission.INTERCEPT, null, null, 0, 160, 45, 180, 1);
        SquadronCommand lined = scenario(csv, Sensors.DEFAULT, shooter, allyInFireLane, target);
        Instruction blocked = lined.advance(lined.start()).commands().get("shooter");
        require("bandit".equals(blocked.assignedTargetId()), "fighter has sensor-acquired bandit");
        require(!blocked.friendlyFireCorridorClear(), "teammate between shooter and hostile blocks lane");
        require(!blocked.decision().firingWindowCandidate(), "unsafe shot never advisory-approved");

        SquadronCommand separated = scenario(csv, Sensors.DEFAULT, shooter, target);
        Instruction permitted = separated.advance(separated.start()).commands().get("shooter");
        require(permitted.friendlyFireCorridorClear(), "same target without friendly has clear geometry");
        require(permitted.decision().firingWindowCandidate(), "aligned clear fighter can report candidate");

        SquadronCommand close = scenario(csv, Sensors.DEFAULT, shooter,
                craft("friend", "p47n", "blue", "two", 0,
                        TacticalAirAI.Mission.PATROL, null, null, 4, 160, 0, 0, 1.4), target);
        Instruction avoidance = close.advance(close.start()).commands().get("shooter");
        require(avoidance.decision().maneuver() == TacticalAirAI.Maneuver.COLLISION_AVOID,
                "nearby friend has collision priority");
        require(!avoidance.decision().firingWindowCandidate(), "collision safety suppresses fire");

        SquadronCommand converging = scenario(csv, Sensors.DEFAULT,
                craft("north", "a6m", "blue", "north", 0,
                        TacticalAirAI.Mission.PATROL, null, null, 0, 170, 0, 0, 1),
                craft("south", "p47n", "blue", "south", 0,
                        TacticalAirAI.Mission.PATROL, null, null, 0, 170, 38, 180, 1));
        Instruction predicted = converging.advance(converging.start()).commands().get("north");
        require(predicted.nearestFriendlyDistance() > 12,
                "predictive collision test starts outside immediate separation threshold");
        require(predicted.safetyClearance().reason()
                == FlightSafetyPlanner.Reason.MOVING_COLLISION_RISK,
                "closing velocity must trigger future collision check");
        require(predicted.decision().maneuver() == TacticalAirAI.Maneuver.COLLISION_AVOID,
                "future collision risk overrides navigation");

        World ridge = new World() {
            @Override public double groundHeight(double x, double z) {
                return z >= 20 ? 150 : 0;
            }
        };
        AircraftSpec climbing = craft("climber", "a6m", "blue", "recovery", 0,
                TacticalAirAI.Mission.PATROL, null, null, 0, 160, 0, 0, 1.2);
        SquadronCommand overRidge = SquadronCommand.load(csv, List.of(climbing), ridge, Sensors.DEFAULT);
        Instruction ridgeGuard = overRidge.advance(overRidge.start()).commands().get("climber");
        require(ridgeGuard.safetyClearance().reason()
                == FlightSafetyPlanner.Reason.TERRAIN_AHEAD,
                "future ground-height sampling must detect unmodeled ridge");
        require(ridgeGuard.decision().maneuver() == TacticalAirAI.Maneuver.TERRAIN_RECOVERY,
                "terrain lookahead overrides patrol with climb command");
        require(ridgeGuard.decision().steeringPoint().y() > climbing.startPosition().y(),
                "predictive terrain recovery requests a higher target");

        // A distant wingman does not automatically inherit another observer's tracks.
        SquadronCommand isolated = scenario(csv, new Sensors(60, 150, 3, 9),
                shooter, craft("far", "p47n", "blue", "two", 0,
                        TacticalAirAI.Mission.INTERCEPT, null, null, 400, 160, 0, 0, 0.9), target);
        Snapshot observed = isolated.advance(isolated.start()).next();
        require(observed.units().get("shooter").tracks().containsKey("bandit"),
                "near pilot sees enemy");
        require(observed.units().get("far").tracks().isEmpty(),
                "far pilot has no omniscient team-shared hostile track");
        boolean readonlyTracks = false;
        try { observed.units().get("shooter").tracks().clear(); }
        catch (UnsupportedOperationException expected) { readonlyTracks = true; }
        require(readonlyTracks, "published per-aircraft track maps are immutable");
        boolean readonlyRoster = false;
        try { observed.units().clear(); }
        catch (UnsupportedOperationException expected) { readonlyRoster = true; }
        require(readonlyRoster, "published simulation roster is immutable");

        SquadronCommand expiring = scenario(csv, new Sensors(30, 150, 2, 9),
                craft("slow", "a6m", "blue", "one", 0,
                        TacticalAirAI.Mission.INTERCEPT, null, null, 0, 160, 0, 0, 0),
                craft("fast", "p47n", "red", "one", 0,
                        TacticalAirAI.Mission.INTERCEPT, null, null, 0, 160, 25, 0, 3));
        Snapshot initial = expiring.start();
        Step seen = expiring.advance(initial);
        require(seen.commands().get("slow").observedTargetThisTick(),
                "enemy initially detected inside short sensor range");
        Snapshot later = seen.next();
        for (int i = 1; i < 18; i++) later = expiring.advance(later).next();
        require(later.units().get("slow").tracks().isEmpty(),
                "expired unseen enemy track is removed");
        require(later.units().get("slow").assignedTargetId() == null,
                "enemy outside sensor memory cannot remain assigned");
    }

    private static void validationAndCoverage(Path csv) throws Exception {
        AircraftSpec lead = craft("lead", "a6m", "blue", "one", 0,
                TacticalAirAI.Mission.INTERCEPT, null, null, 0, 140, 0, 0, 1);
        rejects(() -> scenario(csv, Sensors.DEFAULT, lead, lead), "duplicate instance rejected");
        rejects(() -> scenario(csv, Sensors.DEFAULT,
                craft("other", "a6m", "blue", "one", 0,
                        TacticalAirAI.Mission.INTERCEPT, null, null, 20, 140, 0, 0, 1),
                lead), "duplicate squadron slot rejected");
        rejects(() -> scenario(csv, Sensors.DEFAULT,
                craft("orphan", "a6m", "blue", "one", 1,
                        TacticalAirAI.Mission.INTERCEPT, null, null, 0, 140, 0, 0, 1)),
                "missing squadron leader rejected");
        rejects(() -> scenario(csv, Sensors.DEFAULT,
                craft("bomber", "b17", "blue", "one", 0,
                        TacticalAirAI.Mission.TORPEDO, null, null, 0, 140, 0, 0, 1)),
                "incompatible role rejected");
        rejects(() -> scenario(csv, Sensors.DEFAULT,
                craft("bogus", "nonexistent", "blue", "one", 0,
                        TacticalAirAI.Mission.INTERCEPT, null, null, 0, 140, 0, 0, 1)),
                "unknown aircraft not silently modeled");
        rejects(() -> scenario(csv, Sensors.DEFAULT,
                craft("escort", "a6m", "blue", "one", 0,
                        TacticalAirAI.Mission.ESCORT, "missing", null, 0, 140, 0, 0, 1)),
                "missing escorted asset rejected");
        rejects(() -> scenario(csv, Sensors.DEFAULT, lead,
                craft("escort", "p47n", "red", "other", 0,
                        TacticalAirAI.Mission.ESCORT, "lead", null, 0, 140, 80, 0, 1)),
                "cross-team escort rejected");

        List<AircraftSpec> all = new ArrayList<>();
        int index = 0;
        for (AircraftAtlasMain.Entry entry : AircraftAtlasMain.load(csv)) {
            TacticalAirAI.Mission mission = switch (entry.role()) {
                case "bomber" -> TacticalAirAI.Mission.LEVEL_BOMB;
                case "torpedo_bomber" -> TacticalAirAI.Mission.TORPEDO;
                case "attacker" -> TacticalAirAI.Mission.STRAFE;
                default -> TacticalAirAI.Mission.PATROL;
            };
            all.add(craft("type-" + index, entry.baseId(), "training", "unit-" + index, 0,
                    mission, null, null, index * 250.0, 240, 0, 0, 0.8));
            index++;
        }
        SquadronCommand command = SquadronCommand.load(csv, all, FLAT, Sensors.DEFAULT);
        require(command.supportedAircraftTypes() == 24 && all.size() == 24,
                "every source aircraft loaded without a guessed profile");
        Snapshot current = command.start();
        for (int tick = 0; tick < 30; tick++) current = command.advance(current).next();
        require(current.tick() == 30, "all 24 aircraft stepped at 20Hz");
        for (AircraftSpec spec : all) {
            Local local = current.units().get(spec.unitId());
            require(local.aircraft().tick() == 30, "source type advanced: " + spec.aircraftTypeId());
            require(Double.isFinite(local.aircraft().velocity().length()), "finite 24-aircraft state");
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException(
                "Usage: MissionScenarioSelfTest INPUT_ANCHOR_CSV");
        Path csv = Path.of(args[0]);
        oneVsOne(csv);
        twoVsTwo(csv);
        escortIntercept(csv);
        formationAndHeading(csv);
        strikeRoles(csv);
        safetyAndIsolation(csv);
        validationAndCoverage(csv);
        System.out.println("MissionScenarioSelfTest PASS: " + checks
                + " assertions, 24 Atlas types, 1v1/2v2/escort/intercept/bomber/torpedo"
                + "; SOURCE_ONLY, REAL_MINECRAFT_COMBAT_NOT_RUN");
    }
}
