package com.github.tartaricacid.touhoulittlemaid.sim.debug;
/** Value comparison only; the real adapter reads both sides from Minecraft's current APIs. */
public final class KneekuraDebugCaptureRestoration {
    private KneekuraDebugCaptureRestoration() {}
    public record State(String cameraUuid, String cameraType, boolean hideGui, boolean bob,
                        int fov, boolean paused, boolean mouseGrabbed, String screen,
                        double x, double y, double z, float yaw, float pitch) {}
    public static boolean exact(State expected, State observed) {
        return expected != null && observed != null && expected.equals(observed);
    }
}
