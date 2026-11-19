package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1ShotSpecials;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1ShotSpawner;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
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
 * Special shots (P9): HOMING01, DIFFUSION01, FALL01, BOUND01-04, FIRE, EXPLOSION01, WIND01.
 * Not yet ported: the ISpecialShot registry used by spell cards, the shot-material bonus drop,
 * danmaku-mob damage multipliers and the player-power damage bonus.
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
    /** X1 damageRate: reset to 1 on each impact; WIND01 doubles it for airborne targets. */
    private float damageRate = 1.0F;

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
        @Override public void specialMotion(X1ShotMotion m) { THShotEntity.this.specialMotion(m); }
    };

    // ---- X1 specialMotion ----

    private void specialMotion(X1ShotMotion m) {
        switch (m.special) {
            case X1ShotTables.HOMING01 -> homing(m, 4.0F);
            case X1ShotTables.DIFFUSION01 -> diffusion(m);
            case X1ShotTables.FALL01 -> m.motion = new Vec3d(m.motion.x(), m.motion.y() - 0.02D, m.motion.z());
            default -> {}
        }
    }

    /** EntityTHShot.homing: turn the stored angle (not the motion), then accelerate again. */
    private void homing(X1ShotMotion m, float homingLevel) {
        Entity owner = this.getOwner();
        Vec3 pos = this.position();
        Vec3d shotVec = X1ShotSpecials.normalize(m.angle);
        LivingEntity best = null;
        double bestScore = X1ShotSpecials.homingInitialScore();
        AABB search = this.getBoundingBox().expandTowards(toMc(m.motion)).inflate(24.0D);
        for (Entity e : this.level().getEntities(this, search)) {
            if (!(e instanceof LivingEntity living) || e instanceof Animal || e instanceof Villager || e == owner) continue;
            if (!living.isAlive()) continue;
            Vec3 eye = new Vec3(living.getX(), living.getEyeY(), living.getZ());
            if (clip(pos, eye).getType() != HitResult.Type.MISS) continue; // blocked line of sight
            Vec3d targetVec = X1ShotSpecials.normalize(pure(eye.subtract(pos)));
            float angleSpan = Math.abs(X1ShotSpecials.vectorAngle(shotVec, targetVec));
            double score = X1ShotSpecials.homingScore(pos.distanceTo(eye), angleSpan);
            if (bestScore > score) {
                best = living;
                bestScore = score;
            }
        }
        if (best == null) return;
        Vec3 eye = new Vec3(best.getX(), best.getEyeY(), best.getZ());
        m.angle = X1ShotSpecials.homingTurn(m.angle, pure(eye.subtract(pos)), homingLevel);
        m.accelerate();
    }

    /** EntityTHShot.diffusion: at the end time, burst into three spheres of blue amulets. */
    private void diffusion(X1ShotMotion m) {
        if (this.tickCount != this.getShotEndTime()) return;
        if (this.getOwner() instanceof LivingEntity user && this.level() instanceof ServerLevel server) {
            Vec3d gravity = X1ShotSpecials.diffusionGravity(user.getYRot(), user.getXRot());
            X1ShotPatterns patterns = X1ShotSpawner.patterns(server, user);
            X1ShotData shot = X1ShotSpecials.diffusionShot();
            Vec3d pos = new Vec3d(this.getX(), this.getY(), this.getZ());
            for (double[] burst : X1ShotSpecials.DIFFUSION_BURSTS) {
                patterns.createSphereShot(pos, m.angle, 0F, new Vec3d(0, 1, 0), 0F, 9999, burst[0],
                        X1ShotSpecials.DIFFUSION_LIMIT_SPEED, burst[1], gravity, shot, (int) burst[2], 0.0D,
                        this.random.nextFloat() * 360F);
            }
        }
        this.discard();
    }

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
            isHit = onImpactEntity(hitEntity, m);
        } else if (block.getType() != HitResult.Type.MISS) {
            // onImpact: a surviving special (bound) returns false, so the probes below still run.
            if (!blockHitSpecialProcess(block, m)) {
                this.discard();
                isHit = true;
            }
        }
        if (!isHit) {
            // X1 probes three diameter lines through the centre; each hit goes through
            // blockHitSpecialProcess again (bounces can repeat within one tick).
            probe(pos.add(0, -half, 0), pos.add(0, half, 0), m);
            probe(pos.add(-half, 0, 0), pos.add(half, 0, 0), m);
            probe(pos.add(0, 0, -half), pos.add(0, 0, half), m);
        }
    }

    private void probe(Vec3 start, Vec3 end, X1ShotMotion m) {
        BlockHitResult hit = clip(start, end);
        if (hit.getType() != HitResult.Type.MISS && !blockHitSpecialProcess(hit, m)) this.discard();
    }

    /** blockHitSpecialProcess: true keeps the shot alive. */
    private boolean blockHitSpecialProcess(BlockHitResult hit, X1ShotMotion m) {
        switch (m.special) {
            case X1ShotTables.BOUND01 -> { bound(m, 0.9D, 2); m.special = 0; return true; }
            case X1ShotTables.BOUND02 -> { bound(m, 0.9D, 3); m.special = X1ShotTables.BOUND01; return true; }
            case X1ShotTables.BOUND03 -> { bound(m, 0.9D, 4); m.special = X1ShotTables.BOUND02; return true; }
            case X1ShotTables.BOUND04 -> { bound(m, 0.9D, 9999); return true; }
            case X1ShotTables.EXPLOSION01 -> {
                Vec3 at = hit.getLocation();
                explode(at.x, at.y, at.z, 5.0F);
                return false;
            }
            default -> { return false; }
        }
    }

    /** EntityTHShot.bound: reflect the motion until the next step is clear, at most returnCount times. */
    private void bound(X1ShotMotion m, double returnRate, int returnCount) {
        Vec3 s1 = this.position();
        Vec3 s2 = s1.add(toMc(m.motion));
        BlockHitResult hit = boundClip(s1, s2);
        while (hit.getType() != HitResult.Type.MISS) {
            m.motion = X1ShotSpecials.reflect(m.motion, hit.getDirection().ordinal(), returnRate);
            Vec3 at = hit.getLocation();
            s1 = s1.add(at.subtract(s1).scale(0.99D));
            s2 = s1.add(toMc(m.motion));
            hit = boundClip(s1, s2);
            returnCount--;
            if (returnCount <= 0) {
                this.discard();
                return;
            }
        }
    }

    /** 1.7.10 rayTraceBlocks(a, b, true): outline shapes, source liquids stop the ray. */
    private BlockHitResult boundClip(Vec3 start, Vec3 end) {
        return this.level().clip(new ClipContext(start, end, ClipContext.Block.OUTLINE, ClipContext.Fluid.SOURCE_ONLY, this));
    }

    private void explode(double x, double y, double z, float power) {
        // THKaguyaConfig.MasterSparkDestroysBlocks defaults to true.
        this.level().explode(this.getOwner(), x, y, z, power, Level.ExplosionInteraction.TNT);
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
    private boolean onImpactEntity(Entity hitEntity, X1ShotMotion m) {
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
        damageRate = 1.0F;
        boolean keep = entityHitSpecialProcess(hitEntity, m);
        if (hitEntity != owner) {
            DamageSource source = this.damageSources().indirectMagic(this, owner == null ? this : owner);
            // The danmaku-mob x2 multiplier (youkai / fairy / phantom) arrives with the X1 mobs.
            hitEntity.hurt(source, getShotDamageWithDifficulty() * damageRate);
        }
        if (!keep) {
            this.discard();
            return true;
        }
        return false;
    }

    /** entityHitSpecialProcess: false = the shot disappears as usual. */
    private boolean entityHitSpecialProcess(Entity hit, X1ShotMotion m) {
        switch (m.special) {
            case X1ShotTables.FIRE -> hit.setSecondsOnFire((int) shotDamage);
            case X1ShotTables.EXPLOSION01 -> explode(hit.getX(), hit.getY(), hit.getZ(), 3.0F);
            case X1ShotTables.WIND01 -> {
                Vec3 v = hit.getDeltaMovement();
                hit.setDeltaMovement(v.x + m.motion.x() * 1.7D, v.y + m.motion.y() * 1.7D + 2.0D,
                        v.z + m.motion.z() * 1.7D);
                hit.hurtMarked = true;
                if (!hit.onGround()) damageRate *= 2.0F;
            }
            default -> {}
        }
        return false;
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

    private static Vec3d pure(Vec3 v) {
        return new Vec3d(v.x, v.y, v.z);
    }

    private static Vec3 toMc(Vec3d v) {
        return new Vec3(v.x(), v.y(), v.z());
    }
}
