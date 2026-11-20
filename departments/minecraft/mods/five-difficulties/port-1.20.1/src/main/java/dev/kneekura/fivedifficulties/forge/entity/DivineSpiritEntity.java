package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityDivineSpirit} (小神霊, 1.2 × 1.2): left at a creature's eyes by the Toyosatomimi sword.
 * It drifts toward the nearest player within 10 (speeding up by 0.03 a tick to 0.5; slowing the same way with
 * nobody near, along its last heading) and is gone after 300 ticks. Touching a player gives that player the
 * Divine Spirit block of its colour (if there is room, with the pickup pop) and removes the spirit either way.
 */
public class DivineSpiritEntity extends Entity {
    private static final EntityDataAccessor<Integer> COUNT = SynchedEntityData.defineId(DivineSpiritEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> COLOR = SynchedEntityData.defineId(DivineSpiritEntity.class, EntityDataSerializers.INT);
    private double speed;

    public DivineSpiritEntity(EntityType<? extends DivineSpiritEntity> type, Level level) {
        super(type, level);
        this.noPhysics = true;
    }

    public DivineSpiritEntity(Level level, double x, double y, double z, int color) {
        this(PortRegistries.DIVINE_SPIRIT.get(), level);
        setDivineSpiritColor(color);
        setDivineSpiritCount(0);
        this.moveTo(x, y, z, 0.0F, 0.0F);
        this.speed = 0.0D;
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(COUNT, 0);
        this.entityData.define(COLOR, 0);
    }

    public int getDivineSpiritCount() { return this.entityData.get(COUNT); }
    public void setDivineSpiritCount(int c) { this.entityData.set(COUNT, c); }
    public int getDivineSpiritColor() { return this.entityData.get(COLOR); }
    public void setDivineSpiritColor(int c) { this.entityData.set(COLOR, c); }

    @Override
    public void tick() {
        super.tick();
        if (getDivineSpiritCount() > 300 && !this.level().isClientSide) this.discard();
        setDivineSpiritCount(getDivineSpiritCount() + 1);
        double distance = 999.0D;
        Player nearPlayer = null;
        for (Entity e : this.level().getEntities(this, this.getBoundingBox().inflate(10.0D))) {
            if (e instanceof Player p && distance > p.distanceTo(this)) {
                distance = p.distanceTo(this);
                nearPlayer = p;
            }
        }
        if (nearPlayer != null) {
            if (speed < 0.5D) speed += 0.03D;
            double dx = nearPlayer.getX() - getX(), dz = nearPlayer.getZ() - getZ();
            this.setYRot((float) Math.atan2(dx, dz) / (float) Math.PI * 180F);
            this.setXRot((float) Math.atan2(nearPlayer.getY() + nearPlayer.getEyeHeight() - getY(), Math.sqrt(dx * dx + dz * dz))
                    / (float) Math.PI * 180F);
        } else {
            speed -= 0.03D;
            if (speed < 0.0D) speed = 0.0D;
        }
        Vec3d vec = X1Danmaku.getVecFromAngle(getYRot(), getXRot(), speed);
        this.setPos(getX() - vec.x(), getY() - vec.y(), getZ() + vec.z());
    }

    /** onCollideWithPlayer. */
    @Override
    public void playerTouch(Player player) {
        if (this.level().isClientSide) return;
        int c = getDivineSpiritColor();
        if (c >= 0 && c < PortRegistries.DIVINE_SPIRIT_ITEMS.size()
                && player.getInventory().add(new ItemStack(PortRegistries.DIVINE_SPIRIT_ITEMS.get(c).get()))) {
            this.playSound(SoundEvents.ITEM_PICKUP, 4.0F, ((this.random.nextFloat() - this.random.nextFloat()) * 0.7F + 1.0F) * 0.3F);
            player.take(this, 1);
        }
        this.discard();
    }

    @Override
    public boolean isPickable() { return true; }

    @Override
    public boolean isPushable() { return false; }

    @Override
    public boolean shouldRenderAtSqrDistance(double d) {
        double d1 = this.getBoundingBox().getSize() * 4D * 64D;
        return d < d1 * d1;
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putShort("color", (short) getDivineSpiritColor());
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        setDivineSpiritColor(tag.getShort("color"));
    }
}
