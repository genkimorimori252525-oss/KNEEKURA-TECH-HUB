package org.kneekura.staff;

import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** One self-targeted, non-damaging use ability. Item.use is the right-click hook. */
public final class CelestialStaffItem extends Item {
    public CelestialStaffItem() { super(new Item.Properties().stacksTo(1)); }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        var decision = StaffUsePolicy.decide(level.isClientSide, player.getCooldowns().isOnCooldown(this));
        if (decision == StaffUsePolicy.Decision.CLIENT_ACK) return InteractionResultHolder.success(stack);
        if (decision == StaffUsePolicy.Decision.COOLDOWN) return InteractionResultHolder.fail(stack);
        player.addEffect(new MobEffectInstance(MobEffects.GLOWING, StaffUsePolicy.GLOW_TICKS, 0));
        player.getCooldowns().addCooldown(this, StaffUsePolicy.COOLDOWN_TICKS);
        return InteractionResultHolder.consume(stack);
    }
}
