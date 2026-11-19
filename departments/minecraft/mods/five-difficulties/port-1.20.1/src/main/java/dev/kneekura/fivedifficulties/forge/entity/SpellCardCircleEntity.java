package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntitySpellCardCircle}: the magic circle under a player declaring a spell card.
 * It grows over 5 ticks, then (types below 16) shrinks to nothing at its end time.
 */
public final class SpellCardCircleEntity extends Entity {
    // X1 DataWatcher 19..22
    private static final EntityDataAccessor<Float> DATA_SIZE =
            SynchedEntityData.defineId(SpellCardCircleEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Integer> DATA_TYPE =
            SynchedEntityData.defineId(SpellCardCircleEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_END =
            SynchedEntityData.defineId(SpellCardCircleEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_ANIMATION =
            SynchedEntityData.defineId(SpellCardCircleEntity.class, EntityDataSerializers.INT);

    private LivingEntity user;
    private int lastTime;

    public SpellCardCircleEntity(EntityType<? extends SpellCardCircleEntity> type, Level level) {
        super(type, level);
        this.noCulling = true; // ignoreFrustumCheck
    }

    public SpellCardCircleEntity(Level level, LivingEntity user, int type, int end) {
        this(PortRegistries.SPELL_CARD_CIRCLE.get(), level);
        this.user = user;
        setCircleType(type);
        setEndTime(end);
        follow();
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_SIZE, 0F);
        this.entityData.define(DATA_TYPE, 0);
        this.entityData.define(DATA_END, 0);
        this.entityData.define(DATA_ANIMATION, 0);
    }

    public float getCircleSize() { return this.entityData.get(DATA_SIZE); }
    public void setCircleSize(float size) { this.entityData.set(DATA_SIZE, size); }
    public int getCircleType() { return this.entityData.get(DATA_TYPE); }
    public void setCircleType(int type) { this.entityData.set(DATA_TYPE, type); }
    public int getEndTime() { return this.entityData.get(DATA_END); }
    public void setEndTime(int time) { this.entityData.set(DATA_END, time); }
    public int getAnimationCount() { return this.entityData.get(DATA_ANIMATION); }
    public void setAnimationCount(int count) { this.entityData.set(DATA_ANIMATION, count); }

    private void follow() {
        double y = user instanceof Player ? user.getY() + 0.1D : user.getY() + user.getBbHeight() / 2.0D;
        this.setPos(user.getX(), y, user.getZ());
        float yaw = user.getYHeadRot(), pitch = user.getXRot();
        if (yaw > 180F) yaw -= 360F;
        if (yaw < -180F) yaw += 360F;
        if (pitch > 180F) pitch -= 360F;
        if (pitch < -180F) pitch += 360F;
        this.setYRot(yaw);
        this.setXRot(pitch);
    }

    @Override
    public void tick() {
        if (!this.level().isClientSide && user == null) {
            this.discard();
            return;
        }
        super.tick();
        if (this.tickCount <= lastTime) return;
        if (this.level().isClientSide) return;
        setAnimationCount(lastTime);
        if (getEndTime() < this.tickCount && getEndTime() >= 0) this.discard();
        if (getAnimationCount() < 5) {
            setCircleSize(((float) getAnimationCount()) / 5.0F);
        } else if (getCircleType() < 16) {
            float endTime2 = (float) getEndTime();
            setCircleSize((endTime2 - (float) getAnimationCount()) / endTime2);
        }
        follow();
        if (this.tickCount > lastTime) lastTime = this.tickCount;
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}
}
