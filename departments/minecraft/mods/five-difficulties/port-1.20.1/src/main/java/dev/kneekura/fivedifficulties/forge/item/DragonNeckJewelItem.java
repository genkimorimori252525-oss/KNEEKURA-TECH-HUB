package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.forge.entity.DragonNeckJewelEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import java.util.Random;

/**
 * Port of X1 {@code ItemDragonNeckJewel} (龍の頸の玉). Durability 300 is its charge: a throw costs 70 and
 * needs damage below 229; sneaking at full charge throws five colours at once and costs 299. It
 * recharges 20 every 20 ticks in the inventory.
 */
public class DragonNeckJewelItem extends Item {
    private static final float[] R = {1.0F, 0.1F, 0.1F, 1.0F, 1.0F};
    private static final float[] G = {0.1F, 1.0F, 0.1F, 1.0F, 0.1F};
    private static final float[] B = {0.1F, 0.1F, 1.0F, 0.1F, 1.0F};

    public DragonNeckJewelItem(Properties properties) {
        super(properties.stacksTo(1).durability(300).setNoRepair());
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        Vec3d pos = X1Danmaku.pos(player.getX(), X1Danmaku.getPosYFromEye(player, -0.2D), player.getZ());
        if (!player.isShiftKeyDown() && stack.getDamageValue() < 229) {
            Vec3d look = X1Danmaku.getVecFromAngle(player.getYRot(), player.getXRot(), 1.0D);
            int rand = new Random().nextInt(5);
            orb(level, player);
            if (!level.isClientSide) {
                level.addFreshEntity(new DragonNeckJewelEntity(level, player, pos, look, R[rand], G[rand], B[rand]));
            }
            stack.hurtAndBreak(70, player, p -> p.broadcastBreakEvent(hand));
        } else if (player.isShiftKeyDown() && stack.getDamageValue() < 1) {
            float angle = -40F;
            for (int i = 0; i < 5; i++) {
                Vec3d v = X1Danmaku.getRotationVectorFromAngle(player.getYRot(), player.getXRot(), angle, 1.0D);
                if (!level.isClientSide) {
                    level.addFreshEntity(new DragonNeckJewelEntity(level, player, pos, v, R[i], G[i], B[i]));
                }
                angle += 20F;
            }
            orb(level, player);
            stack.hurtAndBreak(299, player, p -> p.broadcastBreakEvent(hand));
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }

    private static void orb(Level level, Player player) {
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.EXPERIENCE_ORB_PICKUP,
                SoundSource.PLAYERS, 0.5F, 0.4F / (level.random.nextFloat() * 4F + 0.8F));
    }

    /** onUpdate: recharge 20 every 20 ticks of the holder's life. */
    @Override
    public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
        if (entity.tickCount % 20 == 0 && stack.isDamaged() && entity instanceof LivingEntity living) {
            stack.hurtAndBreak(-20, living, l -> {});
        }
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return true;
    }

    @Override
    public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
        return false;
    }
}
