package org.kneekura.techhub.warfarewings.physics;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

/**
 * Immutable per-aircraft profile loader for the Forge runtime adapter.
 * Reuses the laboratory's original CSV parser/evaluator in the same package;
 * no invented runtime flight stats or duplicate model definitions.
 */
public final class RuntimeTacticalAtlas {
    private static final String RESOURCE = "/ww-tactical-anchor-v1.csv";
    private RuntimeTacticalAtlas() {}

    public record Airframe(Ia133Microkernel.Model model, TacticalAirAI.Profile profile) {}

    public static Map<String, Airframe> load() {
        Path file = null;
        try (InputStream stream = RuntimeTacticalAtlas.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) throw new IllegalStateException("Packaged pinned aircraft Atlas absent");
            file = Files.createTempFile("ww-tactical-anchor-", ".csv");
            Files.copy(stream, file, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            var roster = AircraftAtlasMain.load(file);
            if (roster.size() != 24) throw new IllegalStateException("Expected 24 base aircraft");
            Map<String, Airframe> result = new HashMap<>();
            for (var aircraft : roster) {
                var profile = TacticalAirAI.Profile.fromAtlas(AircraftAtlasMain.evaluate(aircraft));
                if (result.put(aircraft.aircraftId(), new Airframe(aircraft.model(), profile)) != null)
                    throw new IllegalStateException("Duplicate aircraft " + aircraft.aircraftId());
            }
            return Map.copyOf(result);
        } catch (IOException ex) {
            throw new IllegalStateException("Failed loading packaged aircraft Atlas", ex);
        } finally {
            if (file != null) {
                try { Files.deleteIfExists(file); } catch (IOException ignored) {}
            }
        }
    }
}
