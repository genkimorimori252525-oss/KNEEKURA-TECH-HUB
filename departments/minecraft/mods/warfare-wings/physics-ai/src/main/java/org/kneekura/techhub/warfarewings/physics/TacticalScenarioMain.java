package org.kneekura.techhub.warfarewings.physics;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.EnumMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.StringJoiner;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

/**
 * Reproducible, source-only mission traces for each of the 24 base aircraft.
 * Each case runs closed-loop decisions and IA controls for 200 ticks (10 seconds).
 * No hit chance, victories, ammo or runtime-equivalence conclusions are computed.
 */
public final class TacticalScenarioMain {
    private static final World FLAT = new FlatWorld(0);
    private static final int TICKS = 200;

    private TacticalScenarioMain() {}
    private enum Case { AIR_CONTACT, ROLE_MISSION, SAFETY_RECOVERY, LOW_FUEL }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("Usage: TacticalScenarioMain ANCHOR_CSV OUTPUT_CSV");
        List<AircraftAtlasMain.Entry> entries = AircraftAtlasMain.load(Path.of(args[0]));
        if (entries.size() != 24) throw new IllegalArgumentException("expected 24 aircraft");
        Path output = Path.of(args[1]);
        if (output.toAbsolutePath().getParent() != null) Files.createDirectories(output.toAbsolutePath().getParent());
        try (BufferedWriter writer = Files.newBufferedWriter(output, StandardCharsets.UTF_8)) {
            writer.write("schema_version,case,aircraft_id,role,mission,ticks,first_maneuver,"
                    + "last_maneuver,move_count,final_distance_to_objective_blocks,"
                    + "final_speed_bps,min_height_above_ground_blocks,fire_candidate_ticks,"
                    + "maneuver_histogram,evidence");
            writer.newLine();
            for (AircraftAtlasMain.Entry entry : entries) {
                Profile profile = Profile.fromAtlas(AircraftAtlasMain.evaluate(entry));
                for (Case scenario : Case.values()) {
                    writer.write(run(entry, profile, scenario));
                    writer.newLine();
                }
            }
        }
        System.out.println("Tactical scenarios: 24 aircraft x 4 cases x " + TICKS
                + " source-microkernel ticks; real Minecraft parity NOT_RUN");
    }

    private static String run(AircraftAtlasMain.Entry entry, Profile profile, Case scenario) {
        Vec3 goal = new Vec3(80, 90, 320);
        Vec3 home = new Vec3(-200, 150, -300);
        Vec3 anchor = new Vec3(45, 160, 130);
        double startHeight = scenario == Case.SAFETY_RECOVERY ? 6 : 160;
        State state = State.airborne(new Vec3(0, startHeight, 0),
                new Vec3(0, scenario == Case.SAFETY_RECOVERY ? -0.12 : 0, 0.8));
        Mission mission = switch (entry.role()) {
            case "bomber" -> Mission.LEVEL_BOMB;
            case "torpedo_bomber" -> Mission.TORPEDO;
            case "attacker" -> Mission.STRAFE;
            default -> scenario == Case.ROLE_MISSION ? Mission.ESCORT : Mission.INTERCEPT;
        };
        double minAlt = Double.POSITIVE_INFINITY;
        Memory memory = Memory.INITIAL;
        Map<Maneuver, Integer> histogram = new EnumMap<>(Maneuver.class);
        Maneuver first = null, last = null;
        int firingCandidates = 0, movement = 0;

        for (int tick = 0; tick < TICKS; tick++) {
            Contact enemy = scenario == Case.AIR_CONTACT && entry.role().equals("fighter")
                    ? new Contact("standardized-hostile",
                        new Vec3(45 + 0.08 * tick, 125, 150 - 0.1 * tick),
                        new Vec3(0.08, 0, -0.1), true)
                    : null;
            Vec3 leader = scenario == Case.ROLE_MISSION ? anchor : null;
            Frame frame = new Frame(profile, entry.model(), state, mission,
                    goal, home, enemy, leader, null,
                    scenario == Case.LOW_FUEL ? 0.07 : 1.0, 1.0,
                    0.0, false, 0.0);
            Decision decision = TacticalAirAI.decide(frame, memory);
            if (first == null) first = decision.maneuver();
            last = decision.maneuver();
            histogram.merge(decision.maneuver(), 1, Integer::sum);
            if (decision.firingWindowCandidate()) firingCandidates++;
            State next = tick(entry.model(), state, decision.controls(), FLAT);
            if (!Double.isFinite(next.position().x()) || !Double.isFinite(next.position().y())
                    || !Double.isFinite(next.position().z()))
                throw new IllegalStateException("non-finite state " + entry.aircraftId());
            if (next.position().add(state.position().scale(-1)).length() > 0) movement++;
            minAlt = Math.min(minAlt, next.position().y());
            state = next;
            memory = decision.nextMemory();
        }
        StringJoiner hist = new StringJoiner("|");
        histogram.forEach((key, value) -> hist.add(key.name() + ":" + value));
        double toGoal = goal.add(state.position().scale(-1)).length();
        return String.join(",",
                SCHEMA, scenario.name(), entry.aircraftId(), entry.role(), mission.name(),
                Integer.toString(TICKS), first.name(), last.name(), Integer.toString(movement),
                fmt(toGoal), fmt(state.velocity().length() * TICKS_PER_SECOND),
                fmt(minAlt), Integer.toString(firingCandidates), hist.toString(),
                "SOURCE_MICROKERNEL+TACTICAL_HEURISTIC");
    }

    private static String fmt(double n) {
        return String.format(Locale.ROOT, "%.9f", n);
    }
}
