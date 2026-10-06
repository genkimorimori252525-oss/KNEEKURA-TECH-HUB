package dev.kneekura.fivedifficulties.forge.timestop;

import net.minecraft.world.entity.LivingEntity;

/**
 * Future bridge for X1 spell-card entities that are explicitly allowed to
 * continue inside their owner's stopped time.
 */
public interface X1TimeStopMovable {
    boolean canMoveInX1TimeStop(LivingEntity source);

    default void onX1TimeStopFieldTick(LivingEntity source) {
    }
}
