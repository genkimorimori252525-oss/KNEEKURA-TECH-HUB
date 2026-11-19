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
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;

/**
 * Port of X1 {@code EntityToziko} (蘇我屠自古): a two-phase boss (1 × 1.8, 40 HP, 160 XP, ghost). Normal: for
 * the first 20 of every 80 ticks, 1 + level blue arrows with the 「雷矢 ガゴウジサイクロン」 Toziko special from a
 * random unit offset in random directions; a random sidestep at 24. Card 40 at 44 HP only declares. Spawns only
 * in the dark during thunder.
 */
public class TozikoEntity extends DanmakuMobEntity {
    public TozikoEntity(EntityType<? extends TozikoEntity> type, Level level) {
        super(type, level);
        this.xpReward = 160;
        this.setDanmakuPattern(NORMAL_ATTACK01);
        this.setMaxHP(40.0F);
        setHealth(40.0F);
        this.setDanmakuMobName("Soga no Toziko");
        this.setSpecies(SPECIES_PHANTOM_GHOST);
        this.setAttackDistance(14.0D);
        this.setDetectionDistance(12.0D);
        this.setFlyingHeight(2);
        this.isFlyingMode = true;
    }

    @Override
    public int getUsingSpellCardNo() {
        return getDanmakuPattern() == SPELLCARD_ATTACK01 ? 40 : -1;
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
                if (attackCounter % 80 < 20) {
                    X1Danmaku.playShotSound(this);
                    for (int i = 0; i < 1 + level; i++) {
                        X1Danmaku.createShot(this, this, X1Danmaku.pos_Random(pos(), attackCounter * 0.2D),
                                X1Danmaku.angle_Random(new java.util.Random()), 0F, 0.3D, 0.0D, -0.03D, Vec3d.ZERO,
                                X1ShotData.shot(X1ShotTables.FORM_ARROW, X1ShotTables.BLUE, 1, 20, SpecialCards.GagoujiCyclone.SPECIAL_TOZIKO01));
                    }
                } else if (attackCounter == 24) {
                    if (this.random.nextInt(2) == 0) moveRight(this.random.nextDouble() * 0.3D + 0.2D, 16);
                    else moveLeft(this.random.nextDouble() * 0.3D + 0.2D, 16);
                }
                if (attackCounter >= 80) attackCounter = 0;
            }
            case SPELLCARD_ATTACK01 -> {
                if (attackCounter == 1) {
                    useSpellCard(getUsingSpellCardNo());
                } else if (attackCounter >= 200) {
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
            dropShotItem(18 /* ItemTHShot.ARROW */, 8 + this.random.nextInt(2) + looting, 5, 32, X1ShotTables.YELLOW, 0,
                    SpecialCards.GagoujiCyclone.SPECIAL_GAGOUJI01, 2);
            dropPowerUpItem(8 + this.random.nextInt(5) + this.random.nextInt(1 + looting));
            dropPointItem(8 + this.random.nextInt(5) + this.random.nextInt(1 + looting));
        }
    }

    /** getCanSpawnHere: not peaceful, dark enough, and only while it thunders. */
    public static boolean checkTozikoSpawnRules(EntityType<? extends TozikoEntity> type, ServerLevelAccessor level,
                                                MobSpawnType reason, BlockPos pos, RandomSource random) {
        if (reason == MobSpawnType.SPAWNER || reason == MobSpawnType.SPAWN_EGG || reason == MobSpawnType.COMMAND) return true;
        return X1Config.spawnDanmakuMob() && X1Config.spawnBoss() && darkEnough(level, pos, random)
                && level.getLevel().isThundering();
    }
}
