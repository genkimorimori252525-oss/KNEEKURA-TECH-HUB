package org.kneekura.bedrockwither.entity;

public enum BedrockWitherState {
    SPAWN_SEQUENCE(0),
    PHASE1_REPOSITION(1),
    PHASE1_BURST(2),
    PHASE1_COOLDOWN(3),
    PHASE1_HURT_REACTION(4),
    PHASE_TRANSITION(5),
    PHASE2_DASH_PREP(6),
    PHASE2_DASH(7),
    PHASE2_RECOVER(8),
    DEATH_SEQUENCE(9);

    private final int id;

    BedrockWitherState(int id) {
        this.id = id;
    }

    public int id() {
        return id;
    }

    public static BedrockWitherState fromId(int id) {
        for (BedrockWitherState value : values()) {
            if (value.id == id) {
                return value;
            }
        }
        return SPAWN_SEQUENCE;
    }
}
