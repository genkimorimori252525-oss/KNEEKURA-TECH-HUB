package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.boss.EnderDragonPart;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;

/**
 * Phase-A port of X1 {@code EntityTHShot}: one entity per legacy shot, server-authoritative.
 *
 * Movement is {@link X1ShotMotion}; this class supplies the world: owner checks, end time,
 * X1 hitCheck / hitEntityCheck / onImpact, difficulty damage and shot-vs-shot cancellation.
 * Like X1 (whose client copy never received the shot parameters), the client does not
 * simulate: it follows server position updates.
 *
 * Not yet ported (P9+): special shots other than FALL01 (homing, diffusion, bound, fire,
 * explosion, wind), the shot-material bonus drop, danmaku-mob damage multipliers and the
 * player-power damage bonus.
 */
public final class THShotEntity extends Projectile {
    // X1 DataWatcher slots 16..20.
    private static final EntityDataAccessor<Float> DATA_ANGLE_Z =
            SynchedEntityData.defineId(THShotEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Integer> DATA_ANIMATION =
            SynchedEntityData.defineId(THShotEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_END_TIME =
            SynchedEntityData.defineId(THShotEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_SHOT_ID =
            SynchedEntityData.defineId(THShotEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> DATA_SIZE =
            SynchedEntityData.defineId(THShotEntity.class, EntityDataSerializers.FLOAT);

    private X1ShotMotion motion;
    public float shotDamage;

    public THShotEntity(EntityType<? extends THShotEntity> type, Level level) {
        super(type, level);
    }

    public THShotEntity(Level level, LivingEntity user, Vec3d pos, Vec3d angle, float slope, Vec3d rotate,
                        float rotationSpeed, int rotationEnd, double firstSpeed, double limitSpeed,
                        double acceleration, Vec3d gravity, X1ShotData shot) {
        this(PortRegistries.TH_SHOT.get(), level);
        this.setOwner(user);
        this.setPos(pos.x(), pos.y(), pos.z());
        this.setAngleZ(slope);
        this.setShotId(shot.shotId());
        this.setShotSize(shot.size);
        this.shotDamage = shot.damage;
        this.setShotEndTime(shot.end);
        this.setAnimationCount(X1ShotMotion.initialAnimationCount(shot.delay));
        this.motion = new X1ShotMotion(pos, angle, rotate, rotationSpeed, rotationEnd, firstSpeed, limitSpeed,
                acceleration, gravity, shot.special);
        this.setDeltaMovement(toMc(this.motion.motion));
        this.syncRotation();
        this.xRotO = this.getXRot();
        this.yRotO = this.getYRot();
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_ANGLE_Z, 0.0F);
        this.entityData.define(DATA_ANIMATION, 0);
        this.entityData.define(DATA_END_TIME, 0);
        this.entityData.define(DATA_SHOT_ID, 0);
        this.entityData.define(DATA_SIZE, 0.1F);
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> accessor) {
        super.onSyncedDataUpdated(accessor);
        if (DATA_SIZE.equals(accessor)) this.refreshDimensions();
    }

    @Override
    public EntityDimensions getDimensions(Pose pose) {
        float size = Math.max(this.getShotSize(), 0.01F);
        return EntityDimensions.scalable(size, size);
    }

    // ---- synced accessors (EntityTHShot getters/setters) ----

    public int getShotId() { return this.entityData.get(DATA_SHOT_ID); }
    public void setShotId(int id) { this.entityData.set(DATA_SHOT_ID, id); }
    public int getShotForm() { return X1ShotTables.formOf(getShotId()); }
    public int getShotColor() { return X1ShotTables.colorOf(getShotId()); }
    public float getShotSize() { return this.entityData.get(DATA_SIZE); }
    public void setShotSize(float size) { this.entityData.set(DATA_SIZE, (float) (int) (size * 100F) / 100F); }
    public int getAnimationCount() { return this.entityData.get(DATA_ANIMATION); }
    public void setAnimationCount(int count) { this.entityData.set(DATA_ANIMATION, count); }
    public int getShotEndTime() { return this.entityData.get(DATA_END_TIME); }
    public void setShotEndTime(int time) { this.entityData.set(DATA_END_TIME, time); }
    public float getAngleZ() { return this.entityData.get(DATA_ANGLE_Z); }
    public void setAngleZ(float angleZ) { this.entityData.set(DATA_ANGLE_Z, (float) (int) (angleZ * 10000F) / 10000F); }

    /** Pure motion state, server only (null on the client). */
    public X1ShotMotion motion() { return motion; }

    // ---- tick ----

    @Override
    public void tick() {
        // X1 onUpdate never calls super.onUpdate(); tickCount is incremented by the level first.
        if (this.level().isClientSide) {
            return; // X1 clients follow server position updates.
        }
        if (motion == null) {
            this.discard(); // loaded from disk: X1 saves nothing and its user is gone.
            return;
        }
        Entity owner = this.getOwner();
        if (!(owner instanceof LivingEntity user)) {
            this.discard();
            return;
        }
        if (shotDamage <= 0.0F) {
            this.discard();
            return;
        }
        if (!user.isAlive() && !(user instanceof Player)) {
            this.discard(); // X1 shotFinishBonus; the shot-material drop is not ported yet.
            return;
        }
        if (X1ShotMotion.isPastEnd(getAnimationCount(), getShotEndTime())) {
            this.discard();
        }
        this.clearFire();

        motion.position = new Vec3d(this.getX(), this.getY(), this.getZ());
        X1ShotMotion.Step step = motion.tick(this.tickCount, hooks);
        if (step == X1ShotMotion.Step.FROZEN || this.isRemoved()) return;

        this.setPos(motion.position.x(), motion.position.y(), motion.position.z());
        this.setDeltaMovement(toMc(motion.motion));
        this.syncRotation();
    }

    private final X1ShotMotion.Hooks hooks = new X1ShotMotion.Hooks() {
        @Override public boolean authoritative() { return true; }
        @Override public int animationCount() { return getAnimationCount(); }
        @Override public void setAnimationCount(int value) { THShotEntity.this.setAnimationCount(value); }
        @Override public void hitCheck(X1ShotMotion m) { THShotEntity.this.hitCheck(m); }
    };

    private void syncRotation() {
        // Store X1's rotationYaw / rotationPitch literally for direction-dependent renderers.
        this.setYRot(motion.yaw);
        this.setXRot(motion.pitch);
    }

    // ---- X1 hitCheck ----

    private void hitCheck(X1ShotMotion m) {
        double half = this.getShotSize() / 2.0D;
        Vec3 pos = this.position();
        Vec3 move = toMc(m.motion);
        Vec3 sizeOffset = toMc(m.angle).scale(half);
        Vec3 start = pos.subtract(sizeOffset);
        Vec3 end = pos.add(move).add(sizeOffset);

        BlockHitResult block = clip(start, end);
        Vec3 entityEnd = block.getType() == HitResult.Type.MISS ? end : block.getLocation();
        Entity hitEntity = findEntityHit(start, entityEnd, toMc(m.angle), (float) half);

        boolean isHit = false;
        if (hitEntity != null) {
            isHit = onImpactEntity(hitEntity);
        } else if (block.getType() != HitResult.Type.MISS) {
            this.discard(); // default blockHitSpecialProcess returns false
            isHit = true;
        }
        if (!isHit) {
            // X1 probes three diameter lines through the centre for block overlap.
            if (clip(pos.add(0, -half, 0), pos.add(0, half, 0)).getType() != HitResult.Type.MISS
                    || clip(pos.add(-half, 0, 0), pos.add(half, 0, 0)).getType() != HitResult.Type.MISS
                    || clip(pos.add(0, 0, -half), pos.add(0, 0, half)).getType() != HitResult.Type.MISS) {
                this.discard();
            }
        }
    }

    private BlockHitResult clip(Vec3 start, Vec3 end) {
        return this.level().clip(new ClipContext(start, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
    }

    /** hitEntityCheck: search box grows along the unit angle (not the motion), targets inflated by half size. */
    private Entity findEntityHit(Vec3 start, Vec3 end, Vec3 angle, float hitSize) {
        AABB search = this.getBoundingBox().expandTowards(angle).inflate(hitSize);
        Entity best = null;
        double bestDistance = 0.0D;
        for (Entity candidate : this.level().getEntities(this, search, this::isCandidate)) {
            Optional<Vec3> intercept = candidate.getBoundingBox().inflate(hitSize).clip(start, end);
            if (intercept.isEmpty()) continue;
            double distance = start.distanceTo(intercept.get());
            if (distance < bestDistance || bestDistance == 0.0D) {
                best = candidate;
                bestDistance = distance;
            }
        }
        return best;
    }

    private boolean isCandidate(Entity e) {
        Entity owner = this.getOwner();
        if (!e.isPickable() || e == owner) return false;
        if (e instanceof Animal || e instanceof Villager) return false;
        if (e instanceof THShotEntity other) return other.getOwner() != owner;
        return e instanceof LivingEntity || e instanceof EnderDragonPart;
    }

    /** onImpact for an entity. Returns true when this shot was consumed. */
    private boolean onImpactEntity(Entity hitEntity) {
        if (this.getShotForm() == X1ShotTables.FORM_FAMILIAR) return false;
        Entity owner = this.getOwner();
        if (hitEntity instanceof THShotEntity other) {
            float damageA = this.shotDamage;
            float damageB = other.shotDamage;
            this.shotDamage -= damageB * (owner instanceof Player ? 0.1F : 0.3F);
            other.shotDamage -= damageA * (other.getOwner() instanceof Player ? 0.1F : 0.3F);
            if (other.shotDamage < 0.0F) other.shotDamage = 0.0F;
            if (this.shotDamage < 0.0F) {
                this.shotDamage = 0.0F;
                return true;
            }
            return false;
        }
        // entityHitSpecialProcess: no special shot keeps the bullet alive in P8.
        if (hitEntity != owner) {
            DamageSource source = this.damageSources().indirectMagic(this, owner == null ? this : owner);
            hitEntity.hurt(source, getShotDamageWithDifficulty());
        }
        this.discard();
        return true;
    }

    /** getShotDamageWithDifficulty: players' shots ignore difficulty. */
    public float getShotDamageWithDifficulty() {
        if (this.getOwner() instanceof Player) return shotDamage;
        return switch (this.level().getDifficulty()) {
            case PEACEFUL, NORMAL -> shotDamage;
            case EASY -> shotDamage * 0.7F;
            case HARD -> shotDamage * 1.5F;
        };
    }

    // ---- X1 entity flags ----

    @Override
    public boolean isPickable() {
        return getAnimationCount() >= 1; // canBeCollidedWith: not during the delay
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        // X1 attackEntityFrom: another player's hit removes the shot (bonus drop not ported yet).
        Entity attacker = source.getEntity();
        if (attacker == null) return false;
        if (attacker instanceof Player && attacker != this.getOwner() && !this.level().isClientSide) {
            this.discard();
        }
        return true;
    }

    @Override
    public boolean shouldBeSaved() {
        return false; // X1 writeEntityToNBT is empty
    }

    @Override
    public boolean shouldRenderAtSqrDistance(double distance) {
        double edge = this.getBoundingBox().getSize() * 4.0D * 64.0D;
        return distance < edge * edge;
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}

    private static Vec3 toMc(Vec3d v) {
        return new Vec3(v.x(), v.y(), v.z());
    }
}
