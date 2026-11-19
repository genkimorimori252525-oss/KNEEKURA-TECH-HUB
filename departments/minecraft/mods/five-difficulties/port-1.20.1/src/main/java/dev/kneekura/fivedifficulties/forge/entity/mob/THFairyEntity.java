package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1DanmakuPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.X1Config;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import java.util.Calendar;

/**
 * Port of X1 {@code EntityTHFairy}: a fairy (0.6 × 1.5, 5 XP) flying 2 up with a random danmaku pattern from
 * {@link X1DanmakuPatterns} (sphere / wide / circle / random ring / ring families, or a laser sphere), firing
 * whenever its attack counter wraps past the pattern's span. It calls fairies within 30 to its target. In the
 * nether or on 31 October a dying fairy does not die: it sinks and comes back as a zombie fairy.
 */
public class THFairyEntity extends DanmakuMobEntity {
    public THFairyEntity(EntityType<? extends THFairyEntity> type, Level level) {
        super(type, level);
        this.lastTime = 0;
        this.xpReward = 5;
        setForm((byte) this.random.nextInt(3));
        X1DanmakuPatterns.ensure(X1Config.danmakuLevel());
        setPattern(this.random.nextInt(X1DanmakuPatterns.PATTERN.size()));
        this.lostTarget = 0;
        this.setSpeed(0.3D);
        this.setSpecies(SPECIES_FAIRY);
        this.isFlyingMode = true;
        this.setAttackDistance(8.0D);
        this.setDetectionDistance(8.0D);
        this.setFlyingHeight(2);
    }

    protected void setPattern(int id) {
        X1DanmakuPatterns.Pattern p = X1DanmakuPatterns.TABLE.get(X1DanmakuPatterns.PATTERN.get(id));
        int shot = p.form();
        setDanmakuPattern(p.danmaku());
        danmakuSpan = p.span();
        speedRate = p.speed();
        shotForm = (byte) ((shot - (shot % 8)) / 8);
        shotColor = (byte) (shot % 8);
    }

    /** onDeathUpdate: in the nether or on Halloween (sunflower fairies excepted) a dying fairy turns into a zombie fairy. */
    @Override
    protected void tickDeath() {
        Calendar calendar = Calendar.getInstance();
        boolean halloween = calendar.get(Calendar.MONTH) + 1 == 10 && calendar.get(Calendar.DATE) == 31;
        if (this.level().dimensionType().ultraWarm() || (halloween && !(this instanceof SunFlowerFairyEntity))) {
            if (this.getDetectionDistance() > 2.0D) {
                this.setFlyingHeight(0);
                this.setDetectionDistance(this.getDetectionDistance() - 0.03D);
                setTarget(null);
            } else {
                setHealth(2.0F);
                setDetectionDistance(8.0D);
                setAttackDistance(2.0D);
                setFlyingHeight(2);
                setSpeed(0.03D);
                setDanmakuPattern(0);
                danmakuSpan = 50 - (X1Config.danmakuLevel() * 10);
                speedRate = 0.2F;
                shotForm = (byte) X1ShotTables.FORM_LIGHT;
                shotColor = (byte) X1ShotTables.RED;
                this.setForm((byte) -1);
            }
        } else {
            super.tickDeath();
        }
    }

    @Override
    public void tick() {
        if (this.getHealth() <= 0) this.setDeltaMovement(0, 0, 0);
        if (this.tickCount <= lastTime) return;
        super.tick();
        if (this.attackCounter > danmakuSpan) attackCounter = 0;
    }

    public LivingEntity getShooter() {
        return this;
    }

    @Override
    protected void danmakuPattern(int level) {
        if (attackCounter > 0) return;
        LivingEntity shooter = getShooter();
        if (shooter == null) return;
        Vec3d look = X1Danmaku.angle(shooter.getYRot(), shooter.getXRot());
        look = X1Danmaku.angle_LimitRandom(new java.util.Random(), look, X1Config.danmakuAccuracy());
        int d = getDanmakuPattern();
        boolean isShot = shotForm < 32;
        boolean isLaser = shotForm == 64;
        X1ShotData shotData = X1ShotData.shot(shotForm, shotColor, 0, 80, special);
        X1LaserData laserData = X1LaserData.laser(X1LaserData.LASER_NORMAL, shotColor, 0.1F, 2.0F, 3.0F, 0, 80, special);
        X1Danmaku.playShotSound(this);
        Vec3d pos = pos();
        if (d >= 0 && d <= 999) {
            int way = d % 100 + 1, num = d / 100 + 1;
            double speed = speedRate, slow = speed / num;
            for (int i = 0; i < num; i++) {
                if (isShot) X1Danmaku.createSphereShot(shooter, shooter, pos, look, 0F, speed, speed, 0.0D, Vec3d.ZERO, shotData, way, 0.0D, 0F);
                else if (isLaser) X1Danmaku.createSphereLaserA(shooter, shooter, pos, look, speed, speed, 0.0D, Vec3d.ZERO, laserData, way, 0F, 0F);
                speed -= slow;
            }
        } else if (d >= 1000 && d <= 1999) {
            int num = d % 100 + 1;
            float span = (d - 1000) / 50F + 1F;
            if (isShot) X1Danmaku.createWideShot(shooter, shooter, pos, look, speedRate, speedRate, 0.0D, Vec3d.ZERO, shotData, num, num * span, 0.0D);
            else if (isLaser) X1Danmaku.createWideLaserA(shooter, shooter, pos, look, speedRate, speedRate, 0.0D, Vec3d.ZERO, laserData, num, num * span, 0.0D);
        } else if (d >= 2000 && d <= 2999) {
            int way = d % 100 + 1, num = (d - 2000) / 100 + 1;
            double speed = speedRate, slow = speed / num;
            for (int i = 0; i < num; i++) {
                if (isShot) X1Danmaku.createCircleShot(shooter, shooter, pos, look, speed, speed, 0.0D, Vec3d.ZERO, shotData, way, shotData.size, 0F);
                else if (isLaser) X1Danmaku.createCircleLaserA(shooter, shooter, pos, look, speed, speed, 0.0D, Vec3d.ZERO, laserData, way, 0.0D);
                speed -= slow;
            }
        } else if (d >= 3000 && d <= 3999) {
            float shotSpan = d % 100 + 1F;
            int num = (d - 3000) / 100 + 1;
            if (isShot) X1Danmaku.createRandomRingShot(shooter, pos, look, speedRate, speedRate, 0.0D, shotData, num, 0.0D, shotSpan);
        } else if (d >= 4000 && d <= 4999) {
            float shotSpan = ((d - 4000) % 100 + 1F) * 1.8F;
            int way = (d - 4000) / 100 * ((d % 100) / 10) + 3;
            X1Danmaku.createRingShot(shooter, pos, look, speedRate, shotData, way, 0, shotSpan, this.random.nextFloat() * 360F);
        } else if (d >= 5000 && d <= 5999) {
            int num = d % 100 + 1;
            X1Danmaku.createRandomRingShot(shooter, pos, look, speedRate, speedRate, 0.0D, shotData, num, 0.0D, 360F);
        }
    }

    @Override
    protected boolean canFairyCall() { return true; }

    @Override
    protected double getFairyCallDistance() { return 30.0D; }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean hitByPlayer) {
        super.dropCustomDeathLoot(source, looting, hitByPlayer);
        if (getForm() < 0) return;
        if (hitByPlayer) {
            if (this.getMaxHealth() == 10.0F) {
                dropShotItem(0, this.random.nextInt(12) + looting * 2, 7, 8, X1ShotTables.RED, 0, 0, 2);
                dropPowerUpItem(this.random.nextInt(20) + this.random.nextInt(3 + looting * 2));
                dropPointItem(this.random.nextInt(20) + this.random.nextInt(3 + looting * 2));
            } else {
                dropShotItem(0, this.random.nextInt(2) + looting, 3, 0, X1ShotTables.RED, 0, 0, 2);
                dropPowerUpItem(this.random.nextInt(5) + this.random.nextInt(1 + looting));
                dropPointItem(this.random.nextInt(5) + this.random.nextInt(1 + looting));
            }
        }
    }

    @Override
    public int getMaxSpawnClusterSize() { return 10; }

    /** getCanSpawnHere: config rate, rarer below y 64, needs sky light above 7 and grass, dirt or sand below. */
    public static boolean checkFairySpawnRules(EntityType<? extends THFairyEntity> type, ServerLevelAccessor level,
                                               MobSpawnType reason, BlockPos pos, RandomSource random) {
        if (reason == MobSpawnType.SPAWNER || reason == MobSpawnType.SPAWN_EGG || reason == MobSpawnType.COMMAND) return true;
        if (!X1Config.spawnDanmakuMob() || !X1Config.spawnFairy()) return false;
        if (level.getDifficulty() == net.minecraft.world.Difficulty.PEACEFUL) return false;
        if (random.nextInt(100) < X1Config.fairySpawnRate()) return false;
        int y = pos.getY();
        if (y < 64 && y < random.nextInt(64)) return false;
        if (level.getBrightness(LightLayer.SKY, pos) - level.getSkyDarken() <= 7) return false;
        BlockState below = level.getBlockState(pos.below());
        return below.is(Blocks.GRASS_BLOCK) || below.is(Blocks.DIRT) || below.is(Blocks.SAND);
    }

    @Override
    protected Component getTypeName() {
        return getForm() >= 32 ? Component.translatable("entity.THGhost.name") : super.getTypeName();
    }

    protected static float sin(float f) {
        return Mth.sin(f);
    }

    @SuppressWarnings("unused")
    private static boolean levelIsAccessor(LevelAccessor l) {
        return l != null;
    }
}
