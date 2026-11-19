package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityShotMaterial}: the bonus left by a cancelled shot. Server side it locks on to
 * the nearest player within 20 blocks that {@link #check} accepts (and vanishes when there is no player
 * at all), accelerates toward them without drag, and turns into a Shot Material item on contact. Lives
 * at most 300 ticks. {@code EntityTHItem} (power / point / bomb / extend) builds on it.
 */
public class ShotMaterialEntity extends Entity {
    protected int lastTime;
    private double lastSpeed;
    private double speed;
    protected double limitSpeed;
    protected double lastMotionX, lastMotionY, lastMotionZ;
    protected Player target;

    public ShotMaterialEntity(EntityType<? extends ShotMaterialEntity> type, Level level) {
        super(type, level);
        this.noPhysics = true;
        this.limitSpeed = 0.5D;
        this.lastTime = -1;
    }

    public ShotMaterialEntity(Level level, double x, double y, double z) {
        this(PortRegistries.SHOT_MATERIAL_ENTITY.get(), level);
        this.moveTo(x, y, z, 0F, 0F);
    }

    @Override
    protected void defineSynchedData() {}

    @Override
    public void tick() {
        if (this.level().isClientSide) return;
        if (this.tickCount < lastTime) {
            this.setDeltaMovement(0, 0, 0);
            lastSpeed = 0.0D;
            return;
        }
        super.tick();
        this.setDeltaMovement(lastMotionX, lastMotionY, lastMotionZ);
        speed = lastSpeed;
        if (this.tickCount > 300) this.discard();
        if (target == null) {
            Player near = null;
            double distance = 999.0D;
            for (Entity e : this.level().getEntities(this, this.getBoundingBox().inflate(20.0D))) {
                if (e instanceof Player p && distance > p.distanceTo(this)) {
                    distance = p.distanceTo(this);
                    near = p;
                }
            }
            if (near != null) {
                if (check(near)) target = near;
            } else {
                this.discard();
            }
        }
        if (target != null) moveToPlayer(target);
        this.setPos(getX(), getY(), getZ());
        if (this.tickCount > lastTime) {
            var m = this.getDeltaMovement();
            lastMotionX = m.x;
            lastMotionY = m.y;
            lastMotionZ = m.z;
            lastSpeed = speed;
        }
    }

    /** May this player draw the bonus in? */
    protected boolean check(Player player) {
        return true;
    }

    /** moveToPlayer: speed ramps by 0.1, but the motion always gains direction × limitSpeed (no drag). */
    protected void moveToPlayer(Player player) {
        speed = speed < limitSpeed ? speed + 0.1D : limitSpeed;
        double dx = player.getX() - getX(), dz = player.getZ() - getZ();
        this.setXRot((float) Math.atan2(player.getY() + player.getEyeHeight() - getY(), Math.sqrt(dx * dx + dz * dz))
                / (float) Math.PI * 180F);
        Vec3d dir = X1Danmaku.angle_ToPos(X1Danmaku.pos_Entity(this), X1Danmaku.pos_Living(player));
        var motion = this.getDeltaMovement().add(dir.x() * limitSpeed, dir.y() * limitSpeed, dir.z() * limitSpeed);
        this.setDeltaMovement(motion);
        this.setPosRaw(getX() + motion.x, getY() + motion.y, getZ() + motion.z);
    }

    @Override
    public void playerTouch(Player player) {
        if (this.level().isClientSide) return;
        if (player.getInventory().add(new ItemStack(PortRegistries.SHOT_MATERIAL.get()))) {
            pop();
            player.take(this, 1);
        }
        this.discard();
    }

    /** "random.pop", 4.0, ((r - r) × 0.7 + 1) × 0.3 */
    protected void pop() {
        this.level().playSound(null, getX(), getY(), getZ(), SoundEvents.ITEM_PICKUP, SoundSource.PLAYERS, 4.0F,
                ((random.nextFloat() - random.nextFloat()) * 0.7F + 1.0F) * 0.3F);
    }

    @Override
    public boolean isPickable() {
        return true;
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
