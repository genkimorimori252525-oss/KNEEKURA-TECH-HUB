package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Port of X1 {@code EntityTHSetLaser} (laser "B"): a laser with no speed, pinned to a {@code set}
 * entity at {@code setLength} along its angle plus {@code setYOffset} up. Its length grows by 6 per
 * tick to the maximum, it can sweep with the yaw rotation of EntityTHShot, and it dies with its
 * set entity (or immediately when it has none).
 */
public class THSetLaserEntity extends THLaserEntity {
    private Entity setting;
    private double settingLength;
    private double settingYOffset;

    public THSetLaserEntity(EntityType<? extends THSetLaserEntity> type, Level level) {
        super(type, level);
    }

    public THSetLaserEntity(Level level, LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float slope,
                            Vec3d rotate, float rotationSpeed, int rotationEnd, X1LaserData laser, Entity set,
                            double setLength, double setYOffset) {
        this(PortRegistries.TH_SET_LASER.get(), level);
        // X1 passes form 0 implicitly: the set-laser constructor takes laser.color as the shot ID.
        initLaser(user, source, pos, angle, slope, rotate, rotationSpeed, rotationEnd, 0.0D, 0.0D, 0.0D, Vec3d.ZERO,
                laser.color, laser.width, laser.length, laser.damage, laser.delay, laser.end, laser.special);
        setLaserLength(laser.length);
        setMaxLaserLength(laser.length);
        this.settingLength = setLength;
        this.settingYOffset = setYOffset;
        this.setting = set;
        if (set != null) {
            this.setPos(set.getX() + angle.x() * setLength, set.getY() + angle.y() * setLength + setYOffset,
                    set.getZ() + angle.z() * setLength);
        }
    }

    @Override
    protected void afterX1Tick(X1ShotMotion m) {
        if (setting != null) {
            if (!setting.isAlive()) {
                this.discard();
                return;
            }
            this.setPos(setting.getX() + settingLength * m.angle.x(),
                    setting.getY() + settingLength * m.angle.y() + settingYOffset,
                    setting.getZ() + settingLength * m.angle.z());
            setLaserLength(getLaserLength() < getMaxLaserLength() ? getLaserLength() + 6.0D : getMaxLaserLength());
        } else {
            m.motion = m.angle;
            this.setPos(getX() + m.angle.x(), getY() + m.angle.y(), getZ() + m.angle.z());
            m.lastTime = 1;
            this.discard();
        }
    }

    // EntityTHSetLaser.hitCheck: endpoints from yaw / pitch, search box grown by the laser length.
    @Override
    protected void hitCheck(X1ShotMotion m) {
        double width = getShotSize();
        double length = getLaserLength();
        Vec3 dir = x1Direction(m);
        Vec3 pos = this.position();
        Vec3 start = pos.add(dir.scale(getShotSize()));
        Vec3 end = pos.add(dir.scale(length - getShotSize()));
        BlockHitResult block = clip(start, end);
        if (block.getType() != HitResult.Type.MISS) {
            end = block.getLocation();
            onImpactBlock(block, m, false);
        }
        Vec3 reach = toMc(m.motion).add(dir.scale(getLaserLength()));
        hitEntitiesAlong(m, start, end, this.getBoundingBox().expandTowards(reach).inflate(getLaserLength()), width);
    }
}
