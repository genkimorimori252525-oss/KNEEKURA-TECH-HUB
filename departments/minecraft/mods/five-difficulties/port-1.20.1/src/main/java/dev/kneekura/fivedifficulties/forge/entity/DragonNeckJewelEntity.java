package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;

import javax.annotation.Nullable;
import java.util.Random;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.FORM_LIGHT;

/**
 * Port of X1 {@code EntityDragonNeckJewel} (龍の頸の玉): an EntityTHShot (form 0, size 1, damage 7, speed
 * 0.9, default gravity) that bursts where it lands into five rising lasers and ten light shots. A block
 * hit on the forward ray bursts twice (once in blockHitSpecialProcess, once in onImpact), as in X1.
 */
public class DragonNeckJewelEntity extends THShotEntity {
    private static final int[] COLORS = {0, 2, 4, 5, 6};
    /** X1 Entity.rand */
    private final Random rand = new Random();
    /** X1 keeps the thrower's colour, but nothing reads it (the renderer flickers on its own). */
    public float colorR, colorG, colorB;

    public DragonNeckJewelEntity(EntityType<? extends DragonNeckJewelEntity> type, Level level) {
        super(type, level);
    }

    public DragonNeckJewelEntity(Level level, LivingEntity user, Vec3d pos, Vec3d angle, float r, float g, float b) {
        this(PortRegistries.DRAGON_NECK_JEWEL.get(), level);
        X1ShotData shot = X1ShotData.shot(0, 0, 1.0F, 7.0F, 0, 80);
        initShot(user, pos, angle, 0F, X1Danmaku.rotate_Default(), 0F, 9999, 0.9D, 0.9D, 0.0D,
                X1Danmaku.gravity_Default(), shot.shotId(), shot.size, shot.damage, shot.delay, shot.end, shot.special, false);
        this.colorR = r;
        this.colorG = g;
        this.colorB = b;
    }

    @Override
    protected boolean onImpact(@Nullable Entity hitEntity, @Nullable BlockHitResult block, X1ShotMotion m) {
        super.onImpact(hitEntity, block, m);
        if (!createLightningBoltDanmaku(hitEntity)) {
            this.delete();
            return true;
        }
        return false;
    }

    /** Returns true (no burst) only for another shot. */
    private boolean createLightningBoltDanmaku(@Nullable Entity hitEntity) {
        if (hitEntity instanceof THShotEntity) return true;
        if (!(getOwner() instanceof LivingEntity user)) return false;
        float angle = rand.nextFloat() * 360F;
        for (int i = 0; i < 5; i++) {
            X1Danmaku.createLaserA(user, this, X1Danmaku.pos(getX(), getY() + 0.4D, getZ()), X1Danmaku.angle(angle, -70F),
                    0.1D, 0.3D, 0.1D, X1Danmaku.gravity_Zero(), X1LaserData.laser(COLORS[i], 0.15F, 3.0F, 3.0F, 0, 40, 0));
            angle += 72F;
        }
        for (int i = 0; i < 10; i++) {
            double xVector = rand.nextGaussian() * 0.2D;
            double yVector = 0.8D + rand.nextDouble() * 0.2D;
            double zVector = rand.nextGaussian() * 0.2D;
            X1ShotData shot = X1ShotData.shot(FORM_LIGHT, COLORS[rand.nextInt(5)], 0.3F, 3.0F, 1, 120);
            X1Danmaku.createShot(user, this, X1Danmaku.pos(getX(), getY() + 0.4D, getZ()),
                    X1Danmaku.angle(xVector, yVector, zVector), 0F, 0.4D, 0.4D, 0.00D, X1Danmaku.gravity(0.0D, -0.01D, 0.0D), shot);
        }
        return false;
    }

    @Override
    protected boolean blockHitSpecialProcess(BlockHitResult hit, X1ShotMotion m) {
        return createLightningBoltDanmaku(null);
    }
}
