package org.kneekura.techhub.warfarewings.physics;

import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

/**
 * Adapter-neutral 20 Hz pipeline for real server-side airborne observations:
 * tactical mission -> optional period/unit doctrine -> world safety -> IA raw controls.
 * Each aircraft owns its Memory; world adapters must apply commands at most once/tick.
 */
public final class FlightControlLoop {
    private FlightControlLoop() {}
    public record Input(Frame frame, Memory memory, HistoricalDoctrineOrders.Order order,
                        FlightSafetyPlanner.Environment environment) {
        public Input {
            if (frame == null || memory == null || environment == null)
                throw new IllegalArgumentException("flight loop input");
        }
    }
    public record Output(Decision decision, FlightSafetyPlanner.Clearance safety) {}

    public static Output step(Input input) {
        Frame f = input.frame();
        Decision selected = input.order() == null
                ? TacticalAirAI.decide(f, input.memory())
                : HistoricalDoctrineOrders.decide(f, input.memory(), input.order());
        FlightSafetyPlanner.Clearance guard = FlightSafetyPlanner.guard(
                f, selected.steeringPoint(), input.environment());
        if (!guard.override()) return new Output(selected, guard);
        Maneuver maneuver = guard.reason() == FlightSafetyPlanner.Reason.MOVING_COLLISION_RISK
                ? Maneuver.COLLISION_AVOID : Maneuver.TERRAIN_RECOVERY;
        if (guard.reason() == FlightSafetyPlanner.Reason.LOW_SPEED_RESERVE)
            maneuver = Maneuver.EXTEND_AND_REENTER;
        var command = FlightGuidance.plan(f, guard.waypoint(), 1.0).control();
        int ticks = selected.maneuver() == maneuver ? selected.nextMemory().ticksActive() : 1;
        return new Output(new Decision(maneuver, command, guard.waypoint(),
                false, new Memory(maneuver, ticks),
                "WORLD_SAFETY_" + guard.reason(), "SOURCE_PREDICTIVE_SAFETY_UNCALIBRATED"),
                guard);
    }
}
