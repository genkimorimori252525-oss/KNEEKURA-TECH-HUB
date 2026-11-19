package org.kneekura.bedrockwither.entity;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;

public final class BedrockWitherAttackController {
    public static final int JAVA_WITHER_SHOOT_LEVEL_EVENT = 1024;

    private final BedrockWitherEntity owner;

    public BedrockWitherAttackController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    /**
     * Cross-version Bedrock invariant candidate for the main/center head.
     *
     * Historical Bedrock native code increments the Wither-owned projectile counter
     * and marks every fourth center-head projectile dangerous. Current BDS still
     * exposes mProjectileCounter, and current gameplay observation reports the same
     * three-normal + one-dangerous cycle.
     *
     * Timing/volley delays are intentionally NOT assigned here.
     */
    public BedrockWitherSkullEntity.Kind nextCenterSkullKind() {
        int next = owner.runtimeState().projectileCounter() + 1;
        owner.runtimeState().setProjectileCounter(next);
        return (next & 3) == 0
                ? BedrockWitherSkullEntity.Kind.DANGEROUS
                : BedrockWitherSkullEntity.Kind.NORMAL;
    }

    public BedrockWitherSkullEntity fireSkull(
            Vec3 origin,
            Vec3 targetPosition,
            BedrockWitherSkullEntity.Kind kind
    ) {
        // Java 1.20.1's level event 1024 maps to the Wither shoot sound and is
        // the closest engine-native bridge for Bedrock's mob.wither.shoot.
        if (!owner.isSilent()) {
            owner.level().levelEvent((Player) null, JAVA_WITHER_SHOOT_LEVEL_EVENT, owner.blockPosition(), 0);
        }

        BedrockWitherSkullEntity skull = BedrockWitherSkullEntity.create(
                owner.level(),
                owner,
                origin,
                targetPosition.subtract(origin),
                kind
        );
        owner.level().addFreshEntity(skull);
        return skull;
    }
}
