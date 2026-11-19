package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THSetLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardDeclaration;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.Optional;

/**
 * Ports of the X1 weapons that spawn no entity of their own (P16b). X1 tool materials keep their numbers;
 * 1.7.10 swords deal 4 + the material damage, so the port's swords use an attack modifier of 4.
 */
public final class X1Weapons {
    private X1Weapons() {}

    /** EnumHelper.addToolMaterial(name, harvestLevel, maxUses, efficiency, damage, enchantability). */
    public record X1Tier(int level, int uses, float speed, float damage, int enchant, Ingredient repair) implements Tier {
        @Override public int getUses() { return uses; }
        @Override public float getSpeed() { return speed; }
        @Override public float getAttackDamageBonus() { return damage; }
        @Override public int getLevel() { return level; }
        @Override public int getEnchantmentValue() { return enchant; }
        @Override public Ingredient getRepairIngredient() { return repair; }
    }

    public static final Tier LAEVATEINN = new X1Tier(0, 95, 9.0F, 3.0F, 0, Ingredient.EMPTY);
    public static final Tier ROUKANKEN = new X1Tier(0, 251, 4.0F, 3.0F, 0, Ingredient.EMPTY);
    public static final Tier ICICLE = new X1Tier(0, 30, 0.0F, 2.0F, 0, Ingredient.EMPTY);
    public static final Tier HAKUROU = new X1Tier(0, 100, 0.0F, 0.0F, 0, Ingredient.EMPTY);
    public static final Tier KAIGO = new X1Tier(0, 1, 0.0F, -4.0F, 0, Ingredient.EMPTY);
    /** ToolMaterial.IRON (2, 250, 6, 2, 14) with ItemDeathScythe's setMaxDamage(444). */
    public static final Tier DEATH_SCYTHE = new X1Tier(2, 444, 6.0F, 2.0F, 14, Ingredient.of(Items.IRON_INGOT));
    /** ToolMaterial.WOOD (0, 59, 2, 0, 15). */
    public static final Tier WOOD = new X1Tier(0, 59, 2.0F, 0.0F, 15, Ingredient.EMPTY);

    static Vec3d vec(Vec3 v) {
        return new Vec3d(v.x, v.y, v.z);
    }

    /** ItemSpearTheGungnir (durability 95, no repair): declares 神槍「スピア・ザ・グングニル」 (card 27) and throws the spear laser. */
    public static final class SpearTheGungnir extends Item {
        public SpearTheGungnir(Properties p) {
            super(p.stacksTo(1).durability(95).setNoRepair());
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (!(level instanceof ServerLevel server)) return InteractionResultHolder.success(stack);
            if (X1SpellCardDeclaration.check(server, stack, player, 27, 2, true)) {
                Vec3 look = player.getLookAngle();
                // X1 passes -x, +y, -z as the angle.
                X1Danmaku.createLaserA(player, player, X1Danmaku.pos(player.getX(), X1Danmaku.getPosYFromEye(player, 0.6D),
                                player.getZ()), X1Danmaku.angle(-look.x, look.y, -look.z), 0.0D, 2.0D, 0.0D, Vec3d.ZERO,
                        X1LaserData.laser(X1LaserData.LASER_GUNGNIR, X1ShotTables.RED, 1.0F, 10.0F, 14F, 0, 120,
                                X1ShotTables.GUNGNIR));
                level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ZOMBIE_VILLAGER_CURE,
                        SoundSource.PLAYERS, 0.5F, 2.7F);
                level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.WITHER_SPAWN,
                        SoundSource.PLAYERS, 0.2F, 10.0F);
                // setItemDamage(+1): never breaks the spear.
                if (!player.getAbilities().instabuild) stack.setDamageValue(stack.getDamageValue() + 1);
            }
            return InteractionResultHolder.pass(stack);
        }

        @Override
        public int getEnchantmentValue() {
            return 0;
        }

        @Override
        public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
            return false;
        }
    }

    /**
     * ItemLaevateinn: a sword that sets its target on fire for 3..5; right-click sweeps a set fire laser
     * around the player (sneak: a vertical cut). Only one at a time per player.
     */
    public static final class Laevateinn extends SwordItem {
        public Laevateinn(Properties p) {
            super(LAEVATEINN, 4, -2.4F, p.setNoRepair());
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
            super.hurtEnemy(stack, target, attacker);
            target.setSecondsOnFire(attacker.getRandom().nextInt(3) + 3);
            return true;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            for (Entity e : level.getEntities(player, player.getBoundingBox().inflate(20.0D))) {
                if (e instanceof THSetLaserEntity laser && laser.source() == player) return InteractionResultHolder.pass(stack);
            }
            if (!level.isClientSide) {
                X1LaserData data = X1LaserData.laser(X1ShotTables.RED + 16, 0.6F, 20.8F, 7.0F, 0, 30, X1ShotTables.FIRE);
                Vec3d pos = X1Danmaku.pos(0.0D, X1Danmaku.getPosYFromEye(player) - player.getY(), 0.0D);
                if (player.isShiftKeyDown()) {
                    Vec3d rotate = X1Danmaku.getVecFromAngle(player.getYRot() + 90F, 0F);
                    Vec3d move = X1Danmaku.getVecFromAngle(player.getYRot(), player.getXRot() - 90F);
                    X1Danmaku.createLaserB(player, player, pos, move, rotate, -6F, 9999, data, player, 1.5D, 1.0F)
                            .setAngleZ(90F);
                } else {
                    Vec3d look = vec(player.getLookAngle());
                    Vec3d rotate = X1Danmaku.getVecFromAngle(player.getYRot(), player.getXRot() - 90F);
                    Vec3d move = X1Danmaku.getVectorFromRotation(rotate, look, 90F);
                    X1Danmaku.createLaserB(player, player, pos, move, rotate, -6F, 9999, data, player, 1.5D, 1.0F);
                }
            }
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.GHAST_SHOOT, SoundSource.PLAYERS,
                    0.5F, 1.0F);
            stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(hand));
            return InteractionResultHolder.pass(stack);
        }

        @Override
        public int getEnchantmentValue() {
            return 0;
        }

        @Override
        public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
            return false;
        }
    }

    /**
     * ItemRoukanken (楼観剣): digs webs and leaves at 30, wool at 20, everything else three times as fast and
     * harvests anything; undead take 16 more. Hold and release on the ground to dash (up to 20 × 0.3); while
     * held, moving faster than 3 cuts what it passes and splits enemy shots.
     */
    public static class Roukanken extends SwordItem {
        public Roukanken(Properties p) {
            super(ROUKANKEN, 4, -2.4F, p);
        }

        @Override
        public float getDestroySpeed(ItemStack stack, BlockState state) {
            if (state.is(Blocks.COBWEB) || state.is(BlockTags.LEAVES)) return 30F;
            if (state.is(BlockTags.WOOL)) return 20F;
            return super.getDestroySpeed(stack, state) * 3F;
        }

        @Override
        public boolean isCorrectToolForDrops(BlockState state) {
            return true;
        }

        @Override
        public boolean isCorrectToolForDrops(ItemStack stack, BlockState state) {
            return true;
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
            if (target.getMobType() == MobType.UNDEAD) {
                target.hurt(attacker.damageSources().mobAttack(attacker), 16.0F);
                if (attacker instanceof Player player) player.magicCrit(target);
            }
            stack.hurtAndBreak(1, attacker, a -> a.broadcastBreakEvent(InteractionHand.MAIN_HAND));
            return true;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.startUsingItem(hand);
            return InteractionResultHolder.consume(player.getItemInHand(hand));
        }

        @Override
        public int getUseDuration(ItemStack stack) {
            return 72000;
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return UseAnim.BOW;
        }

        @Override
        public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
            if (!(entity instanceof Player player) || !player.onGround()) return;
            double power = (double) getUseDuration(stack) - timeLeft;
            if (power > 20.0D) power = 20.0D;
            power *= 0.3D;
            Vec3 v = player.getDeltaMovement();
            player.setDeltaMovement(-Math.sin(Math.toRadians(player.getYRot())) * power, v.y,
                    Math.cos(Math.toRadians(player.getYRot())) * power);
            if (!player.getAbilities().instabuild) player.causeFoodExhaustion(1.5F);
            stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(player.getUsedItemHand()));
        }

        /** onUpdate: only while this very stack is selected, and only for roukanken itself (senpuuzin overrides). */
        @Override
        public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
            if (!(entity instanceof Player player) || player.getInventory().getSelected() != stack) return;
            Vec3 m = player.getDeltaMovement();
            if (Math.sqrt(m.x * m.x + m.z * m.z) <= 3.0D) return;
            cut(stack, level, player, player.getBoundingBox().expandTowards(m).inflate(1.0D));
        }

        static void cut(ItemStack stack, Level level, Player player, AABB box) {
            List<Entity> list = level.getEntities(player, box);
            for (Entity hit : list) {
                if (!hit.isPickable()) continue;
                boolean isShot = false;
                if (hit instanceof LivingEntity living) {
                    if (player.hasLineOfSight(living)) {
                        if (living.getMobType() == MobType.UNDEAD) {
                            living.hurt(player.damageSources().mobAttack(player), 16.0F);
                            player.magicCrit(living);
                        } else {
                            living.hurt(player.damageSources().mobAttack(player), 8F);
                        }
                        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ARROW_SHOOT,
                                SoundSource.PLAYERS, 0.5F, 0.4F / (player.getRandom().nextFloat() * 4F + 0.8F));
                    }
                } else if (hit instanceof THShotEntity shot && !(hit instanceof THLaserEntity)) {
                    splitShot(shot, 90F);
                    if (!level.isClientSide) shot.discard();
                    isShot = true;
                }
                if (!isShot) stack.hurtAndBreak(1, player, p -> {});
                player.swing(InteractionHand.MAIN_HAND);
                if (stack.isEmpty() || stack.getDamageValue() == stack.getMaxDamage()) {
                    stack.shrink(1);
                    break;
                }
            }
        }

        static void splitShot(THShotEntity shot, float span) {
            if (shot.getOwner() instanceof LivingEntity user && shot.motion() != null && !shot.level().isClientSide) {
                X1Danmaku.createRandomRingShot(user, X1Danmaku.pos(shot.getX(), shot.getY(), shot.getZ()),
                        shot.motion().angle, 0.0D, 0.4D, 0.03D,
                        X1ShotData.shot(shot.getShotForm(), X1ShotTables.WHITE, shot.getShotSize() / 2.0F,
                                shot.shotDamage, 0, 80),
                        3, 0.0D, span);
            }
        }

        @Override
        public int getEnchantmentValue() {
            return 0;
        }

        @Override
        public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
            return false;
        }
    }

    /**
     * ItemRoukanSenpuuzin (楼観剣・旋風刃, glint): while selected it cuts everything within 1.5 at any speed,
     * stopping at the first target still in its hurt time; it does not wear and does not split shots.
     */
    public static final class RoukanSenpuuzin extends Roukanken {
        public RoukanSenpuuzin(Properties p) {
            super(p);
        }

        @Override
        public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
            if (!(entity instanceof Player player) || player.getInventory().getSelected() != stack) return;
            Vec3 m = player.getDeltaMovement();
            for (Entity hit : level.getEntities(player, player.getBoundingBox().expandTowards(m).inflate(1.5D))) {
                if (!hit.isPickable()) continue;
                if (hit instanceof LivingEntity living) {
                    if (living.hurtTime > 0 || living.getHealth() <= 0.0F) break;
                    if (player.hasLineOfSight(living)) {
                        if (living.getMobType() == MobType.UNDEAD) {
                            living.hurt(player.damageSources().mobAttack(player), 16.0F);
                            player.magicCrit(living);
                        } else {
                            living.hurt(player.damageSources().mobAttack(player), 8F);
                        }
                        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ARROW_SHOOT,
                                SoundSource.PLAYERS, 0.5F, 0.4F / (player.getRandom().nextFloat() * 4F + 0.8F));
                    }
                }
                player.swing(InteractionHand.MAIN_HAND);
                if (stack.getDamageValue() == stack.getMaxDamage()) {
                    stack.shrink(1);
                    break;
                }
            }
        }

        @Override
        public boolean isFoil(ItemStack stack) {
            return true;
        }
    }

    /**
     * ItemDeathScythe (iron, durability 444): right-click picks the nearest living thing on a 16-block line
     * and pulls it 0.6 toward the player (sneak: pushes it away).
     */
    public static final class DeathScythe extends SwordItem {
        public DeathScythe(Properties p) {
            super(DEATH_SCYTHE, 4, -2.4F, p);
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            double range = 16.0D;
            Vec3 look = player.getLookAngle();
            Vec3 from = new Vec3(player.getX(), player.getY() + player.getEyeHeight(), player.getZ());
            // X1 quirk: the far end is measured from the feet.
            Vec3 to = new Vec3(player.getX() + look.x * range, player.getY() + look.y * range, player.getZ() + look.z * range);
            HitResult block = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
            if (block.getType() != HitResult.Type.MISS) to = block.getLocation();
            Entity target = null;
            double d = 0.0D;
            for (Entity e : level.getEntities(player, player.getBoundingBox().expandTowards(look.scale(range)).inflate(1.0D))) {
                if (!(e instanceof LivingEntity)) continue;
                Optional<Vec3> at = e.getBoundingBox().inflate(0.3D).clip(from, to);
                if (at.isPresent()) {
                    double d1 = from.distanceTo(at.get());
                    if (d1 < d || d == 0.0D) {
                        target = e;
                        d = d1;
                    }
                }
            }
            if (target != null && !level.isClientSide) {
                double power = player.isShiftKeyDown() ? 0.6D : -0.6D;
                target.setDeltaMovement(target.getDeltaMovement().add(look.x * power, look.y * power, look.z * power));
                target.hurtMarked = true;
                stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(hand));
            }
            return InteractionResultHolder.pass(stack);
        }
    }

    /**
     * ItemKaigo (悔悟の棒, unbreakable, 1 damage): a charged rod (glint) knocks anything above 3/4 health down to
     * 3/4 and goes dull; right-click with an ink sac anywhere in the main inventory recharges it.
     */
    public static final class Kaigo extends SwordItem {
        public static final String TAG = "KaigoUsed";

        public Kaigo(Properties p) {
            super(KAIGO, 4, -2.4F, p.durability(0));
        }

        public static boolean used(ItemStack stack) {
            return stack.getTag() != null && stack.getTag().getBoolean(TAG);
        }

        private static void setUsed(ItemStack stack, boolean used) {
            if (used) stack.getOrCreateTag().putBoolean(TAG, true);
            else if (stack.getTag() != null) stack.getTag().remove(TAG);
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
            if ((double) target.getMaxHealth() * 0.75D < (double) target.getHealth() && !used(stack)) {
                target.setHealth((int) ((double) target.getMaxHealth() * 0.75D));
                setUsed(stack, true);
                return true;
            }
            return false;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            int ink = -1;
            var items = player.getInventory().items;
            for (int i = 0; i < items.size(); i++) {
                if (items.get(i).is(Items.INK_SAC)) {
                    ink = i;
                    break;
                }
            }
            if (ink >= 0 && used(stack)) {
                items.get(ink).shrink(1);
                setUsed(stack, false);
            }
            player.startUsingItem(hand);
            return InteractionResultHolder.consume(stack);
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return UseAnim.BLOCK;
        }

        @Override
        public int getUseDuration(ItemStack stack) {
            return 72000;
        }

        @Override
        public boolean isFoil(ItemStack stack) {
            return !used(stack);
        }

        @Override
        public boolean isDamageable(ItemStack stack) {
            return false;
        }
    }

    /** 1.7.10 ItemSword right-click: guard (block) for 72000 ticks. */
    public abstract static class GuardSword extends SwordItem {
        protected GuardSword(Tier tier, Properties p) {
            super(tier, 4, -2.4F, p);
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.startUsingItem(hand);
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
        public int getEnchantmentValue() {
            return 0;
        }

        @Override
        public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
            return false;
        }
    }

    /**
     * ItemIcicleSword (icicle 0/30/0/2): freezes what it hits in a Cirno ice box (not things over 3 wide or tall,
     * nor one already frozen); repaired with ice.
     */
    public static final class IcicleSword extends GuardSword {
        public IcicleSword(Properties p) {
            super(ICICLE, p);
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
            Level level = target.level();
            for (Entity e : level.getEntities(target, target.getBoundingBox())) {
                if (e instanceof dev.kneekura.fivedifficulties.forge.entity.CirnoIceBoxEntity box && target.equals(box.frozen)) {
                    return super.hurtEnemy(stack, target, attacker);
                }
            }
            if (target.getBbWidth() > 3.0F || target.getBbHeight() > 3.0F) return super.hurtEnemy(stack, target, attacker);
            if (!level.isClientSide) {
                level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.CirnoIceBoxEntity(level, target));
            }
            return super.hurtEnemy(stack, target, attacker);
        }

        @Override
        public boolean isValidRepairItem(ItemStack stack, ItemStack repair) {
            return repair.is(Items.ICE) || super.isValidRepairItem(stack, repair);
        }
    }

    /**
     * ItemHakurouken (hakurou 0/100/0/0): release a guard to throw a shot-reflecting wall (sneak) or, on the
     * ground while moving, to step back 1.5; either costs 1 durability.
     */
    public static final class Hakurouken extends GuardSword {
        public Hakurouken(Properties p) {
            super(HAKUROU, p);
        }

        @Override
        public void releaseUsing(ItemStack stack, Level level, LivingEntity entity, int timeLeft) {
            if (!(entity instanceof Player player)) return;
            boolean used = false;
            if (player.isShiftKeyDown()) {
                if (!level.isClientSide) {
                    level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.HakurouReflecterEntity(level, player));
                }
                used = true;
            } else {
                Vec3 m = player.getDeltaMovement();
                if (player.onGround() && (m.x != 0.0D || m.z != 0.0D)) {
                    double angle = Math.atan2(m.x, m.z);
                    player.setDeltaMovement(m.x - Math.sin(angle) * 1.5D, m.y, m.z - Math.cos(angle) * 1.5D);
                    used = true;
                }
            }
            if (used) stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(player.getUsedItemHand()));
        }
    }
}
