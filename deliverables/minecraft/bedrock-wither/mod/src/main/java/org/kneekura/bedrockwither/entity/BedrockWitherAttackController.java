package org.kneekura.bedrockwither.entity;

import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;

public final class BedrockWitherAttackController {
    private final BedrockWitherEntity owner;

    public BedrockWitherAttackController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public BedrockWitherSkullEntity fireSkull(
            Vec3 origin,
            Vec3 targetPosition,
            BedrockWitherSkullEntity.Kind kind
    ) {
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
