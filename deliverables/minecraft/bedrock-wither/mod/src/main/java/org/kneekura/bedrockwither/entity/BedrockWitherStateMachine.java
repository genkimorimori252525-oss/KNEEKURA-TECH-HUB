package org.kneekura.bedrockwither.entity;

public final class BedrockWitherStateMachine {
    private final BedrockWitherEntity owner;
    private long enteredAtGameTime;

    public BedrockWitherStateMachine(BedrockWitherEntity owner) {
        this.owner = owner;
        this.enteredAtGameTime = owner.level().getGameTime();
    }

    public void tick() {
        // M1 intentionally owns state timing before it owns phase behavior.
        // Phase transitions are added only with an explicit evidence-backed contract.
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
