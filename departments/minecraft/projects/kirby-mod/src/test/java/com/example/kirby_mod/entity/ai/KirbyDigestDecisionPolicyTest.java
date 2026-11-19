package com.example.kirby_mod.entity.ai;

public final class KirbyDigestDecisionPolicyTest {

    public static void main(String[] args) {
        clearDistantTargetsFavorSpitting();
        singleClearTargetBeatsHeldMobCaution();
        blockedFriendlyLineFavorsSwallowing();
        multipleLargeHeldMobsIncreaseSpitValue();
    }

    private static void clearDistantTargetsFavorSpitting() {
        KirbyDigestDecisionPolicy.Scores scores = KirbyDigestDecisionPolicy.evaluate(
                new KirbyDigestDecisionPolicy.Inputs(2, 2, false, false, 1, 1.0D, 20.0D, 0.0D));
        assertTrue(scores.shouldSpit(), "clear distant targets should favor spit");
    }

    private static void singleClearTargetBeatsHeldMobCaution() {
        KirbyDigestDecisionPolicy.Scores scores = KirbyDigestDecisionPolicy.evaluate(
                new KirbyDigestDecisionPolicy.Inputs(
                        1, 0, false, false, 1, 0.1D, 35.0D, -0.35D));
        assertTrue(scores.shouldSpit(),
                "one clear target should reliably favor spit despite held-mob caution");
    }

    private static void blockedFriendlyLineFavorsSwallowing() {
        KirbyDigestDecisionPolicy.Scores scores = KirbyDigestDecisionPolicy.evaluate(
                new KirbyDigestDecisionPolicy.Inputs(0, 0, true, true, 1, 1.0D, 35.0D, 0.35D));
        assertTrue(!scores.shouldSpit(), "blocked friendly line should favor swallow");
    }

    private static void multipleLargeHeldMobsIncreaseSpitValue() {
        KirbyDigestDecisionPolicy.Scores single = KirbyDigestDecisionPolicy.evaluate(
                new KirbyDigestDecisionPolicy.Inputs(0, 0, false, false, 1, 1.0D, 20.0D, 0.0D));
        KirbyDigestDecisionPolicy.Scores multiple = KirbyDigestDecisionPolicy.evaluate(
                new KirbyDigestDecisionPolicy.Inputs(0, 0, false, false, 4, 8.0D, 20.0D, 0.0D));
        assertTrue(multiple.spitScore > single.spitScore, "multiple large held mobs should raise spit score");
    }

    private static void assertTrue(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private KirbyDigestDecisionPolicyTest() {}
}
