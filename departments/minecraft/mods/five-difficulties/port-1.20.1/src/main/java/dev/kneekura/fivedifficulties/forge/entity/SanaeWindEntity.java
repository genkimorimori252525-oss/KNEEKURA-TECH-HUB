package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntitySanaeWind}: an EntityTHShot (form 0, colour = wind type) steered by its user's
 * movement: its gravity is 0.2 × the user's last-tick displacement (never downward, −0.1 while sneaking).
 * Wind type 1 instead turns 2° per tick at the user's speed. WIND01 knocks back what it hits.
 */
public class SanaeWindEntity extends THShotEntity {
    private double lastPlayerPosX, lastPlayerPosY, lastPlayerPosZ;

    public SanaeWindEntity(EntityType<? extends SanaeWindEntity> type, Level level) {
        super(type, level);
    }

    public SanaeWindEntity(Level level, LivingEntity user, Vec3d pos, Vec3d angle, float slope, Vec3d rotate,
                           float rotationSpeed, int rotationEnd, double firstSpeed, double limitSpeed, double acceleration,
                           Vec3d gravity, int kazeType, float size, float damage, int delay, int end, int special) {
        this(PortRegistries.SANAE_WIND.get(), level);
        initShot(user, pos, angle, slope, rotate, rotationSpeed, rotationEnd, firstSpeed, limitSpeed, acceleration,
                gravity, kazeType, size, damage, delay, end, special, false);
        lastPlayerPosX = user.getX();
        lastPlayerPosY = user.getY();
        lastPlayerPosZ = user.getZ();
    }

    @Override
    public void tick() {
        X1ShotMotion m = motion();
        Entity owner = this.getOwner();
        if (!this.level().isClientSide && m != null && owner != null) {
            double ux = owner.getX() - lastPlayerPosX;
            double uy = owner.getY() - lastPlayerPosY;
            double uz = owner.getZ() - lastPlayerPosZ;
            if (getShotColor() == 1) {
                m.yaw += 2F;
                m.shotSpeed = (double) (float) Math.sqrt(ux * ux + uy * uy + uz * uz);
                m.setVector();
            } else {
                double gy = uy * 0.2D;
                if (gy < 0.0D) gy = 0.0D;
                if (owner.isShiftKeyDown()) gy = -0.1D;
                m.gravity = new Vec3d(ux * 0.2D, gy, uz * 0.2D);
            }
        }
        super.tick();
        if (owner != null) {
            lastPlayerPosX = owner.getX();
            lastPlayerPosY = owner.getY();
            lastPlayerPosZ = owner.getZ();
        }
    }

    /** RenderSanaeWind animation frame. */
    public int getWindRenderPattern() {
        return this.tickCount % 4;
    }
}
