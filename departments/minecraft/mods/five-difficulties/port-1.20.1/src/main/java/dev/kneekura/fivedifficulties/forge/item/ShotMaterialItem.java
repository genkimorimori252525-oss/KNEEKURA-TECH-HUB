package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Port of X1 {@code ItemShotMaterial}: right click fires one white tiny shot at speed 1.0. */
public final class ShotMaterialItem extends Item {
    public ShotMaterialItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!level.isClientSide) {
            X1Danmaku.createShot(player, X1Danmaku.pos_Living(player), X1Danmaku.look(player), 1.0D,
                    X1ShotData.shot(X1ShotTables.FORM_TINY, X1ShotTables.WHITE));
            X1Danmaku.playShotSound(player);
            if (!player.getAbilities().instabuild) stack.shrink(1);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }
}
