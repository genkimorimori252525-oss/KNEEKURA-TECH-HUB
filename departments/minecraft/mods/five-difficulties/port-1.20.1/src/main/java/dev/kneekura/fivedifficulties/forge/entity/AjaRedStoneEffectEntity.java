package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityAjaRedStoneEffect}: held 1.2 ahead of the user's eyes while the stone is in use, it
 * adds the light level at its block every tick. On release {@code light / 40} (max 30) becomes a red laser of
 * width damage × 0.01, length damage × 0.3 and that damage, with special 351 (undead burn). With no light
 * gathered nothing is fired and the effect stays until the next release.
 */
public class AjaRedStoneEffectEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_LIGHT =
            SynchedEntityData.defineId(AjaRedStoneEffectEntity.class, EntityDataSerializers.INT);
    public LivingEntity user;
    public int lightLevel;
    private final double length = 1.2D;

    public AjaRedStoneEffectEntity(EntityType<? extends AjaRedStoneEffectEntity> type, Level level) {
        super(type, level);
        this.lightLevel = 0;
    }

    public AjaRedStoneEffectEntity(Level level, LivingEntity living) {
        this(PortRegistries.AJA_RED_STONE_EFFECT.get(), level);
        this.user = living;
        this.moveTo(aheadX(), aheadY(), aheadZ(), living.getYRot(), living.getXRot());
    }

    private double aheadX() {
        return user.getX() - Math.sin(user.getYRot() / 180F * 3.141593F) * Math.cos(user.getXRot() / 180F * 3.141593F) * length;
    }

    private double aheadY() {
        return user.getY() - Math.sin(user.getXRot() / 180F * 3.141593F) * length + (double) user.getEyeHeight();
    }

    private double aheadZ() {
        return user.getZ() + Math.cos(user.getYRot() / 180F * 3.141593F) * Math.cos(user.getXRot() / 180F * 3.141593F) * length;
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_LIGHT, 0);
    }

    public int getLightPower() {
        return this.entityData.get(DATA_LIGHT);
    }

    public void setLightPower(int power) {
        this.entityData.set(DATA_LIGHT, power);
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public void tick() {
        if (!this.level().isClientSide && user == null) {
            this.discard();
            return;
        }
        super.tick();
        if (user != null) {
            if (user instanceof Player player) {
                if (!player.isUsingItem()) {
                    int damage = (int) ((double) lightLevel / 40.0D);
                    if (damage > 30) damage = 30;
                    if (damage > 0 && !this.level().isClientSide) {
                        X1Danmaku.createLaserA(user, this, new Vec3d(getX(), getY(), getZ()),
                                X1Danmaku.angle(user.getYRot(), user.getXRot()), 0.1D, 4.0D, 0.3D, Vec3d.ZERO,
                                X1LaserData.laser(X1ShotTables.RED, (float) damage * 0.01F, (float) damage * 0.3F, damage,
                                        0, 60, SPECIAL_AJA_REDSTONE));
                        this.discard();
                    }
                }
            } else if (!this.level().isClientSide) {
                this.discard();
            }
        }
        // getBlockLightValue at the (int)-truncated position: sky (darkened) and block light combined.
        BlockPos at = new BlockPos((int) getX(), (int) getY(), (int) getZ());
        setLightPower(this.level().getMaxLocalRawBrightness(at));
        lightLevel += getLightPower();
        if (user != null) {
            this.setPos(aheadX(), aheadY(), aheadZ());
            this.setYRot(user.getYHeadRot());
            this.setXRot(user.getXRot());
        }
        float yaw = getYRot(), pitch = getXRot();
        if (yaw > 180F) yaw -= 360F;
        if (yaw < -180F) yaw += 360F;
        if (pitch > 180F) pitch -= 360F;
        if (pitch < -180F) pitch += 360F;
        this.setRot(yaw, pitch);
    }

    public static final int SPECIAL_AJA_REDSTONE = 351;

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}
}
