package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import dev.kneekura.fivedifficulties.forge.shot.X1SpecialShotRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;

/** Ports of the X1 items that fire danmaku without an entity of their own (P16c). */
public final class X1ShotItems {
    private X1ShotItems() {}

    /** X1 getMovingObjectPositionFromPlayer(.., true) landed on a water source block. */
    static boolean lookingAtWaterSource(Level level, Player player) {
        BlockHitResult hit = ItemAccess.pov(level, player);
        if (hit.getType() != HitResult.Type.BLOCK) return false;
        BlockPos pos = hit.getBlockPos();
        return level.getFluidState(pos).is(FluidTags.WATER) && level.getFluidState(pos).isSource();
    }

    /** Opens Item.getPlayerPOVHitResult (protected) for the helpers above. */
    private static final class ItemAccess extends Item {
        private ItemAccess() {
            super(new Properties());
        }

        static BlockHitResult pov(Level level, Player player) {
            return getPlayerPOVHitResult(level, player, ClipContext.Fluid.SOURCE_ONLY);
        }
    }

    /**
     * ItemSoulTorch (stack 16): hold 12 ticks to release three homing purple phantoms upward (special 352: homing
     * 16, not stopped by blocks). Creative players also fire at once on the click, as X1 does.
     */
    public static final class SoulTorch extends Item {
        public static final int SPECIAL_SOULTORCH = 352;

        public SoulTorch(Properties p) {
            super(p.stacksTo(16));
            X1SpecialShotRegistry.register(new X1SpecialShotRegistry.SpecialShot() {
                @Override
                public void move(THShotEntity shot, X1ShotMotion motion, int id) {
                    shot.homing(motion, 16.0F);
                }

                @Override
                public boolean hitBlock(THShotEntity shot, X1ShotMotion motion, int id, BlockHitResult hit) {
                    return true;
                }

                @Override
                public boolean hitEntity(THShotEntity shot, X1ShotMotion motion, int id, Entity hit) {
                    return false;
                }
            }, SPECIAL_SOULTORCH);
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (player.getAbilities().instabuild) fire(stack, level, player);
            player.startUsingItem(hand);
            return InteractionResultHolder.consume(stack);
        }

        @Override
        public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
            if (entity instanceof Player player) fire(stack, level, player);
            return stack;
        }

        static void fire(ItemStack stack, Level level, Player player) {
            if (!level.isClientSide) {
                X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_PHANTOM, X1ShotTables.PURPLE, 0.4F, 7.0F, 0, 480,
                        SPECIAL_SOULTORCH);
                X1Danmaku.createRingShot(player, player, X1Danmaku.pos_Living(player),
                        X1Danmaku.angle(player.getYRot(), -90F), 0F, 9999, 0.01D, 0.4D, 0.03D, Vec3d.ZERO, shot, 3, 0.3D,
                        30F, 0F);
                X1Danmaku.playShotSound(player);
            }
            if (!player.getAbilities().instabuild) stack.shrink(1);
        }

        @Override
        public int getUseDuration(ItemStack stack) {
            return 12;
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return UseAnim.BOW;
        }
    }

    /**
     * ItemYuyukoFan (durability 444, glint): hold and release to spread 32..72 butterflies (in threes) — two
     * mirrored fans ahead, or (sneak) six rings turning both ways. A hit on a wounded target under 20 health
     * has a 5% chance to take its life (4444) and heal the user by what it had left.
     */
    public static final class YuyukoFan extends Item {
        public YuyukoFan(Properties p) {
            super(p.stacksTo(1).durability(444));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.startUsingItem(hand);
            return InteractionResultHolder.consume(player.getItemInHand(hand));
        }

        @Override
        public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
            if (!(entity instanceof Player player)) return;
            int shotNum = 32 + getUseDuration(stack) - timeLeft;
            if (shotNum > 72) shotNum = 72;
            else if (shotNum % 3 != 0) shotNum = (shotNum / 3) * 3;
            int shotNum3 = shotNum / 3;
            int color = X1ShotTables.BLUE + player.getRandom().nextInt(4);
            int color2 = color + 1;
            if (color2 >= X1ShotTables.BLUE + 4) color2 = X1ShotTables.BLUE;
            float size = X1ShotTables.SIZE[X1ShotTables.FORM_BUTTERFLY];
            if (!level.isClientSide) {
                if (player.isShiftKeyDown()) {
                    Vec3d look = X1Weapons.vec(player.getLookAngle());
                    for (int i = 0; i < 3; i++) {
                        int color3 = i == 1 ? color2 : color;
                        double speed = 0.1D + (double) (i * 0.1D);
                        X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_BUTTERFLY, color3, size, 4.0F, 1, 80);
                        X1Danmaku.createCircleShot(player, player, X1Danmaku.pos_Living(player), look, 12F, 10, speed, speed,
                                0.0D, Vec3d.ZERO, shot, shotNum3, 0.5D, 0F);
                        X1Danmaku.createCircleShot(player, player, X1Danmaku.pos_Living(player), look, -12F, 10, speed, speed,
                                0.0D, Vec3d.ZERO, shot, shotNum3, 0.5D, 0F);
                    }
                } else {
                    Vec3d look = X1Danmaku.angle(player.getYRot(), player.getXRot());
                    Vec3d pos = X1Danmaku.pos(player.getX() + look.x() * 0.5D, X1Danmaku.getPosYFromEye(player) + look.y() * 0.5D,
                            player.getZ() + look.z() * 0.5D);
                    X1Danmaku.createWideShot(player, player, pos, look, 14.4F, 8, 0.0D, 0.45D, 0.02D, Vec3d.ZERO,
                            X1ShotData.shot(X1ShotTables.FORM_BUTTERFLY, color, size, 4.0F, 1, 80), shotNum3 + 1, 90F, 0.2D,
                            -120F);
                    X1Danmaku.createWideShot(player, player, pos, look, -14.4F, 8, 0.0D, 0.45D, 0.02D, Vec3d.ZERO,
                            X1ShotData.shot(X1ShotTables.FORM_BUTTERFLY, color2, size, 4.0F, 1, 80), shotNum3 + 1, 90F, 0.2D,
                            120F);
                }
            }
            if (!player.getAbilities().instabuild) player.causeFoodExhaustion(1.5F);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.EXPERIENCE_ORB_PICKUP,
                    SoundSource.PLAYERS, 0.5F, 1.0F);
            stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(player.getUsedItemHand()));
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
            if (target.getHealth() > 0 && target.getHealth() < 20 && target.hurtTime > 0
                    && attacker.getRandom().nextInt(100) < 5) {
                attacker.heal(target.getHealth());
                target.hurt(attacker.damageSources().mobAttack(attacker), 4444);
                attacker.level().playSound(null, attacker.getX(), attacker.getY(), attacker.getZ(),
                        SoundEvents.ZOMBIE_INFECT, SoundSource.PLAYERS, 1.0F, 40.0F);
            }
            stack.hurtAndBreak(1, attacker, a -> a.broadcastBreakEvent(InteractionHand.MAIN_HAND));
            return true;
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
     * ItemKappaWaterPistol (durability 39, no repair): three falling blue light shots per click; sneak-click a
     * water source to refill 2. The last charge (damage 38) is never fired.
     */
    public static final class KappaWaterPistol extends Item {
        public KappaWaterPistol(Properties p) {
            super(p.stacksTo(1).durability(39).setNoRepair());
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (player.isShiftKeyDown() && lookingAtWaterSource(level, player)) {
                stack.setDamageValue(stack.getDamageValue() - 2);
                player.swing(hand);
                return InteractionResultHolder.pass(stack);
            }
            if (stack.getDamageValue() == stack.getMaxDamage() - 1) return InteractionResultHolder.pass(stack);
            double speed = 0.3D;
            Vec3d v = X1Danmaku.getVecFromAngle(player.getYRot() + 40F, player.getXRot(), 0.4D);
            Vec3d pos = X1Danmaku.pos(player.getX() + v.x(), X1Danmaku.getPosYFromEye(player, -0.1D) + v.y(),
                    player.getZ() + v.z());
            if (!level.isClientSide) {
                X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_LIGHT, X1ShotTables.BLUE, 0.2F, 4.0F, 0, 120);
                X1Danmaku.createShot(player, player, pos, X1Danmaku.angle(player.getYRot(), player.getXRot() - 7F), 0F,
                        1.0D - speed, 0.0D, 0.4D, X1Danmaku.gravity_Default(), shot);
                X1Danmaku.createShot(player, player, pos, X1Danmaku.angle(player.getYRot(), player.getXRot()), 0F,
                        1.1D - speed, 0.0D, 0.4D, X1Danmaku.gravity_Default(), shot);
                X1Danmaku.createShot(player, player, pos, X1Danmaku.angle(player.getYRot(), player.getXRot() + 7F), 0F,
                        1.2D - speed, 0.0D, 0.4D, X1Danmaku.gravity_Default(), shot);
            }
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.GENERIC_SPLASH,
                    SoundSource.PLAYERS, 0.5F, 4.0F);
            stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(hand));
            return InteractionResultHolder.pass(stack);
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return UseAnim.BOW;
        }
    }

    /**
     * ItemIbukihyou (伊吹瓢, durability 11, always drinkable): a drink costs 5 and gives Strength for 15 s and
     * Nausea III for 20 s; it can be drunk while damage is under 6. Right-clicking a water source refills 1.
     * Sneaking when the drink finishes keeps it untouched.
     */
    public static final class IbukiGourd extends Item {
        public IbukiGourd(Properties p) {
            super(p.stacksTo(1).durability(11).setNoRepair()
                    .food(new FoodProperties.Builder().nutrition(0).saturationMod(0F).alwaysEat().build()));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (lookingAtWaterSource(level, player)) {
                if (stack.isDamaged()) {
                    player.swing(hand);
                    stack.setDamageValue(stack.getDamageValue() - 1);
                }
                return InteractionResultHolder.pass(stack);
            }
            if (stack.getDamageValue() < 6) {
                player.startUsingItem(hand);
                return InteractionResultHolder.consume(stack);
            }
            return InteractionResultHolder.pass(stack);
        }

        @Override
        public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
            if (!(entity instanceof Player player) || player.isShiftKeyDown()) return stack;
            if (stack.getDamageValue() < 6) {
                stack.hurtAndBreak(5, player, p -> {});
                level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.PLAYER_BURP,
                        SoundSource.PLAYERS, 0.5F, level.random.nextFloat() * 0.1F + 0.9F);
                if (!level.isClientSide) {
                    player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 15 * 20, 0));
                    player.addEffect(new MobEffectInstance(MobEffects.CONFUSION, 20 * 20, 2));
                }
            }
            return stack;
        }

        @Override
        public int getUseDuration(ItemStack stack) {
            return 16;
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return stack.getDamageValue() >= 6 ? UseAnim.NONE : UseAnim.DRINK;
        }
    }
}
