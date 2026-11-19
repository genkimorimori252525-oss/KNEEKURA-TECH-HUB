package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotSpecials;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1ShotSpawner;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Port of X1 {@code EntityShotMaterial}: the bonus left by a cancelled shot. Server side it locks on
 * to the nearest player within 20 blocks (or vanishes when there is none), accelerates toward them
 * without drag, and turns into a Shot Material item on contact. Lives at most 300 ticks.
 */
public final class ShotMaterialEntity extends Entity {
    private static final double LIMIT_SPEED = 0.5D;

    private Player target;
    private double speed;

    public ShotMaterialEntity(EntityType<? extends ShotMaterialEntity> type, Level level) {
        super(type, level);
        this.noPhysics = true;
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
        if (this.tickCount > 300) {
            this.discard();
        }
        if (target == null) {
            Player near = null;
            double distance = 999.0D;
            for (Entity e : this.level().getEntities(this, this.getBoundingBox().inflate(20.0D))) {
                if (e instanceof Player p && distance > p.distanceTo(this)) {
                    distance = p.distanceTo(this);
                    near = p;
                }
            }
            if (near != null) target = near;
            else this.discard();
        }
        if (target != null) moveToPlayer(target);
        this.setPos(getX(), getY(), getZ());
    }

    /** moveToPlayer: speed ramps by 0.1, but the motion always gains direction * limitSpeed (no drag). */
    private void moveToPlayer(Player player) {
        speed = speed < LIMIT_SPEED ? speed + 0.1D : LIMIT_SPEED;
        Vec3d from = new Vec3d(getX(), getY(), getZ());
        Vec3d dir = X1ShotSpecials.normalize(X1ShotSpawner.posLiving(player).subtract(from));
        Vec3 motion = this.getDeltaMovement().add(dir.x() * LIMIT_SPEED, dir.y() * LIMIT_SPEED, dir.z() * LIMIT_SPEED);
        this.setDeltaMovement(motion);
        this.setPosRaw(getX() + motion.x, getY() + motion.y, getZ() + motion.z);
    }

    @Override
    public void playerTouch(Player player) {
        if (this.level().isClientSide) return;
        if (player.getInventory().add(new ItemStack(PortRegistries.SHOT_MATERIAL.get()))) {
            this.level().playSound(null, getX(), getY(), getZ(), SoundEvents.ITEM_PICKUP, SoundSource.PLAYERS, 4.0F,
                    ((random.nextFloat() - random.nextFloat()) * 0.7F + 1.0F) * 0.3F);
            player.take(this, 1);
        }
        this.discard();
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
