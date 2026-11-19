package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/** Ports of the small X1 items that spawn no entity of their own (P16a). Potion IDs are 1.7.10's. */
public final class X1SmallItems {
    private X1SmallItems() {}

    /** ItemHeavenlyPeach (food 2, wolf food, always edible, stack 10): Resistance III (id 11, level 2) for 20 s. */
    public static final class HeavenlyPeach extends Item {
        public HeavenlyPeach(Properties p) {
            super(p.stacksTo(10).food(new FoodProperties.Builder().nutrition(2).saturationMod(0.6F).meat().alwaysEat().build()));
        }

        @Override
        public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
            if (!level.isClientSide && entity instanceof Player player) {
                player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 20 * 20, 2));
            }
            return super.finishUsingItem(stack, level, entity);
        }
    }

    /**
     * ItemSwallowCowrieShell (燕の子安貝, stack 1, glint, always edible): X1 replaces onEaten entirely, so the
     * shell is never used up and gives no normal food. It turns up to 10 levels into hunger (2 per level,
     * saturation 5) and Regeneration II; standing, only as much as the hunger bar is missing.
     */
    public static final class SwallowCowrieShell extends Item {
        public SwallowCowrieShell(Properties p) {
            super(p.stacksTo(1).food(new FoodProperties.Builder().nutrition(0).saturationMod(0.6F).alwaysEat().build()));
        }

        @Override
        public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
            if (!(entity instanceof Player player)) return stack;
            int performance = player.experienceLevel;
            if (!player.isShiftKeyDown()) {
                performance = (int) ((20 - player.getFoodData().getFoodLevel()) / 2.0 + 0.5);
                if (performance < 0) performance = 0;
                else if (performance > player.experienceLevel) performance = player.experienceLevel;
            }
            if (performance > 10) performance = 10;
            player.giveExperienceLevels(-performance);
            player.getFoodData().eat(performance * 2, 5F);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.PLAYER_BURP, SoundSource.PLAYERS,
                    0.5F, level.random.nextFloat() * 0.1F + 0.9F);
            if (!level.isClientSide) player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, performance * 3 * 20, 1));
            return stack;
        }

        @Override
        public boolean isFoil(ItemStack stack) {
            return true;
        }
    }

    /**
     * ItemClosedThirdEye (閉じたサードアイ): one second of Invisibility, and mobs within 30 that cannot see the
     * player or are more than 8 away forget them as a target.
     */
    public static final class ClosedThirdEye extends Item {
        public ClosedThirdEye(Properties p) {
            super(p.stacksTo(1));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 20, 0));
            for (Entity e : level.getEntities(player, player.getBoundingBox().inflate(30.0D))) {
                if (e instanceof Mob mob && (!mob.hasLineOfSight(player) || mob.distanceTo(player) > 8.0D)
                        && mob.getTarget() == player) {
                    mob.setTarget(null);
                }
            }
            return InteractionResultHolder.pass(player.getItemInHand(hand));
        }
    }

    /**
     * ItemTenguFan (天狗の団扇, durability 40): hold up to 24 ticks and release to blow an aqua wind shot
     * (WIND01, end 20) at charge / 7 speed. Holding the full 24 ticks finishes the use and blows nothing.
     */
    public static final class TenguFan extends Item {
        public TenguFan(Properties p) {
            super(p.stacksTo(1).durability(40));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.startUsingItem(hand);
            return InteractionResultHolder.consume(player.getItemInHand(hand));
        }

        @Override
        public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
            if (!(entity instanceof Player player)) return;
            X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_WIND, X1ShotTables.AQUA, 0, 20, X1ShotTables.WIND01);
            double speed = (double) (getUseDuration(stack) - timeLeft) / 7.0D;
            if (!level.isClientSide) {
                X1Danmaku.createShot(player, X1Danmaku.pos_Living(player), X1Danmaku.angle(player.getYRot(), player.getXRot()),
                        speed, shot);
            }
            player.swing(player.getUsedItemHand());
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ARROW_SHOOT, SoundSource.PLAYERS,
                    0.5F, 0.4F / (level.random.nextFloat() * 4F + 0.8F));
            stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(player.getUsedItemHand()));
        }

        @Override
        public int getUseDuration(ItemStack stack) {
            return 24;
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return UseAnim.BOW;
        }
    }

    /**
     * ItemOnbashira (御柱): a wooden sword that digs everything at 3, adds 5..22 mob damage to each hit, and
     * slows whoever carries it anywhere in the inventory (×0.9 sideways and upward every tick).
     */
    public static final class Onbashira extends SwordItem {
        public Onbashira(Properties p) {
            super(Tiers.WOOD, 4, -2.4F, p); // 1.7.10 swords: 4 + material damage
        }

        @Override
        public float getDestroySpeed(ItemStack stack, BlockState state) {
            return 3F;
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
            target.hurt(attacker.damageSources().mobAttack(attacker), 5 + attacker.getRandom().nextInt(18));
            stack.hurtAndBreak(1, attacker, a -> a.broadcastBreakEvent(InteractionHand.MAIN_HAND));
            return true;
        }

        @Override
        public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
            var v = entity.getDeltaMovement();
            entity.setDeltaMovement(v.x * 0.9, v.y > 0.0 ? v.y * 0.9 : v.y, v.z * 0.9);
        }
    }

    /** ItemHouraiPearl: eight coloured pearls (X1 damage 0..7); the creative list shows the first seven. */
    public static final String[] PEARL_NAMES = {"red", "blue", "green", "yellow", "purple", "aqua", "orange", "white"};
    public static final String[] PEARL_ICONS = {"RedPearl", "BluePearl", "GreenPearl", "YellowPearl", "PurplePearl",
            "AquaPearl", "OrangePearl", "WhitePearl"};
}
