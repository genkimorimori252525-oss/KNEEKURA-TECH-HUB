package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.OnmyoudamaEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code ItemOharaibouR} (博麗のお祓い棒): hold right-click to charge a Yin-Yang Orb (orange,
 * bounces forever: BOUND04, end 180), release to throw it. Each throw costs 1 of 89 durability.
 */
public class OharaibouRItem extends Item {
    public OharaibouRItem(Properties properties) {
        super(properties.stacksTo(1).durability(89));
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        player.startUsingItem(hand);
        if (!level.isClientSide) {
            // X1 passes the negated rotation (the X1 rotationYaw convention).
            Vec3d v = X1Danmaku.getVecFromAngle(-player.getYRot(), -player.getXRot(), 0.6D);
            level.addFreshEntity(new OnmyoudamaEntity(level, player,
                    X1Danmaku.pos(player.getX() + v.x(), X1Danmaku.getPosYFromEye(player, -0.1D) + v.y(), player.getZ() + v.z()),
                    v, 0F, X1Danmaku.rotate_Default(), 0F, 9999, 0.0D, 1.8D, 0.00D, X1Danmaku.gravity_Default(),
                    X1ShotTables.ORANGE, 0.3F, 10.0F, 0, 180, X1ShotTables.BOUND04));
        }
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
        if (!(entity instanceof Player player)) return;
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ARROW_SHOOT, SoundSource.PLAYERS,
                2.0F, 0.3F);
        stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(player.getUsedItemHand()));
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.BLOCK;
    }

    @Override
    public int getEnchantmentValue() {
        return 0;
    }

    @Override
    public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
        return false;
    }
}
