package org.kneekura.techhub.warfarewings.physics;

import java.util.List;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

/**
 * Conservative world/squadron safety layer between tactical waypoints and raw controls.
 * All distances are Minecraft blocks, velocities blocks/tick. Terrain samples are
 * supplied by the real world adapter or a deterministic synthetic test field.
 * The altitude guard is an engineering margin, not a certified stall or collision model.
 */
public final class FlightSafetyPlanner {
    private static final int[] LOOKAHEAD_TICKS = {4, 8, 15, 25};
    private FlightSafetyPlanner() {}

    public interface Terrain {
        double topY(double x, double z);
    }
    public record MovingObstacle(String id, Vec3 position, Vec3 velocity, double radius) {
        public MovingObstacle {
            if (id == null || id.isBlank() || !finite(position) || !finite(velocity)
                    || !Double.isFinite(radius) || radius <= 0)
                throw new IllegalArgumentException("obstacle");
        }
    }
    public record Environment(Terrain terrain, List<MovingObstacle> obstacles, double ownRadius) {
        public Environment {
            if (terrain == null || obstacles == null || !Double.isFinite(ownRadius) || ownRadius <= 0)
                throw new IllegalArgumentException("environment");
            obstacles = List.copyOf(obstacles);
        }
    }
    public enum Reason { CLEAR, TERRAIN_AHEAD, MOVING_COLLISION_RISK, LOW_SPEED_RESERVE }
    public record Clearance(Vec3 waypoint, Reason reason, double minPredictedClearance,
                            String obstacleId, boolean override) {}

    public static Clearance guard(Frame frame, Vec3 tacticalWaypoint, Environment environment) {
        if (frame == null || !finite(tacticalWaypoint) || environment == null)
            throw new IllegalArgumentException("safety inputs");
        State self = frame.self();
        Vec3 pos = self.position(), velocity = self.velocity();
        double currentSpeedBps = velocity.length() * TICKS_PER_SECOND;
        double required = Math.max(12, currentSpeedBps * 0.38);
        double minimum = pos.y() - checkedTop(environment.terrain(), pos.x(), pos.z());
        boolean terrainThreat = minimum < required;
        for (int t : LOOKAHEAD_TICKS) {
            Vec3 predicted = pos.add(velocity.scale(t));
            // Conservative additional sink from unmodeled speed loss/gravity,
            // not a physical prediction of IA's custom gravity.
            double sinkAllowance = Math.min(9, t * t * 0.009);
            double clearance = predicted.y() - sinkAllowance
                    - checkedTop(environment.terrain(), predicted.x(), predicted.z());
            minimum = Math.min(minimum, clearance);
            if (clearance < required + 4) terrainThreat = true;
        }
        if (terrainThreat) {
            Vec3 horizontal = new Vec3(velocity.x(), 0, velocity.z()).normalize();
            if (horizontal.lengthSquared() < 1e-9) {
                Vec3 f = forward(self.yawDeg(), 0);
                horizontal = new Vec3(f.x(), 0, f.z()).normalize();
            }
            Vec3 climb = pos.add(horizontal.scale(65)).add(0, Math.max(70, required * 3), 0);
            return new Clearance(climb, Reason.TERRAIN_AHEAD, minimum, null, true);
        }

        MovingObstacle nearest = null;
        double closestGap = Double.POSITIVE_INFINITY;
        double atTick = 0;
        for (MovingObstacle obstacle : environment.obstacles()) {
            Vec3 delta = obstacle.position().add(pos.scale(-1));
            Vec3 relativeVelocity = obstacle.velocity().add(velocity.scale(-1));
            double relLen2 = relativeVelocity.lengthSquared();
            double t = relLen2 < 1e-12 ? 0
                    : clamp(-delta.dot(relativeVelocity) / relLen2, 0, 30);
            double gap = delta.add(relativeVelocity.scale(t)).length()
                    - obstacle.radius() - environment.ownRadius();
            if (gap < closestGap) {
                closestGap = gap;
                nearest = obstacle;
                atTick = t;
            }
        }
        if (nearest != null && closestGap < 8.0) {
            Vec3 projectedSelf = pos.add(velocity.scale(atTick));
            Vec3 projectedObstacle = nearest.position().add(nearest.velocity().scale(atTick));
            Vec3 away = projectedSelf.add(projectedObstacle.scale(-1));
            Vec3 horizontal = new Vec3(away.x(), 0, away.z()).normalize();
            if (horizontal.lengthSquared() < 1e-9) {
                Vec3 f = forward(self.yawDeg(), 0);
                horizontal = new Vec3(f.z(), 0, -f.x());
            }
            Vec3 avoid = pos.add(horizontal.scale(65)).add(0, 24, 0);
            return new Clearance(avoid, Reason.MOVING_COLLISION_RISK,
                    minimum, nearest.id(), true);
        }

        // A SOURCE-only reserve: never call this an aerodynamic stall speed.
        if (currentSpeedBps < frame.profile().predictedTopSpeedBps() * 0.23
                && self.position().y() - frame.terrainHeight() < 65
                && self.position().y() > frame.terrainHeight() + required + 5) {
            Vec3 f = forward(self.yawDeg(), 0);
            return new Clearance(pos.add(f.scale(75)).add(0, -5, 0),
                    Reason.LOW_SPEED_RESERVE, minimum, null, true);
        }
        return new Clearance(tacticalWaypoint, Reason.CLEAR, minimum, null, false);
    }

    private static double checkedTop(Terrain terrain, double x, double z) {
        double top = terrain.topY(x, z);
        if (!Double.isFinite(top)) throw new IllegalArgumentException("unknown terrain elevation");
        return top;
    }
    private static boolean finite(Vec3 v) {
        return v != null && Double.isFinite(v.x()) && Double.isFinite(v.y())
                && Double.isFinite(v.z());
    }
    private static double clamp(double v, double a, double b) {
        return Math.max(a, Math.min(b, v));
    }
}
