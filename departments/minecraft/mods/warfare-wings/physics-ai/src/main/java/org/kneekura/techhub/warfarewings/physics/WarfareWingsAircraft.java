package org.kneekura.techhub.warfarewings.physics;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.Model;

/**
 * Two-aircraft seed catalog.
 * Raw aircraft values were re-read from the user-supplied ANCHOR JAR:
 * warfare_wings-1.1.4-1.20.1-forge.jar
 * SHA-256 dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43
 */
public final class WarfareWingsAircraft {
    public static final String WARFARE_WINGS_ANCHOR_SHA256 = "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43";
    public static final String IA_SOURCE_TAG = "1.3.3+1.20.1";
    public static final String IA_SOURCE_COMMIT = "550b38d3dfdbf5cb6ec3f78468e0e60725a47605";

    public static final double DEFAULT_FRICTION = 0.015;
    private static final double DEFAULT_ACCELERATION = 1.0;
    private static final double DEFAULT_GROUND_FRICTION = 0.95;
    private static final double DEFAULT_WATER_FRICTION = 0.90;
    private static final double DEFAULT_ROTATION_DECAY = 0.97;
    private static final double DEFAULT_HORIZONTAL_DECAY = 0.97;
    private static final double DEFAULT_VERTICAL_DECAY = 0.97;

    private WarfareWingsAircraft() {}

    public static Model a6m() {
        return base("warfare_wings:a6m", "fighter", "turn_fighter",
                0.075, 3.8, 3.5, 0.05, 2.5, 2.1,
                0.065, 0.135, 60, 11.8, 0.0015, 5.4, 0.008);
    }

    public static Model p47n() {
        return base("warfare_wings:p47n", "fighter", "energy_fighter",
                0.102, 2.5, 2.4, 0.05, 5.0, 3.4,
                0.055, 0.165, 58, 15.5, 0.004, 9.0, 0.013);
    }

    private static Model base(String id, String role, String doctrine,
                              double engineSpeed, double yawSpeed, double pitchSpeed, double pushSpeed,
                              double durability, double fuel, double glideFactor, double lift,
                              double rollFactor, double groundPitch, double wind, double mass,
                              double rawDriftDrag) {
        return new Model(id, role, doctrine,
                engineSpeed, yawSpeed, pitchSpeed, pushSpeed,
                DEFAULT_ACCELERATION, durability, fuel,
                DEFAULT_FRICTION, glideFactor, lift, rollFactor,
                groundPitch, 0.0, wind, mass,
                DEFAULT_GROUND_FRICTION, DEFAULT_WATER_FRICTION,
                DEFAULT_ROTATION_DECAY, DEFAULT_HORIZONTAL_DECAY, DEFAULT_VERTICAL_DECAY,
                rawDriftDrag);
    }

    public record LegacyMeasuredProfile(String aircraftId,
                                        double stallGuardSpeedBps,
                                        double cruiseSpeedBps,
                                        double climbTargetSpeedBps,
                                        double turnSpeedFloorBps,
                                        double measuredTopSpeedBps,
                                        String provenance) {}

    public static LegacyMeasuredProfile legacyA6m() {
        return new LegacyMeasuredProfile("warfare_wings:a6m",
                10.273020653865627, 32.723952272022544, 31.99485535959444,
                34.644173364843915, 43.63193636269672,
                "legacy exact-runtime profile; older public Warfare Wings artifact; reference-only");
    }

    public static LegacyMeasuredProfile legacyP47n() {
        return new LegacyMeasuredProfile("warfare_wings:p47n",
                10.166213720253028, 33.67418756620284, 33.62807841873141,
                37.357554760673516, 44.89891675493712,
                "legacy exact-runtime profile; older public Warfare Wings artifact; reference-only");
    }
}
