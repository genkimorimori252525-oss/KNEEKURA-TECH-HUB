package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1LaserPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1ShotPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.shot.X1LaserSpawner;
import dev.kneekura.fivedifficulties.forge.shot.X1ShotSpawner;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.DyeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * Port of X1 {@code ItemTHLaser} (damage 0 middle, 1 short, 2 long). The colour comes from a dye
 * in the hotbar slot to the right, as in X1, unless the stack NBT sets one.
 */
public final class THLaserItem extends Item {
    /** ItemTHLaser.speed (only the first three entries are reachable). */
    private static final float[] SPEED = {0.6F, 0.6F, 0.5F};
    /** 1.7.10 dye metadata (0 = ink sac ... 15 = bone meal) to X1 colour. */
    private static final int[] SELECTABLE_COLOR = {7, 0, 2, 0, 1, 4, 5, 7, 7, 4, 2, 3, 5, 4, 6, 7};

    private final int x1Type;

    public THLaserItem(int x1Type, Properties properties) {
        super(properties);
        this.x1Type = x1Type;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(level instanceof ServerLevel server)) return InteractionResultHolder.success(stack);

        int color = level.getRandom().nextInt(7);
        int slot = player.getInventory().selected;
        if (slot < 8 && player.getInventory().getItem(slot + 1).getItem() instanceof DyeItem dye) {
            color = SELECTABLE_COLOR[15 - dye.getDyeColor().getId()]; // 1.20 dye id = 15 - 1.7.10 meta
        }
        float length = x1Type == 1 ? 2.0F : x1Type == 2 ? 8.0F : 5.0F;
        int way = 1;
        double shotSpeed = SPEED[x1Type];
        int danmakuForm = 0;
        float damage = 5.0F;
        CompoundTag nbt = stack.getTag();
        if (nbt != null) {
            way = nbt.getShort("Number");
            danmakuForm = nbt.getByte("DanmakuForm");
            shotSpeed = SPEED[x1Type] * (1.0D + (double) nbt.getByte("Speed") * 0.03D);
            int setColor = nbt.getByte("Color");
            if (setColor != 9) color = setColor;
        }
        if (way > X1ShotTables.LASER_MAX_NUMBER) way = X1ShotTables.LASER_MAX_NUMBER;

        Vec3d pos = X1ShotSpawner.posLiving(player);
        Vec3d look = X1ShotPatterns.vecFromAngle(player.getYRot(), player.getXRot(), 1.0D);
        Vec3d lookVec = X1ShotSpawner.pure(player.getLookAngle());
        X1LaserData laser = X1LaserData.laser(color, 0.1F, length, damage);
        X1LaserPatterns p = X1LaserSpawner.patterns(server, player, player);
        float wide;
        switch (danmakuForm) {
            case 0 -> {
                double speed2 = shotSpeed;
                for (int i = 1; i <= way; i++) {
                    p.createLaserA(pos, look, speed2, speed2, 0.0D, Vec3d.ZERO, laser);
                    speed2 = shotSpeed / (double) way * (double) i;
                }
            }
            case 1 -> {
                wide = player.isShiftKeyDown() ? 15F : 30F;
                p.createRandomRingLaser(pos, look, shotSpeed, shotSpeed, 0.0D, Vec3d.ZERO, laser, way, 0.2D, wide);
            }
            case 2 -> {
                wide = way * 5F;
                if (player.isShiftKeyDown()) wide *= 0.5F;
                p.createWideLaserA(pos, lookVec, shotSpeed, shotSpeed, 0.0D, Vec3d.ZERO, laser, way, wide, 0.1D);
            }
            case 3 -> p.createCircleLaserA(pos, lookVec, shotSpeed, shotSpeed, 0.0D, Vec3d.ZERO, laser, way, 0.1D);
            case 4 -> p.createSphereLaserA(pos, look, shotSpeed, shotSpeed, 0.0D, Vec3d.ZERO, laser, way, 0.2D, 0F);
            case 5 -> {
                wide = player.isShiftKeyDown() ? 7.5F : 15F;
                p.createRingLaserA(pos, look, shotSpeed, shotSpeed, 0.0D, Vec3d.ZERO, laser, way, 0.1D, wide,
                        level.getRandom().nextFloat() * 360F);
            }
            default -> {}
        }
        stack.shrink(1); // X1 always consumes one laser
        return InteractionResultHolder.success(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> list, TooltipFlag flag) {
        short shotNum = 1;
        byte form = 0;
        float shotSpeed = SPEED[x1Type];
        int color = 8;
        CompoundTag nbt = stack.getTag();
        if (nbt != null) {
            shotNum = nbt.getShort("Number");
            form = nbt.getByte("DanmakuForm");
            shotSpeed = SPEED[x1Type] * (1.0F + (float) nbt.getByte("Speed") * 0.03F);
            color = nbt.getByte("Color");
        }
        if (form >= 6) form = 5;
        list.add(Component.translatable("danmakuCrafting.damage").append(" : 2.5"));
        list.add(Component.translatable("danmakuCrafting.number").append(" : " + shotNum));
        list.add(Component.translatable("danmakuCrafting.form").append(" : ")
                .append(Component.translatable("thKaguya.danmakuForm." + form)));
        list.add(Component.translatable("danmakuCrafting.speed").append(" : " + shotSpeed));
        list.add(Component.translatable("danmakuCrafting.color").append(" : ")
                .append(Component.translatable("thKaguya.color." + color)));
    }
}
