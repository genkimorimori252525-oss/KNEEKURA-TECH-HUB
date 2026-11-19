package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Port of X1 {@code EntityHakurouReflecter} (白楼剣, sneak release): a wall that flies along the user's look at
 * 0.18 a tick for 20 ticks. Every non-laser shot within 1 of it is removed (the user's own too); another's shot
 * is answered with an aqua scale shot from the user along the user's look. A block in its (mirrored) path ends
 * it. X1's knock-back branch for non-shots is unreachable and stays so.
 */
public class HakurouReflecterEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_MODE =
            SynchedEntityData.defineId(HakurouReflecterEntity.class, EntityDataSerializers.INT);
    public Player user;
    public int count;
    public double xVec, yVec, zVec;

    public HakurouReflecterEntity(EntityType<? extends HakurouReflecterEntity> type, Level level) {
        super(type, level);
        this.count = 4;
    }

    public HakurouReflecterEntity(Level level, Player player) {
        this(PortRegistries.HAKUROU_REFLECTER.get(), level);
        this.user = player;
        Vec3d v = X1Danmaku.getVecFromAngle(player.getYRot(), player.getXRot(), 1.0D);
        this.setPos(player.getX() + v.x(), player.getY() + v.y() + player.getEyeHeight(), player.getZ() + v.z());
        this.setYRot(-player.getYRot());
        this.setXRot(player.getXRot());
        Vec3d v2 = X1Danmaku.getVecFromAngle(getYRot(), getXRot(), 0.18D);
        this.xVec = v2.x();
        this.yVec = v2.y();
        this.zVec = v2.z();
        this.count = 0;
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_MODE, 0);
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean isPickable() {
        return true;
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        return true;
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide) {
            if (user == null || !user.isAlive()) this.discard();
            if (this.tickCount >= 20) this.discard();
        }
        Vec3 motion = new Vec3(xVec, yVec, zVec);
        this.setDeltaMovement(motion);
        double x = getX() - motion.x, y = getY() + motion.y, z = getZ() + motion.z;
        // X1 traces from the new position along +motion (x mirrored against the movement).
        Vec3 from = new Vec3(x, y, z), to = new Vec3(x + motion.x, y + motion.y, z + motion.z);
        HitResult block = this.level().clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        if (block.getType() != HitResult.Type.MISS && !this.level().isClientSide) this.discard();
        double width = 0.5D, length = 0.5D;
        double yLength = motion.y - Math.sin(getXRot() / 180F * 3.141593F) * length;
        for (Entity e : this.level().getEntities(this, this.getBoundingBox().expandTowards(0.0D, yLength, 0.0D).inflate(width * 2D))) {
            if (!(e instanceof THShotEntity shot) || e instanceof THLaserEntity) continue;
            if (user != null && user != shot.getOwner()) {
                X1ShotData reflect = X1ShotData.shot(X1ShotTables.FORM_SCALE, X1ShotTables.AQUA,
                        X1ShotTables.SIZE[X1ShotTables.FORM_SCALE], 3.0F, 0, 40, 0);
                if (!this.level().isClientSide) {
                    X1Danmaku.createShot(user, user, new Vec3d(shot.getX(), shot.getY(), shot.getZ()),
                            X1Danmaku.angle(-getYRot(), getXRot()), 0F, 0.3D, 0.7D, 0.05D, Vec3d.ZERO, reflect);
                    shot.discard();
                }
                this.level().playSound(null, shot.getX(), shot.getY(), shot.getZ(), SoundEvents.ARROW_SHOOT,
                        SoundSource.NEUTRAL, 0.5F, 0.4F / (this.random.nextFloat() * 4F + 0.8F));
            }
            if (!this.level().isClientSide) shot.discard(); // onImpact: any shot it touches is removed
        }
        this.setPos(x, y, z);
        count++;
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}
}
