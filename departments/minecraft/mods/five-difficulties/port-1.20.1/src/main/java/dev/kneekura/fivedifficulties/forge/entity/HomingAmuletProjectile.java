package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.HomingAmuletContract;
import dev.kneekura.fivedifficulties.core.x1.X1HomingMath;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.ForgeEventFactory;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;

/**
 * First live X1 preservation projectile.
 *
 * P2 scope is deliberately the red Homing Amulet only.
 */
public final class HomingAmuletProjectile extends Projectile {
    private static final EntityDataAccessor<Boolean> DATA_FOCUSED =
            SynchedEntityData.defineId(HomingAmuletProjectile.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> DATA_LEGACY_ANIMATION =
            SynchedEntityData.defineId(HomingAmuletProjectile.class, EntityDataSerializers.INT);

    public HomingAmuletProjectile(EntityType<? extends HomingAmuletProjectile> type, Level level) {
        super(type, level);
    }

    public HomingAmuletProjectile(
            Level level,
            LivingEntity owner,
            Vec3 position,
            Vec3 direction,
            boolean focused
    ) {
        this(PortRegistries.HOMING_AMULET_PROJECTILE.get(), level);
        this.setOwner(owner);
        this.setFocused(focused);
        this.setPos(position);
        this.setDeltaMovement(direction.normalize().scale(HomingAmuletContract.resolve(focused).speed()));
        this.updateRotation();
        this.xRotO = this.getXRot();
        this.yRotO = this.getYRot();
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_FOCUSED, false);
        this.entityData.define(DATA_LEGACY_ANIMATION, 0);
    }

    public boolean isFocused() {
        return this.entityData.get(DATA_FOCUSED);
    }

    public void setFocused(boolean focused) {
        if (this.entityData.get(DATA_FOCUSED) != focused) {
            this.entityData.set(DATA_FOCUSED, focused);
            this.refreshDimensions();
        }
    }

    public int getLegacyAnimationCount() {
        return this.entityData.get(DATA_LEGACY_ANIMATION);
    }

    private void setLegacyAnimationCount(int value) {
        this.entityData.set(DATA_LEGACY_ANIMATION, value);
    }

    public float getX1Damage() {
        return (float) HomingAmuletContract.resolve(this.isFocused()).damage();
    }

    @Override
    public EntityDimensions getDimensions(Pose pose) {
        float size = (float) HomingAmuletContract.resolve(this.isFocused()).shotSize();
        return EntityDimensions.scalable(size, size);
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> accessor) {
        super.onSyncedDataUpdated(accessor);
        if (DATA_FOCUSED.equals(accessor)) {
            this.refreshDimensions();
        }
    }

    @Override
    public void tick() {
        super.tick();

        if (!this.level().isClientSide) {
            Entity owner = this.getOwner();
            if (!(owner instanceof LivingEntity livingOwner) || !livingOwner.isAlive()) {
                this.discard();
                return;
            }

            if (this.getLegacyAnimationCount() > HomingAmuletContract.LIFETIME_TICKS) {
                this.discard();
                return;
            }

            this.applyX1Homing();

            HitResult hit = this.findX1Hit();
            if (hit != null && hit.getType() != HitResult.Type.MISS && !ForgeEventFactory.onProjectileImpact(this, hit)) {
                this.onHit(hit);
            }
            if (this.isRemoved()) {
                return;
            }
        }

        Vec3 movement = this.getDeltaMovement();
        this.setPos(this.getX() + movement.x, this.getY() + movement.y, this.getZ() + movement.z);
        this.updateRotation();

        if (!this.level().isClientSide) {
            this.setLegacyAnimationCount(this.getLegacyAnimationCount() + 1);
        }
    }

    /**
     * Port of EntityTHShot.hitCheck/hitEntityCheck for the live P2 red amulet.
     *
     * X1 extends the center sweep by half the logical shot size along the shot
     * direction and expands candidate target AABBs by the same half-size.
     * If that primary sweep misses, X1 also probes three diameter lines through
     * the current shot center to catch block overlap.
     */
    private HitResult findX1Hit() {
        Vec3 movement = this.getDeltaMovement();
        if (movement.lengthSqr() <= 1.0e-12) {
            return this.findX1CrossSectionBlockHit();
        }

        double half = HomingAmuletContract.resolve(this.isFocused()).shotSize() * 0.5D;
        Vec3 direction = movement.normalize();
        Vec3 start = this.position().subtract(direction.scale(half));
        Vec3 end = this.position().add(movement).add(direction.scale(half));

        BlockHitResult blockHit = this.level().clip(new ClipContext(
                start,
                end,
                ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE,
                this
        ));
        Vec3 entityEnd = blockHit.getType() == HitResult.Type.MISS ? end : blockHit.getLocation();

        EntityHitResult entityHit = this.findX1EntityHit(start, entityEnd, direction, half);
        if (entityHit != null) {
            return entityHit;
        }
        if (blockHit.getType() != HitResult.Type.MISS) {
            return blockHit;
        }
        return this.findX1CrossSectionBlockHit();
    }

    private EntityHitResult findX1EntityHit(Vec3 start, Vec3 end, Vec3 direction, double half) {
        AABB search = this.getBoundingBox().expandTowards(direction).inflate(half);
        Entity best = null;
        Vec3 bestPoint = null;
        double bestDistance = 0.0D;

        for (Entity candidate : this.level().getEntities(this, search, this::isX1EntityCollisionCandidate)) {
            AABB expanded = candidate.getBoundingBox().inflate(half);
            Optional<Vec3> intercept = expanded.clip(start, end);
            if (intercept.isEmpty()) {
                continue;
            }

            double distance = start.distanceTo(intercept.get());
            if (best == null || distance < bestDistance) {
                best = candidate;
                bestPoint = intercept.get();
                bestDistance = distance;
            }
        }

        return best == null ? null : new EntityHitResult(best, bestPoint);
    }

    private boolean isX1EntityCollisionCandidate(Entity entity) {
        if (!entity.isPickable() || entity == this.getOwner()) {
            return false;
        }
        if (entity instanceof Animal || entity instanceof Villager) {
            return false;
        }
        if (entity instanceof HomingAmuletProjectile) {
            // X1 supports cross-owner THShot cancellation; the generalized
            // danmaku-vs-danmaku damage subtraction system is not in P2 yet.
            return false;
        }
        return entity instanceof LivingEntity
                || entity.getType() == EntityType.ENDER_DRAGON;
    }

    private BlockHitResult findX1CrossSectionBlockHit() {
        double half = HomingAmuletContract.resolve(this.isFocused()).shotSize() * 0.5D;
        Vec3 center = this.position();

        BlockHitResult vertical = clipBlock(
                center.add(0.0D, -half, 0.0D),
                center.add(0.0D, half, 0.0D)
        );
        if (vertical.getType() != HitResult.Type.MISS) return vertical;

        BlockHitResult x = clipBlock(
                center.add(-half, 0.0D, 0.0D),
                center.add(half, 0.0D, 0.0D)
        );
        if (x.getType() != HitResult.Type.MISS) return x;

        BlockHitResult z = clipBlock(
                center.add(0.0D, 0.0D, -half),
                center.add(0.0D, 0.0D, half)
        );
        return z.getType() == HitResult.Type.MISS ? null : z;
    }

    private BlockHitResult clipBlock(Vec3 start, Vec3 end) {
        return this.level().clip(new ClipContext(
                start,
                end,
                ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE,
                this
        ));
    }

    @Override
    protected boolean canHitEntity(Entity entity) {
        if (entity == this.getOwner() || entity instanceof Animal || entity instanceof Villager) {
            return false;
        }
        return super.canHitEntity(entity);
    }

    private void applyX1Homing() {
        Vec3 movement = this.getDeltaMovement();
        if (movement.lengthSqr() <= 1.0e-12) {
            return;
        }

        Vec3 currentPos = this.position();
        List<LivingEntity> candidates = this.level().getEntitiesOfClass(
                LivingEntity.class,
                this.getBoundingBox().expandTowards(movement).inflate(24.0D),
                living -> living.isAlive()
                        && living != this.getOwner()
                        && !(living instanceof Animal)
                        && !(living instanceof Villager)
                        && this.hasLegacyLineOfSight(currentPos, living)
        );
        if (candidates.isEmpty()) {
            return;
        }

        Vec3d currentDirection = pure(movement).normalized();

        LivingEntity target = candidates.stream()
                .min(Comparator.comparingDouble(living -> {
                    Vec3 targetPoint = living.getEyePosition();
                    Vec3d targetDirection = pure(targetPoint.subtract(currentPos)).normalized();
                    double angle = X1HomingMath.angleDegrees(currentDirection, targetDirection);
                    double distance = currentPos.distanceTo(targetPoint);
                    return X1HomingMath.targetScore(distance, angle);
                }))
                .orElse(null);

        if (target == null) {
            return;
        }

        Vec3d targetDirection = pure(target.getEyePosition().subtract(currentPos)).normalized();
        Vec3d newDirection = X1HomingMath.turnToward(
                currentDirection,
                targetDirection,
                HomingAmuletContract.NORMAL.maxHomingTurnDegreesPerTick()
        );
        double speed = movement.length();
        this.setDeltaMovement(new Vec3(
                newDirection.x() * speed,
                newDirection.y() * speed,
                newDirection.z() * speed
        ));
    }

    private boolean hasLegacyLineOfSight(Vec3 start, LivingEntity target) {
        HitResult blockHit = this.level().clip(new ClipContext(
                start,
                target.getEyePosition(),
                ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE,
                this
        ));
        return blockHit.getType() == HitResult.Type.MISS;
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        super.onHitEntity(result);
        if (this.level().isClientSide) {
            return;
        }

        Entity target = result.getEntity();
        Entity owner = this.getOwner();
        if (target == owner || target instanceof Animal || target instanceof Villager) {
            return;
        }

        target.hurt(this.damageSources().indirectMagic(this, owner == null ? this : owner), this.getX1Damage());
        this.discard();
    }

    @Override
    protected void onHitBlock(BlockHitResult result) {
        super.onHitBlock(result);
        if (!this.level().isClientSide) {
            this.discard();
        }
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putBoolean("X1Focused", this.isFocused());
        tag.putInt("X1Animation", this.getLegacyAnimationCount());
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.setFocused(tag.getBoolean("X1Focused"));
        this.setLegacyAnimationCount(Math.max(0, tag.getInt("X1Animation")));
    }

    private static Vec3d pure(Vec3 vec) {
        return new Vec3d(vec.x, vec.y, vec.z);
    }
}
