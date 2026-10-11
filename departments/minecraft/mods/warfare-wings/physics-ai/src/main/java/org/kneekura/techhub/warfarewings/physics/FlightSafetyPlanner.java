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
    public record MovingObstacle(String id, Vec3 position, Vec3 velocity,
                                 double radius, boolean observedHostile) {
        public MovingObstacle(String id, Vec3 position, Vec3 velocity, double radius) {
            this(id, position, velocity, radius, false);
        }
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
        MovingObstacle urgentFriendly = null;
        // Squadmates' current measured positions/velocities arrive by team
        // radio. Large formations need an additional vertical deconfliction
        // lane because the IA steering filter limits fast lateral avoidance.
        // Small independent patrols and original escort flight envelopes
        // retain their original right-turn policy and altitude requests.
        long knownSquadmates = environment.obstacles().stream()
                .filter(obstacle -> !obstacle.observedHostile()).count();
        boolean largeFormation = knownSquadmates >= 4;
        double closestGap = Double.POSITIVE_INFINITY;
        double highestRisk = Double.POSITIVE_INFINITY;
        double atTick = 0;
        double urgentFriendlyGap = Double.POSITIVE_INFINITY;
        double urgentFriendlyTick = 0;
        for (MovingObstacle obstacle : environment.obstacles()) {
            Vec3 delta = obstacle.position().add(pos.scale(-1));
            Vec3 relativeVelocity = obstacle.velocity().add(velocity.scale(-1));
            double relLen2 = relativeVelocity.lengthSquared();
            // Aircraft closing head-on need lead time for IA's filtered X input
            // to turn the aircraft. The 55-tick horizon is a laboratory guard,
            // not a predicted exact Minecraft collision envelope.
            double horizon = obstacle.observedHostile() ? 55 : 30;
            double t = relLen2 < 1e-12 ? 0
                    : clamp(-delta.dot(relativeVelocity) / relLen2, 0, horizon);
            double gap = delta.add(relativeVelocity.scale(t)).length()
                    - obstacle.radius() - environment.ownRadius();
            // A team aircraft is independently observed via squadron radio.
            // Give a near-term real body encounter its own right of way:
            // otherwise a low-scoring, *later* hostile CPA can mask this
            // physically imminent friendly encounter until steering is late.
            if (largeFormation && !obstacle.observedHostile() && t <= 16.0 && gap < 0
                    && delta.length() < 45
                    && (gap < urgentFriendlyGap - 1e-9
                        || Math.abs(gap - urgentFriendlyGap) <= 1e-9
                        && (urgentFriendly == null || obstacle.id().compareTo(urgentFriendly.id()) < 0))) {
                urgentFriendly = obstacle;
                urgentFriendlyGap = gap;
                urgentFriendlyTick = t;
            }
            // Compare each encounter to its own action margin; otherwise a
            // safe ally with a smaller raw gap can hide a hostile collision.
            double risk = gap - (obstacle.observedHostile() ? 22.0 : 8.0);
            if (risk < highestRisk - 1e-9
                    || Math.abs(risk - highestRisk) <= 1e-9
                    && (nearest == null || obstacle.id().compareTo(nearest.id()) < 0)) {
                highestRisk = risk;
                closestGap = gap;
                nearest = obstacle;
                atTick = t;
            }
        }
        if (urgentFriendly != null) {
            nearest = urgentFriendly;
            closestGap = urgentFriendlyGap;
            atTick = urgentFriendlyTick;
            highestRisk = urgentFriendlyGap - 8.0;
        }
        if (nearest != null && highestRisk < 0) {
            // An aircraft already withdrawing for fuel or structural integrity
            // must not be held indefinitely by a distant hypothetical CPA.
            // Retain immediate collision safeguards inside the short horizon.
            if (nearest.observedHostile()
                    && (frame.fuelFraction() < 0.12 || frame.integrityFraction() < 0.22)
                    && (atTick > 3.0
                        || nearest.position().add(pos.scale(-1)).length() > 14.0))
                return new Clearance(tacticalWaypoint, Reason.CLEAR, minimum, null, false);
            Vec3 projectedSelf = pos.add(velocity.scale(atTick));
            Vec3 projectedObstacle = nearest.position().add(nearest.velocity().scale(atTick));
            Vec3 away = projectedSelf.add(projectedObstacle.scale(-1));
            Vec3 forwardHorizontal = forward(self.yawDeg(), 0);
            Vec3 right = new Vec3(forwardHorizontal.z(), 0, -forwardHorizontal.x()).normalize();
            // Reciprocal head-on aircraft use their respective right sides,
            // placing them on opposite sides of the same projected track.
            // For allies retain the measured projected CPA outward direction.
            Vec3 horizontal = nearest.observedHostile()
                    ? right : new Vec3(away.x(), 0, away.z()).normalize();
            if (horizontal.lengthSquared() < 1e-9) {
                horizontal = right;
            }
            // A reciprocal horizontal pass can still have overlapping wings:
            // source aircraft have IA input latency and finite turn radius.
            // When BOTH pilots can currently see one another, their measured
            // relative altitude gives reciprocal up/down avoidance without
            // consulting global aircraft positions. Keep the older horizontal
            // reciprocal turn; add a physically commanded vertical separation.
            double verticalOffset = nearest.observedHostile() ? 3 : 24;
            if (largeFormation && (nearest.observedHostile() || nearest == urgentFriendly)) {
                double altitudeDifference = pos.y() - nearest.position().y();
                if (Math.abs(altitudeDifference) < 0.5) {
                    // Equal-height pilots must make opposite choices too.
                    // Absolute-world position is directly observed and
                    // antisymmetric in the two aircraft's perspectives.
                    double lateralDifference = pos.x() - nearest.position().x();
                    if (Math.abs(lateralDifference) < 0.5)
                        lateralDifference = pos.z() - nearest.position().z();
                    altitudeDifference = lateralDifference;
                }
                double verticalDistance = nearest.observedHostile() ? 60 : 45;
                if (altitudeDifference >= 0) {
                    verticalOffset = verticalDistance;
                } else {
                    double terrainReserve = pos.y() - checkedTop(environment.terrain(), pos.x(), pos.z())
                            - required - 18;
                    verticalOffset = -Math.min(verticalDistance, Math.max(0, terrainReserve));
                }
            }
            Vec3 avoid = pos.add(horizontal.scale(nearest.observedHostile() ? 125 : 65))
                    .add(forwardHorizontal.scale(nearest.observedHostile() ? 35 : 0))
                    .add(0, verticalOffset, 0);
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
