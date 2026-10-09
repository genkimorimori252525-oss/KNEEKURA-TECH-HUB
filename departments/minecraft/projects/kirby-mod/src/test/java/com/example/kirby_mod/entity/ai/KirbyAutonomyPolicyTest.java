package com.example.kirby_mod.entity.ai;

public final class KirbyAutonomyPolicyTest {

    public static void main(String[] args) {
        check(KirbyAutonomyPolicy.chooseGroundMode(0.0F) == KirbyLocomotionMode.RUN,
                "the run range should start at zero");
        check(KirbyAutonomyPolicy.chooseGroundMode(0.249999F) == KirbyLocomotionMode.RUN,
                "rolls below the boundary should run");
        check(KirbyAutonomyPolicy.chooseGroundMode(0.25F) == KirbyLocomotionMode.WALK,
                "the boundary should enter the walk range");
        check(KirbyAutonomyPolicy.chooseGroundMode(0.999999F) == KirbyLocomotionMode.WALK,
                "high rolls should walk");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
