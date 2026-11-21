package dev.kneekura.fivedifficulties.forge.spellcard;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;
import java.util.function.Supplier;

/** Port of THKaguyaLib.checkSpellCardDeclaration / spellCardDeclaration. */
public final class X1SpellCardDeclaration {
    /** DanmakuConstants.NORMAL: players always declare at level 2. */
    public static final int NORMAL = 2;
    /** Bomb item (P14); while it is not ported, no bombs are counted. */
    public static Supplier<Item> bombItem = () -> null;

    private X1SpellCardDeclaration() {}

    private static float rad(float deg) {
        return deg / 180F * (float) Math.PI;
    }

    /**
     * Declares spell card {@code number} for {@code user} at a living target within 32 blocks of its
     * line of sight. Returns true when a card was declared.
     * <p>Port change (not X1): a player no longer needs an enemy on the exact sight line. Without one, the
     * enemy closest to the view direction (within {@link #LOCK_ON_ANGLE_DEG} degrees, {@link #LOCK_ON_RANGE}
     * blocks, visible) is locked on; with none at all, the card is declared at an invisible point where the
     * player is looking. Mobs keep X1's rule.
     */
    public static boolean check(ServerLevel world, ItemStack stack, LivingEntity user, int number, int level,
                                boolean firstAttack) {
        int needLevel = 0;
        if (user instanceof Player player && !player.getAbilities().instabuild) {
            if (stack.getItem() instanceof SpellCardItem && number >= 14 && number <= 18) {
                CompoundTag nbt = stack.getTag();
                if (nbt == null || nbt.getInt("Charge") <= 0) return false;
            }
            X1SpellCardRegistry.Entry entry = X1SpellCardRegistry.get(number);
            if (entry != null) needLevel = entry.create().getNeedLevel();
            if (player.experienceLevel + countBombs(player) < needLevel) return false;
        }

        double angleX = -Math.sin(rad(user.getYRot())) * Math.cos(rad(user.getXRot()));
        double angleY = -Math.sin(rad(user.getXRot()));
        double angleZ = Math.cos(rad(user.getYRot())) * Math.cos(rad(user.getXRot()));
        Vec3 start = new Vec3(user.getX(), user.getY() + user.getEyeHeight(), user.getZ());
        // X1 quirk: the far end is measured from the feet, not the eyes.
        Vec3 end = new Vec3(user.getX() + angleX * 32.0D, user.getY() + angleY * 32.0D, user.getZ() + angleZ * 32.0D);
        BlockHitResult block = world.clip(new ClipContext(start, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, user));
        if (block.getType() != HitResult.Type.MISS) end = block.getLocation();

        LivingEntity hit = null;
        double nearDistance = 0.0D;
        AABB search = user.getBoundingBox().expandTowards(angleX * 32.0D, angleY * 32.0D, angleZ * 32.0D).inflate(1.0D);
        for (Entity e : world.getEntities(user, search)) {
            if (!(e instanceof LivingEntity living) || e instanceof Animal || e instanceof Villager) continue;
            Optional<Vec3> intercept = dev.kneekura.fivedifficulties.forge.shot.X1Hit.intercept(e.getBoundingBox().inflate(0.3F), start, end);
            if (intercept.isEmpty()) continue;
            double distance = start.distanceTo(intercept.get());
            if (distance < nearDistance || nearDistance == 0.0D) {
                hit = living;
                nearDistance = distance;
            }
        }
        for (SpellCardEntity active : world.getEntitiesOfClass(SpellCardEntity.class, user.getBoundingBox().inflate(64.0D))) {
            if (active.user == user) return false;
        }
        if (hit == null && user instanceof Player) {
            hit = lockOn(world, user);
            if (hit == null) hit = aimPoint(world, user);
        }
        if (hit == null) return false;
        declare(world, user, hit, number, needLevel, level, firstAttack);
        return true;
    }

    /** Soft lock-on cone half angle and reach (the reach is X1's 32-block sight line). */
    public static final double LOCK_ON_ANGLE_DEG = 30.0D;
    public static final double LOCK_ON_RANGE = 32.0D;
    /** Distance of the invisible aim point when the sight line hits nothing. */
    public static final double AIM_POINT_DISTANCE = 16.0D;

    /** The visible enemy nearest to the view direction inside the lock-on cone, or null. */
    public static LivingEntity lockOn(ServerLevel world, LivingEntity user) {
        Vec3 eye = user.getEyePosition();
        Vec3 look = user.getLookAngle();
        double minCos = Math.cos(Math.toRadians(LOCK_ON_ANGLE_DEG));
        LivingEntity best = null;
        double bestCos = minCos;
        double bestDist = Double.MAX_VALUE;
        for (LivingEntity e : world.getEntitiesOfClass(LivingEntity.class, user.getBoundingBox().inflate(LOCK_ON_RANGE),
                e -> e != user && e.isAlive() && lockOnCandidate(user, e))) {
            Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
            double dist = to.length();
            if (dist > LOCK_ON_RANGE || dist < 1.0E-4D) continue;
            double cos = to.dot(look) / dist;
            if (cos < minCos) continue;
            // Prefer the smaller angle; within 1 degree of each other, the nearer one.
            boolean closerAngle = cos > bestCos + 1.5E-4D;
            boolean sameAngle = Math.abs(cos - bestCos) <= 1.5E-4D;
            if (!(closerAngle || (sameAngle && dist < bestDist))) continue;
            if (!visible(world, user, eye, e)) continue;
            best = e;
            bestCos = cos;
            bestDist = dist;
        }
        return best;
    }

    private static boolean lockOnCandidate(LivingEntity user, LivingEntity e) {
        // X1's sight line skips animals and villagers; the cone also skips players, allies, golems and armour stands.
        return !(e instanceof Animal) && !(e instanceof Villager) && !(e instanceof Player)
                && !(e instanceof net.minecraft.world.entity.decoration.ArmorStand)
                && !(e instanceof net.minecraft.world.entity.animal.IronGolem)
                && !(e instanceof net.minecraft.world.entity.animal.SnowGolem)
                && !e.isSpectator() && !e.isInvisible() && !e.isAlliedTo(user) && e.isPickable();
    }

    private static boolean visible(ServerLevel world, LivingEntity user, Vec3 eye, LivingEntity e) {
        Vec3 c = e.getBoundingBox().getCenter();
        return world.clip(new ClipContext(eye, c, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, user)).getType()
                == HitResult.Type.MISS
                || world.clip(new ClipContext(eye, e.getEyePosition(), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, user))
                .getType() == HitResult.Type.MISS;
    }

    /**
     * An invisible, never-spawned target where the player looks (the first block on the eye line within
     * {@link #AIM_POINT_DISTANCE}, otherwise that far ahead). The card aims at it and it never dies, so the
     * card runs its whole pattern instead of turning on its user.
     */
    public static LivingEntity aimPoint(ServerLevel world, LivingEntity user) {
        Vec3 eye = user.getEyePosition();
        Vec3 far = eye.add(user.getLookAngle().scale(AIM_POINT_DISTANCE));
        BlockHitResult b = world.clip(new ClipContext(eye, far, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, user));
        Vec3 at = b.getType() == HitResult.Type.MISS ? far : b.getLocation();
        var stand = new net.minecraft.world.entity.decoration.ArmorStand(world, at.x, at.y, at.z);
        stand.setInvisible(true);
        stand.setNoGravity(true);
        stand.setInvulnerable(true);
        return stand;
    }

    private static int countBombs(Player player) {
        Item bomb = bombItem.get();
        if (bomb == null) return 0;
        int n = 0;
        for (ItemStack s : player.getInventory().items) if (s.is(bomb)) n += s.getCount();
        return n;
    }

    /** spellCardDeclaration. */
    public static void declare(ServerLevel world, LivingEntity user, LivingEntity target, int number, int needLevel,
                               int level, boolean firstAttack) {
        SpellCardEntity card = new SpellCardEntity(world, user, target, number, level);
        world.addFreshEntity(card);
        Component name = Component.translatable("item.thSpellCard." + number + ".name");
        if (user instanceof Player player) {
            player.sendSystemMessage(name);
            world.playSound(null, player.getX(), player.getY(), player.getZ(), PortRegistries.SOUND_SPELLCARD.get(),
                    SoundSource.PLAYERS, dev.kneekura.fivedifficulties.forge.X1Config.spellCardVol(), 1.0F);
            int bomb = 0;
            Item bombItemType = bombItem.get();
            while (bombItemType != null && bomb < needLevel && consumeOne(player, bombItemType)) bomb++;
            player.giveExperienceLevels(bomb - needLevel);
        }
        if (target instanceof Player targetPlayer && firstAttack) {
            targetPlayer.sendSystemMessage(name);
            world.playSound(null, targetPlayer.getX(), targetPlayer.getY(), targetPlayer.getZ(),
                    PortRegistries.SOUND_SPELLCARD.get(), SoundSource.PLAYERS, dev.kneekura.fivedifficulties.forge.X1Config.spellCardVol(), 1.0F);
        }
        if (firstAttack) X1Danmaku.danmakuRemove(user, 40.0F, "Enemy", true);
    }

    private static boolean consumeOne(Player player, Item item) {
        for (ItemStack s : player.getInventory().items) {
            if (s.is(item)) {
                s.shrink(1);
                return true;
            }
        }
        return false;
    }
}
