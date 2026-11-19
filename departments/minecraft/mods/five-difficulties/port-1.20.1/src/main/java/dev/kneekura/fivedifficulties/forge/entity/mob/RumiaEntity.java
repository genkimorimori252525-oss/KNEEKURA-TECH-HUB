package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.X1Config;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;

/**
 * Port of X1 {@code EntityRumia}: a two-phase boss (1 × 1.8, 36 HP, 160 XP, youkai). Phase 1 fires blue then red
 * circles, sidesteps, sweeps tiny rainbow circles and steps back (a 127-tick loop); on "death" she declares
 * 「ムーンライトレイ」 (card 28, 44 HP) and rings tiny white circles; the second death is final.
 */
public class RumiaEntity extends DanmakuMobEntity {
    public RumiaEntity(EntityType<? extends RumiaEntity> type, Level level) {
        super(type, level);
        this.xpReward = 160;
        this.noCulling = true;
        this.setDanmakuPattern(NORMAL_ATTACK01);
        this.setMaxHP(36.0F);
        setHealth(36.0F);
        this.setDanmakuMobName("Rumia");
        this.setSpecies(SPECIES_YOUKAI);
        this.setAttackDistance(14.0D);
        this.setDetectionDistance(12.0D);
        this.setFlyingHeight(2);
        this.isFlyingMode = true;
    }

    @Override
    public int getUsingSpellCardNo() {
        return getDanmakuPattern() == SPELLCARD_ATTACK01 ? 28 : -1;
    }

    @Override
    protected void tickDeath() {
        if (this.tickCount <= lastTime) return;
        switch (getDanmakuPattern()) {
            case NORMAL_ATTACK01 -> {
                moveDanmakuAttack(SPELLCARD_ATTACK01, 40, 44.0F, 60);
                this.setAttackDistance(14.0D);
                this.setDetectionDistance(30.0D);
                this.setFlyingHeight(2);
            }
            case SPELLCARD_ATTACK01 -> moveDanmakuAttack(ATTACK_END, 30, 0F, 60);
            default -> {
                if (deathTime % 9 == 0) explosionEffect(this.level(), getX(), getY(), getZ(), 1.0F + deathTime * 0.1F);
                super.tickDeath();
            }
        }
    }

    @Override
    protected void danmakuPattern(int level) {
        switch (getDanmakuPattern()) {
            case NORMAL_ATTACK01 -> {
                Vec3d ang = angle(getYRot(), getXRot());
                if (attackCounter == 1 || attackCounter == 14) {
                    X1Danmaku.playShotSound(this);
                    int color = attackCounter == 1 ? X1ShotTables.BLUE : X1ShotTables.RED;
                    for (int i = 0; i < 1 + level; i++) {
                        X1Danmaku.createCircleShot(this, this, pos(), ang, 2.0D, 0.4D, -0.3D, Vec3d.ZERO,
                                X1ShotData.shot(X1ShotTables.FORM_CIRCLE, color, 10 + i, 80, 0),
                                12 + 3 * level, X1ShotData.shot(X1ShotTables.FORM_CIRCLE, color, 10 + i, 80, 0).size, 0F);
                    }
                } else if (attackCounter == 24) {
                    moveRight(0.3D, 20);
                } else if (attackCounter >= 62 && attackCounter < 67) {
                    X1Danmaku.playShotSound(this);
                    int i = attackCounter - 62;
                    X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_TINY, attackCounter % 7, 0, 80, 0);
                    double speed = 0.2D + level * 0.1D;
                    X1Danmaku.createCircleShot(this, this, pos(), angle(getYRot() + i * 5F, getXRot()), speed, speed, 0.0D,
                            Vec3d.ZERO, shot, 5 + level * 2, shot.size, 0F);
                } else if (attackCounter == 67) {
                    moveLeft(0.3D, 20);
                }
                if (attackCounter >= 127) attackCounter = 0;
            }
            case SPELLCARD_ATTACK01 -> {
                if (attackCounter == 1) {
                    useSpellCard(getUsingSpellCardNo());
                } else if (attackCounter < 60 && attackCounter % 9 == 0) {
                    X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_TINY, X1ShotTables.WHITE, 0, 80, 0);
                    double speed = 0.1D + level * 0.1D;
                    X1Danmaku.createCircleShot(this, this, pos(), angle(getYRot(), getXRot()), speed, speed, 0.0D, Vec3d.ZERO,
                            shot, 15 + level * 3, shot.size, 0F);
                    X1Danmaku.playShotSound(this);
                } else if (attackCounter >= 120) {
                    attackCounter = 0;
                }
            }
            default -> {}
        }
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean hitByPlayer) {
        super.dropCustomDeathLoot(source, looting, hitByPlayer);
        if (hitByPlayer) {
            dropShotItem(0, 8 + this.random.nextInt(2) + looting, 5, 32, X1ShotTables.BLUE, 0, 0, 2);
            dropPowerUpItem(8 + this.random.nextInt(5) + this.random.nextInt(1 + looting));
            dropPointItem(8 + this.random.nextInt(5) + this.random.nextInt(1 + looting));
        }
    }

    /**
     * X1 wraps the base attackEntityFrom once more: the magic reduction is applied a third time and the motion is
     * scaled by 0.01 on top of the base's 0.0001.
     */
    @Override
    public boolean hurt(DamageSource source, float damage) {
        if (super.hurt(source, this.getDamageAfterMagicAbsorb(source, damage))) {
            if (source.getEntity() instanceof LivingEntity) this.setDeltaMovement(getDeltaMovement().scale(0.01D));
            return true;
        }
        return false;
    }

    @Override
    public int getMaxSpawnClusterSize() { return 1; }

    public static boolean checkRumiaSpawnRules(EntityType<? extends RumiaEntity> type, ServerLevelAccessor level,
                                               MobSpawnType reason, BlockPos pos, RandomSource random) {
        if (reason == MobSpawnType.SPAWNER || reason == MobSpawnType.SPAWN_EGG || reason == MobSpawnType.COMMAND) return true;
        return X1Config.spawnDanmakuMob() && X1Config.spawnBoss() && darkEnough(level, pos, random);
    }

    @SuppressWarnings("unused")
    private static boolean isPlayer(Object o) {
        return o instanceof Player;
    }
}
