package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Port of X1 {@code EntityTHItem}: the power / point / bomb / extend bonuses danmaku mobs drop. For 16
 * ticks it only drifts (×0.87 sideways, falling to at most 0.2); after that it is a shot material that
 * only homes on a sneaking player (at 0.3). Landing on top of a block removes it, as in X1.
 */
public class THItemEntity extends ShotMaterialEntity {
    public static final byte ITEM_ID_SHOTMATERIAL = 0, ITEM_ID_SMALLPOWER = 1, ITEM_ID_BIGPOWER = 2, ITEM_ID_POINT = 4,
            ITEM_ID_BOMB = 10, ITEM_ID_EXTEND = 11;
    private static final EntityDataAccessor<Byte> DATA_TYPE =
            SynchedEntityData.defineId(THItemEntity.class, EntityDataSerializers.BYTE);

    public THItemEntity(EntityType<? extends THItemEntity> type, Level level) {
        super(type, level);
        this.limitSpeed = 0.5D;
    }

    public THItemEntity(Level level, double x, double y, double z, Vec3d angle, byte itemId) {
        this(PortRegistries.TH_ITEM.get(), level);
        this.moveTo(x, y, z, 0F, 0F);
        this.lastTime = -1;
        setItemType(itemId);
        this.limitSpeed = 0.5D;
        this.lastMotionX = angle.x() * limitSpeed;
        this.lastMotionY = angle.y() * limitSpeed;
        this.lastMotionZ = angle.z() * limitSpeed;
        this.setDeltaMovement(lastMotionX, lastMotionY, lastMotionZ);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_TYPE, (byte) 0);
    }

    public void setItemType(byte id) {
        this.entityData.set(DATA_TYPE, id);
    }

    public byte getItemType() {
        return this.entityData.get(DATA_TYPE);
    }

    @Override
    public void tick() {
        if (this.level().isClientSide) return;
        if (this.tickCount > 16) super.tick();
        if (target != null || this.isRemoved()) return;
        double mx, my, mz;
        if (this.tickCount <= lastTime) {
            this.setDeltaMovement(0, 0, 0);
            return;
        }
        mx = lastMotionX;
        my = lastMotionY;
        mz = lastMotionZ;
        mx = Math.abs(mx) < 0.01 ? 0.0D : mx * 0.87D;
        mz = Math.abs(mz) < 0.01 ? 0.0D : mz * 0.87D;
        if (my > -0.2D) my -= 0.03D;
        if (my < -0.2D) my = -0.2D;
        double px = getX() + mx, py = getY() + my, pz = getZ() + mz;
        Vec3 start = new Vec3(px, py, pz);
        Vec3 end = new Vec3(px + mx, py + my, pz + mz);
        BlockHitResult hit = this.level().clip(new ClipContext(start, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        if (hit.getType() != HitResult.Type.MISS) {
            // X1's switch has no breaks: sides 2..5 fall through, flipping some motions twice.
            int side = hit.getDirection().ordinal();
            if (side == 0) {
                my = 0.0D;
                py = hit.getBlockPos().getY();
            } else if (side == 1) {
                this.discard();
            } else {
                if (side <= 2) { mz = -mz; pz = hit.getBlockPos().getZ(); }
                if (side <= 3) { mz = -mz; pz = hit.getBlockPos().getZ(); }
                if (side <= 4) { mx = -mx; px = hit.getBlockPos().getX(); }
                mx = -mx;
                px = hit.getBlockPos().getX();
            }
        }
        lastMotionX = mx;
        lastMotionY = my;
        lastMotionZ = mz;
        this.setDeltaMovement(mx, my, mz);
        this.setPos(px, py, pz);
    }

    /** Only a sneaking player draws it in. */
    @Override
    protected boolean check(Player player) {
        return player.isShiftKeyDown();
    }

    @Override
    protected void moveToPlayer(Player player) {
        limitSpeed = 0.3D;
        super.moveToPlayer(player);
    }

    @Override
    public void playerTouch(Player player) {
        if (this.level().isClientSide) return;
        boolean got = switch (getItemType()) {
            case ITEM_ID_SMALLPOWER -> player.getInventory().add(new ItemStack(PortRegistries.POWER_ITEM_SMALL.get()));
            case ITEM_ID_BIGPOWER -> player.getInventory().add(new ItemStack(PortRegistries.POWER_ITEM_BIG.get()));
            case ITEM_ID_POINT -> player.getInventory().add(new ItemStack(PortRegistries.POINT_ITEM.get()));
            case ITEM_ID_BOMB -> giveOrDrop(player, PortRegistries.BOMB_ITEM.get());
            case ITEM_ID_EXTEND -> giveOrDrop(player, PortRegistries.EXTEND_ITEM.get());
            default -> false;
        };
        if (got) {
            pop();
            player.take(this, 1);
        }
        this.discard();
    }

    /** Bombs and extends are never lost: a full inventory drops them at the player. */
    private static boolean giveOrDrop(Player player, Item item) {
        boolean got = player.getInventory().add(new ItemStack(item));
        if (!got) player.drop(new ItemStack(item), false);
        return got;
    }
}
