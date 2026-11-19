package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.shot.X1ShotSpawner;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * Port of X1 {@code ItemTHShot}. X1 used one item with 19 damage values; 1.20.1 has no item
 * damage subtypes, so each X1 subtype is its own item carrying its X1 index. The stack NBT keys
 * (Number, DanmakuForm, Speed, Special, Gravity, Color, Infinity) are X1's own.
 */
public final class THShotItem extends Item {
    private final int x1Type;

    public THShotItem(int x1Type, Properties properties) {
        super(properties);
        this.x1Type = x1Type;
    }

    public int x1Type() {
        return x1Type;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level instanceof ServerLevel server) {
            shootDanmaku(server, stack, player, player.isShiftKeyDown(), X1ShotSpawner.posLiving(player),
                    X1ShotSpawner.pure(player.getLookAngle()),
                    X1ShotTables.SIZE[X1ShotTables.ITEM_SHOT_TYPE_TRANS[x1Type]]);
            // THShotLib.playShotSound: "random.bow", volume 2.0, pitch 1.2.
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ARROW_SHOOT,
                    SoundSource.PLAYERS, 2.0F, 1.2F);
            CompoundTag tag = stack.getTag();
            boolean infinity = tag != null && tag.getBoolean("Infinity");
            if (!infinity) stack.shrink(1);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }

    /** ItemTHShot.shootDanmaku, literal order including the creative NBT quirk. */
    public void shootDanmaku(ServerLevel level, ItemStack stack, LivingEntity living, boolean slowMode, Vec3d pos,
                             Vec3d angle, double distance) {
        RandomSource rand = level.getRandom();
        int type2 = X1ShotTables.ITEM_FORM[x1Type];
        int color = rand.nextInt(7);
        int special = 0;
        int way = 1;
        double shotSpeed = X1ShotTables.ITEM_SPEED[x1Type];
        int danmakuForm = 0;
        double gravity = 0.0D;

        CompoundTag nbt = stack.getTag();
        if (nbt != null) {
            way = nbt.getShort("Number");
            danmakuForm = nbt.getByte("DanmakuForm");
            shotSpeed = X1ShotTables.ITEM_SPEED[x1Type] * (1.0D + (double) nbt.getByte("Speed") * 0.03D);
            special = nbt.getInt("Special");
            gravity = (double) nbt.getByte("Gravity") * -0.003D;
            color = nbt.getByte("Color");
        }
        // X1 creates the creative tag only after reading it, so later creative shots see Color=0 (red).
        if (living instanceof Player player && player.getAbilities().instabuild) {
            if (nbt == null) {
                nbt = new CompoundTag();
                stack.setTag(nbt);
                nbt.putShort("Number", (short) 1);
            }
            nbt.putBoolean("Infinity", true);
        }
        if (way > X1ShotTables.SHOT_MAX_NUMBER) way = X1ShotTables.SHOT_MAX_NUMBER;

        // Player power (THKaguyaLib.getPlayerPower / 400) is not ported yet: bonus 0.
        float damagePlus = 0.0F;
        X1ShotData shot = X1ShotData.shot(type2, color, X1ShotTables.SIZE[type2],
                X1ShotTables.DAMAGE[type2] + damagePlus, 0, 80, special);
        X1ShotPatterns patterns = X1ShotSpawner.patterns(level, living);
        Vec3d gravityVec = X1ShotPatterns.gravity(gravity);
        float wide;

        switch (danmakuForm) {
            case 0 -> { // Point
                double speed2 = shotSpeed;
                Vec3d point = pos.add(angle.scale(distance));
                for (int i = 1; i <= way; i++) {
                    patterns.createShot(point, angle, 0F, speed2, speed2, 0.0D, gravityVec, shot);
                    speed2 = shotSpeed / (double) way * (double) i;
                }
            }
            case 1 -> { // Random (forward)
                wide = slowMode ? 60F : 120F;
                patterns.createRandomRingShot(pos, angle, 0F, 9999, shotSpeed, shotSpeed, 0.0D, gravityVec, shot, way,
                        distance, wide);
            }
            case 2 -> { // Sector
                wide = way * 3F;
                if (slowMode) wide *= 0.5F;
                patterns.createWideShot(pos, angle, shotSpeed, shotSpeed, 0.0D, gravityVec, shot, way, wide, distance);
            }
            case 3 -> // Around
                    patterns.createCircleShot(pos, angle, shotSpeed, shotSpeed, 0.0D, gravityVec, shot, way, distance, 0F);
            case 4 -> // Sphere (X1 ignores gravity here)
                    patterns.createSphereShot(pos, angle, 0F, new Vec3d(0, 1, 0), 0F, 99999, shotSpeed, shotSpeed, 0.0D,
                            Vec3d.ZERO, shot, way, distance, 0F);
            case 5 -> { // Ring
                wide = 15F;
                if (slowMode) wide *= 0.5F;
                patterns.createRingShot(pos, angle, 0F, 9999, shotSpeed, shotSpeed, 0.0D, gravityVec, shot, way,
                        distance, wide, rand.nextFloat() * 360F);
            }
            default -> {}
        }
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        CompoundTag nbt = stack.getTag();
        return nbt != null && nbt.getBoolean("Infinity");
    }

    /** ItemTHShot.getColorFromItemStack, pass 0; pass 1 is white. */
    public static int tint(ItemStack stack, int pass) {
        if (pass == 1) return 0xFFFFFF;
        int color = 7;
        CompoundTag nbt = stack.getTag();
        if (nbt != null) {
            color = nbt.getByte("Color");
            if (color >= 8) color = 7;
            if (color < 0) color = 7;
        }
        return X1ShotTables.ITEM_COLOR_R[color] * 65536 + X1ShotTables.ITEM_COLOR_G[color] * 256
                + X1ShotTables.ITEM_COLOR_B[color];
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> list, TooltipFlag flag) {
        short shotNum = 1;
        byte form = 0;
        float shotSpeed = X1ShotTables.ITEM_SPEED[x1Type];
        int color = 8;
        double gravity = 0.0D;
        int bound = 0;
        CompoundTag nbt = stack.getTag();
        if (nbt != null) {
            shotNum = nbt.getShort("Number");
            form = nbt.getByte("DanmakuForm");
            shotSpeed = X1ShotTables.ITEM_SPEED[x1Type] * (1.0F + (float) nbt.getByte("Speed") * 0.03F);
            color = nbt.getByte("Color");
            gravity = (double) nbt.getByte("Gravity") * 0.003D;
            bound = nbt.getInt("Special") - X1ShotTables.BOUND01 + 1;
        }
        if (bound < 0) bound = 0;
        if (form >= 6) form = 6;
        float damage = X1ShotTables.DAMAGE[X1ShotTables.ITEM_SHOT_TYPE_TRANS[x1Type]] / 2F;
        list.add(Component.translatable("danmakuCrafting.damage").append(" : " + damage + " + 0.0"));
        list.add(Component.translatable("danmakuCrafting.number").append(" : " + shotNum));
        list.add(Component.translatable("danmakuCrafting.form").append(" : ")
                .append(Component.translatable("thKaguya.danmakuForm." + form)));
        list.add(Component.translatable("danmakuCrafting.speed").append(" : " + shotSpeed));
        list.add(Component.translatable("danmakuCrafting.gravity").append(gravity != 0.0D ? " : " + gravity : " : GFree"));
        list.add(Component.translatable("danmakuCrafting.color").append(" : ")
                .append(Component.translatable("thKaguya.color." + color)));
        if (bound >= 1 && bound <= 3) {
            list.add(Component.translatable("danmakuCrafting.bound").append(" : " + bound));
        } else if (bound == 4) {
            list.add(Component.translatable("danmakuCrafting.bound").append(" : Infinity"));
        } else {
            list.add(Component.translatable("danmakuCrafting.bound").append(" : 0"));
        }
        if (nbt != null && nbt.getBoolean("Infinity")) {
            list.add(Component.translatable("Infinity"));
        }
    }
}
