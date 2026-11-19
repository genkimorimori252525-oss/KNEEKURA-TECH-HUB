package org.kneekura.techhub.warfarewings.physics;

import java.util.Map;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Pure SOURCE observation contract fixture. Real twin integration is tested
 * separately with simultaneous full microkernel trajectories in Python.
 */
public final class FlightTwinSensorSelfTestMain {
    private static int assertions;
    private FlightTwinSensorSelfTestMain() {}

    private static void require(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }
    private static State craft(double x,double y,double z,double yaw) {
        return new State(0,new Vec3(x,y,z),new Vec3(0,0,0),
                yaw,0,0,0,0,0,0,0,0,1,0,1,0,false,false);
    }
    public static void main(String[] args) {
        var liveAligned = FlightTwinSensor.Parameters.DEFAULT;
        require(liveAligned.rangeBlocks() == 240.0
                        && liveAligned.halfConeDegrees() == 75.0,
                "Twin default must match Forge LiveAirSensor range 240 and FULL FOV 150");
        var forward = craft(0,170,0,0);
        require(FlightTwinSensor.assess(forward,craft(0,170,239.5,0),
                        PinnedIa133WindWorld.calmAirCalibration(),liveAligned).visible(),
                "original real Forge 240b range includes an in-front 239.5b contact");
        require(FlightTwinSensor.assess(forward,craft(0,170,241,0),
                        PinnedIa133WindWorld.calmAirCalibration(),liveAligned).visibility()
                        == FlightTwinSensor.Visibility.OUT_OF_RANGE,
                "original real Forge 240b range cannot see 241b contact");
        require(FlightTwinSensor.assess(forward,craft(180,170,0,0),
                        PinnedIa133WindWorld.calmAirCalibration(),liveAligned).visibility()
                        == FlightTwinSensor.Visibility.OUTSIDE_FOV,
                "full 150-degree, not erroneous full 300-degree FOV");
        var params = new FlightTwinSensor.Parameters(190,60,2,24,1.5);
        var flat = PinnedIa133WindWorld.calmAirCalibration();
        var hill = new FlightTwinScenario.SyntheticRidgeWorld();
        var blue = craft(0,170,0,0);
        var hostile = craft(0,170,90,180);
        require(FlightTwinSensor.assess(blue,hostile,flat,params).visible(),
                "front, nearby and unoccluded hostile must be seen");
        require(FlightTwinSensor.assess(blue,hostile,hill,params).visibility()
                        == FlightTwinSensor.Visibility.TERRAIN_OCCLUDED,
                "height ray LOS must suppress a hill-hidden hostile");
        require(FlightTwinSensor.assess(blue,craft(0,170,-90,0),flat,params).visibility()
                        == FlightTwinSensor.Visibility.OUTSIDE_FOV,
                "narrow forward FOV must reject the rear hemisphere");
        require(FlightTwinSensor.assess(blue,craft(0,170,210,180),flat,params).visibility()
                        == FlightTwinSensor.Visibility.OUT_OF_RANGE,
                "finite sensor range must not be an omniscient contact");

        var visible = FlightTwinSensor.update(0,blue,Map.of("red",hostile),
                Map.of(),flat,params);
        require(visible.currentlyVisible().equals(java.util.Set.of("red")),
                "valid hostile is visible and own-track is created");
        require(visible.tracks().get("red").lastSeenTick() == 0,
                "track timestamp comes from actual observation tick");
        State movedTruth = craft(20,170,90,180);
        var hidden1 = FlightTwinSensor.update(1,blue,Map.of("red",movedTruth),
                visible.tracks(),hill,params);
        require(hidden1.currentlyVisible().isEmpty() && hidden1.rememberedCount()==1,
                "occluded contact persists ONLY as stale local track");
        require(hidden1.tracks().get("red").lastPosition().x()==0,
                "occluded hostile's real moved position MUST NOT leak into track");
        require(hidden1.tracks().get("red").lastSeenTick()==0,
                "unseen track timestamp must never refresh");
        var hidden2 = FlightTwinSensor.update(2,blue,Map.of("red",movedTruth),
                hidden1.tracks(),hill,params);
        require(hidden2.tracks().containsKey("red") && hidden2.rememberedCount()==1,
                "track TTL includes exactly its configured last tick");
        var expired = FlightTwinSensor.update(3,blue,Map.of("red",movedTruth),
                hidden2.tracks(),hill,params);
        require(expired.tracks().isEmpty() && expired.expired().contains("red"),
                "memory MUST expire when now-lastSeen exceeds TTL");
        var reacquired = FlightTwinSensor.update(4,blue,Map.of("red",movedTruth),
                expired.tracks(),flat,params);
        require(reacquired.currentlyVisible().contains("red")
                        && reacquired.tracks().get("red").lastPosition().x()==20,
                "true target location may refresh only after actual reacquisition");
        require(FlightTwinSensor.update(5,blue,Map.of(),Map.of(),flat,params)
                        .assessments().isEmpty(),
                "friendly telemetry cannot be imported as enemy observations");
        System.out.println("FLIGHT_TWIN_SENSOR_SELFTEST PASS assertions="+assertions);
    }
}
