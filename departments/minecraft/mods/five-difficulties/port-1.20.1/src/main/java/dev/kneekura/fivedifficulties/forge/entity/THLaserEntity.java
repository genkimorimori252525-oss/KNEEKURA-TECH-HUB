package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.core.x1.X1WideShotGeometry;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1ShotSpawner;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Port of X1 {@code EntityTHLaser} (laser "A"): an EntityTHShot whose yaw / pitch follow the
 * stored angle, whose length grows by {@code speed * 2} per tick up to its maximum (also during the
 * delay), and which hurts every living entity along its segment each tick.
 */
public class THLaserEntity extends THShotEntity {
    // X1 DataWatcher 21 / 22: lengths stored as (int) (length * 10000).
    private static final EntityDataAccessor<Integer> DATA_LENGTH =
            SynchedEntityData.defineId(THLaserEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_MAX_LENGTH =
            SynchedEntityData.defineId(THLaserEntity.class, EntityDataSerializers.INT);

    /** X1 {@code source}: lasers never hit it. */
    protected Entity source;

    public THLaserEntity(EntityType<? extends THLaserEntity> type, Level level) {
        super(type, level);
        this.noCulling = true; // X1 ignoreFrustumCheck
    }

    public THLaserEntity(Level level, LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float slope,
                         Vec3d rotate, float rotationSpeed, int rotationEnd, double firstSpeed, double limitSpeed,
                         double acceleration, Vec3d gravity, X1LaserData laser) {
        this(PortRegistries.TH_LASER.get(), level);
        initLaser(user, source, pos, angle, slope, rotate, rotationSpeed, rotationEnd, firstSpeed, limitSpeed,
                acceleration, gravity, laser.shotId(), laser.width, laser.length, laser.damage, laser.delay, laser.end,
                laser.special);
    }

    protected final void initLaser(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float slope,
                                   Vec3d rotate, float rotationSpeed, int rotationEnd, double firstSpeed,
                                   double limitSpeed, double acceleration, Vec3d gravity, int shotId, float width,
                                   float length, float damage, int delay, int end, int special) {
        initShot(user, pos, angle, slope, rotate, rotationSpeed, rotationEnd, firstSpeed, limitSpeed, acceleration,
                gravity, shotId, width, damage, delay, end, special, true);
        this.source = source;
        setLaserLength(0.0D);
        setMaxLaserLength(length);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_LENGTH, 0);
        this.entityData.define(DATA_MAX_LENGTH, 0);
    }

    public double getLaserLength() { return (double) this.entityData.get(DATA_LENGTH) / 10000.0D; }
    public void setLaserLength(double length) { this.entityData.set(DATA_LENGTH, (int) (length * 10000.0D)); }
    public double getMaxLaserLength() { return (double) this.entityData.get(DATA_MAX_LENGTH) / 10000.0D; }
    public void setMaxLaserLength(double length) { this.entityData.set(DATA_MAX_LENGTH, (int) (length * 10000.0D)); }

    /** EntityTHLaser.onUpdate after super: length += speed * 2, capped at the maximum. */
    @Override
    protected void afterX1Tick(X1ShotMotion m) {
        double laserLength = getLaserLength() + m.speed() * 2.0D;
        setLaserLength(laserLength > getMaxLaserLength() ? getMaxLaserLength() : laserLength);
    }

    // ---- EntityTHLaser.hitCheck ----

    @Override
    protected void hitCheck(X1ShotMotion m) {
        double width = getShotSize();
        double length = getLaserLength() - getShotSize();
        Vec3 pos = this.position();
        Vec3 angle = toMc(m.angle);
        Vec3 start = pos.add(angle.scale(width));
        Vec3 end = pos.add(toMc(m.motion)).add(angle.scale(length));
        BlockHitResult block = clip(start, end);
        if (block.getType() != HitResult.Type.MISS) {
            end = block.getLocation();
            onImpactBlock(block, m, true);
        }
        Vec3 reach = toMc(m.motion).add(x1Direction(m).scale(getLaserLength()));
        hitEntitiesAlong(m, start, end, this.getBoundingBox().expandTowards(reach).inflate(width), width);
    }

    /** (sin yaw cos pitch, sin pitch, cos yaw cos pitch) in X1's yaw convention, float pi like X1. */
    protected static Vec3 x1Direction(X1ShotMotion m) {
        double yaw = m.yaw / 180F * 3.141593F;
        double pitch = m.pitch / 180F * 3.141593F;
        return new Vec3(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
    }

    protected final void hitEntitiesAlong(X1ShotMotion m, Vec3 start, Vec3 end, AABB search, double width) {
        Entity user = this.getOwner();
        for (Entity e : this.level().getEntities(this, search)) {
            if (!e.isPickable() || e == user || e == source) continue;
            if (e instanceof SakuyaTimeControllerEntity || e instanceof Animal || e instanceof Villager) continue;
            if (!(e instanceof LivingEntity)) continue;
            if (e.getBoundingBox().inflate(width).clip(start, end).isEmpty()) continue;
            if (e instanceof Player player && (player.getAbilities().invulnerable || source instanceof Player)) continue;
            onImpactLaserEntity(e, m);
            if (this.isRemoved()) return;
        }
    }

    /** EntityTHLaser.onImpact for an entity: special process, damage, then the shotDamage check. */
    protected void onImpactLaserEntity(Entity hit, X1ShotMotion m) {
        entityHitSpecialProcess(hit, m);
        Entity user = this.getOwner();
        DamageSource damage = this.damageSources().indirectMagic(this, user == null ? this : user);
        hit.hurt(damage, getShotDamageWithDifficulty());
        if (shotDamage <= 0) this.discard();
    }

    /**
     * EntityTHLaser.onImpact for a block: the laser is cut at the hit point; within 0.3 blocks it
     * disappears. {@code updateMax} is false for the set laser (only its current length is cut).
     */
    protected void onImpactBlock(BlockHitResult hit, X1ShotMotion m, boolean updateMax) {
        blockHitSpecialProcess(hit, m);
        double hitDistance = this.position().distanceTo(hit.getLocation());
        if (hitDistance > 0.3D) {
            setLaserLength(hitDistance);
            if (updateMax) setMaxLaserLength(hitDistance);
        } else if (updateMax) {
            this.discard();
        }
        if (shotDamage <= 0) this.discard();
    }

    // ---- EntityTHLaser.specialMotion ----

    @Override
    protected void specialMotion(X1ShotMotion m) {
        super.specialMotion(m);
        if (m.special != X1ShotTables.GUNGNIR) return;
        if (this.tickCount <= 10) {
            Vec3d move = X1WideShotGeometry.rotateAroundAxisRaw(m.rotate, m.angle, 18F);
            setLaserLength(getLaserLength() < getMaxLaserLength() ? getLaserLength() + 1.0D : getMaxLaserLength());
            m.angle = move;
            m.updateAngle();
        }
        if (this.tickCount == 10 && this.getOwner() instanceof LivingEntity user) {
            Vec3 v = user.getDeltaMovement();
            user.setDeltaMovement(v.x - m.angle.x(), v.y, v.z - m.angle.z());
            user.hurtMarked = true;
            m.limitSpeed = 2.0D;
            m.acceleration = 0.6D;
        }
        if (this.tickCount > 10 && this.getOwner() instanceof LivingEntity user
                && this.level() instanceof ServerLevel server) {
            X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_CRYSTAL, X1ShotTables.RED, 0.45F, 6.0F, 0, 40);
            X1ShotSpawner.patterns(server, user).createRingShot(new Vec3d(getX(), getY(), getZ()), m.angle, 0F, 9999,
                    1.4D, 0.1D, -0.1D, Vec3d.ZERO, shot, 4, 0.3D, 240F, this.tickCount * 10F);
        }
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        return false; // EntityTHLaser.attackEntityFrom
    }
}
