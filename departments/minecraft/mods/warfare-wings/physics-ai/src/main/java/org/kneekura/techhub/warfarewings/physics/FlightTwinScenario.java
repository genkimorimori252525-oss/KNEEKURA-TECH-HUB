package org.kneekura.techhub.warfarewings.physics;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.SplittableRandom;
import java.util.TreeMap;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/** Fixed historical-game test geometries and a separately seeded all-24 stress case. */
public final class FlightTwinScenario {
    public static final double BODY_SEPARATION_BLOCKS = 6.0;
    public static final double B17_PROTECTION_BLOCKS = 95.0;
    public static final Vec3 ORIGINAL_OBJECTIVE = new Vec3(0, 170, 280);
    public static final Vec3 ORIGINAL_HOME = new Vec3(0, 170, -220);

    private FlightTwinScenario() {}

    public record Plane(String id, String typeId, String team, String flight, int slot,
                        TacticalAirAI.Mission mission, String escortAsset,
                        Vec3 start, Vec3 velocity, double yaw,
                        Vec3 objective, Vec3 home, double fuelFraction) {
        public Plane {
            if (id == null || id.isBlank() || typeId == null || typeId.isBlank()
                    || team == null || team.isBlank()
                    || flight == null || flight.isBlank() || mission == null
                    || start == null || velocity == null || objective == null || home == null
                    || slot < 0 || slot > 5 || !Double.isFinite(yaw)
                    || !Double.isFinite(fuelFraction) || fuelFraction < 0 || fuelFraction > 1)
                throw new IllegalArgumentException("invalid Flight Twin plane specification");
        }
    }

    public record Case(String id, List<Plane> planes, Map<String, String> escortAssets,
                       int ticks, World world, boolean unique24, String environmentLabel) {
        public Case {
            if (id == null || id.isBlank() || planes == null || planes.size() < 2
                    || escortAssets == null || world == null
                    || ticks < 10 || ticks > 2400 || environmentLabel == null)
                throw new IllegalArgumentException("invalid Flight Twin case");
            planes = List.copyOf(planes);
            escortAssets = Map.copyOf(escortAssets);
            Set<String> ids = new HashSet<>();
            for (Plane p : planes)
                if (!ids.add(p.id())) throw new IllegalArgumentException("duplicate twin unit ID");
            for (var escorted : escortAssets.entrySet()) {
                Plane fighter = planes.stream().filter(p -> p.id().equals(escorted.getKey()))
                        .findFirst().orElseThrow();
                Plane asset = planes.stream().filter(p -> p.id().equals(escorted.getValue()))
                        .findFirst().orElseThrow();
                if (!fighter.team().equals(asset.team())
                        || !asset.id().equals(fighter.escortAsset())
                        || fighter.mission() != TacticalAirAI.Mission.ESCORT)
                    throw new IllegalArgumentException("invalid Flight Twin escort pair");
            }
        }
    }

    /** Flat SOURCE terrain + exact, speed-dependent pinned calm-weather wind. */
    public static final World PINNED_FLAT = PinnedIa133WindWorld.calmAirCalibration();

    /** Terrain height is an analytical *synthetic* silhouette for the sensor LOS probe. */
    public static final class SyntheticRidgeWorld implements World {
        @Override public double groundHeight(double x, double z) {
            // Deliberate LOS barrier in the centre of the original 90-block
            // opposing start. It is not Minecraft collision geometry.
            return z >= 37 && z <= 58 && Math.abs(x) <= 48 ? 220.0 : 0.0;
        }
        @Override public Wind windAfterFriction(Model model, State state, Vec3 velocity) {
            return PINNED_FLAT.windAfterFriction(model, state, velocity);
        }
    }

    private static Plane plane(String id, String type, String team,
                               String flight, int slot, TacticalAirAI.Mission mission,
                               String asset, double x, double y, double z,
                               double yaw, double speed) {
        return new Plane(id, "warfare_wings:" + type, team, flight, slot,
                mission, asset, new Vec3(x, y, z),
                forward(yaw, 0).scale(speed), yaw,
                ORIGINAL_OBJECTIVE, ORIGINAL_HOME, 1.0);
    }

    public static Case original2v2() {
        // Exact undiluted 2v2 start from CombatSimulationSelfTest.twoVsTwo.
        return new Case("original_2v2",
                List.of(
                        plane("a1","a6m","a","patrol",0,TacticalAirAI.Mission.INTERCEPT,
                                null,-35,170,0,0,1.2),
                        plane("a2","f4u","a","patrol",1,TacticalAirAI.Mission.INTERCEPT,
                                null,35,170,0,0,1.2),
                        plane("b1","bf109","b","patrol",0,TacticalAirAI.Mission.INTERCEPT,
                                null,-35,170,105,180,1.2),
                        plane("b2","p47n","b","patrol",1,TacticalAirAI.Mission.INTERCEPT,
                                null,35,170,105,180,1.2)),
                Map.of(),160,PINNED_FLAT,false,"PINNED_IA133_CALM_FLAT");
    }

    public static Case originalB17Aft() {
        return b17("original_b17_aft", -65, -20, 65, -20);
    }

    public static Case originalB17Forward() {
        return b17("original_b17_forward", -27, 115, 27, 115);
    }

    private static Case b17(String name, double escort1X, double escort1Z,
                             double escort2X, double escort2Z) {
        // Both cases preserve the CombatSimulationSelfTest original B17
        // reference, incoming A6M and 95b protection radius.
        return new Case(name,
                List.of(
                        plane("cargo","b17","blue","bomb",0,
                                TacticalAirAI.Mission.LEVEL_BOMB,null,
                                0,170,0,0,0.8),
                        plane("cover1","f4u","blue","cover",0,
                                TacticalAirAI.Mission.ESCORT,"cargo",
                                escort1X,190,escort1Z,0,1.0),
                        plane("cover2","p47n","blue","cover",1,
                                TacticalAirAI.Mission.ESCORT,"cargo",
                                escort2X,190,escort2Z,0,1.0),
                        plane("raid","a6m","red","raid",0,
                                TacticalAirAI.Mission.INTERCEPT,null,
                                0,170,170,180,1.3)),
                Map.of("cover1","cargo","cover2","cargo"),
                190,PINNED_FLAT,false,"PINNED_IA133_CALM_FLAT");
    }

    public static Case occludedContact() {
        return new Case("synthetic_los_occluded",
                List.of(
                        plane("seen_from_blue","a6m","blue","probe",0,
                                TacticalAirAI.Mission.INTERCEPT,null,
                                0,170,0,0,1.2),
                        plane("seen_from_red","bf109","red","probe",0,
                                TacticalAirAI.Mission.INTERCEPT,null,
                                0,170,90,180,1.2)),
                Map.of(),90,new SyntheticRidgeWorld(),false,
                "SYNTHETIC_TERRAIN_OCCLUSION_PINNED_IA133_WIND");
    }

    /**
     * Explicit *scenario operator* team choices for an arbitrary 12v12 physics
     * stress experiment. No nationality, manufacturer, faction, uniform or
     * historical allegiance is inferred by any sensor, pilot or policy.
     */
    private static final Set<String> OPERATOR_SELECTED_BLUE_TYPES = Set.of(
            "a6m","b17","b29","d4y","f4u","f6f","g4m","il2","ju87",
            "p47n","p51d","spitfire");

    public static Case all24(List<AircraftAtlasMain.Entry> atlas, long seed, int ticks) {
        if (atlas.size() != 24) throw new IllegalArgumentException("Expected 24 unique airframes");
        Map<String, AircraftAtlasMain.Entry> sorted = new TreeMap<>();
        for (var entry : atlas)
            if (sorted.putIfAbsent(entry.baseId(), entry) != null)
                throw new IllegalArgumentException("Duplicate 24-aircraft model");
        if (sorted.size() != 24) throw new IllegalArgumentException("Duplicate 24-aircraft types");
        List<Plane> roster = new ArrayList<>();
        int blue = 0, red = 0;
        for (var entry : sorted.values()) {
            String base = entry.baseId();
            boolean friendly = OPERATOR_SELECTED_BLUE_TYPES.contains(base);
            int index = friendly ? blue++ : red++;
            SplittableRandom rng = new SplittableRandom(
                    stableSeed(seed, entry.aircraftId()));
            int column = index % 4, lane = index / 4;
            double x = (column - 1.5) * 63 + rng.nextDouble(-5,5);
            double y = 184 + 27 * lane + rng.nextDouble(-4,4);
            double z = friendly ? -20 - 38 * lane + rng.nextDouble(-5,5)
                    : 200 + 38 * lane + rng.nextDouble(-5,5);
            double yaw = friendly ? 0 : 180;
            double airspeed = 0.78 + rng.nextDouble(0.2, 0.48);
            TacticalAirAI.Mission mission = switch (entry.role()) {
                case "bomber" -> TacticalAirAI.Mission.LEVEL_BOMB;
                case "torpedo_bomber" -> TacticalAirAI.Mission.TORPEDO;
                case "attacker" -> TacticalAirAI.Mission.DIVE_BOMB;
                default -> TacticalAirAI.Mission.INTERCEPT;
            };
            String escort = null;
            String flight = base + "-flight";
            int slot = 0;
            // A true 24-airframe concurrent stress test includes an actual
            // B17 with living physical F4U/P47N escorts on the allied team.
            if (base.equals("f4u") || base.equals("p47n")) {
                escort = "type-b17";
                mission = TacticalAirAI.Mission.ESCORT;
                flight = "b17-cover";
                slot = base.equals("f4u") ? 0 : 1;
            }
            roster.add(new Plane("type-" + base, entry.aircraftId(),
                    friendly ? "blue" : "red", flight, slot, mission, escort,
                    new Vec3(x,y,z), forward(yaw,0).scale(airspeed), yaw,
                    new Vec3(x,y, friendly ? 340 : -210),
                    new Vec3(x,y, friendly ? -330 : 420), 1.0));
        }
        if (blue != 12 || red != 12)
            throw new IllegalStateException("Expected explicit balanced 12v12 unique models");
        return new Case("all_24_unique", roster,
                Map.of("type-f4u","type-b17","type-p47n","type-b17"),
                ticks,PINNED_FLAT,true,"PINNED_IA133_CALM_FLAT");
    }

    private static long stableSeed(long seed, String aircraftId) {
        long v = seed ^ ((long) aircraftId.hashCode() * 0x9E3779B97F4A7C15L);
        v ^= (v >>> 30); v *= 0xBF58476D1CE4E5B9L;
        v ^= (v >>> 27); v *= 0x94D049BB133111EBL;
        return v ^ (v >>> 31);
    }
}
