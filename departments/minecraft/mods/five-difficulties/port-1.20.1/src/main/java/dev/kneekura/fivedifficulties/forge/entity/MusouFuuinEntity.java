package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotSpecials;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityMusouFuuin}: an EntityTHShot (shot ID 0, end 40) that grows by 0.1 per
 * tick, brakes ×0.8 for 15 ticks, then homes on the card's target turning at most 12° per tick.
 */
public class MusouFuuinEntity extends THShotEntity {
    /** The spell card's target (null once it is dead). */
    public LivingEntity target;
    private float maxSize;

    public MusouFuuinEntity(EntityType<? extends MusouFuuinEntity> type, Level level) {
        super(type, level);
    }

    public MusouFuuinEntity(Level level, LivingEntity user, Vec3d pos, Vec3d angle, float slope, Vec3d rotate,
                            float rotationSpeed, int rotationEnd, double firstSpeed, double limitSpeed,
                            double acceleration, Vec3d gravity, float size, float damage, LivingEntity target) {
        this(PortRegistries.MUSOU_FUUIN.get(), level);
        initShot(user, pos, angle, slope, rotate, rotationSpeed, rotationEnd, firstSpeed, limitSpeed, acceleration,
                gravity, 0, size, damage, 0, 40, 0, false);
        this.maxSize = size;
        this.setShotSize(0.1F);
        this.target = target;
    }

    @Override
    protected void specialMotion(X1ShotMotion m) {
        if (this.getShotSize() < maxSize) setShotSize(getShotSize() + 0.1F);
        if (this.tickCount < 15) {
            m.motion = m.motion.scale(0.8D);
            return;
        }
        m.limitSpeed = 0.6D;
        m.acceleration = 0.03D;
        if (target == null) return;
        if (target.isRemoved()) { // 1.7.10 isDead
            m.setVector();
            target = null;
            return;
        }
        Vec3d toTarget = new Vec3d(target.getX() - getX(), target.getY() + target.getEyeHeight() - getY(),
                target.getZ() - getZ());
        m.angle = X1ShotSpecials.homingTurn(m.angle, toTarget, 12.0F);
        m.accelerate();
        // updateYawAndPitch
        m.yaw = X1ShotMotion.yawFromVector(m.angle.x(), m.angle.z());
        m.pitch = X1ShotMotion.pitchFromVector(m.angle.x(), m.angle.y(), m.angle.z());
    }
}
