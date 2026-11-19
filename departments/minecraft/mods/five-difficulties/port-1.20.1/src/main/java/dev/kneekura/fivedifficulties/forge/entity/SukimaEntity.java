package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntitySukima} as far as the spell cards use it: colour 17 (Hikouchuu Nest) fires
 * one purple laser at tick 5 and closes after tick 9; colours 16 and 32+ (direct-warp gaps) close
 * after tick 24. The coloured warp gaps of the Gap item (warp search, entity warp, dye / remorse-rod
 * interaction) arrive with that item.
 */
public class SukimaEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_COLOR =
            SynchedEntityData.defineId(SukimaEntity.class, EntityDataSerializers.INT);

    /** userEntity */
    public LivingEntity userEntity;

    public SukimaEntity(EntityType<? extends SukimaEntity> type, Level level) {
        super(type, level);
    }

    /** EntitySukima(world, living, x, y, z, angle, sukimaColor) */
    public SukimaEntity(Level level, LivingEntity user, double x, double y, double z, float angle, int sukimaColor) {
        this(PortRegistries.SUKIMA.get(), level);
        this.setPos(x, y, z);
        // setRotation(angle + 180F, 0F): 1.7.10 keeps yaw % 360.
        this.setYRot((angle + 180F) % 360.0F);
        this.setXRot(0.0F);
        this.yRotO = this.getYRot();
        this.setColor(sukimaColor);
        this.userEntity = user;
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
        super.tick();
        if (this.level().isClientSide) return; // X1 removes / fires on the server only
        int color = getColor();
        if ((color == 16 || color >= 32) && this.tickCount > 24) this.discard();
        if (color == 17) {
            if (this.tickCount == 5 && userEntity != null) {
                X1Danmaku.createLaserA(userEntity, this, X1Danmaku.pos_Entity(this),
                        X1Danmaku.angle(this.getYRot() - 180F, this.getXRot()), 0.1D, 1.4D, 0.1D,
                        X1Danmaku.gravity_Zero(), X1LaserData.laser(X1ShotTables.PURPLE, 0.1F, 4.0F, 8.0F, 0, 40, 0));
            }
            if (this.tickCount > 9) this.discard();
        }
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean isPickable() {
        return true;
    }

    @Override
    public boolean shouldBeSaved() {
        return getColor() < 16; // the timed spell-card gaps live at most 25 ticks and have no user after a reload
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        setColor(tag.getShort("color"));
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putShort("color", (short) getColor());
    }
}
