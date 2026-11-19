package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityMiracleCircle}: the pentagram drawn 3 blocks in front of a player charging
 * the wind gohei. Each one takes 30 ticks (a line per 6) and starts the next colour (up to five), then
 * circles the player's view at 2.4° per tick; all vanish when the player stops using the item.
 */
public class MiracleCircleEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_COLOR =
            SynchedEntityData.defineId(MiracleCircleEntity.class, EntityDataSerializers.INT);

    public Player user;
    public int count;
    public float turnAngle;
    public int befUseCount;

    public MiracleCircleEntity(EntityType<? extends MiracleCircleEntity> type, Level level) {
        super(type, level);
    }

    public MiracleCircleEntity(Level level, Player player, int color) {
        this(PortRegistries.MIRACLE_CIRCLE.get(), level);
        this.user = player;
        Vec3d v = X1Danmaku.getRotationVectorFromAngle(player.getYRot(), player.getXRot(), turnAngle, 3.0D);
        this.setPos(player.getX() + v.x(), player.getY() + v.y() + player.getEyeHeight(), player.getZ() + v.z());
        this.setYRot(player.getYRot());
        this.setXRot(0.0F);
        setColor(color);
        count = 0;
        befUseCount = 0;
        turnAngle = 0F;
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_COLOR, 0);
    }

    public int getColor() {
        return this.entityData.get(DATA_COLOR);
    }

    public void setColor(int color) {
        this.entityData.set(DATA_COLOR, color);
    }

    @Override
    public void tick() {
        if (!this.level().isClientSide && user == null) this.discard();
        super.tick();
        if (user != null && !user.isUsingItem()) {
            // X1 checks -befUseCount >= 250 for Yasaka's Divine Wind here, with the wind commented out.
            if (!this.level().isClientSide) this.discard();
        }
        count++;
        if (count == 30 && getColor() < 4 && user != null && !this.level().isClientSide) {
            this.level().addFreshEntity(new MiracleCircleEntity(this.level(), user, getColor() + 1));
        }
        float yaw = getYRot(), pitch = getXRot();
        if (user != null) {
            Vec3d v = X1Danmaku.getRotationVectorFromAngle(user.getYRot(), user.getXRot(), turnAngle, 3.0D);
            this.setPos(user.getX() + v.x(), user.getY() + v.y() + user.getEyeHeight(), user.getZ() + v.z());
            yaw = user.getYRot();
            pitch = user.getXRot();
            befUseCount = getColor() * 30 + count;
        }
        if (count > 30) turnAngle += 2.4F;
        if (yaw > 180F) yaw -= 360F;
        if (yaw < -180F) yaw += 360F;
        if (pitch > 180F) pitch -= 360F;
        if (pitch < -180F) pitch += 360F;
        this.setYRot(yaw);
        this.setXRot(pitch);
    }

    /** Lines drawn so far (5 once complete). */
    public int getNumberOfDrewLine() {
        return count > 30 ? 5 : count / 6 + 1;
    }

    /** Progress of the line being drawn, in tenths (10 once complete). */
    public int getLastLineTime() {
        return count > 30 ? 10 : count % 6;
    }

    @Override
    public boolean shouldBeSaved() {
        return false; // X1 saves nothing and the user is gone after a reload
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}
}
