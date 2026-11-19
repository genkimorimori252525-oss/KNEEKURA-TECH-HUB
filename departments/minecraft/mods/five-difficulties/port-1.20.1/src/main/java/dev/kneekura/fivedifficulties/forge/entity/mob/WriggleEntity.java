package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.X1Config;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import dev.kneekura.fivedifficulties.forge.spellcard.cards.SpecialCards;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;

/**
 * Port of X1 {@code EntityWriggle}: a three-phase boss (1 × 1.8, 30 HP, 140 XP, bug youkai, flying height 3).
 * Normal: yellow / aqua rice fans with the 「リトルバグストーム」 specials, then a slowing 5-way yellow fan
 * (147-tick loop). Card 35 (X1 numbers it so; 36 HP) adds blue sphere bursts; card 34 (42 HP) only declares.
 * X1 quirks kept: the sidesteps at counters 24 / 67 sit behind earlier branches and never run; the hard extra
 * rice reuses {@code angle} instead of the computed {@code angle2}.
 */
public class WriggleEntity extends DanmakuMobEntity {
    private static final int NORMAL = 2, HARD = 3, LUNATIC = 4;

    public WriggleEntity(EntityType<? extends WriggleEntity> type, Level level) {
        super(type, level);
        this.xpReward = 140;
        this.setDanmakuPattern(NORMAL_ATTACK01);
        this.setMaxHP(30.0F);
        setHealth(30.0F);
        this.setDanmakuMobName("Wriggle");
        this.setSpecies(SPECIES_YOUKAI_BUG);
        this.setAttackDistance(14.0D);
        this.setDetectionDistance(12.0D);
        this.setFlyingHeight(3);
        this.isFlyingMode = true;
    }

    @Override
    public int getUsingSpellCardNo() {
        return switch (getDanmakuPattern()) {
            case SPELLCARD_ATTACK01 -> 35;
            case SPELLCARD_ATTACK02 -> 34;
            default -> -1;
        };
    }

    @Override
    protected void tickDeath() {
        if (this.tickCount <= lastTime) return;
        switch (getDanmakuPattern()) {
            case NORMAL_ATTACK01 -> {
                moveDanmakuAttack(SPELLCARD_ATTACK01, 20, 36.0F, 40);
                this.setAttackDistance(16.0D);
                this.setDetectionDistance(30.0D);
                this.setFlyingHeight(2);
            }
            case SPELLCARD_ATTACK01 -> {
                moveDanmakuAttack(SPELLCARD_ATTACK02, 60, 42.0F, 80);
                this.setAttackDistance(15.0D);
                this.setDetectionDistance(30.0D);
                this.setFlyingHeight(4);
            }
            case SPELLCARD_ATTACK02 -> moveDanmakuAttack(ATTACK_END, 30, 0F, 60);
            default -> {
                if (deathTime % 9 == 0) explosionEffect(this.level(), getX(), getY(), getZ(), 1.0F + deathTime * 0.1F);
                super.tickDeath();
            }
        }
    }

    private Vec3d lookVec() {
        var l = getLookAngle();
        return new Vec3d(l.x, l.y, l.z);
    }

    @Override
    protected void danmakuPattern(int level) {
        switch (getDanmakuPattern()) {
            case NORMAL_ATTACK01 -> {
                Vec3d look = lookVec();
                Vec3d angle;
                if (attackCounter < 30) {
                    if (attackCounter % 15 >= 1 && attackCounter % 15 < 8) {
                        angle = X1Danmaku.getRotationVectorFromAngle(getYRot(), getXRot(), (attackCounter % 8) * 10F, 1.0);
                        X1Danmaku.playShotSound(this);
                        X1Danmaku.createShot(this, this, pos(), angle, 0F, 1.0, 0.0, -0.2, Vec3d.ZERO,
                                X1ShotData.shot(X1ShotTables.FORM_RICE, X1ShotTables.YELLOW, 3, 15, SpecialCards.LittleBugStorm.SP_ATTACK01_01));
                        if (level >= HARD) {
                            X1Danmaku.createShot(this, this, pos(), angle, 0F, 1.0, 0.0, -0.4, Vec3d.ZERO,
                                    X1ShotData.shot(X1ShotTables.FORM_RICE, X1ShotTables.YELLOW, 3, 15, SpecialCards.LittleBugStorm.SP_ATTACK01_01));
                        }
                    } else if (attackCounter % 15 >= 8 && attackCounter % 15 < 15) {
                        angle = X1Danmaku.getRotationVectorFromAngle(getYRot(), getXRot(), -(attackCounter % 8) * 10F, 1.0);
                        X1Danmaku.playShotSound(this);
                        X1Danmaku.createShot(this, this, pos(), angle, 0F, 1.0, 0.0, -0.2, Vec3d.ZERO,
                                X1ShotData.shot(X1ShotTables.FORM_RICE, X1ShotTables.AQUA, 3, 15, SpecialCards.LittleBugStorm.SP_ATTACK01_02));
                        if (level >= HARD) {
                            X1Danmaku.createShot(this, this, pos(), angle, 0F, 1.0, 0.0, -0.4, Vec3d.ZERO,
                                    X1ShotData.shot(X1ShotTables.FORM_RICE, X1ShotTables.AQUA, 3, 15, SpecialCards.LittleBugStorm.SP_ATTACK01_02));
                        }
                    }
                } else if (attackCounter == 24) {
                    moveRight(0.3D, 20);
                } else if (attackCounter >= 62 && attackCounter < 72) {
                    X1Danmaku.playShotSound(this);
                    double firstSpeed = 0.3 + 0.1 * level;
                    double limit = 0.3;
                    double acceleration = -(attackCounter - 61) * 0.005;
                    X1Danmaku.createWideShot(this, this, pos(), look, firstSpeed, limit, acceleration, Vec3d.ZERO,
                            X1ShotData.shot(X1ShotTables.FORM_SMALL, X1ShotTables.YELLOW, 10, 80, 0), 5, 90F, 0.0D);
                } else if (attackCounter == 67) {
                    moveLeft(0.3D, 20);
                }
                if (attackCounter >= 147) attackCounter = 0;
            }
            case SPELLCARD_ATTACK01 -> {
                if (attackCounter % 15 == 1 && attackCounter < 120) {
                    int way = level == NORMAL ? 16 : level == HARD ? 24 : level == LUNATIC ? 32 : 0;
                    double speed = level == NORMAL ? 0.2D : level == HARD ? 0.3D : 0.4D;
                    if (way > 0) {
                        X1Danmaku.createSphereShot(this, this, pos(), look(), 0F, speed, speed, 0.0D, Vec3d.ZERO,
                                X1ShotData.shot(X1ShotTables.FORM_MEDIUM, X1ShotTables.BLUE), way, 0.0D, this.tickCount * 13F);
                    }
                }
                if (attackCounter == 1) {
                    useSpellCard(getUsingSpellCardNo());
                } else if (attackCounter >= 180) {
                    attackCounter = 0;
                }
            }
            case SPELLCARD_ATTACK02 -> {
                if (attackCounter == 1) {
                    useSpellCard(getUsingSpellCardNo());
                } else if (attackCounter >= 260) {
                    attackCounter = 0;
                }
            }
            default -> {}
        }
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean hitByPlayer) {
        super.dropCustomDeathLoot(source, looting, hitByPlayer);
        if (hitByPlayer && isSpellCardAttack()) {
            dropShotItem(15 /* ItemTHShot.RICE */, 8 + this.random.nextInt(2) + looting, 5, 32, X1ShotTables.YELLOW, 0, 0, 2);
            dropPowerUpItem(8 + this.random.nextInt(5) + this.random.nextInt(1 + looting));
            dropPointItem(8 + this.random.nextInt(5) + this.random.nextInt(1 + looting));
        }
    }

    /** X1 wraps the base attackEntityFrom once more (another magic reduction, motion × 0.01), as Rumia. */
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

    /** getCanSpawnHere: dark enough, not peaceful, with water within 5 × 5 one below. */
    public static boolean checkWriggleSpawnRules(EntityType<? extends WriggleEntity> type, ServerLevelAccessor level,
                                                 MobSpawnType reason, BlockPos pos, RandomSource random) {
        if (reason == MobSpawnType.SPAWNER || reason == MobSpawnType.SPAWN_EGG || reason == MobSpawnType.COMMAND) return true;
        if (!X1Config.spawnDanmakuMob() || !X1Config.spawnBoss()) return false;
        if (!darkEnough(level, pos, random)) return false;
        for (int i = -2; i <= 2; i++) {
            for (int j = -2; j <= 2; j++) {
                if (level.getBlockState(pos.offset(i, -1, j)).is(Blocks.WATER)) return true;
            }
        }
        return false;
    }
}
