package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.forge.entity.MiniHakkeroEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code ItemMiniHakkero}: right-click with 32 fire charges (counted over the whole main
 * inventory) puts a Mini Hakkero 1.3 blocks ahead, unless a normal cube is there, and fires an explosive
 * Master Spark. The hakkero returns to the inventory when it leaves.
 */
public class MiniHakkeroItem extends Item {
    /** THKaguyaConfig "Use Master Spark" default. */
    public static boolean usingMasterSpark = true;

    public MiniHakkeroItem(Properties properties) {
        super(properties.stacksTo(1));
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!usingMasterSpark) return InteractionResultHolder.pass(stack);
        float yaw = player.getYRot(), pitch = player.getXRot();
        // (int) casts truncate toward zero, as in X1.
        BlockPos at = new BlockPos(
                (int) (player.getX() - Math.sin(yaw / 180F * 3.141593F) * Math.cos(pitch / 180F * 3.141593F) * 1.3D),
                (int) (player.getY() - Math.sin(pitch / 180F * 3.141593F) * 1.3D + player.getEyeHeight()),
                (int) (player.getZ() + Math.cos(yaw / 180F * 3.141593F) * Math.cos(pitch / 180F * 3.141593F) * 1.3D));
        if (level.getBlockState(at).isRedstoneConductor(level, at)) return InteractionResultHolder.pass(stack); // isBlockNormalCube
        var items = player.getInventory().items;
        int count = 0;
        for (ItemStack s : items) if (s.is(Items.FIRE_CHARGE)) count += s.getCount();
        if (count < 32) return InteractionResultHolder.pass(stack);
        if (level.isClientSide) return InteractionResultHolder.success(stack);
        for (int i = 0; i < 32; i++) { // consumeInventoryItem: the first stack each time
            for (ItemStack s : items) {
                if (s.is(Items.FIRE_CHARGE)) {
                    s.shrink(1);
                    break;
                }
            }
        }
        level.addFreshEntity(new MiniHakkeroEntity(level, player, stack.getDamageValue()));
        // 1.7.10 restores the held stack size for creative players.
        if (!player.getAbilities().instabuild) stack.shrink(1);
        return InteractionResultHolder.consume(stack);
    }
}
