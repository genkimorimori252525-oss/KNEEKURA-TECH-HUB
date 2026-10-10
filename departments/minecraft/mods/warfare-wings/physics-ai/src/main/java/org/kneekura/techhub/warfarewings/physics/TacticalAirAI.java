package org.kneekura.techhub.warfarewings.physics;

import java.util.Locale;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Deterministic mission/engagement decision layer for the Warfare Wings source laboratory.
 *
 * Aircraft-specific control authority comes from the 24-aircraft source Atlas. Mission and
 * historical doctrine are explicit inputs: nationality alone never selects a combat tactic.
 * Steering returns raw IA X/Z inputs; the microkernel applies the real input phase lag.
 *
 * This is a headless decision model, not a Forge entity controller or a claim of runtime
 * combat parity. No projectile is emitted by this class.
 */
public final class TacticalAirAI {
    public static final String SCHEMA = "ww.tactics.decision.v1";
    private static final double EPS = 1e-9;

    private TacticalAirAI() {}

    public enum Mission { PATROL, INTERCEPT, ESCORT, LEVEL_BOMB, DIVE_BOMB, STRAFE, TORPEDO }
    public enum Maneuver {
        PATROL_ROUTE, INTERCEPT, TURN_PURSUIT, HIGH_SIDE_PASS, EXTEND_AND_REENTER,
        DEFENSIVE_BREAK, ESCORT_SCREEN, FORMATION_HOLD, LEVEL_BOMB_RUN,
        DIVE_ATTACK, STRAFING_RUN, TORPEDO_APPROACH, RETURN_HOME,
        COLLISION_AVOID, TERRAIN_RECOVERY, FINGER_FOUR_HOLD, PAIRED_FORMATION_HOLD,
        COMBAT_BOX_HOLD, MUTUAL_SUPPORT_WEAVE
    }

    /** All performance axes are SOURCE_MICROKERNEL until exact-runtime calibration. */
    public record Profile(
            String aircraftId, String role, String faction, String atlasDoctrine,
            double predictedTopSpeedBps, double yawChange20TicksDeg,
            int ticksTo90Yaw, double equalAngle90SpeedRetention) {
        public Profile {
            if (aircraftId == null || aircraftId.isBlank()
                    || role == null || faction == null || atlasDoctrine == null)
                throw new IllegalArgumentException("aircraft identity");
            if (!Double.isFinite(predictedTopSpeedBps) || predictedTopSpeedBps <= 0
                    || !Double.isFinite(yawChange20TicksDeg) || yawChange20TicksDeg <= 0
                    || ticksTo90Yaw <= 0
                    || !Double.isFinite(equalAngle90SpeedRetention)
                    || equalAngle90SpeedRetention <= 0 || equalAngle90SpeedRetention > 1.01)
                throw new IllegalArgumentException("invalid Atlas metrics");
        }
        public static Profile fromAtlas(AircraftAtlasMain.Metrics row) {
            if (!row.evidence().startsWith("SOURCE_MICROKERNEL+"))
                throw new IllegalArgumentException("Atlas provenance must be explicit");
            return new Profile(row.aircraftId(), row.role(), row.faction(), row.doctrine(),
                    row.predictedTopSpeedBps(), row.yawChange20TicksDeg(),
                    row.ticksTo90Yaw(), row.equalAngle90SpeedRetention());
        }
    }

    public record Contact(String id, Vec3 position, Vec3 velocity, boolean hostile) {
        public Contact {
            if (id == null || id.isBlank() || position == null || velocity == null)
                throw new IllegalArgumentException("contact");
            requireFinite(position);
            requireFinite(velocity);
        }
    }

    /**
     * Explicit scenario facts; objective/home/formationAnchor are world-space coordinates.
     * A null enemy/formationAnchor means no observed contact/leader. nearestFriendlyPosition
     * is an independent collision contact and MUST NOT be synthesized from an abstract
     * formation station or objective.
     * Historical training
     * cases can override Mission independently of the aircraft's faction.
     */
    public record Frame(
            Profile profile, Model model, State self, Mission mission,
            Vec3 objective, Vec3 home, Contact enemy, Vec3 formationAnchor,
            Vec3 nearestFriendlyPosition,
            double fuelFraction, double integrityFraction,
            double terrainHeight, boolean lineOfFireClear, double projectileSpeedBpt) {
        public Frame {
            if (profile == null || model == null || self == null || mission == null
                    || objective == null || home == null) throw new IllegalArgumentException("frame");
            if (!profile.aircraftId().equals(model.id())
                    || !profile.role().equals(model.role())
                    || !profile.atlasDoctrine().equals(model.doctrine()))
                throw new IllegalArgumentException("model and Atlas identity/role/doctrine disagree");
            if (mission == Mission.TORPEDO && !profile.role().equals("torpedo_bomber")
                    || mission == Mission.DIVE_BOMB && !profile.role().equals("attacker")
                    || mission == Mission.LEVEL_BOMB && !profile.role().equals("bomber")
                    || mission == Mission.STRAFE && !(profile.role().equals("attacker")
                        || profile.role().equals("fighter")))
                throw new IllegalArgumentException("unsupported mission/aircraft role (weapon loadout still requires Forge check)");
            requireFinite(objective);
            requireFinite(home);
            if (formationAnchor != null) requireFinite(formationAnchor);
            if (nearestFriendlyPosition != null) requireFinite(nearestFriendlyPosition);
            if (!Double.isFinite(fuelFraction) || fuelFraction < 0 || fuelFraction > 1
                    || !Double.isFinite(integrityFraction) || integrityFraction < 0 || integrityFraction > 1
                    || !Double.isFinite(terrainHeight)
                    || !Double.isFinite(projectileSpeedBpt) || projectileSpeedBpt < 0)
                throw new IllegalArgumentException("frame fractions/terrain/weapon");
        }
    }

    public record Memory(Maneuver last, int ticksActive) {
        public static final Memory INITIAL = new Memory(Maneuver.PATROL_ROUTE, 0);
        public Memory {
            if (last == null || ticksActive < 0) throw new IllegalArgumentException("memory");
        }
    }

    public record Decision(Maneuver maneuver, Control controls, Vec3 steeringPoint,
                           boolean firingWindowCandidate, Memory nextMemory,
                           String reasonCode, String performanceEvidence) {}

    /**
     * Single deterministic 20 Hz decision. Priority:
     * terrain -> friendly separation -> aircraft survival -> mission -> hostile contact.
     */
    public static Decision decide(Frame frame, Memory memory) {
        if (frame == null || memory == null) throw new IllegalArgumentException("null decision");
        State self = frame.self();
        Vec3 position = self.position();
        Vec3 forward = forward(self.yawDeg(), self.pitchDeg());
        double speed = self.velocity().length() * TICKS_PER_SECOND;
        Vec3 target = frame.objective();
        Maneuver maneuver;
        String why;

        double altitude = position.y() - frame.terrainHeight();
        double minRecoveryAlt = Math.max(12.0, speed * 0.45);
        if (altitude < minRecoveryAlt && (self.velocity().y() < 0.02 || altitude < 8)) {
            maneuver = Maneuver.TERRAIN_RECOVERY;
            Vec3 horizontal = new Vec3(forward.x(), 0, forward.z()).normalize();
            if (horizontal.lengthSquared() < EPS) {
                horizontal = new Vec3(self.velocity().x(), 0, self.velocity().z()).normalize();
            }
            if (horizontal.lengthSquared() < EPS) horizontal = new Vec3(0, 0, 1);
            target = position.add(horizontal.scale(55)).add(0, Math.max(60, speed * 2), 0);
            why = "TERRAIN_CLEARANCE";
        } else if (frame.nearestFriendlyPosition() != null
                && frame.nearestFriendlyPosition().add(position.scale(-1)).length() < 12.0) {
            maneuver = Maneuver.COLLISION_AVOID;
            Vec3 away = position.add(frame.nearestFriendlyPosition().scale(-1)).normalize();
            if (away.lengthSquared() < EPS) away = new Vec3(1, 0, 0);
            target = position.add(away.scale(36)).add(0, 12, 0);
            why = "FRIENDLY_SEPARATION";
        } else if (frame.fuelFraction() < 0.12 || frame.integrityFraction() < 0.22) {
            maneuver = Maneuver.RETURN_HOME;
            target = frame.home();
            why = "FUEL_OR_DAMAGE_WITHDRAWAL";
        } else if (frame.mission() == Mission.ESCORT && frame.profile().role().equals("fighter")
                && frame.formationAnchor() != null && frame.enemy() != null
                && frame.enemy().hostile()
                && frame.enemy().position().add(frame.formationAnchor().scale(-1)).length() > 100) {
            maneuver = Maneuver.ESCORT_SCREEN;
            target = frame.formationAnchor().add(0, 22, 26);
            why = "ESCORT_ENGAGEMENT_LEASH";
        } else if (!frame.profile().role().equals("fighter")
                && frame.enemy() != null && frame.enemy().hostile()
                && frame.enemy().position().add(position.scale(-1)).length() < 65
                && forward.dot(frame.enemy().position().add(position.scale(-1)).normalize()) < -0.25
                && frame.enemy().velocity().normalize()
                    .dot(position.add(frame.enemy().position().scale(-1)).normalize()) > 0.5) {
            maneuver = Maneuver.DEFENSIVE_BREAK;
            Vec3 away = position.add(frame.enemy().position().scale(-1)).normalize();
            target = position.add(away.scale(55)).add(0, 20, 0);
            why = "REAR_THREAT_ABORT_ATTACK_RUN";
        } else if (frame.mission() == Mission.LEVEL_BOMB) {
            maneuver = Maneuver.LEVEL_BOMB_RUN;
            target = new Vec3(target.x(), Math.max(position.y(), frame.terrainHeight() + 45), target.z());
            why = "BOMBER_LEVEL_APPROACH";
        } else if (frame.mission() == Mission.TORPEDO) {
            maneuver = Maneuver.TORPEDO_APPROACH;
            target = new Vec3(target.x(), frame.terrainHeight() + 14, target.z());
            why = "LOW_ALTITUDE_TARGET_APPROACH";
        } else if (frame.mission() == Mission.DIVE_BOMB) {
            maneuver = Maneuver.DIVE_ATTACK;
            why = "DIVE_BOMB_APPROACH";
        } else if (frame.mission() == Mission.STRAFE) {
            maneuver = Maneuver.STRAFING_RUN;
            why = "GROUND_ATTACK_APPROACH";
        } else if (frame.enemy() != null && frame.enemy().hostile()
                && !frame.profile().role().equals("fighter")) {
            maneuver = Maneuver.DEFENSIVE_BREAK;
            Vec3 away = position.add(frame.enemy().position().scale(-1)).normalize();
            if (away.lengthSquared() < EPS) away = new Vec3(1, 0, 0);
            target = position.add(away.scale(55)).add(0, 12, 0);
            why = "NON_FIGHTER_SURVIVAL";
        } else if (frame.enemy() != null && frame.enemy().hostile()) {
            Contact enemy = frame.enemy();
            double range = enemy.position().add(position.scale(-1)).length();
            Vec3 toEnemy = enemy.position().add(position.scale(-1)).normalize();
            boolean enemyOnTail = range < 75 && enemy.velocity().normalize()
                    .dot(position.add(enemy.position().scale(-1)).normalize()) > 0.80
                    && forward.dot(toEnemy) < -0.25;
            boolean above = position.y() - enemy.position().y() > 15;
            boolean fastEnough = speed >= frame.profile().predictedTopSpeedBps() * 0.80;
            if (enemyOnTail && range < 45 && !above) {
                maneuver = Maneuver.DEFENSIVE_BREAK;
                Vec3 lateral = new Vec3(forward.z(), 0, -forward.x());
                double sign = Math.signum(lateral.dot(toEnemy));
                if (sign == 0) sign = 1;
                target = position.add(lateral.scale(-sign * 50)).add(forward.scale(12)).add(0, 10, 0);
                why = "REAR_HEMISPHERE_THREAT";
            } else if (!fastEnough
                    && frame.profile().equalAngle90SpeedRetention() >= 0.945) {
                maneuver = Maneuver.EXTEND_AND_REENTER;
                Vec3 away = position.add(enemy.position().scale(-1)).normalize();
                target = position.add(away.scale(95)).add(0, 20, 0);
                why = "REBUILD_SPEED_BEFORE_REENTRY";
            } else if (above && fastEnough && range > 18) {
                maneuver = Maneuver.HIGH_SIDE_PASS;
                target = leadPoint(enemy, range, speed / TICKS_PER_SECOND);
                why = "ALTITUDE_SPEED_ADVANTAGE";
            } else if (frame.profile().ticksTo90Yaw() <= 48
                    && frame.profile().equalAngle90SpeedRetention() < 0.95
                    && range < 70) {
                maneuver = Maneuver.TURN_PURSUIT;
                target = leadPoint(enemy, range, Math.max(0.2, speed / TICKS_PER_SECOND));
                why = "ATLAS_FAST_YAW_RESPONSE";
            } else {
                maneuver = Maneuver.INTERCEPT;
                target = leadPoint(enemy, range, Math.max(0.2, speed / TICKS_PER_SECOND));
                why = "TARGET_INTERCEPT";
            }
        } else if (frame.mission() == Mission.ESCORT && frame.formationAnchor() != null) {
            maneuver = Maneuver.ESCORT_SCREEN;
            target = frame.formationAnchor().add(0, 18, 24);
            why = "ESCORT_COVER";
        } else if (frame.formationAnchor() != null) {
            maneuver = Maneuver.FORMATION_HOLD;
            target = frame.formationAnchor().add(0, 4, 16);
            why = "FORMATION_REGROUP";
        } else {
            maneuver = Maneuver.PATROL_ROUTE;
            why = "NO_VISIBLE_HOSTILE";
        }

        double throttle = switch (maneuver) {
            case LEVEL_BOMB_RUN, FORMATION_HOLD, TORPEDO_APPROACH -> 0.78;
            case PATROL_ROUTE, ESCORT_SCREEN -> 0.85;
            default -> 1.0;
        };
        Control command = steer(frame, target, throttle);
        boolean fireCandidate = candidateFire(frame, maneuver);
        int age = memory.last() == maneuver
                ? (memory.ticksActive() == Integer.MAX_VALUE ? Integer.MAX_VALUE : memory.ticksActive() + 1)
                : 1;
        return new Decision(maneuver, command, target, fireCandidate,
                new Memory(maneuver, age), why,
                "SOURCE_MICROKERNEL+TACTICAL_HEURISTIC; historical doctrine requires scenario evidence");
    }

    /** Navigation-only control law: no fake bank-to-turn or instantaneous yaw update. */
    public static Control steer(Frame frame, Vec3 point, double throttle) {
        return FlightGuidance.plan(frame, point, throttle).control();
    }

    /** Advisory window only. Projectile type, mounts, spread and hit testing are Forge-owned. */
    static boolean candidateFire(Frame frame, Maneuver maneuver) {
        if (frame.enemy() == null || !frame.enemy().hostile()
                || !frame.lineOfFireClear() || frame.projectileSpeedBpt() <= 0) return false;
        if (maneuver != Maneuver.TURN_PURSUIT && maneuver != Maneuver.HIGH_SIDE_PASS
                && maneuver != Maneuver.INTERCEPT) return false;
        Vec3 relative = frame.enemy().position().add(frame.self().position().scale(-1));
        Vec3 enemyVelocity = frame.enemy().velocity();
        double projectileSpeed = frame.projectileSpeedBpt();
        double a = enemyVelocity.lengthSquared() - projectileSpeed * projectileSpeed;
        double b = 2 * relative.dot(enemyVelocity);
        double c = relative.lengthSquared();
        if (c < EPS || Math.sqrt(c) > 65) return false;
        double interceptTicks;
        if (Math.abs(a) < EPS) {
            if (Math.abs(b) < EPS) return false;
            interceptTicks = -c / b;
        } else {
            double discriminant = b * b - 4 * a * c;
            if (discriminant < 0) return false;
            double root = Math.sqrt(discriminant);
            double t1 = (-b - root) / (2 * a);
            double t2 = (-b + root) / (2 * a);
            interceptTicks = t1 > EPS && t2 > EPS ? Math.min(t1, t2) : Math.max(t1, t2);
        }
        if (!Double.isFinite(interceptTicks) || interceptTicks <= 0 || interceptTicks > 60) return false;
        Vec3 delta = relative.add(enemyVelocity.scale(interceptTicks));
        return forward(frame.self().yawDeg(), frame.self().pitchDeg())
                .dot(delta.normalize()) > Math.cos(Math.toRadians(5.0));
    }

    private static Vec3 leadPoint(Contact target, double range, double ownSpeedBpt) {
        double horizonTicks = Math.min(30, range / Math.max(0.20, ownSpeedBpt + target.velocity().length()));
        return target.position().add(target.velocity().scale(horizonTicks));
    }

    private static double angleDiff(double desired, double current) {
        double d = (desired - current) % 360;
        if (d > 180) d -= 360;
        if (d < -180) d += 360;
        return d;
    }

    private static void requireFinite(Vec3 value) {
        if (!Double.isFinite(value.x()) || !Double.isFinite(value.y()) || !Double.isFinite(value.z()))
            throw new IllegalArgumentException("non-finite vector");
    }
    private static double clamp(double n, double lo, double hi) {
        return Math.max(lo, Math.min(hi, n));
    }

    public static String debug(Decision decision) {
        return String.format(Locale.ROOT, "%s %s x=%.3f z=%.3f throttle=%.2f fireCandidate=%s",
                decision.maneuver(), decision.reasonCode(), decision.controls().x(),
                decision.controls().z(), decision.controls().engineTarget(),
                decision.firingWindowCandidate());
    }
}
