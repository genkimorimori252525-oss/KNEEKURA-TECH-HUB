package org.kneekura.bedrockwither.entity.ai;

import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.targeting.TargetingConditions;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;

/**
 * Java adapter for the pinned Bedrock Wither look_at_target / look_at_player goals.
 *
 * Mojang's current Wither definition sets look_time=1..2 seconds at priorities
 * 5 and 6. The component defaults supply look_distance=8 and probability=0.02.
 * This goal deliberately owns only LOOK control and does not replace the
 * Bedrock-specific three-head pitch controller.
 */
public final class BedrockLookGoal extends Goal {
    public enum Source {
        CURRENT_TARGET,
        NEAREST_PLAYER
    }

    public static final double LOOK_DISTANCE = 8.0D;
    public static final float START_PROBABILITY = 0.02F;
    public static final int MIN_LOOK_TICKS = 20;
    public static final int MAX_LOOK_TICKS = 40;

    private final BedrockWitherEntity owner;
    private final Source source;
    private final TargetingConditions playerConditions;
    @Nullable
    private LivingEntity lookAt;
    private int lookTicks;

    public BedrockLookGoal(BedrockWitherEntity owner, Source source) {
        this.owner = owner;
        this.source = source;
        this.playerConditions = TargetingConditions.forNonCombat()
                .range(LOOK_DISTANCE)
                .selector(entity -> EntitySelector.notRiding(owner).test(entity));
        this.setFlags(EnumSet.of(Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        if (owner.getRandom().nextFloat() >= START_PROBABILITY) {
            return false;
        }

        LivingEntity candidate;
        if (source == Source.CURRENT_TARGET) {
            candidate = owner.getTarget();
            if (!owner.isValidCombatTarget(candidate)) {
                return false;
            }
        } else {
            candidate = owner.level().getNearestPlayer(
                    playerConditions,
                    owner,
                    owner.getX(),
                    owner.getEyeY(),
                    owner.getZ()
            );
        }

        if (candidate == null || owner.distanceToSqr(candidate) > LOOK_DISTANCE * LOOK_DISTANCE) {
            return false;
        }
        lookAt = candidate;
        return true;
    }

    @Override
    public boolean canContinueToUse() {
        if (lookAt == null || !lookAt.isAlive() || lookTicks <= 0
                || owner.distanceToSqr(lookAt) > LOOK_DISTANCE * LOOK_DISTANCE) {
            return false;
        }
        return source != Source.CURRENT_TARGET || owner.getTarget() == lookAt;
    }

    @Override
    public void start() {
        lookTicks = MIN_LOOK_TICKS
                + owner.getRandom().nextInt(MAX_LOOK_TICKS - MIN_LOOK_TICKS + 1);
    }

    @Override
    public void stop() {
        lookAt = null;
        lookTicks = 0;
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        if (lookAt == null) {
            return;
        }
        owner.getLookControl().setLookAt(lookAt.getX(), lookAt.getEyeY(), lookAt.getZ());
        lookTicks--;
    }

    public Source source() {
        return source;
    }
}
