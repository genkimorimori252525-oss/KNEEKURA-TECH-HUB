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

    /**
     * ItemAjaRedStone (エイジャの赤石, glint): while held in use, an effect gathers light; release fires a laser
     * (special 351: undead hit are set on fire for the shot damage, damage rate x2, fizz).
     */
    public static final class AjaRedStone extends Item {
        public AjaRedStone(Properties p) {
            super(p.stacksTo(1));
            dev.kneekura.fivedifficulties.forge.shot.X1SpecialShotRegistry.register(
                    new dev.kneekura.fivedifficulties.forge.shot.X1SpecialShotRegistry.SpecialShot() {
                        @Override
                        public void move(dev.kneekura.fivedifficulties.forge.entity.THShotEntity shot,
                                         dev.kneekura.fivedifficulties.core.x1.X1ShotMotion motion, int id) {}

                        @Override
                        public boolean hitBlock(dev.kneekura.fivedifficulties.forge.entity.THShotEntity shot,
                                                dev.kneekura.fivedifficulties.core.x1.X1ShotMotion motion, int id,
                                                net.minecraft.world.phys.BlockHitResult hit) {
                            return false;
                        }

                        @Override
                        public boolean hitEntity(dev.kneekura.fivedifficulties.forge.entity.THShotEntity shot,
                                                 dev.kneekura.fivedifficulties.core.x1.X1ShotMotion motion, int id,
                                                 net.minecraft.world.entity.Entity hit) {
                            if (hit instanceof net.minecraft.world.entity.LivingEntity living
                                    && living.getMobType() == net.minecraft.world.entity.MobType.UNDEAD) {
                                living.setSecondsOnFire((int) shot.shotDamage);
                                shot.multiplyDamageRate(2.0F);
                                Level level = shot.level();
                                level.playSound(null, shot.getX(), shot.getY(), shot.getZ(), SoundEvents.FIRE_EXTINGUISH,
                                        SoundSource.NEUTRAL, 0.5F,
                                        2.6F + (level.random.nextFloat() - level.random.nextFloat()) * 0.8F);
                            }
                            return false;
                        }
                    }, dev.kneekura.fivedifficulties.forge.entity.AjaRedStoneEffectEntity.SPECIAL_AJA_REDSTONE);
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.startUsingItem(hand);
            if (!level.isClientSide) {
                level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.AjaRedStoneEffectEntity(level, player));
            }
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

        @Override
        public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
            return false;
        }
    }

    /**
     * ItemPendulum (ナズーリンペンデュラム): searches for the block item in the slot right of it (sneak: high
     * sensitivity), announcing it in chat; the pendulum leaves the inventory while it hangs.
     */
    public static final class Pendulum extends Item {
        public Pendulum(Properties p) {
            super(p.stacksTo(1));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            var inv = player.getInventory();
            ItemStack search = inv.items.get(inv.selected + 1);
            if (search.isEmpty() || !(search.getItem() instanceof net.minecraft.world.item.BlockItem block)
                    || inv.selected >= 8) {
                return InteractionResultHolder.pass(stack);
            }
            int mode = player.isShiftKeyDown() ? 1 : 0;
            String key = block.getBlock().getDescriptionId();
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.EXPERIENCE_ORB_PICKUP,
                    SoundSource.PLAYERS, 0.5F, 0.9F);
            if (!level.isClientSide) {
                level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.PendulumEntity(level, player, mode, key));
                stack.shrink(1);
                player.sendSystemMessage(net.minecraft.network.chat.Component.translatable("thKaguya.msg.pendulum1")
                        .append(net.minecraft.network.chat.Component.translatable(search.getItem().getDescriptionId()))
                        .append(net.minecraft.network.chat.Component.translatable(
                                mode == 0 ? "thKaguya.msg.pendulum2" : "thKaguya.msg.pendulum3")));
            }
            return InteractionResultHolder.pass(stack);
        }
    }
}
