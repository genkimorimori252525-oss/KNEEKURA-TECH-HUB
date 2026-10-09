package com.example.kirby_mod.entity.ai;

import java.util.ArrayList;
import java.util.List;

final class KirbyDigestDecisionPolicy {

    private KirbyDigestDecisionPolicy() {}

    static Scores evaluate(Inputs input) {
        double swallowScore = 1.0D;
        double spitScore = 1.0D;
        List<String> reasons = new ArrayList<>();

        if (input.clearTargetCount > 0) {
            spitScore += Math.min(6.0D, input.clearTargetCount * 2.0D);
            reasons.add("clearTargets=" + input.clearTargetCount);
        } else {
            swallowScore += 1.5D;
            reasons.add("noClearTarget");
        }
        if (input.distantTargetCount > 0) {
            spitScore += Math.min(2.0D, input.distantTargetCount * 0.75D);
            reasons.add("distantTargets=" + input.distantTargetCount);
        }
        if (input.clearTargetCount > 1) {
            spitScore += 1.0D;
            reasons.add("multipleTargets");
        }
        if (input.heldCount > 1) {
            spitScore += Math.min(2.0D, (input.heldCount - 1) * 0.75D);
            reasons.add("multipleHeld=" + input.heldCount);
        }

        spitScore += Math.min(1.25D, input.fullness / 10.0D * 1.25D);
        if (input.fullness >= 5.0D) {
            reasons.add("largeMouthLoad");
        }

        if (input.wallAhead) {
            swallowScore += 2.5D;
            spitScore -= 2.0D;
            reasons.add("wallAhead");
        }
        if (input.friendlyInLine) {
            swallowScore += 3.0D;
            spitScore -= 3.0D;
            reasons.add("friendlyInLine");
        }
        if (input.strongestHeldMaxHealth >= 30.0D) {
            swallowScore += 1.25D;
            reasons.add("dangerousHeld");
        }

        spitScore += input.randomJitter;
        reasons.add("jitter=" + input.randomJitter);
        return new Scores(swallowScore, Math.max(0.0D, spitScore), List.copyOf(reasons));
    }

    static final class Inputs {
        final int clearTargetCount;
        final int distantTargetCount;
        final boolean wallAhead;
        final boolean friendlyInLine;
        final int heldCount;
        final double fullness;
        final double strongestHeldMaxHealth;
        final double randomJitter;

        Inputs(int clearTargetCount, int distantTargetCount, boolean wallAhead,
               boolean friendlyInLine, int heldCount, double fullness,
               double strongestHeldMaxHealth, double randomJitter) {
            this.clearTargetCount = clearTargetCount;
            this.distantTargetCount = distantTargetCount;
            this.wallAhead = wallAhead;
            this.friendlyInLine = friendlyInLine;
            this.heldCount = heldCount;
            this.fullness = fullness;
            this.strongestHeldMaxHealth = strongestHeldMaxHealth;
            this.randomJitter = randomJitter;
        }
    }

    static final class Scores {
        final double swallowScore;
        final double spitScore;
        final List<String> reasons;

        Scores(double swallowScore, double spitScore, List<String> reasons) {
            this.swallowScore = swallowScore;
            this.spitScore = spitScore;
            this.reasons = reasons;
        }

        boolean shouldSpit() {
            return spitScore > swallowScore;
        }
    }
}
