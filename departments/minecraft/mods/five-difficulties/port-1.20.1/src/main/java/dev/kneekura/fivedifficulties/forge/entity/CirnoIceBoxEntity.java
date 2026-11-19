package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;

/**
 * Port of X1 {@code EntityCirnoIceBox}: a solid ice box around a living thing hit by the icicle sword. Each tick
 * the frozen one is put back where it was, its motion all but stopped, its look and age held, a creeper's
 * fuse wound back. After 50 ticks the box melts 0.08 a tick and is gone at height −0.7.
 *
 * Not ported: X1 also bumps 1.7.10 {@code attackTime} (no 1.20 field), rewinds a ghast's attack counter (private
 * in 1.20) and melts twice as fast around Cirno (P17 mob).
 */
public class CirnoIceBoxEntity extends net.minecraft.world.entity.Entity {
    private static final EntityDataAccessor<Float> DATA_WIDTH =
            SynchedEntityData.defineId(CirnoIceBoxEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Float> DATA_HEIGHT =
            SynchedEntityData.defineId(CirnoIceBoxEntity.class, EntityDataSerializers.FLOAT);
    public LivingEntity frozen;
    private int count;

    public CirnoIceBoxEntity(EntityType<? extends CirnoIceBoxEntity> type, Level level) {
        super(type, level);
        this.blocksBuilding = true;
    }

    public CirnoIceBoxEntity(Level level, LivingEntity frozen) {
        this(PortRegistries.CIRNO_ICE_BOX.get(), level);
        this.frozen = frozen;
        setIceBoxWidth(1.0F);
        setIceBoxHeight(frozen.getBbHeight());
        this.setPos(frozen.getX(), frozen.getY(), frozen.getZ());
        float w = getIceBoxWidth() + 0.8F, h = getIceBoxHeight() + 0.8F;
        this.setBoundingBox(new AABB(getX() - w / 2, getY(), getZ() - w / 2, getX() + w / 2, getY() + h, getZ() + w / 2));
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_WIDTH, 0.5F);
        this.entityData.define(DATA_HEIGHT, 0.5F);
    }

    protected void setIceBoxWidth(float width) {
        this.entityData.set(DATA_WIDTH, width);
    }

    public float getIceBoxWidth() {
        return this.entityData.get(DATA_WIDTH);
    }

    protected void setIceBoxHeight(float height) {
        this.entityData.set(DATA_HEIGHT, height);
    }

    public float getIceBoxHeight() {
        return this.entityData.get(DATA_HEIGHT);
    }

    @Override
    public boolean isPushable() {
        return true;
    }

    @Override
    public boolean isPickable() {
        return true;
    }

    @Override
    public boolean canBeCollidedWith() {
        return true;
    }

    @Override
    public void tick() {
        super.tick();
        if (frozen != null && !frozen.isRemoved()) { // X1 isDead = removed (a dying mob stays frozen)
            float w = getIceBoxWidth(), h = getIceBoxHeight();
            double minX = frozen.getX() - (double) w / 2.0D, minZ = frozen.getZ() - (double) w / 2.0D;
            this.setBoundingBox(new AABB(minX, frozen.getY(), minZ, minX + w, frozen.getY() + h, minZ + w));
            frozenInIce();
        }
        if (this.tickCount > 50) setIceBoxHeight(getIceBoxHeight() - 0.08F);
        if (getIceBoxHeight() <= -0.7F && !this.level().isClientSide) this.discard();
    }

    protected void frozenInIce() {
        frozen.setPos(frozen.xo, frozen.yo, frozen.zo);
        var m = frozen.getDeltaMovement();
        frozen.setDeltaMovement(m.x * 0.000000001D, m.y * 0.000000001D, m.z * 0.000000001D);
        frozen.setYRot(frozen.yRotO);
        frozen.setXRot(frozen.xRotO);
        frozen.tickCount--;
        frozen.yHeadRot = frozen.yHeadRotO;
        if (frozen.isRemoved()) frozen.deathTime = 0;
        if (frozen instanceof Creeper creeper) creeper.setSwellDir(-1);
        if (frozen instanceof TamableAnimal) {
            var t = frozen.getDeltaMovement();
            frozen.setDeltaMovement(t.x, t.y - 0.000001D, t.z);
        }
        if (frozen instanceof ServerPlayer player) {
            player.connection.teleport(player.xo, player.yo, player.zo, player.getYRot(), player.getXRot());
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
