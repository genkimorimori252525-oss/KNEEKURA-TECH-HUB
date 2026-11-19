package com.example.kirby_mod.entity.ai;

public final class KirbyDamageFacePolicyTest {

    public static void main(String[] args) {
        check(KirbyDamageFacePolicy.classify(0.0F)
                        == KirbyDamageFacePolicy.Severity.NONE,
                "zero damage must not display a damage face");
        check(KirbyDamageFacePolicy.classify(0.01F)
                        == KirbyDamageFacePolicy.Severity.LIGHT,
                "any positive damage must display a damage face");
        check(KirbyDamageFacePolicy.classify(3.99F)
                        == KirbyDamageFacePolicy.Severity.LIGHT,
                "damage below four should remain light");
        check(KirbyDamageFacePolicy.classify(4.0F)
                        == KirbyDamageFacePolicy.Severity.MEDIUM,
                "four damage should enter the medium tier");
        check(KirbyDamageFacePolicy.classify(10.0F)
                        == KirbyDamageFacePolicy.Severity.CATASTROPHIC,
                "ten damage should enter the catastrophic tier");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
