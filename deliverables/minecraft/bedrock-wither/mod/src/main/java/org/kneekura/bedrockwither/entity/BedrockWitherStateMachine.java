package org.kneekura.bedrockwither.entity;

public final class BedrockWitherStateMachine {
    private final BedrockWitherEntity owner;
    private long enteredAtGameTime;

    public BedrockWitherStateMachine(BedrockWitherEntity owner) {
        this.owner = owner;
        this.enteredAtGameTime = owner.level().getGameTime();
    }

    public void tick() {
        // Spawn duration is still a direct-measurement target. The native-shaped
        // spawningFrames slot is already authoritative for this gate: a positive
        // value keeps SPAWN_SEQUENCE active; zero means combat may begin.
        if (owner.getBedrockState() == BedrockWitherState.SPAWN_SEQUENCE
                && owner.runtimeState().spawningFrames() <= 0) {
            enter(BedrockWitherState.PHASE1_REPOSITION);
        }
    }

    public void enter(BedrockWitherState next) {
        if (owner.getBedrockState() == next) {
            return;
        }
        owner.setBedrockState(next);
        enteredAtGameTime = owner.level().getGameTime();
    }

    public void restore(BedrockWitherState state, long enteredAtGameTime) {
        owner.setBedrockState(state);
        this.enteredAtGameTime = Math.max(0L, enteredAtGameTime);
    }

    public long enteredAtGameTime() {
        return enteredAtGameTime;
    }

    public long ticksInState() {
        return Math.max(0L, owner.level().getGameTime() - enteredAtGameTime);
    }
}
