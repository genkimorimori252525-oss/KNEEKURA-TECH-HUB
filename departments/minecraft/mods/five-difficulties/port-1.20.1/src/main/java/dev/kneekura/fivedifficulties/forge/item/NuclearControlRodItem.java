package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity;
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
 * Port of X1 {@code ItemNuclearControlRod} (お空の制御棒): holding right-click grows a nuclear shot in
 * front of the player (it explodes if the rod leaves the hand); releasing it fires the shot, pushes the
 * player back by up to 4 blocks per tick of charge / 25 and costs 1 durability (36).
 */
public class NuclearControlRodItem extends Item {
    public NuclearControlRodItem(Properties properties) {
        super(properties.stacksTo(1).durability(36));
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        player.startUsingItem(hand);
        if (!level.isClientSide) {
            Vec3d look = X1Danmaku.getVecFromAngle(player.getYRot(), player.getXRot(), 1.0D);
            Vec3d side = X1Danmaku.getVecFromAngle(player.getYRot() + 20F, player.getXRot(), 0.3D + 0.3D / 2.0D);
            X1ShotData shot = X1ShotData.shot(0, X1ShotTables.ORANGE, 0.3F, 10.0F, 0, 70);
            // THShotLib.createNuclearShot passes firstSpeed (0.0) as the acceleration.
            level.addFreshEntity(new NuclearShotEntity(level, player,
                    X1Danmaku.pos(player.getX() + side.x(), X1Danmaku.getPosYFromEye(player, -0.1D) + side.y(), player.getZ() + side.z()),
                    look, 0F, X1Danmaku.rotate_Default(), 0F, 9999, 0.0D, 0.8D, 0.0D, X1Danmaku.gravity_Zero(), shot));
        }
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
        if (!(entity instanceof Player player)) return;
        int time = Math.min(getUseDuration(stack) - timeLeft, 100);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.GENERIC_EXPLODE, SoundSource.PLAYERS,
                4.0F, (1.0F + (level.random.nextFloat() - level.random.nextFloat()) * 0.2F) * 0.7F);
        Vec3d recoil = X1Danmaku.getVecFromAngle(player.getYRot(), player.getXRot(), time / 25.0D);
        player.setDeltaMovement(player.getDeltaMovement().subtract(recoil.x(), recoil.y(), recoil.z()));
        player.hurtMarked = true;
        stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(player.getUsedItemHand()));
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.BOW;
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
