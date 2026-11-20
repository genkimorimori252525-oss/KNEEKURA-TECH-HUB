package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.entity.mob.CursedDecoyDollEntity;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** X1 ItemUchide (打ち出の小槌) and ItemCursedDecoyDoll (呪いのデコイ人形). */
public final class X1MalletItems {
    private X1MalletItems() {}

    /**
     * ItemUchide: durability 100, misc tab. Right-click with any food left grows every shot of yours within 20 by
     * 0.5, plays the bow sound and adds 30 damage (with no cap and no break: 1.7.10 setItemDamage does neither);
     * in an inventory it heals 1 damage every tick. The GUI and item-transforming parts are commented out in X1.
     */
    public static final class MiracleMallet extends Item {
        public MiracleMallet(Properties properties) {
            super(properties.durability(100));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (player.getFoodData().getFoodLevel() > 0) {
                for (Entity e : level.getEntities(player, player.getBoundingBox().inflate(20.0D))) {
                    if (e instanceof THShotEntity shot && shot.getOwner() == player) shot.setShotSize(shot.getShotSize() + 0.5F);
                }
                level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ARROW_SHOOT, SoundSource.PLAYERS,
                        0.5F, 0.4F / (level.random.nextFloat() * 4F + 0.8F));
                player.swing(hand);
                stack.setDamageValue(stack.getDamageValue() + 30);
            }
            return InteractionResultHolder.pass(stack);
        }

        @Override
        public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
            stack.setDamageValue(stack.getDamageValue() - 1);
        }

        /** The 1.20 damage bar would hide the over-max damage X1 allows; show it only while damaged. */
        @Override
        public boolean isBarVisible(ItemStack stack) {
            return stack.getDamageValue() > 0;
        }

        @Override
        public int getBarWidth(ItemStack stack) {
            return Math.max(0, Math.round(13.0F - Math.min(stack.getDamageValue(), 100) * 13.0F / 100.0F));
        }
    }

    /**
     * ItemCursedDecoyDoll: one per stack, durability 30, glints. Right-click does nothing while any doll is within
     * 40; otherwise it places a doll at the player and takes 1 damage. At 30 damage it turns into the item named
     * by its "OriginalItemID" tag (X1's Miracle Mallet GUI, commented out, wrote it); with no tag that is item 0,
     * i.e. nothing.
     */
    public static final class CursedDecoyDoll extends Item {
        public CursedDecoyDoll(Properties properties) {
            super(properties.durability(30));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            for (Entity e : level.getEntities(player, player.getBoundingBox().inflate(40.0D))) {
                if (e instanceof CursedDecoyDollEntity) return InteractionResultHolder.pass(stack);
            }
            if (!level.isClientSide) level.addFreshEntity(new CursedDecoyDollEntity(level, player));
            stack.setDamageValue(stack.getDamageValue() + 1);
            if (stack.getDamageValue() >= stack.getMaxDamage()) {
                // X1 rebuilds from OriginalItemID / OriginalDamage; 1.20 has no numeric ids, and nothing sets them.
                stack = ItemStack.EMPTY;
                player.setItemInHand(hand, stack);
            }
            return InteractionResultHolder.pass(stack);
        }

        @Override
        public boolean isFoil(ItemStack stack) {
            return true;
        }
    }
}
