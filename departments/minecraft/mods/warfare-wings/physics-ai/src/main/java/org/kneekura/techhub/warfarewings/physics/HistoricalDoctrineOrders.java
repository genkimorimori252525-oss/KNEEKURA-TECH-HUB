package org.kneekura.techhub.warfarewings.physics;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

/**
 * Explicit scenario-level doctrinal orders, separate from aircraft nationality/physics.
 *
 * Historical sources support the *existence and purpose* of these patterns. The block
 * spacings, weave period and steering gains below are gameplay research hypotheses, not
 * archival aircraft dimensions or Minecraft-calibrated tactics. No combat outcome claim.
 */
public final class HistoricalDoctrineOrders {
    private HistoricalDoctrineOrders() {}

    public enum Pattern {
        NONE("NONE"),
        RAF_FINGER_FOUR_1940("https://www.rafbf.org/news-and-stories/raf-history/ten-rules-air-fighting"),
        USN_MUTUAL_SUPPORT_1942("https://www.history.navy.mil/content/history/museums/nnam/education/articles/history-up-close/captured-zero-fighters-yielded-intelligence-for-allies.html"),
        USAAF_COMBAT_BOX_1943("https://www.nationalmuseum.af.mil/Visit/Museum-Exhibits/Fact-Sheets/Display/Article/1513340/combat-box-bomber-formations/"),
        USAAF_ESCORT_COVER_1944("https://www.nationalmuseum.af.mil/Visit/Museum-Exhibits/Fact-Sheets/Display/Article/1519676/fighter-escort-little-friends/");

        public final String sourceUrl;
        Pattern(String sourceUrl) { this.sourceUrl = sourceUrl; }
    }

    /** Slot is explicitly assigned by the mission designer, leader heading is observed. */
    public record Order(Pattern pattern, int slot, double leaderYawDeg, int scenarioYear) {
        public Order {
            if (pattern == null || slot < 0 || !Double.isFinite(leaderYawDeg)
                    || scenarioYear < 1939 || scenarioYear > 1950)
                throw new IllegalArgumentException("historical order");
            if (pattern == Pattern.RAF_FINGER_FOUR_1940 && scenarioYear < 1940
                    || pattern == Pattern.USN_MUTUAL_SUPPORT_1942 && scenarioYear < 1942
                    || pattern == Pattern.USAAF_COMBAT_BOX_1943 && scenarioYear < 1943
                    || pattern == Pattern.USAAF_ESCORT_COVER_1944 && scenarioYear < 1944)
                throw new IllegalArgumentException("pattern not yet documented for year");
        }
    }

    /** Fallback to general-purpose tactics whenever an order has no applicable situation. */
    public static Decision decide(Frame frame, Memory memory, Order order) {
        if (order == null) throw new IllegalArgumentException("order");
        Decision base = TacticalAirAI.decide(frame, memory);
        if (order.pattern() == Pattern.NONE) return base;

        switch (base.maneuver()) {
            case TERRAIN_RECOVERY, COLLISION_AVOID, RETURN_HOME -> { return base; }
            default -> { }
        }

        boolean fighter = frame.profile().role().equals("fighter");
        boolean bomber = frame.profile().role().equals("bomber");
        if (order.pattern() == Pattern.USN_MUTUAL_SUPPORT_1942
                && frame.profile().aircraftId().equals("warfare_wings:f6f")
                && order.scenarioYear() < 1943)
            throw new IllegalArgumentException("F6F 1942 anachronism: historical pattern transfer is 1943+ adaptation");
        // Doctrinal units are task-specific, not universal rules for aircraft of a nation.
        if (order.pattern() == Pattern.USAAF_COMBAT_BOX_1943 && !bomber)
            throw new IllegalArgumentException("combat box needs a bomber");
        if (order.pattern() != Pattern.USAAF_COMBAT_BOX_1943 && !fighter)
            throw new IllegalArgumentException("fighter doctrine needs a fighter");
        if (frame.formationAnchor() == null) return base;

        Vec3 local;
        Vec3 waypoint;
        Maneuver maneuver;
        String reason;

        if (order.pattern() == Pattern.USN_MUTUAL_SUPPORT_1942
                && frame.enemy() != null && frame.enemy().hostile()
                && frame.enemy().position().add(frame.self().position().scale(-1)).length() < 105
                && isEnemyBehind(frame)) {
            if (order.slot() > 1) throw new IllegalArgumentException("mutual-support pair has two slots");
            // Alternating cross-over is a deliberately simplified evasive weaving *candidate*.
            int phase = (int) ((frame.self().tick() / 45) % 2);
            double side = (order.slot() == phase ? -1 : 1) * 26;
            // Separate the two tracks vertically as an explicit collision safeguard.
            waypoint = station(frame.formationAnchor(), order.leaderYawDeg(),
                    new Vec3(side, order.slot() * 14, 16));
            maneuver = Maneuver.MUTUAL_SUPPORT_WEAVE;
            reason = "USN_MUTUAL_SUPPORT_REAR_THREAT";
        } else if ((order.pattern() == Pattern.RAF_FINGER_FOUR_1940
                || order.pattern() == Pattern.USN_MUTUAL_SUPPORT_1942)
                && (frame.enemy() == null || !frame.enemy().hostile())) {
            local = order.pattern() == Pattern.RAF_FINGER_FOUR_1940
                    ? fingerFourSlot(order.slot()) : pairedSlot(order.slot());
            waypoint = station(frame.formationAnchor(), order.leaderYawDeg(), local);
            maneuver = order.pattern() == Pattern.RAF_FINGER_FOUR_1940
                    ? Maneuver.FINGER_FOUR_HOLD : Maneuver.PAIRED_FORMATION_HOLD;
            reason = "HISTORICAL_FORMATION_STATION";
        } else if (order.pattern() == Pattern.USAAF_COMBAT_BOX_1943
                && frame.mission() == Mission.LEVEL_BOMB) {
            local = combatBoxSlot(order.slot());
            waypoint = station(frame.formationAnchor(), order.leaderYawDeg(), local);
            maneuver = Maneuver.COMBAT_BOX_HOLD;
            reason = "USAAF_BOMBER_MUTUAL_DEFENSE_STATION";
        } else if (order.pattern() == Pattern.USAAF_ESCORT_COVER_1944
                && frame.mission() == Mission.ESCORT
                && (frame.enemy() == null || !frame.enemy().hostile())) {
            local = escortSlot(order.slot());
            waypoint = station(frame.formationAnchor(), order.leaderYawDeg(), local);
            maneuver = Maneuver.ESCORT_SCREEN;
            reason = "USAAF_ESCORT_COVER_STATION";
        } else {
            return base;
        }

        double throttle = maneuver == Maneuver.COMBAT_BOX_HOLD ? 0.78 : 0.9;
        int ticks = memory.last() == maneuver
                ? (memory.ticksActive() == Integer.MAX_VALUE ? Integer.MAX_VALUE : memory.ticksActive() + 1)
                : 1;
        return new Decision(maneuver, TacticalAirAI.steer(frame, waypoint, throttle),
                waypoint, false, new Memory(maneuver, ticks), reason,
                "HISTORICAL_PATTERN+GAME_HEURISTIC:" + order.pattern().sourceUrl);
    }

    /** Right/forward/up offsets are Minecraft blocks and must be calibrated as gameplay. */
    public static Vec3 station(Vec3 leader, double headingDeg, Vec3 rightUpForward) {
        if (leader == null || rightUpForward == null || !Double.isFinite(headingDeg))
            throw new IllegalArgumentException("formation station");
        Vec3 f = forward(headingDeg, 0);
        Vec3 right = new Vec3(f.z(), 0, -f.x());
        return leader.add(right.scale(rightUpForward.x()))
                .add(0, rightUpForward.y(), 0)
                .add(f.scale(rightUpForward.z()));
    }

    private static boolean isEnemyBehind(Frame frame) {
        Vec3 toEnemy = frame.enemy().position().add(frame.self().position().scale(-1)).normalize();
        return forward(frame.self().yawDeg(), frame.self().pitchDeg()).dot(toEnemy) < -0.25;
    }

    private static Vec3 fingerFourSlot(int slot) {
        return switch (slot) {
            case 0 -> new Vec3(0, 0, 0);
            case 1 -> new Vec3(-20, 3, -18);
            case 2 -> new Vec3(22, 0, -24);
            case 3 -> new Vec3(39, 3, -40);
            default -> throw new IllegalArgumentException("finger-four slot must be 0..3");
        };
    }

    private static Vec3 pairedSlot(int slot) {
        return switch (slot) {
            case 0 -> new Vec3(-18, 0, -8);
            case 1 -> new Vec3(18, 0, -8);
            default -> throw new IllegalArgumentException("pair slot must be 0..1");
        };
    }

    private static Vec3 combatBoxSlot(int slot) {
        return switch (slot) {
            case 0 -> new Vec3(0, 0, 0);
            case 1 -> new Vec3(-24, 6, -18);
            case 2 -> new Vec3(24, 6, -18);
            case 3 -> new Vec3(-24, -8, -36);
            case 4 -> new Vec3(24, -8, -36);
            case 5 -> new Vec3(0, -14, -52);
            default -> throw new IllegalArgumentException("combat-box slot must be 0..5");
        };
    }

    private static Vec3 escortSlot(int slot) {
        return switch (slot) {
            case 0 -> new Vec3(-42, 28, 28);
            case 1 -> new Vec3(42, 28, 28);
            case 2 -> new Vec3(-48, 28, -40);
            case 3 -> new Vec3(48, 28, -40);
            default -> throw new IllegalArgumentException("escort slot must be 0..3");
        };
    }
}
