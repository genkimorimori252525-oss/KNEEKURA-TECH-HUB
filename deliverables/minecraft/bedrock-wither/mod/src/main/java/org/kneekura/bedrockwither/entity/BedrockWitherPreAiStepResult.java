package org.kneekura.bedrockwither.entity;

/**
 * Mirrors current BDS WitherBossPreAIStepResult names.
 *
 * Semantics are structural evidence only until mapped by runtime observation.
 */
public enum BedrockWitherPreAiStepResult {
    STOP_AI_STEP_EXECUTION(0),
    RUN_AI_STEP(1),
    RUN_POST_AI_STEP_AND_AI_STEP(2);

    private final int nativeId;

    BedrockWitherPreAiStepResult(int nativeId) {
        this.nativeId = nativeId;
    }

    public int nativeId() {
        return nativeId;
    }
}
