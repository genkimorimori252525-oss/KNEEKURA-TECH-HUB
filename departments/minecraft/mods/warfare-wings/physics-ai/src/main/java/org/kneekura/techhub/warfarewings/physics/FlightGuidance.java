package org.kneekura.techhub.warfarewings.physics;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

/**
 * Autopilot for IA 1.3.3 raw pilot X/Z/engineTarget, not direct entity rotation.
 * Uses the previously smoothed controller state to anticipate residual turn
 * after releasing a key. No physical roll-to-turn or unverified stall law.
 */
public final class FlightGuidance {
    private static final double EPS = 1e-9;
    private FlightGuidance() {}

    public record Guidance(Control control, double yawErrorDeg, double pitchErrorDeg,
                           double predictedYawOvershootDeg, double predictedPitchOvershootDeg,
                           double distanceBlocks) {}

    public static Guidance plan(Frame frame, Vec3 waypoint, double cruiseThrottle) {
        if (frame == null || waypoint == null) throw new IllegalArgumentException("guidance");
        if (!finite(waypoint) || !Double.isFinite(cruiseThrottle))
            throw new IllegalArgumentException("nonfinite guidance input");
        State state = frame.self();
        Vec3 relative = waypoint.add(state.position().scale(-1));
        double distance = relative.length();
        double desiredYaw = distance < EPS ? state.yawDeg()
                : Math.toDegrees(Math.atan2(-relative.x(), relative.z()));
        double horizontal = Math.hypot(relative.x(), relative.z());
        // IA positive pitch looks DOWN; negative Z input rotates nose UP.
        double desiredPitch = distance < EPS ? state.pitchDeg()
                : -Math.toDegrees(Math.atan2(relative.y(), horizontal));
        // Model produces raw control -> 10-tick smoothing -> extra rotation decay.
        // A small damping horizon anticipates the momentum in the *input filter*.
        double rotDecay = clamp((1.0 - frame.model().friction())
                * frame.model().rotationDecay(), 0.0, 0.995);
        double controllerRetention = 0.9 * rotDecay;
        double horizon = 1.0 / Math.max(0.1, 1.0 - controllerRetention);
        double nextX = state.smoothX() * rotDecay;
        double nextZ = state.smoothZ() * rotDecay;
        double yawDrift = -frame.model().yawSpeed() * nextX * horizon;
        double pitchDrift = frame.model().pitchSpeed() * nextZ * horizon;

        double yawErr = wrapDeg(desiredYaw - state.yawDeg());
        double pitchErr = clamp(desiredPitch - state.pitchDeg(), -120, 120);
        double correctiveYaw = wrapDeg(yawErr - yawDrift);
        double correctivePitch = pitchErr - pitchDrift;
        double yawGain = Math.max(9.0, frame.model().yawSpeed() * 10.0);
        double pitchGain = Math.max(9.0, frame.model().pitchSpeed() * 10.0);
        double rawX = clamp(-correctiveYaw / yawGain, -1, 1);
        double rawZ = clamp(correctivePitch / pitchGain, -1, 1);

        // A saturated steering command with small distance may repeatedly overshoot
        // a position point; reduce desired speed near station without using an
        // instantaneous speed override. Never use brake (rawY<0) in mid-air by default.
        double throttle = clamp(cruiseThrottle, 0, 1);
        if (distance < 16 && distance > EPS) throttle = Math.min(throttle, 0.58);
        if (frame.self().position().y() - frame.terrainHeight() < 18 && relative.y() > 0)
            throttle = Math.max(throttle, 0.95);
        return new Guidance(new Control(rawX, 0, rawZ, throttle),
                yawErr, pitchErr, yawDrift, pitchDrift, distance);
    }

    public static double wrapDeg(double degrees) {
        double d = (degrees % 360.0 + 360.0) % 360.0;
        return d > 180 ? d - 360 : d;
    }
    private static boolean finite(Vec3 p) {
        return Double.isFinite(p.x()) && Double.isFinite(p.y()) && Double.isFinite(p.z());
    }
    private static double clamp(double n, double lo, double hi) {
        return Math.max(lo, Math.min(hi, n));
    }
}
