package dev.kneekura.fivedifficulties.forge.entity.mob;

import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityFamiliar}: a 0.6 fairy that rides another entity and fires its pattern as that rider's
 * shooter (the first non-familiar down the riding chain); it takes its target from what it rides, and vanishes
 * when it has no shooter or dies. No sounds, no drops, not collidable.
 */
public class FamiliarEntity extends THFairyEntity {
    public FamiliarEntity(EntityType<? extends FamiliarEntity> type, Level level) {
        super(type, level);
        this.xpReward = 0;
        this.setSpecies(SPECIES_SHIKIGAMI_FAMILIAR);
        this.setAttackDistance(8.0D);
        this.setDetectionDistance(0.0D);
        this.setFlyingHeight(2);
    }

    @Override
    protected void tickDeath() {
        if (!this.level().isClientSide) this.discard();
    }

    @Override
    public LivingEntity getShooter() {
        Entity riding = this.getVehicle();
        if (riding instanceof LivingEntity current) {
            if (current.getHealth() <= 0.0F) return null;
            if (riding instanceof FamiliarEntity) {
                do {
                    if (current.getVehicle() instanceof LivingEntity next) current = next;
                    else return null;
                } while (current.getVehicle() instanceof FamiliarEntity);
                return current;
            }
            return current;
        }
        return null;
    }

    @Override
    public void tick() {
        if (this.tickCount <= lastTime) return;
        if (this.tickCount >= 1 && getShooter() == null) {
            if (!this.level().isClientSide) this.discard();
            return;
        }
        if (this.getVehicle() instanceof Mob riding) setTarget(riding.getTarget());
        super.tick();
    }

    @Override
    protected boolean canFairyCall() { return false; }

    @Override
    protected double getFairyCallDistance() { return 0.0D; }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean hitByPlayer) {}

    @Override
    protected SoundEvent getAmbientSound() { return null; }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) { return null; }

    @Override
    protected SoundEvent getDeathSound() { return null; }

    @Override
    public double getMyRidingOffset() {
        return 0.0D;
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }
}
