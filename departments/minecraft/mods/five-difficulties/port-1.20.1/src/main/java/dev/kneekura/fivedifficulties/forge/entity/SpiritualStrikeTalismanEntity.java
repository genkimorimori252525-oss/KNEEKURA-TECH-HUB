package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.item.X1ItemEffects;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntitySpiritualStrikeTalisman} (霊撃札): lives 4 ticks; each tick everything within
 * {@code ticks × 4} other than the user (and what the user rides) is blown away from it by
 * {@code (range − distance) × 0.1} (living things only, not animals or villagers; upward 0.5 × power), and
 * shots inside turn into their finish bonus. The user is not synced, so a client copy pushes its own player
 * as X1's did.
 */
public class SpiritualStrikeTalismanEntity extends Entity {
    public LivingEntity userEntity;
    private int count;

    public SpiritualStrikeTalismanEntity(EntityType<? extends SpiritualStrikeTalismanEntity> type, Level level) {
        super(type, level);
        this.blocksBuilding = true;
        this.noCulling = true;
    }

    public SpiritualStrikeTalismanEntity(Level level, LivingEntity living) {
        this(PortRegistries.SPIRITUAL_STRIKE_TALISMAN_ENTITY.get(), level);
        this.userEntity = living;
        X1ItemEffects.followUser(this, living, 2.0D, 30F);
    }

    @Override
    protected void defineSynchedData() {}

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public void tick() {
        super.tick();
        if (this.tickCount > 3 && !this.level().isClientSide) this.discard();
        double range = (double) this.tickCount * 4.0D;
        for (Entity entity : this.level().getEntities(this, this.getBoundingBox().inflate(range))) {
            if (entity == userEntity || (userEntity != null && entity.getFirstPassenger() == userEntity)) continue;
            double distance = entity.distanceTo(this);
            if (distance > range) continue;
            Vec3d angle = X1Danmaku.angle_ToPos(new Vec3d(getX(), getY(), getZ()),
                    new Vec3d(entity.getX(), entity.getY(), entity.getZ()));
            double power = (range - distance) * 0.1D;
            if (entity instanceof LivingEntity) {
                if (!(entity instanceof Animal) && !(entity instanceof Villager)) {
                    entity.setDeltaMovement(angle.x() * power, 0.5D * power, angle.z() * power);
                }
            } else if (entity instanceof THShotEntity shot) {
                shot.shotFinishBonus();
            }
        }
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putShort("count", (short) count);
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        count = tag.getShort("count");
    }
}
