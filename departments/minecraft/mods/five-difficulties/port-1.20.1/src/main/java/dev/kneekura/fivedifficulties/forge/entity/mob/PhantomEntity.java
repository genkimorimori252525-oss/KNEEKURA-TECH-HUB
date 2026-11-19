package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.X1Config;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.ServerLevelAccessor;

/**
 * Port of X1 {@code EntityTHPhantom} (幽霊): a 1 × 1 fairy-pattern ghost, form 0..7 (its colour), speed 0.18,
 * attack 6, detection 30, flying 3, silent. In bright sky light it may simply die; it leaves no corpse. Drops the
 * fairy loot and then its own (the same again plus 1 in 10 a soul torch). Spawns in the dark like monsters.
 */
public class PhantomEntity extends THFairyEntity {
    public PhantomEntity(EntityType<? extends PhantomEntity> type, Level level) {
        super(type, level);
        this.lastTime = 0;
        this.xpReward = 5;
        setForm((byte) this.random.nextInt(8));
        this.setSpeed(0.18D);
        this.setSpecies(SPECIES_PHANTOM);
        this.isFlyingMode = true;
        this.setAttackDistance(6.0D);
        this.setDetectionDistance(30.0D);
        this.setFlyingHeight(3);
    }

    @Override
    public void tickDeath() {
        if (!this.level().isClientSide) this.discard();
    }

    @Override
    public void tick() {
        if (this.getHealth() <= 0) this.setDeltaMovement(0, 0, 0);
        if (this.tickCount <= lastTime) return;
        super.tick();
        if (this.attackCounter > danmakuSpan) attackCounter = 0;
        float f = this.getLightLevelDependentMagicValue();
        if (f > 0.5F && this.random.nextFloat() * 30.0F < (f - 0.4F) * 2.0F && this.level().canSeeSky(this.blockPosition())) {
            setHealth(0.0F);
        }
    }

    @Override
    protected boolean canFairyCall() { return false; }

    @Override
    protected double getFairyCallDistance() { return 0.0D; }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean hitByPlayer) {
        super.dropCustomDeathLoot(source, looting, hitByPlayer);
        if (getForm() < 0) return;
        if (hitByPlayer) {
            dropShotItem(0, this.random.nextInt(2) + looting, 3, 0, X1ShotTables.RED, 0, 0, 2);
            dropPowerUpItem(this.random.nextInt(5) + this.random.nextInt(1 + looting));
            dropPointItem(this.random.nextInt(5) + this.random.nextInt(1 + looting));
            int torches = (this.random.nextInt(10) / 9) + this.random.nextInt(1 + looting);
            if (torches > 0) this.spawnAtLocation(new ItemStack(PortRegistries.SOUL_TORCH.get(), torches), 0.0F);
        }
    }

    @Override
    public int getMaxSpawnClusterSize() { return 10; }

    @Override
    protected float getSoundVolume() { return 0.0F; }

    /** getCanSpawnHere: not peaceful and isValidLightLevel (sky ≤ rand 32, light ≤ rand 8, thunder darkens to 10). */
    public static boolean checkPhantomSpawnRules(EntityType<? extends PhantomEntity> type, ServerLevelAccessor level,
                                                 MobSpawnType reason, BlockPos pos, RandomSource random) {
        if (reason == MobSpawnType.SPAWNER || reason == MobSpawnType.SPAWN_EGG || reason == MobSpawnType.COMMAND) return true;
        if (!X1Config.spawnDanmakuMob() || !X1Config.spawnPhantom()) return false;
        if (level.getDifficulty() == Difficulty.PEACEFUL) return false;
        if (level.getBrightness(LightLayer.SKY, pos) > random.nextInt(32)) return false;
        int light = level.getLevel().isThundering() ? level.getMaxLocalRawBrightness(pos, 10) : level.getMaxLocalRawBrightness(pos);
        return light <= random.nextInt(8);
    }
}
