package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.forge.entity.MazinkyoukanEntity;
import dev.kneekura.fivedifficulties.forge.entity.SpiritualStrikeTalismanEntity;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;

/** Ports of the X1 items whose effect is an entity of their own (P16d). */
public final class X1EffectItems {
    private X1EffectItems() {}

    /** ItemSpiritualStrikeTalisman (霊撃札, stack 16): a 4-tick blast at the user's front right. */
    public static final class SpiritualStrikeTalisman extends Item {
        public SpiritualStrikeTalisman(Properties p) {
            super(p.stacksTo(16));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (!level.isClientSide) level.addFreshEntity(new SpiritualStrikeTalismanEntity(level, player));
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FIRE_EXTINGUISH,
                    SoundSource.PLAYERS, 2.0F, 12.0F);
            if (!player.getAbilities().instabuild) stack.shrink(1);
            return InteractionResultHolder.pass(stack);
        }
    }

    /** ItemMazinKyoukan (魔人経巻, glint): unrolls the scroll entity while held in use (each click spawns one). */
    public static final class MazinKyoukan extends Item {
        public MazinKyoukan(Properties p) {
            super(p.stacksTo(1));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.startUsingItem(hand);
            if (!level.isClientSide) level.addFreshEntity(new MazinkyoukanEntity(level, player));
            return InteractionResultHolder.consume(player.getItemInHand(hand));
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
        public boolean isFoil(ItemStack stack) {
            return true;
        }
    }
}
