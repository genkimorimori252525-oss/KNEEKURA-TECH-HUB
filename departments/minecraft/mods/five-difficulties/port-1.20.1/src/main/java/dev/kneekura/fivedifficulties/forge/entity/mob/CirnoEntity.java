package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.X1Config;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;

/**
 * Port of X1 {@code EntityCirno}: a four-phase boss (1 × 1.8, 250 XP, fairy / ice fairy, speed 0.5). Normal 1:
 * rings of aqua crystals (38 HP); 「アイシクルフォール」 (card 19, 46 HP, yellow fans from level 2); normal 2: white
 * and blue circles and white laser fans (32 HP); 「パーフェクトフリーズ」 (card 9, 58 HP, blue fans). Spell-card kills
 * shower point / power bonuses and crystal shots; the last card also drops the icicle sword and an extend.
 */
public class CirnoEntity extends DanmakuMobEntity {
    public static final int SC_CIRNO_PERFECT_FREEZE = 9, SC_CIRNO_ICICLE_FALL = 19;
    public static final int NORMAL_ATTACK02 = 2, SPELLCARD_ATTACK02 = 102;
    private int randomWay;

    public CirnoEntity(EntityType<? extends CirnoEntity> type, Level level) {
        super(type, level);
        this.xpReward = 250;
        this.setDanmakuMobName("Cirno");
        this.setSpecies(SPECIES_FAIRY, SPECIES_FAIRY_ICE);
        this.setDanmakuPattern(NORMAL_ATTACK01);
        this.setMaxHP(38.0F);
        this.setHealth(38.0F);
        this.setSpeed(0.5F);
        this.setAttackDistance(14.0D);
        this.setDetectionDistance(30.0D);
        this.setFlyingHeight(2);
        this.isFlyingMode = true;
        this.isSpellCardMode = false;
        this.attackInterval = 0;
        this.randomWay = 0;
    }

    @Override
    public int getUsingSpellCardNo() {
        return switch (getDanmakuPattern()) {
            case SPELLCARD_ATTACK01 -> SC_CIRNO_ICICLE_FALL;
            case SPELLCARD_ATTACK02 -> SC_CIRNO_PERFECT_FREEZE;
            default -> -1;
        };
    }

    @Override
    protected void tickDeath() {
        if (this.tickCount <= lastTime) return;
        switch (getDanmakuPattern()) {
            case NORMAL_ATTACK01 -> moveDanmakuAttack(SPELLCARD_ATTACK01, 40, 46.0F, 60);
            case SPELLCARD_ATTACK01 -> moveDanmakuAttack(NORMAL_ATTACK02, 60, 32.0F, 20);
            case NORMAL_ATTACK02 -> moveDanmakuAttack(SPELLCARD_ATTACK02, 40, 58.0F, 60);
            case SPELLCARD_ATTACK02 -> moveDanmakuAttack(ATTACK_END, 30, 0F, 60);
            default -> {
                if (deathTime % 9 == 0) explosionEffect(this.level(), getX(), getY(), getZ(), 1.0F + deathTime * 0.1F);
                super.tickDeath();
            }
        }
    }

    private void bow() {
        this.level().playSound(null, getX(), getY(), getZ(), SoundEvents.ARROW_SHOOT, SoundSource.HOSTILE, 2.0F, 0.8F);
    }

    private Vec3d lookVec() {
        var l = getLookAngle();
        return new Vec3d(l.x, l.y, l.z);
    }

    @Override
    protected void danmakuPattern(int level) {
        Vec3d angle = X1Danmaku.angle(getYRot(), getXRot());
        switch (getDanmakuPattern()) {
            case NORMAL_ATTACK01 -> {
                if (attackCounter == 40) {
                    Vec3d look = lookVec();
                    for (int i = 0; i < 7; i++) {
                        double speed = 0.6D + level * 0.15D;
                        X1Danmaku.createRingShot(this, this, pos(), look, 0F, 9999, speed, speed, 0.1D, Vec3d.ZERO,
                                X1ShotData.shot(X1ShotTables.FORM_CRYSTAL, X1ShotTables.AQUA, 0.2F, 4.0F, i, 120, 0), i + 2, 0.0D,
                                i * (level), this.random.nextFloat() * 360F);
                    }
                    bow();
                }
                if (attackCounter >= 50) attackCounter = 0;
            }
            case SPELLCARD_ATTACK01 -> {
                if (attackCounter == 1) {
                    useSpellCard(getUsingSpellCardNo());
                } else if (attackCounter > 30 && attackCounter < 170 && attackCounter % 17 == 0 && level >= 2) {
                    float size = X1ShotTables.SIZE[level >= 3 ? X1ShotTables.FORM_MEDIUM : X1ShotTables.FORM_SMALL];
                    X1Danmaku.createWideShot(this, this, pos(), angle, 0.3D + level * 0.1D, 0.5D, 1.0D, Vec3d.ZERO,
                            X1ShotData.shot(X1ShotTables.FORM_SMALL, X1ShotTables.YELLOW, size, 4.0F, 3, 80), 3, 70F, 0.2D);
                    bow();
                } else if (attackCounter >= 240) {
                    attackCounter = 0;
                }
            }
            case NORMAL_ATTACK02 -> {
                if (attackCounter < 50 && attackCounter % 6 == 0) {
                    X1ShotData tiny = X1ShotData.shot(X1ShotTables.FORM_TINY, X1ShotTables.WHITE);
                    X1ShotData circle = X1ShotData.shot(X1ShotTables.FORM_CIRCLE, X1ShotTables.BLUE);
                    double s2 = 0.3D + level * 0.1D;
                    X1Danmaku.createCircleShot(this, this, pos(), angle, 0.2D, 0.2D, 0.0D, Vec3d.ZERO, tiny, 5 + level * 2, tiny.size, 0F);
                    X1Danmaku.createCircleShot(this, this, pos(), angle, s2, s2, 0.0D, Vec3d.ZERO, circle, 5 + level * 2, circle.size, 0F);
                    bow();
                } else if (attackCounter == 55 || attackCounter == 65 || attackCounter == 75) {
                    double s = 0.3D + level * 0.2D;
                    X1Danmaku.createWideLaserA(this, this, pos(), lookVec(), s, s, 0.0D, Vec3d.ZERO,
                            X1LaserData.laser(X1ShotTables.WHITE, 0.1F, 4.0F, 4.0F), 3, 30F, 0.0D);
                }
                if (attackCounter > 128) attackCounter = 0;
            }
            case SPELLCARD_ATTACK02 -> {
                if (attackCounter == 1) {
                    randomWay = this.random.nextInt(2);
                    useSpellCard(getUsingSpellCardNo());
                } else if (attackCounter >= 70 && attackCounter <= 90 && attackCounter % 3 == 0) {
                    int way = 4 + randomWay;
                    for (int i = 0; i < 3 + level; i++) {
                        X1Danmaku.createWideShot(this, this, pos(), angle, 0.3D + level * 0.1D, 0.5D, 1.0D, Vec3d.ZERO,
                                X1ShotData.shot(X1ShotTables.FORM_CIRCLE, X1ShotTables.BLUE, 0.3F, 4.0F, i, 80), way, 70F, 0.2D);
                    }
                    bow();
                } else if (attackCounter >= 170) {
                    attackCounter = 0;
                }
            }
            default -> {}
        }
    }

    @Override
    protected boolean canFairyCall() { return false; }

    /** applyPotionDamageCalculations: × 0.05 while invulnerable between phases. */
    @Override
    protected float getDamageAfterMagicAbsorb(DamageSource source, float damage) {
        damage = super.getDamageAfterMagicAbsorb(source, damage);
        if (attackInterval > 0) damage = (float) ((double) damage * 0.05D);
        return damage;
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean hitByPlayer) {
        super.dropCustomDeathLoot(source, looting, hitByPlayer);
        if (hitByPlayer && isSpellCardAttack()) {
            int j = 40;
            for (int k = 0; k < j; k += 2) {
                float yaw = 360F / (float) j * (float) k;
                float pitch = Mth.sin(yaw / 180F * 3.141593F * 4F) * 20F - 60F;
                dropItem(4, pos(), X1Danmaku.getVecFromAngle(yaw, pitch, 1.0F));
                yaw = 360F / (float) j * (float) (k + 1);
                pitch = Mth.cos(yaw / 180F * 3.141593F * 4F) * 20F - 60F;
                dropItem(1, pos(), X1Danmaku.getVecFromAngle(yaw, pitch, 1.0F));
            }
            dropShotItem(17, 17 + this.random.nextInt(2) + looting, 5, 32, X1ShotTables.AQUA, 0, 0, 2);
        }
        if (hitByPlayer && getDanmakuPattern() == SPELLCARD_ATTACK02) {
            this.spawnAtLocation(new ItemStack(PortRegistries.ICICLE_SWORD.get()), 0.0F);
            dropItem(11, pos(), angle(getYRot(), -90F));
        }
    }

    @Override
    public boolean isIgnoringBlockTriggers() { return true; }

    @Override
    public int getMaxSpawnClusterSize() { return 1; }

    /** getCanSpawnHere: config rate, standing in a snow layer with ice within 2 below. */
    public static boolean checkCirnoSpawnRules(EntityType<? extends CirnoEntity> type, ServerLevelAccessor level,
                                               MobSpawnType reason, BlockPos pos, RandomSource random) {
        if (reason == MobSpawnType.SPAWNER || reason == MobSpawnType.SPAWN_EGG || reason == MobSpawnType.COMMAND) return true;
        if (!X1Config.spawnDanmakuMob() || !X1Config.spawnBoss()) return false;
        if (random.nextInt(100) < X1Config.fairySpawnRate()) return false;
        if (!level.getBlockState(pos).is(Blocks.SNOW)) return false;
        for (int i = -2; i <= 2; i++) {
            for (int j = -2; j <= 2; j++) {
                if (level.getBlockState(pos.offset(i, -1, j)).is(Blocks.ICE)) return true;
            }
        }
        return false;
    }
}
