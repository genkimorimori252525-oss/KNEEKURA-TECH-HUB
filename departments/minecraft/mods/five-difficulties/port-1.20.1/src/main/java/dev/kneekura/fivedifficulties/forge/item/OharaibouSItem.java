package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.MiracleCircleEntity;
import dev.kneekura.fivedifficulties.forge.entity.SanaeWindEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import dev.kneekura.fivedifficulties.forge.spellcard.SpellCardItem;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code ItemOharaibouS} (風祝のお祓い棒). Holding right-click draws pentagrams (30 ticks each).
 * Released before the first is done it blows a wind (damage level / 5, lifetime level × 3 in 15..120,
 * WIND01) for 1 durability; after enough pentagrams and levels it charges the miracle cards in the
 * inventory (Charge 1000) and repairs itself: Miracle Fruit (1, Lv 20), Fafrotskies (2, 25),
 * Youryoku Spoiler (3, 30), Moses (4, 35), Yasaka's Divine Wind (5, 40).
 */
public class OharaibouSItem extends Item {
    public OharaibouSItem(Properties properties) {
        super(properties.stacksTo(1).durability(50));
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        player.startUsingItem(hand);
        if (!level.isClientSide) level.addFreshEntity(new MiracleCircleEntity(level, player, 0));
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
        if (!(entity instanceof Player player)) return;
        int time = getUseDuration(stack) - timeLeft;
        if (time >= 30) {
            for (ItemStack s : player.getInventory().items) {
                if (!(s.getItem() instanceof SpellCardItem card)) continue;
                int n = card.number();
                int lv = player.experienceLevel;
                if (time >= 150 && lv >= 40 && n == 18) {
                    setMiraclePower(s);
                    repair(stack, player, 30);
                } else if (time >= 120 && lv >= 35 && n == 17) {
                    setMiraclePower(s);
                    repair(stack, player, 20);
                } else if (time >= 90 && lv >= 30 && n == 16) {
                    setMiraclePower(s);
                    repair(stack, player, 15);
                } else if (time >= 60 && lv >= 25 && n == 15) {
                    setMiraclePower(s);
                    repair(stack, player, 10);
                } else if (lv >= 20 && n == 14) {
                    setMiraclePower(s);
                    stack.setDamageValue(stack.getDamageValue() - 5); // setItemDamage: also in creative
                }
            }
        }
        if (time < 30) {
            Vec3d look = X1Danmaku.getVecFromAngle(player.getYRot(), player.getXRot(), 1.0D);
            float damage = player.experienceLevel / 5F;
            int endurance = Math.max(15, Math.min(120, player.experienceLevel * 3));
            if (damage == 0) damage = 0.1F;
            if (!level.isClientSide) {
                level.addFreshEntity(new SanaeWindEntity(level, player, X1Danmaku.pos_Living(player), look, 0F,
                        X1Danmaku.rotate_Default(), 0F, 9999, 0.4D, 0.01D, 0.99D, X1Danmaku.gravity_Zero(), 0, 1.0F,
                        damage, 0, endurance, X1ShotTables.WIND01));
            }
            stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(player.getUsedItemHand()));
        }
    }

    /** damageItem(-n): no effect for creative players, as in 1.7.10. */
    private static void repair(ItemStack stack, Player player, int n) {
        stack.hurtAndBreak(-n, player, p -> {});
    }

    private static void setMiraclePower(ItemStack card) {
        card.getOrCreateTag().putInt("Charge", 1000);
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 72000;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.BLOCK;
    }
}
