package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;

/**
 * Port of X1 {@code EntitySunFlowerFairy}: a larger fairy (0.9 × 1.7, 20 HP, 30 XP, form 10) that spawns with a
 * familiar riding it and drops more: medium green shots, power and point items, and 5% an extend or else 25% a
 * spell-card bonus. Its fairy drops come first (X1 calls the fairy's drops, then its own).
 */
public class SunFlowerFairyEntity extends THFairyEntity {
    public SunFlowerFairyEntity(EntityType<? extends SunFlowerFairyEntity> type, Level level) {
        super(type, level);
        this.xpReward = 30;
        setForm((byte) 10);
        this.setMaxHP(20.0F);
        this.setHealth(20.0F);
    }

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, MobSpawnType reason,
                                        SpawnGroupData data, CompoundTag tag) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data, tag);
        FamiliarEntity familiar = PortRegistries.FAMILIAR.get().create(level.getLevel());
        if (familiar != null) {
            familiar.moveTo(getX(), getY(), getZ(), getYRot(), 0.0F);
            level.addFreshEntity(familiar);
            familiar.startRiding(this, true);
        }
        return result;
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean hitByPlayer) {
        super.dropCustomDeathLoot(source, looting, hitByPlayer);
        if (getForm() < 0) return;
        if (hitByPlayer) {
            dropShotItem(2, this.random.nextInt(12) + looting * 2, 7, 8, X1ShotTables.GREEN, 0, 0, 2);
            dropPowerUpItem(this.random.nextInt(20) + this.random.nextInt(3 + looting * 2));
            dropPointItem(this.random.nextInt(20) + this.random.nextInt(3 + looting * 2));
            if (this.random.nextInt(100) < 5) dropItem(11, pos(), angle(getYRot(), -90F));
            else if (this.random.nextInt(100) < 25) dropItem(10, pos(), angle(getYRot(), -90F));
        }
    }

    @Override
    public int getMaxSpawnClusterSize() { return 3; }
}
