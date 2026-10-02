package org.kneekura.bedrockwither.entity.ai;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.AABB;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;
import org.kneekura.bedrockwither.entity.BedrockWitherThreatLedger;

import java.util.EnumSet;
import java.util.List;

public final class BedrockHighestDamageTargetGoal extends Goal {
    private final BedrockWitherEntity mob;
    private LivingEntity selected;

    public BedrockHighestDamageTargetGoal(BedrockWitherEntity mob) {
        this.mob = mob;
        this.setFlags(EnumSet.of(Flag.TARGET));
    }

    @Override
    public boolean canUse() {
        selected = select();
        return selected != null;
    }

    @Override
    public boolean canContinueToUse() {
        LivingEntity next = select();
        if (next == null) {
            return false;
        }
        selected = next;
        if (mob.getTarget() != selected) {
            mob.setTarget(selected);
        }
        return true;
    }

    @Override
    public void start() {
        mob.setTarget(selected);
    }

    @Override
    public void stop() {
        if (mob.getTarget() == selected) {
            mob.setTarget(null);
        }
        selected = null;
    }

    private LivingEntity select() {
        double range = mob.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.FOLLOW_RANGE);
        AABB area = mob.getBoundingBox().inflate(range);
        List<LivingEntity> candidates = mob.level().getEntitiesOfClass(
                LivingEntity.class,
                area,
                entity -> entity != mob && entity.isAlive()
        );

        return mob.threatLedger()
                .selectHighestDamageTarget(
                        candidates,
                        BedrockWitherThreatLedger.Metric.TOTAL_DAMAGE,
                        mob.level().getGameTime(),
                        -1L
                )
                .orElse(null);
    }
}
