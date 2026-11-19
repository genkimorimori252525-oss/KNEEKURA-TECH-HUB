package com.example.kirby_mod.entity.ai;

public final class KirbySlideMotionTest {

    public static void main(String[] args) {
        startsAtTwiceWalkSpeed();
        slowsMonotonicallyAcrossMotionWindow();
        clampsTicksAndNegativeSpeed();
    }

    private static void startsAtTwiceWalkSpeed() {
        assertEquals(0.5D, KirbySlideMotion.horizontalSpeed(0.25D, 0), "initial speed");
    }

    private static void slowsMonotonicallyAcrossMotionWindow() {
        double previous = Double.MAX_VALUE;
        for (int tick = 0; tick < KirbySlideMotion.MOTION_TICKS; tick++) {
            double current = KirbySlideMotion.horizontalSpeed(0.25D, tick);
            if (current >= previous) {
                throw new AssertionError("speed must decrease at tick " + tick);
            }
            previous = current;
        }
        if (previous >= 0.1D) {
            throw new AssertionError("final speed should be nearly stopped: " + previous);
        }
    }

    private static void clampsTicksAndNegativeSpeed() {
        assertEquals(KirbySlideMotion.horizontalSpeed(0.25D, 0),
                KirbySlideMotion.horizontalSpeed(0.25D, -1), "negative tick");
        assertEquals(0.0D, KirbySlideMotion.horizontalSpeed(-1.0D, 0), "negative walk speed");
    }

    private static void assertEquals(double expected, double actual, String label) {
        if (Math.abs(expected - actual) > 1.0E-9D) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private KirbySlideMotionTest() {}
}
