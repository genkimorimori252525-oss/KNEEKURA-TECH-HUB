package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.entity.SukimaEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code ItemGapFoldingUmbrella} (隙間の折りたたみ傘). Sneak right-click cycles its colour (16);
 * right-click opens a 24-tick direct gap of colour 32 + c, 2 blocks ahead, which pairs with gaps of colour
 * c. After 30 uses it folds back into a Gap item (with the damage it was made from). The ribbon layer is
 * tinted with the gap colour.
 */
public class GapFoldingUmbrellaItem extends Item {
    static final int[] R = {30, 179, 59, 81, 37, 123, 40, 128, 51, 216, 65, 222, 102, 211, 237, 240, 179};
    static final int[] G = {27, 49, 81, 48, 49, 47, 118, 128, 51, 129, 203, 207, 133, 84, 136, 240, 49};
    static final int[] B = {27, 44, 26, 26, 146, 190, 151, 128, 51, 152, 51, 42, 219, 205, 68, 240, 44};

    public GapFoldingUmbrellaItem(Properties properties) {
        super(properties.stacksTo(1).durability(30));
    }

    /** getColorFromItemStack (layer 1). */
    public static int tint(ItemStack stack, int layer) {
        if (layer == 0) return 0xFFFFFF;
        int color = stack.hasTag() ? stack.getTag().getByte("GapColor") : 0;
        if (color >= 16 || color < 0) color = 0;
        return R[color] * 65536 + G[color] * 256 + B[color];
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        float yaw = player.getYRot(), pitch = player.getXRot();
        double setX = player.getX() - Math.sin(yaw / 180F * (float) Math.PI) * Math.cos(pitch / 180F * (float) Math.PI) * 2.0D;
        double setY = player.getY() - Math.sin(pitch / 180F * (float) Math.PI) * 2.0D + player.getEyeHeight() / 2.0D;
        double setZ = player.getZ() + Math.cos(yaw / 180F * (float) Math.PI) * Math.cos(pitch / 180F * (float) Math.PI) * 2.0D;
        // 1.20 damageable stacks always carry a tag (Damage): X1's "no NBT yet" is "no GapColor yet".
        CompoundTag nbt = stack.hasTag() && stack.getTag().contains("GapColor") ? stack.getTag() : null;
        int color = 0;
        if (player.isShiftKeyDown()) {
            if (nbt != null) {
                color = nbt.getByte("GapColor") + 1;
                if (color >= 16) color = 0;
            } else {
                nbt = stack.getOrCreateTag();
            }
            nbt.putByte("GapColor", (byte) color);
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
        }
        BlockPos at = new BlockPos((int) setX, (int) setY, (int) setZ);
        if (level.getBlockState(at).isRedstoneConductor(level, at)) return InteractionResultHolder.pass(stack);
        if (dev.kneekura.fivedifficulties.forge.X1Config.useDefaultGapSE()) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ENDERMAN_TELEPORT,
                    SoundSource.PLAYERS, 0.5F, 0.4F / (level.random.nextFloat() * 4F + 0.8F));
        } else {
            level.playSound(null, player.getX(), player.getY(), player.getZ(), dev.kneekura.fivedifficulties.forge.PortRegistries.SOUND_SUKIMA.get(), SoundSource.PLAYERS, 1.0F, 1.0F);
        }
        if (nbt != null) {
            color = nbt.getByte("GapColor");
            if (color >= 16) color = 0;
        } else {
            nbt = stack.getOrCreateTag();
            nbt.putByte("Color", (byte) color); // X1 writes "Color" here, not "GapColor"
        }
        if (!level.isClientSide) level.addFreshEntity(SukimaEntity.colored(level, player, setX, setY, setZ, 32 + color));
        // damageItem(1): 1.7.10 only breaks above the max, so the umbrella reaches 30 and folds instead.
        if (!player.getAbilities().instabuild) stack.setDamageValue(stack.getDamageValue() + 1);
        if (stack.getDamageValue() >= stack.getMaxDamage()) {
            int originalDamage = nbt.getInt("OriginalDamage");
            ItemStack gap = new ItemStack(PortRegistries.GAP.get());
            gap.setDamageValue(originalDamage);
            return InteractionResultHolder.sidedSuccess(gap, level.isClientSide);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return true;
    }
}
