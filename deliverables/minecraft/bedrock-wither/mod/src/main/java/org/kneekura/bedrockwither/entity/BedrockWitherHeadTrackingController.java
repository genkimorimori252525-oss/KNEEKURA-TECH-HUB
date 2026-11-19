package org.kneekura.bedrockwither.entity;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;
import java.util.UUID;

/**
 * Server authority for the three Bedrock Wither head pitch queries.
 *
 * Current Mojang client animation consumes head_x_rotation(0..2). Current BDS
 * exposes mHeadRots[3] and mOldHeadRots[3]. Historical native aiStep rotates
 * the head pitch toward a target with a 40-degree clamp step.
 *
 * Y rotation is not synchronized per head here because the current Mojang
 * animation explicitly uses one shared query.target_y_rotation for all heads.
 */
public final class BedrockWitherHeadTrackingController {
    private static final float HISTORICAL_PITCH_CLAMP_DEGREES_PER_TICK = 40.0F;

    private final BedrockWitherEntity owner;

    public BedrockWitherHeadTrackingController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    public void tick() {
        updateHead(0, owner.getTarget());

        if (!(owner.level() instanceof ServerLevel level)) {
            return;
        }

        updateHead(1, resolveAlternative(level, owner.getAlternativeHeadTarget(1)));
        updateHead(2, resolveAlternative(level, owner.getAlternativeHeadTarget(2)));
    }

    private void updateHead(int headIndex, LivingEntity target) {
        BedrockWitherHeadRuntime state = owner.runtimeState().head(headIndex);
        state.setOldPitch(state.pitch());

        float desiredPitch = 0.0F;
        if (target != null && target.isAlive()) {
            Vec3 origin = firingPosition(headIndex);
            Vec3 targetPos = target.getEyePosition();
            double dx = targetPos.x - origin.x;
            double dy = targetPos.y - origin.y;
            double dz = targetPos.z - origin.z;
            double horizontal = Math.sqrt(dx * dx + dz * dz);

            desiredPitch = (float) (-Math.atan2(dy, horizontal) * (180.0D / Math.PI));
        }

        float nextPitch = Mth.approachDegrees(
                state.pitch(),
                desiredPitch,
                HISTORICAL_PITCH_CLAMP_DEGREES_PER_TICK
        );
        state.setPitch(nextPitch);
        owner.setSyncedHeadPitch(headIndex, nextPitch);
    }

    private LivingEntity resolveAlternative(ServerLevel level, Optional<UUID> targetUuid) {
        if (targetUuid.isEmpty()) {
            return null;
        }
        Entity entity = level.getEntity(targetUuid.get());
        return entity instanceof LivingEntity living && living.isAlive() ? living : null;
    }

    private Vec3 firingPosition(int headIndex) {
        if (headIndex == 0) {
            return new Vec3(owner.getX(), owner.getY() + 3.0D, owner.getZ());
        }

        float angleDegrees = owner.getYRot() + 180.0F * headIndex - 180.0F;
        float angleRadians = angleDegrees * Mth.DEG_TO_RAD;
        return new Vec3(
                owner.getX() + Mth.cos(angleRadians) * 1.3D,
                owner.getY() + 2.2D,
                owner.getZ() + Mth.sin(angleRadians) * 1.3D
        );
    }
}
