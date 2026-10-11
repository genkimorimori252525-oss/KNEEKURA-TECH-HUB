package org.kneekura.techhub.warfarewings.physics;

import java.util.Collections;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Independent, per-aircraft battlefield observation for the external 20 Hz twin.
 *
 * Synthetic sensors, terrain-height ray sampling, range, FOV and track lifetime
 * are explicit assumptions. This is NOT Minecraft's clip/voxel collision raycast.
 * Enemy truths can enter policy only through a current observation or a prior
 * track owned by that observer. Friendly telemetry is a separate team channel.
 */
public final class FlightTwinSensor {
    private FlightTwinSensor() {}

    public enum Visibility {
        VISIBLE, OUT_OF_RANGE, OUTSIDE_FOV, TERRAIN_OCCLUDED, COINCIDENT
    }

    public record Parameters(double rangeBlocks, double halfConeDegrees,
                             int trackLifetimeTicks, int terrainSamples,
                             double terrainMarginBlocks) {
        public Parameters {
            if (!Double.isFinite(rangeBlocks) || rangeBlocks <= 0
                    || !Double.isFinite(halfConeDegrees)
                    || halfConeDegrees <= 0 || halfConeDegrees > 180
                    || trackLifetimeTicks < 0 || trackLifetimeTicks > 200
                    || terrainSamples < 2 || terrainSamples > 2048
                    || !Double.isFinite(terrainMarginBlocks)
                    || terrainMarginBlocks < 0 || terrainMarginBlocks > 20)
                throw new IllegalArgumentException("invalid synthetic sensor specification");
        }

        /** Matches the existing SquadronCommand range/cone/TTL, with added LOS. */
        public static final Parameters DEFAULT = new Parameters(190, 150, 6, 24, 1.5);
    }

    public record Assessment(Visibility visibility, double rangeBlocks,
                             double noseDot, double sampledRayMinClearance) {
        public Assessment {
            if (visibility == null || !Double.isFinite(rangeBlocks)
                    || !Double.isFinite(noseDot))
                throw new IllegalArgumentException("invalid observation assessment");
        }
        public boolean visible() { return visibility == Visibility.VISIBLE; }
    }

    public record Track(Vec3 lastPosition, Vec3 lastVelocity, long lastSeenTick) {
        public Track {
            if (!finite(lastPosition) || !finite(lastVelocity) || lastSeenTick < 0)
                throw new IllegalArgumentException("invalid sensor track");
        }
        public Vec3 extrapolate(long now) {
            if (now < lastSeenTick) throw new IllegalArgumentException("reverse sensor clock");
            return lastPosition.add(lastVelocity.scale(now - lastSeenTick));
        }
    }

    public record Update(Map<String, Track> tracks, Map<String, Assessment> assessments,
                         Set<String> currentlyVisible, Set<String> expired,
                         int rememberedCount, int fovRejected, int losRejected,
                         int rangeRejected) {
        public Update {
            tracks = Collections.unmodifiableMap(new TreeMap<>(tracks));
            assessments = Collections.unmodifiableMap(new TreeMap<>(assessments));
            currentlyVisible = Collections.unmodifiableSet(new TreeSet<>(currentlyVisible));
            expired = Collections.unmodifiableSet(new TreeSet<>(expired));
        }
    }

    public static Assessment assess(State observer, State candidate,
                                    World terrain, Parameters p) {
        if (observer == null || candidate == null || terrain == null || p == null)
            throw new IllegalArgumentException("null sensor input");
        Vec3 eye = observer.position(), other = candidate.position();
        if (!finite(eye) || !finite(other))
            throw new IllegalArgumentException("nonfinite sensor state");
        Vec3 delta = other.add(eye.scale(-1));
        double distance = delta.length();
        if (distance <= 1e-9)
            return new Assessment(Visibility.COINCIDENT, distance, 0, Double.NaN);
        Vec3 towards = delta.scale(1.0 / distance);
        double dot = forward(observer.yawDeg(), observer.pitchDeg()).dot(towards);
        if (distance > p.rangeBlocks())
            return new Assessment(Visibility.OUT_OF_RANGE, distance, dot, Double.NaN);
        if (dot < Math.cos(Math.toRadians(p.halfConeDegrees())))
            return new Assessment(Visibility.OUTSIDE_FOV, distance, dot, Double.NaN);
        // Sample the entire line including endpoints. Each endpoint must be
        // geometrically above the estimated local terrain by the given margin.
        // No ability to see through an analytic ridge between the aircraft.
        double minClearance = Double.POSITIVE_INFINITY;
        for (int i = 0; i <= p.terrainSamples(); i++) {
            double fraction = (double) i / p.terrainSamples();
            Vec3 sample = eye.add(delta.scale(fraction));
            double ground = terrain.groundHeight(sample.x(), sample.z());
            if (!Double.isFinite(ground))
                throw new IllegalArgumentException("unresolved synthetic terrain LOS height");
            minClearance = Math.min(minClearance, sample.y() - ground);
            if (sample.y() - ground <= p.terrainMarginBlocks())
                return new Assessment(Visibility.TERRAIN_OCCLUDED, distance, dot, minClearance);
        }
        return new Assessment(Visibility.VISIBLE, distance, dot, minClearance);
    }

    public static Update update(long tick, State own, Map<String, State> hostiles,
                                Map<String, Track> remembered,
                                World terrain, Parameters p) {
        if (tick < 0 || own == null || hostiles == null || remembered == null
                || terrain == null || p == null)
            throw new IllegalArgumentException("invalid sensor snapshot");
        Map<String, Track> next = new TreeMap<>();
        Set<String> visible = new TreeSet<>(), expired = new TreeSet<>();
        Map<String, Assessment> assessments = new TreeMap<>();
        int los = 0, fov = 0, range = 0;
        for (var entry : remembered.entrySet()) {
            if (!hostiles.containsKey(entry.getKey()))
                throw new IllegalArgumentException("remembered target not on enemy roster");
            if (entry.getValue().lastSeenTick() > tick)
                throw new IllegalArgumentException("track recorded in the future");
            if (tick - entry.getValue().lastSeenTick() <= p.trackLifetimeTicks())
                next.put(entry.getKey(), entry.getValue());
            else expired.add(entry.getKey());
        }
        for (var hostile : new TreeMap<>(hostiles).entrySet()) {
            Assessment verdict = assess(own, hostile.getValue(), terrain, p);
            assessments.put(hostile.getKey(), verdict);
            switch (verdict.visibility()) {
                case VISIBLE -> {
                    next.put(hostile.getKey(), new Track(
                            hostile.getValue().position(), hostile.getValue().velocity(), tick));
                    visible.add(hostile.getKey());
                }
                case OUT_OF_RANGE -> range++;
                case OUTSIDE_FOV -> fov++;
                case TERRAIN_OCCLUDED -> los++;
                case COINCIDENT -> { }
            }
        }
        int stale = 0;
        for (var value : next.values()) if (value.lastSeenTick() < tick) stale++;
        return new Update(next, assessments, visible, expired, stale, fov, los, range);
    }

    private static boolean finite(Vec3 value) {
        return value != null && Double.isFinite(value.x())
                && Double.isFinite(value.y()) && Double.isFinite(value.z());
    }
}
