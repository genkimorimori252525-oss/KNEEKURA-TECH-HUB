package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotSpecials;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.DyeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.function.Supplier;

/**
 * Port of X1 {@code EntitySukima} (スキマ). A gap warps anything that steps into its 2 × 2.5 × 2 box to
 * the nearest other gap of the same colour (mod 32) more than 5 blocks away (searched within 128), 1.8
 * blocks in front of it, and turns it by the angle between the two gaps; a warped entity is immune for
 * 40 ticks. Colours 0–15 are placed by the Gap item and can be re-dyed or picked up; 16 (the Gap's
 * direct pair) and 32+ (the folding umbrella) close after 24 ticks; 17 is Hikouchuu Nest's laser gap.
 */
public class SukimaEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_COLOR =
            SynchedEntityData.defineId(SukimaEntity.class, EntityDataSerializers.INT);
    /** THKaguyaItems.remorse_rod (arrives with the items; null until then). */
    public static Supplier<Item> remorseRod = () -> null;

    /** userEntity */
    public LivingEntity userEntity;
    private double warpPosX, warpPosY, warpPosZ;
    private float warpAngle;
    private boolean warp;

    public SukimaEntity(EntityType<? extends SukimaEntity> type, Level level) {
        super(type, level);
    }

    /** EntitySukima(world, living, x, y, z, angle): a Gap placed against a block or in the air (colour 1). */
    public static SukimaEntity placed(Level level, LivingEntity user, double x, double y, double z, float angle) {
        SukimaEntity s = new SukimaEntity(PortRegistries.SUKIMA.get(), level);
        s.setPos(x, y, z);
        s.x1SetRotation(angle, 0.0F);
        s.setColor(1);
        s.setNewWarpPoint();
        s.userEntity = user;
        return s;
    }

    /** EntitySukima(world, living, x, y, z, sukimaColor): faces away from the user (direct warps). */
    public static SukimaEntity colored(Level level, LivingEntity user, double x, double y, double z, int sukimaColor) {
        SukimaEntity s = new SukimaEntity(PortRegistries.SUKIMA.get(), level);
        s.setPos(x, y, z);
        float yaw = (float) Math.atan2(x - user.getX(), z - user.getZ()) / 3.141593F * 180F;
        s.x1SetRotation(360F - yaw, 0.0F);
        s.setColor(sukimaColor);
        s.setNewWarpPoint();
        s.userEntity = user;
        return s;
    }

    /** EntitySukima(world, living, x, y, z, angle, sukimaColor) (Hikouchuu Nest). */
    public SukimaEntity(Level level, LivingEntity user, double x, double y, double z, float angle, int sukimaColor) {
        this(PortRegistries.SUKIMA.get(), level);
        this.setPos(x, y, z);
        this.x1SetRotation(angle + 180F, 0.0F);
        this.setColor(sukimaColor);
        this.setNewWarpPoint();
        this.userEntity = user;
    }

    /** 1.7.10 setRotation keeps yaw % 360. */
    private void x1SetRotation(float yaw, float pitch) {
        this.setYRot(yaw % 360.0F);
        this.setXRot(pitch % 360.0F);
        this.yRotO = this.getYRot();
        this.xRotO = this.getXRot();
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
        int color = getColor();
        if ((color == 16 || color >= 32) && this.tickCount > 24 && !this.level().isClientSide) this.discard();
        if (color == 17) {
            if (this.tickCount == 5 && userEntity != null && !this.level().isClientSide) {
                X1Danmaku.createLaserA(userEntity, this, X1Danmaku.pos_Entity(this),
                        X1Danmaku.angle(this.getYRot() - 180F, this.getXRot()), 0.1D, 1.4D, 0.1D,
                        X1Danmaku.gravity_Zero(), X1LaserData.laser(X1ShotTables.PURPLE, 0.1F, 4.0F, 8.0F, 0, 40, 0));
            }
            if (this.tickCount > 9 && !this.level().isClientSide) this.discard();
            return;
        }
        if (this.level().isClientSide) return; // the warp itself only happens on the server
        double minX = getX() - 1.0D, minY = getY() - 1.5D, minZ = getZ() - 1.0D;
        double maxX = getX() + 1.0D, maxY = getY() + 1.0D, maxZ = getZ() + 1.0D;
        for (Entity e : this.level().getEntities(this, this.getBoundingBox().inflate(10.0D))) {
            if (e instanceof SukimaEntity) continue;
            if (!(e.getX() > minX && e.getX() < maxX && e.getY() > minY && e.getY() < maxY
                    && e.getZ() > minZ && e.getZ() < maxZ)) continue;
            setNewWarpPoint();
            if (!warp || e.isOnPortalCooldown()) continue;
            e.xo += warpPosX - e.getX();
            e.yo += warpPosY - e.getY();
            e.zo += warpPosZ - e.getZ();
            if (e instanceof ServerPlayer player) {
                player.connection.teleport(warpPosX, warpPosY, warpPosZ, player.getYRot(), player.getXRot());
            } else {
                e.setPos(warpPosX, warpPosY, warpPosZ);
            }
            if (e instanceof THShotEntity shot && shot.motion() != null) {
                X1ShotMotion m = shot.motion();
                Vec3d move = X1Danmaku.getVecFromAngle(warpAngle - X1ShotSpecials.angleAndAngleSpan(this.getYRot(), m.yaw), m.pitch);
                m.angle = new Vec3d(-move.x(), -move.y(), move.z());
                double speed = m.speed();
                m.motion = m.angle.scale(speed);
                m.lastMotion = m.motion;
            } else {
                // X1 feeds degrees to Math.sin / cos here; kept.
                e.setYRot(e.getYRot() + warpAngle);
                Vec3 v = e.getDeltaMovement();
                e.setDeltaMovement(v.x * -Math.sin(e.getYRot()), v.y, v.z * Math.cos(e.getYRot()));
                e.hurtMarked = true;
            }
            e.setPortalCooldown(40); // timeUntilPortal: two seconds of immunity
            this.level().playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.ENDERMAN_TELEPORT, SoundSource.NEUTRAL,
                    1.0F, 1.0F);
        }
    }

    /** setNewWarpPoint: the nearest same-colour gap beyond 5 blocks; an empty search keeps the old target. */
    public void setNewWarpPoint() {
        var list = this.level().getEntities(this, this.getBoundingBox().inflate(128.0D));
        if (list.isEmpty()) return;
        double nearDistance = 1000.0D;
        SukimaEntity near = null;
        for (Entity e : list) {
            if (e instanceof SukimaEntity s && (getColor() % 32) == (s.getColor() % 32)) {
                double d = this.distanceTo(s);
                if (d < nearDistance && d > 5.0D) {
                    nearDistance = d;
                    near = s;
                }
            }
        }
        if (near != null) {
            float a = near.getYRot() / 180F * 3.141593F;
            warpPosX = near.getX() + Math.sin(a) * 1.8D;
            warpPosY = near.getY();
            warpPosZ = near.getZ() - Math.cos(a) * 1.8D;
            warpAngle = 180F - ((this.getYRot() % 360) - (near.getYRot() % 360));
            warp = true;
        } else {
            warp = false;
        }
    }

    /** interactFirst: dye re-colours a placed gap; the remorse rod or sneaking picks it up as a Gap item. */
    @Override
    public InteractionResult interact(Player player, InteractionHand hand) {
        if (getColor() >= 16) return InteractionResult.PASS;
        ItemStack held = player.getItemInHand(hand);
        if (!this.level().isClientSide) {
            Item rod = remorseRod.get();
            if (held.getItem() instanceof DyeItem dye) {
                this.level().playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ENDERMAN_TELEPORT,
                        SoundSource.PLAYERS, 0.5F, 0.4F);
                setColor(15 - dye.getDyeColor().getId()); // 1.7.10 dye damage order
            } else if ((rod != null && held.is(rod)) || player.isShiftKeyDown()) {
                this.spawnAtLocation(PortRegistries.GAP.get());
                this.discard();
            }
        }
        return InteractionResult.sidedSuccess(this.level().isClientSide);
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
        return getColor() < 16; // the timed gaps live at most 25 ticks and have no user after a reload
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
