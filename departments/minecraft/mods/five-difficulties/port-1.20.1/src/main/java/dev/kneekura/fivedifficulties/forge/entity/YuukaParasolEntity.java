package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.item.X1ItemEffects;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;

/**
 * Port of X1 {@code EntityYuukaParasol} (幽香の日傘, opened with a sneak right-click): it hangs 1.6 above the
 * user's eyes, a solid 2 × 2 × 2 box. Mode 0 holds it up and cuts the user's fall distance to 0.7 a tick;
 * sneaking after 10 ticks tilts it (mode 1), again folds it (mode 2), again returns it to the inventory.
 *
 * X1 also sets {@code ridingEntity} to the player without mounting, so its {@code updateRidden} (which would
 * slow the player's fall) runs never: 1.7.10 clears the half-made ride on the first world tick. Not ported.
 */
public class YuukaParasolEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_MODE =
            SynchedEntityData.defineId(YuukaParasolEntity.class, EntityDataSerializers.INT);
    public static final int PARASOL_MAX_DAMAGE = 60;
    public Player user;
    public int damage;

    public YuukaParasolEntity(EntityType<? extends YuukaParasolEntity> type, Level level) {
        super(type, level);
        this.noCulling = true;
    }

    public YuukaParasolEntity(Level level, Player player, int damage) {
        this(PortRegistries.YUUKA_PARASOL_ENTITY.get(), level);
        setParasolMode(0);
        this.user = player;
        place(-23F, 0.5D);
        this.setYRot(player.getYRot());
        this.setXRot(0.0F);
        this.damage = damage;
    }

    private void place(float posAngle, double distance) {
        double x = user.getX() - Math.sin((user.getYRot() + posAngle) / 180F * 3.141593F) * Math.cos(user.getXRot() / 180F * 3.141593F) * distance;
        double y = user.getY() - Math.sin(user.getXRot() / 180F * 3.141593F) * Math.cos(posAngle / 180F * 3.141593F) * distance
                + user.getEyeHeight() + 1.6D;
        double z = user.getZ() + Math.cos((user.getYRot() + posAngle) / 180F * 3.141593F) * Math.cos(user.getXRot() / 180F * 3.141593F) * distance;
        this.setPos(x, y, z);
    }

    @Override
    protected AABB makeBoundingBox() {
        return new AABB(getX() - 1.0D, getY() - 1.0D, getZ() - 1.0D, getX() + 1.0D, getY() + 1.0D, getZ() + 1.0D);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_MODE, 0);
    }

    public void setParasolMode(int mode) { this.entityData.set(DATA_MODE, mode); }
    public int getParasolMode() { return this.entityData.get(DATA_MODE); }

    @Override
    public boolean isPushable() {
        return false;
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
        if (!this.level().isClientSide && (user == null || !user.isAlive())) {
            X1ItemEffects.itemEffectFinish(this, user, PortRegistries.YUUKA_PARASOL.get(), damage);
            return;
        }
        float posAngle = -23F;
        double distance = 1.0D;
        float pitch = this.getXRot();
        if (user != null) {
            int mode = getParasolMode();
            if (mode == 0) {
                distance = 0.5F;
                pitch = -user.getXRot();
            } else if (mode == 1) {
                pitch = -user.getXRot() + 40F;
            } else {
                pitch = -user.getXRot() - 90F;
                distance = 0.7D;
            }
            if (mode == 0) {
                if (user.isShiftKeyDown() && this.tickCount > 10) {
                    setParasolMode(1);
                    this.tickCount = 0;
                }
                user.fallDistance *= 0.7F;
            } else if (mode == 1) {
                if (user.isShiftKeyDown() && this.tickCount > 10) {
                    setParasolMode(2);
                    this.tickCount = 0;
                }
            } else if (user.isShiftKeyDown() && this.tickCount > 10) {
                X1ItemEffects.itemEffectFinish(this, user, PortRegistries.YUUKA_PARASOL.get(), damage);
            }
            this.setYRot(user.getYRot());
            place(posAngle, distance); // X1 adds (pos − prevPos), which is always 0 here
        }
        if (!this.level().isClientSide && damage >= PARASOL_MAX_DAMAGE) this.discard();
        this.setXRot(pitch);
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putInt("damage", damage);
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        damage = tag.getInt("damage");
    }
}
