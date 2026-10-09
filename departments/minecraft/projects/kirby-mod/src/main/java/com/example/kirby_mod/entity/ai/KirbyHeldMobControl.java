package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.KirbyMod;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.living.LivingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.UUID;

/**
 * Owns temporary held/spit Mob flags and restores them if the controlling Kirby disappears.
 */
@Mod.EventBusSubscriber(modid = KirbyMod.MODID)
public final class KirbyHeldMobControl {

    private static final String CONTROL_TAG = "kirby_mod:held_mob_control";
    private static final String RELEASE_RECOVERY_TAG = "kirby_mod:released_mob_recovery";
    private static final String VERIFY_UNTIL = "verify_until";
    private static final String MODE = "mode";
    private static final String OWNER = "owner";
    private static final String LEASE_UNTIL = "lease_until";
    private static final String ORIGINAL_INVISIBLE = "original_invisible";
    private static final String ORIGINAL_INVULNERABLE = "original_invulnerable";
    private static final String ORIGINAL_SILENT = "original_silent";
    private static final String ORIGINAL_NO_GRAVITY = "original_no_gravity";
    private static final String ORIGINAL_NO_PHYSICS = "original_no_physics";
    private static final String ORIGINAL_NO_AI = "original_no_ai";
    private static final String MODE_HELD = "held";
    private static final String MODE_SPIT = "spit";
    private static int expiredRecoveryCount;
    private static String lastExpiredRecovery = "none";

    private KirbyHeldMobControl() {}

    public static boolean capture(LivingEntity entity, UUID owner) {
        CompoundTag control = claim(entity, owner);
        if (control == null) return false;
        renew(control, entity.level().getGameTime(), MODE_HELD);
        applyContained(entity);
        return true;
    }

    public static boolean hold(LivingEntity entity, UUID owner) {
        CompoundTag control = ownedControl(entity, owner);
        if (control == null) return false;
        renew(control, entity.level().getGameTime(), MODE_HELD);
        applyContained(entity);
        return true;
    }

    public static boolean beginSpit(LivingEntity entity, UUID owner) {
        CompoundTag control = ownedControl(entity, owner);
        if (control == null) return false;
        renew(control, entity.level().getGameTime(), MODE_SPIT);
        entity.setInvisible(false);
        entity.setInvulnerable(false);
        entity.setSilent(false);
        entity.noPhysics = false;
        entity.setNoGravity(true);
        if (entity instanceof Mob mob) mob.setNoAi(true);
        return true;
    }

    public static boolean refreshSpit(LivingEntity entity, UUID owner) {
        CompoundTag control = ownedControl(entity, owner);
        if (control == null) return false;
        renew(control, entity.level().getGameTime(), MODE_SPIT);
        return true;
    }

    public static boolean release(LivingEntity entity, UUID owner) {
        CompoundTag control = ownedControl(entity, owner);
        if (control == null) return false;
        restore(entity, control);
        return true;
    }

    public static boolean isControlledBy(LivingEntity entity, UUID owner) {
        return ownedControl(entity, owner) != null;
    }

    private static void forceRelease(LivingEntity entity) {
        CompoundTag persistent = entity.getPersistentData();
        if (!persistent.contains(CONTROL_TAG, Tag.TAG_COMPOUND)) {
            return;
        }
        CompoundTag control = persistent.getCompound(CONTROL_TAG);
        restore(entity, control);
    }

    private static void restore(LivingEntity entity, CompoundTag control) {
        CompoundTag persistent = entity.getPersistentData();
        applyStoredState(entity, control, true);
        persistent.remove(CONTROL_TAG);

        // Keep the original snapshot briefly after release. This closes the gap where
        // a stale goal/mod tick can reapply projectile flags after the one-shot restore.
        CompoundTag recovery = control.copy();
        recovery.putLong(VERIFY_UNTIL, KirbyMobControlLeasePolicy.releaseVerifyUntil(
                entity.level().getGameTime()));
        persistent.put(RELEASE_RECOVERY_TAG, recovery);
    }

    private static void applyStoredState(
            LivingEntity entity, CompoundTag original, boolean beginFalling) {
        boolean originalNoGravity = original.getBoolean(ORIGINAL_NO_GRAVITY);
        boolean originalNoPhysics = original.getBoolean(ORIGINAL_NO_PHYSICS);
        entity.setInvisible(original.getBoolean(ORIGINAL_INVISIBLE));
        entity.setInvulnerable(original.getBoolean(ORIGINAL_INVULNERABLE));
        entity.setSilent(original.getBoolean(ORIGINAL_SILENT));
        entity.setNoGravity(originalNoGravity);
        entity.noPhysics = originalNoPhysics;
        if (entity instanceof Mob mob) {
            mob.setNoAi(original.getBoolean(ORIGINAL_NO_AI));
        }
        if (beginFalling) {
            Vec3 movement = entity.getDeltaMovement();
            double releasedY = KirbyMobControlLeasePolicy.releasedVerticalVelocity(
                    movement.y, originalNoGravity, originalNoPhysics);
            entity.setDeltaMovement(movement.x, releasedY, movement.z);
            if (!originalNoGravity && !originalNoPhysics) {
                entity.setOnGround(false);
                entity.fallDistance = 0.0F;
            }
        }
        entity.hurtMarked = true;
    }

    public static String debugSummary(LivingEntity entity) {
        CompoundTag control = control(entity);
        if (control == null) return "uncontrolled";
        long gameTime = entity.level().getGameTime();
        return "owner=" + ownerSummary(control)
                + " mode=" + control.getString(MODE)
                + " leaseRemaining=" + KirbyMobControlLeasePolicy.remaining(
                        gameTime, control.getLong(LEASE_UNTIL))
                + " invisible=" + entity.isInvisible()
                + " invulnerable=" + entity.isInvulnerable()
                + " silent=" + entity.isSilent()
                + " noGravity=" + entity.isNoGravity()
                + " noPhysics=" + entity.noPhysics
                + " onFire=" + entity.isOnFire()
                + (entity instanceof Mob mob ? " noAi=" + mob.isNoAi() : "");
    }

    public static String recoveryDebugSummary() {
        return "expiredRecoveries=" + expiredRecoveryCount
                + " last=" + lastExpiredRecovery;
    }

    @SubscribeEvent
    public static void onLivingTick(LivingEvent.LivingTickEvent event) {
        LivingEntity entity = event.getEntity();
        if (entity.level().isClientSide) return;
        verifyReleasedState(entity);
        CompoundTag control = control(entity);
        if (control == null) return;
        if (KirbyMobControlLeasePolicy.expired(
                entity.level().getGameTime(), control.getLong(LEASE_UNTIL))) {
            String mode = control.getString(MODE);
            lastExpiredRecovery = "id=" + entity.getUUID().toString().substring(0, 8)
                    + " mode=" + mode
                    + " tick=" + entity.level().getGameTime();
            expiredRecoveryCount++;
            forceRelease(entity);
        }
    }

    private static CompoundTag claim(LivingEntity entity, UUID owner) {
        finishPendingRelease(entity);
        CompoundTag existing = control(entity);
        if (existing != null) {
            boolean sameOwner = hasOwner(existing, owner);
            boolean expired = KirbyMobControlLeasePolicy.expired(
                    entity.level().getGameTime(), existing.getLong(LEASE_UNTIL));
            if (!KirbyMobControlOwnerPolicy.canClaim(true, sameOwner, expired)) {
                return null;
            }
            if (!sameOwner) {
                forceRelease(entity);
            } else {
                return existing;
            }
        }

        CompoundTag created = createControl(entity);
        created.putUUID(OWNER, owner);
        return created;
    }

    private static CompoundTag ownedControl(LivingEntity entity, UUID owner) {
        CompoundTag control = control(entity);
        return control != null && hasOwner(control, owner) ? control : null;
    }

    private static boolean hasOwner(CompoundTag control, UUID owner) {
        return control.hasUUID(OWNER) && control.getUUID(OWNER).equals(owner);
    }

    private static CompoundTag control(LivingEntity entity) {
        CompoundTag persistent = entity.getPersistentData();
        if (persistent.contains(CONTROL_TAG, Tag.TAG_COMPOUND)) {
            return persistent.getCompound(CONTROL_TAG);
        }
        return null;
    }

    private static void verifyReleasedState(LivingEntity entity) {
        CompoundTag persistent = entity.getPersistentData();
        if (!persistent.contains(RELEASE_RECOVERY_TAG, Tag.TAG_COMPOUND)) return;
        if (persistent.contains(CONTROL_TAG, Tag.TAG_COMPOUND)) {
            persistent.remove(RELEASE_RECOVERY_TAG);
            return;
        }

        CompoundTag recovery = persistent.getCompound(RELEASE_RECOVERY_TAG);
        applyStoredState(entity, recovery, false);
        if (KirbyMobControlLeasePolicy.releaseVerificationFinished(
                entity.level().getGameTime(), recovery.getLong(VERIFY_UNTIL))) {
            persistent.remove(RELEASE_RECOVERY_TAG);
        }
    }

    private static void finishPendingRelease(LivingEntity entity) {
        CompoundTag persistent = entity.getPersistentData();
        if (!persistent.contains(RELEASE_RECOVERY_TAG, Tag.TAG_COMPOUND)) return;
        applyStoredState(entity, persistent.getCompound(RELEASE_RECOVERY_TAG), false);
        persistent.remove(RELEASE_RECOVERY_TAG);
    }

    private static CompoundTag createControl(LivingEntity entity) {
        CompoundTag persistent = entity.getPersistentData();
        CompoundTag control = new CompoundTag();
        control.putBoolean(ORIGINAL_INVISIBLE, entity.isInvisible());
        control.putBoolean(ORIGINAL_INVULNERABLE, entity.isInvulnerable());
        control.putBoolean(ORIGINAL_SILENT, entity.isSilent());
        control.putBoolean(ORIGINAL_NO_GRAVITY, entity.isNoGravity());
        control.putBoolean(ORIGINAL_NO_PHYSICS, entity.noPhysics);
        control.putBoolean(ORIGINAL_NO_AI, entity instanceof Mob mob && mob.isNoAi());
        persistent.put(CONTROL_TAG, control);
        return control;
    }

    private static void applyContained(LivingEntity entity) {
        entity.setInvisible(true);
        entity.setInvulnerable(true);
        entity.setSilent(true);
        entity.setNoGravity(true);
        entity.noPhysics = true;
        if (entity instanceof Mob mob) mob.setNoAi(true);
        entity.setDeltaMovement(Vec3.ZERO);
        if (entity.isOnFire()) {
            entity.clearFire();
            entity.hurtMarked = true;
        }
    }

    private static String ownerSummary(CompoundTag control) {
        return control.hasUUID(OWNER)
                ? control.getUUID(OWNER).toString().substring(0, 8)
                : "legacy";
    }

    private static void renew(CompoundTag control, long gameTime, String mode) {
        control.putString(MODE, mode);
        control.putLong(LEASE_UNTIL, KirbyMobControlLeasePolicy.leaseUntil(gameTime));
    }

}
