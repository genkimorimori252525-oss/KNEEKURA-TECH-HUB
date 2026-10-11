package org.kneekura.techhub.warfarewings.physics;

import java.util.Map;

/**
 * Exact ANCHOR binary bytecode overrides of
 * immersive_aircraft.entity.EngineVehicle.getEngineReactionSpeed().
 *
 * Evidence: javap -c -p -cp <SHA-256-verified WW 1.1.4> on each of the
 * 24 net.velleagle.warfare_wings.entity.*Entity classes.
 * SHA-256: dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43
 * These are MOD engine response ticks, NOT historical engine observations.
 *
 * Deliberately separate from Atlas v2 legacy prediction constants: historical
 * golden source profiles must remain reproducible and never be silently
 * relabeled as measurements. Explicitly opt into tickWithReaction instead.
 */
public final class WarfareWingsEngineReaction {
    public static final String PROVENANCE_SHA256 =
            WarfareWingsAircraft.WARFARE_WINGS_ANCHOR_SHA256;
    private static final Map<String, Integer> REACTION_TICKS = Map.ofEntries(
            Map.entry("warfare_wings:a6m", 100),
            Map.entry("warfare_wings:b17", 150),
            Map.entry("warfare_wings:b29", 150),
            Map.entry("warfare_wings:bf109", 100),
            Map.entry("warfare_wings:d4y", 100),
            Map.entry("warfare_wings:f4u", 100),
            Map.entry("warfare_wings:f6f", 100),
            Map.entry("warfare_wings:fw190", 100),
            Map.entry("warfare_wings:g10n1", 200),
            Map.entry("warfare_wings:g10n2", 170),
            Map.entry("warfare_wings:g4m", 120),
            Map.entry("warfare_wings:he111", 120),
            Map.entry("warfare_wings:il2", 100),
            Map.entry("warfare_wings:ju87", 100),
            Map.entry("warfare_wings:ki61", 100),
            Map.entry("warfare_wings:ki84", 100),
            Map.entry("warfare_wings:mc202", 100),
            Map.entry("warfare_wings:mig3", 100),
            Map.entry("warfare_wings:p40e", 100),
            Map.entry("warfare_wings:p47n", 100),
            Map.entry("warfare_wings:p51d", 100),
            Map.entry("warfare_wings:sbd", 100),
            Map.entry("warfare_wings:spitfire", 100),
            Map.entry("warfare_wings:yak3", 100)
    );

    private WarfareWingsEngineReaction() {}

    public static int ticks(String aircraftId) {
        Integer result = REACTION_TICKS.get(aircraftId);
        if (result == null) throw new IllegalArgumentException(
                "No exact SHA-proven engine-reaction override: " + aircraftId);
        return result;
    }

    public static Map<String, Integer> all() { return REACTION_TICKS; }
}
