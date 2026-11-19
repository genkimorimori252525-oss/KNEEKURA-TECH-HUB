package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.item.X1ItemEffects;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityPendulum} (ナズーリンペンデュラム): hangs 1.2 ahead, 30° to the left of the user at
 * eye height − 0.5. Every 60 ticks it counts the blocks named like the searched block in a cube of ±12
 * (sneak mode ±24) around it, capped at 32; the count turns it (count / 3 degrees per tick) and widens its
 * swing in the renderer. It returns to the inventory when the user sneaks after 10 ticks or is hurt.
 *
 * X1 compares localized names; the port compares the block's translation key, so 1.7.10 metadata variants
 * that shared a name (all wool colours, say) are separate blocks here.
 */
public class PendulumEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_ANGLE =
            SynchedEntityData.defineId(PendulumEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_COUNT =
            SynchedEntityData.defineId(PendulumEntity.class, EntityDataSerializers.INT);
    public Player user;
    private int mode;
    private int searchLength;
    private int count;
    private String searchBlockName = "";

    public PendulumEntity(EntityType<? extends PendulumEntity> type, Level level) {
        super(type, level);
        this.blocksBuilding = true;
    }

    public PendulumEntity(Level level, Player player, int mode, String blockKey) {
        this(PortRegistries.PENDULUM_ENTITY.get(), level);
        this.user = player;
        X1ItemEffects.followUser(this, user, 1.2D, -30F, false, (double) user.getEyeHeight() - 0.5D);
        this.mode = mode;
        this.searchLength = mode == 1 ? 24 : 12;
        this.searchBlockName = blockKey;
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_ANGLE, 0);
        this.entityData.define(DATA_COUNT, 0);
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    private void finish() {
        if (user != null && user.getAbilities().instabuild) {
            this.discard();
            return;
        }
        ItemStack back = new ItemStack(PortRegistries.NAZRIN_PENDULUM.get());
        if (user != null) {
            if (!user.getInventory().add(back) && !this.level().isClientSide) user.drop(back, false);
        } else if (!this.level().isClientSide) {
            this.spawnAtLocation(back);
        }
        this.discard();
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide && user == null) finish();
        if (!this.level().isClientSide && user != null) {
            if (this.tickCount > 10 && user.isShiftKeyDown()) finish();
            if (user.hurtTime > 0) finish();
        }
        if (count % 60 == 0 && !this.level().isClientSide) {
            int found = 0;
            int x0 = (int) getX() - searchLength, z0 = (int) getZ() - searchLength, y0 = (int) getY() - searchLength;
            int x1 = x0 + searchLength * 2 + 1, y1 = y0 + searchLength * 2 + 1, z1 = z0 + searchLength * 2 + 1;
            BlockPos.MutableBlockPos at = new BlockPos.MutableBlockPos();
            for (int si = x0; si < x1; si++) {
                for (int sk = z0; sk < z1; sk++) {
                    for (int sj = y0; sj < y1; sj++) {
                        if (this.level().getBlockState(at.set(si, sj, sk)).getBlock().getDescriptionId().equals(searchBlockName)) {
                            found++;
                        }
                    }
                }
            }
            if (found > 32) found = 32;
            setSearchCount(found);
        }
        if (getSearchCount() != 0) {
            setSearchAngle(getSearchAngle() + (float) getSearchCount() / 3.0F);
            this.setYRot(this.getYRot() + 3.0F);
        }
        if (user != null) X1ItemEffects.followUser(this, user, 1.2D, -30F, false, (double) user.getEyeHeight() - 0.5D);
        count++;
    }

    public void setSearchAngle(float angle) {
        this.entityData.set(DATA_ANGLE, (int) (angle * 100.0F));
    }

    public float getSearchAngle() {
        return (float) this.entityData.get(DATA_ANGLE) / 100.0F;
    }

    public void setSearchCount(int n) {
        this.entityData.set(DATA_COUNT, n);
    }

    public int getSearchCount() {
        return this.entityData.get(DATA_COUNT);
    }

    public int mode() {
        return mode;
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}
}
