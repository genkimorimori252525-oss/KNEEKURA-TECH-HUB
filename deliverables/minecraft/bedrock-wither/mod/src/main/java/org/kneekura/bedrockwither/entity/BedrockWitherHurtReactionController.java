package org.kneekura.bedrockwither.entity;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;

import java.util.UUID;

public final class BedrockWitherHurtReactionController {
    /**
     * Current Bedrock observation and historical native body agree that the
     * phase-1 hurt destruction is delayed by 20 game ticks.
     */
    public static final int HURT_REACTION_DELAY_TICKS = 20;

    private final BedrockWitherEntity owner;
    private UUID attackerUuid;
    private Vec3 attackerPosition = Vec3.ZERO;

    public BedrockWitherHurtReactionController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public void onAcceptedDamage(LivingEntity attacker) {
        if (owner.phaseController().isSecondPhase()) {
            return;
        }

        // Historical Bedrock only arms the block-destruction timer when it is not
        // already active. Repeated hits do not keep pushing the break event back.
        if (owner.runtimeState().destroyBlocksTick() <= 0) {
            owner.runtimeState().setDestroyBlocksTick(HURT_REACTION_DELAY_TICKS);
            attackerUuid = attacker.getUUID();
            attackerPosition = attacker.position();
        }
    }

    public void tick() {
        int remaining = owner.runtimeState().destroyBlocksTick();
        if (remaining <= 0) {
            return;
        }

        remaining--;
        owner.runtimeState().setDestroyBlocksTick(remaining);
        if (remaining == 0) {
            performReaction();
        }
    }

    private void performReaction() {
        if (!(owner.level() instanceof ServerLevel level) || owner.phaseController().isSecondPhase()) {
            clearPendingAttacker();
            return;
        }

        owner.destructionController().destroyAroundSelf(
                1,
                BedrockWitherAttackType.HURT_EXPLOSION
        );

        Vec3 targetPosition = resolveAttackerPosition(level);
        Vec3 origin = owner.position().add(0.0D, 2.0D, 0.0D);

        owner.attackController().fireSkull(
                origin,
                targetPosition,
                BedrockWitherSkullEntity.Kind.DANGEROUS
        );

        clearPendingAttacker();
    }

    private Vec3 resolveAttackerPosition(ServerLevel level) {
        if (attackerUuid != null) {
            net.minecraft.world.entity.Entity entity = level.getEntity(attackerUuid);
            if (entity instanceof LivingEntity living && living.isAlive()) {
                return living.getEyePosition();
            }
        }

        if (attackerPosition.distanceToSqr(owner.position()) > 1.0E-8D) {
            return attackerPosition;
        }

        LivingEntity currentTarget = owner.getTarget();
        if (currentTarget != null && currentTarget.isAlive()) {
            return currentTarget.getEyePosition();
        }

        // Exact current Bedrock fallback direction is not publicly exposed.
        // Forward firing is an explicit Java adaptation for the no-target case.
        return owner.getEyePosition().add(owner.getLookAngle().scale(16.0D));
    }

    public void addAdditionalSaveData(CompoundTag tag) {
        if (attackerUuid != null) {
            tag.putUUID("HurtReactionAttacker", attackerUuid);
        }
        tag.putDouble("HurtReactionAttackerX", attackerPosition.x);
        tag.putDouble("HurtReactionAttackerY", attackerPosition.y);
        tag.putDouble("HurtReactionAttackerZ", attackerPosition.z);
    }

    public void readAdditionalSaveData(CompoundTag tag) {
        attackerUuid = tag.hasUUID("HurtReactionAttacker")
                ? tag.getUUID("HurtReactionAttacker")
                : null;
        attackerPosition = new Vec3(
                tag.getDouble("HurtReactionAttackerX"),
                tag.getDouble("HurtReactionAttackerY"),
                tag.getDouble("HurtReactionAttackerZ")
        );
    }

    private void clearPendingAttacker() {
        attackerUuid = null;
        attackerPosition = Vec3.ZERO;
    }
}
