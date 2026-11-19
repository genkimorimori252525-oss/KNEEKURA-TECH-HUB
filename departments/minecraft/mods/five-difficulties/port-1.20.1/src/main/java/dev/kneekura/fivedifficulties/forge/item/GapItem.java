package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.forge.entity.SukimaEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;

/**
 * Port of X1 {@code ItemSukima} (スキマ). Right-click places a warp gap (colour 1) on the block face you
 * look at, or 2 blocks ahead in the air, and uses up the item. Sneak right-click opens a pair of
 * 24-tick direct-warp gaps (colour 16): one 2 blocks ahead, one where the look ray (128) hits a block or a
 * living entity more than 5 blocks away; that use is lost only 15% of the time.
 */
public class GapItem extends Item {
    public GapItem(Properties properties) {
        super(properties);
    }

    /** getSetAngle: the yaw toward the spot, snapped to 45°, negated. */
    static float getSetAngle(Player player, double setX, double setZ) {
        float yaw = (float) Math.atan2(setX - player.getX(), setZ - player.getZ()) / 3.141593F * 180F;
        if (yaw < 0F) yaw += 360F;
        if (yaw % 90F < 45F) yaw = yaw - (yaw % 45F);
        else yaw = yaw - (yaw % 45F) + 45F;
        return -yaw;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        float yaw = player.getYRot(), pitch = player.getXRot();
        double setX = player.getX() - Math.sin(yaw / 180F * (float) Math.PI) * Math.cos(pitch / 180F * (float) Math.PI) * 2.0D;
        double setY = player.getY() - Math.sin(pitch / 180F * (float) Math.PI) * 2.0D + player.getEyeHeight() / 2.0D;
        double setZ = player.getZ() + Math.cos(yaw / 180F * (float) Math.PI) * Math.cos(pitch / 180F * (float) Math.PI) * 2.0D;
        BlockPos setPos = new BlockPos((int) setX, (int) setY, (int) setZ);
        if (level.getBlockState(setPos).isRedstoneConductor(level, setPos)) return InteractionResultHolder.pass(stack);

        SukimaEntity sukima;
        boolean lost = true;
        if (!player.isShiftKeyDown()) {
            double i, j, k;
            float rotationYaw = 0F;
            BlockHitResult hit = getPlayerPOVHitResult(level, player, ClipContext.Fluid.SOURCE_ONLY);
            if (hit.getType() == HitResult.Type.MISS) {
                Vec3 look = player.getLookAngle();
                i = player.getX() + look.x * 2.0D - 0.5D;
                j = player.getY() + look.y * 2.0D + 1.0D;
                k = player.getZ() + look.z * 2.0D - 0.5D;
                rotationYaw = player.getYRot();
            } else {
                i = hit.getBlockPos().getX();
                j = hit.getBlockPos().getY();
                k = hit.getBlockPos().getZ();
                switch (hit.getDirection().ordinal()) { // 1.7.10 sideHit
                    case 0 -> { j--; rotationYaw = getSetAngle(player, i, k); }
                    case 1 -> { j++; rotationYaw = getSetAngle(player, i, k); }
                    case 2 -> { k--; rotationYaw = 0F; }
                    case 3 -> { k++; rotationYaw = 180F; }
                    case 4 -> { i--; rotationYaw = 270F; }
                    default -> { i++; rotationYaw = 90F; }
                }
            }
            sukima = SukimaEntity.placed(level, player, i + 0.5D, j, k + 0.5D, rotationYaw);
        } else {
            double xMax = -Math.sin(yaw / 180F * (float) Math.PI) * Math.cos(pitch / 180F * (float) Math.PI) * 128.0D;
            double yMax = -Math.sin(pitch / 180F * (float) Math.PI) * 128.0D;
            double zMax = Math.cos(yaw / 180F * (float) Math.PI) * Math.cos(pitch / 180F * (float) Math.PI) * 128.0D;
            Vec3 from = new Vec3(player.getX(), player.getY() + player.getEyeHeight(), player.getZ());
            Vec3 to = new Vec3(player.getX() + xMax, player.getY() + yMax, player.getZ() + zMax); // X1: from the feet
            BlockHitResult block = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
            if (block.getType() == HitResult.Type.MISS) return InteractionResultHolder.pass(stack);
            to = block.getLocation();
            double hitX = to.x, hitY = to.y, hitZ = to.z;
            double xz = (hitX - setX) * (hitX - setX) + (hitZ - setZ) * (hitZ - setZ);
            if (Math.sqrt(xz + (hitY - setY) * (hitY - setY)) <= 5.0D) return InteractionResultHolder.pass(stack);
            Entity entity = null;
            double d = 0.0D;
            AABB search = player.getBoundingBox().expandTowards(xMax, yMax, zMax).inflate(1.0D);
            for (Entity e : level.getEntities(player, search)) {
                if (!(e instanceof LivingEntity)) continue;
                Optional<Vec3> at = dev.kneekura.fivedifficulties.forge.shot.X1Hit.intercept(e.getBoundingBox().inflate(0.3F), from, to);
                if (at.isEmpty()) continue;
                double d1 = from.distanceTo(at.get());
                if ((d1 < d || d == 0.0D) && d1 > 5.0D) {
                    entity = e;
                    d = d1;
                }
            }
            if (entity != null) {
                hitX = entity.getX();
                hitY = entity.getY(); // + yOffset / 2: 0 for 1.20 entities
                hitZ = entity.getZ();
                setY += 1.0D;
            }
            sukima = SukimaEntity.colored(level, player, setX, setY, setZ, 16);
            SukimaEntity sukima2 = SukimaEntity.colored(level, player, hitX, hitY, hitZ, 16);
            lost = level.random.nextInt(100) < 15;
            if (!level.isClientSide) level.addFreshEntity(sukima2);
        }
        if (dev.kneekura.fivedifficulties.forge.X1Config.useDefaultGapSE()) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ENDERMAN_TELEPORT,
                    SoundSource.PLAYERS, 0.5F, 0.4F / (level.random.nextFloat() * 4F + 0.8F));
        } else {
            level.playSound(null, player.getX(), player.getY(), player.getZ(), dev.kneekura.fivedifficulties.forge.PortRegistries.SOUND_SUKIMA.get(), SoundSource.PLAYERS, 1.0F, 1.0F);
        }
        if (!level.isClientSide) {
            level.addFreshEntity(sukima);
            if (lost && !player.getAbilities().instabuild) stack.shrink(1);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }
}
