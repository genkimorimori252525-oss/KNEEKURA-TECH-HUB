package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;

/**
 * Port of X1 {@code EntityMarisaBroom} (魔法の箒). X1 reads the movement keys only on the client, but runs the
 * ridden movement only on the server, where "forward" is fixed on and the other keys off; the client copy is
 * never told it is ridden and just interpolates. So in play the broom always accelerates 0.04 along the rider's
 * look (vertically by the rider's pitch), speeds above 0.8 are multiplied by themselves (X1 quirk), and the rider
 * never takes fall damage. Empty, it sinks 0.03 a tick, slows to 0.9 and pops up 0.06 on the ground.
 *
 * Positions follow X1's {@code yOffset = 0.8}: the entity sits 0.8 above its box bottom.
 */
public class MarisaBroomEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_TIME_SINCE_HIT =
            SynchedEntityData.defineId(MarisaBroomEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_FORWARD =
            SynchedEntityData.defineId(MarisaBroomEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> DATA_DAMAGE =
            SynchedEntityData.defineId(MarisaBroomEntity.class, EntityDataSerializers.FLOAT);

    public MarisaBroomEntity(EntityType<? extends MarisaBroomEntity> type, Level level) {
        super(type, level);
        this.blocksBuilding = true;
    }

    public MarisaBroomEntity(Level level, double x, double y, double z) {
        this(PortRegistries.MARISA_BROOM_ENTITY.get(), level);
        this.setPos(x, y + 0.8D, z);
        this.setDeltaMovement(0, 0, 0);
        this.xo = x;
        this.yo = y;
        this.zo = z;
    }

    @Override
    protected AABB makeBoundingBox() {
        return new AABB(getX() - 0.45D, getY() - 0.8D, getZ() - 0.45D, getX() + 0.45D, getY() - 0.3D, getZ() + 0.45D);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_TIME_SINCE_HIT, 0);
        this.entityData.define(DATA_FORWARD, 1);
        this.entityData.define(DATA_DAMAGE, 0.0F);
    }

    public void setTimeSinceHit(int t) { this.entityData.set(DATA_TIME_SINCE_HIT, t); }
    public int getTimeSinceHit() { return this.entityData.get(DATA_TIME_SINCE_HIT); }
    public void setForwardDirection(int d) { this.entityData.set(DATA_FORWARD, d); }
    public int getForwardDirection() { return this.entityData.get(DATA_FORWARD); }
    public void setDamageTaken(float d) { this.entityData.set(DATA_DAMAGE, d); }
    public float getDamageTaken() { return this.entityData.get(DATA_DAMAGE); }

    @Override
    public boolean canBeCollidedWith() {
        return true;
    }

    @Override
    public boolean isPushable() {
        return true;
    }

    @Override
    public boolean isPickable() {
        return !this.isRemoved();
    }

    @Override
    protected boolean canAddPassenger(Entity passenger) {
        return this.getPassengers().isEmpty();
    }

    @Override
    protected void positionRider(Entity passenger, MoveFunction move) {
        // X1: posY + getMountedYOffset() (-0.15) + the player's server-side getYOffset() (-0.5).
        move.accept(passenger, getX(), getY() - 0.15D - 0.5D, getZ());
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        if (this.isInvulnerableTo(source)) return false;
        if (!this.level().isClientSide && !this.isRemoved()) {
            setForwardDirection(-getForwardDirection());
            setTimeSinceHit(10);
            setDamageTaken(getDamageTaken() + amount * 10.0F);
            this.markHurt();
            boolean creative = source.getEntity() instanceof Player p && p.getAbilities().instabuild;
            if (creative || getDamageTaken() > 40.0F) {
                this.ejectPassengers();
                if (!creative) this.spawnAtLocation(PortRegistries.MARISA_BROOM.get());
                this.discard();
            }
        }
        return true;
    }

    @Override
    public InteractionResult interact(Player player, InteractionHand hand) {
        Entity rider = this.getFirstPassenger();
        if (rider instanceof Player && rider != player) return InteractionResult.SUCCESS;
        if (!this.level().isClientSide) player.startRiding(this);
        return InteractionResult.sidedSuccess(this.level().isClientSide);
    }

    @Override
    public void tick() {
        super.tick();
        if (getTimeSinceHit() > 0) setTimeSinceHit(getTimeSinceHit() - 1);
        if (getDamageTaken() > 0.0F) setDamageTaken(getDamageTaken() - 1.0F);
        if (!this.level().isClientSide) serverTick();
    }

    /** X1's server branch of onUpdate. */
    public void serverTick() {
        var m = getDeltaMovement();
        double mx = m.x, my = m.y, mz = m.z;
        Entity rider = this.getFirstPassenger();
        if (rider instanceof Player) {
            double acceleration = 0.04D;
            my += -Math.sin(getXRot() / 180F * 3.141593F) * acceleration;
            // move_up is fixed on in X1's server branch
            mx += Math.sin((getYRot() - 90F) / 180F * (float) Math.PI) * acceleration;
            mz += -Math.cos((getYRot() - 90F) / 180F * (float) Math.PI) * acceleration;
            this.setXRot(rider.getXRot());
            this.setYRot(rider.getYRot() - 90F);
            double speed = Math.sqrt(mx * mx + my * my + mz * mz);
            if (speed > 0.8D) {
                mx *= speed;
                my *= speed;
                mz *= speed;
            }
        }
        if (this.isInWater()) {
            mx *= 0.5D;
            my *= 0.5D;
            mz *= 0.5D;
        }
        this.setDeltaMovement(mx, my, mz);
        this.move(MoverType.SELF, this.getDeltaMovement());
        var after = getDeltaMovement();
        mx = after.x * 0.9900000095367432D;
        my = after.y * 0.949999988079071D;
        mz = after.z * 0.9900000095367432D;
        for (Entity e : this.level().getEntities(this, getBoundingBox().inflate(0.20000000298023224D, 0.0D, 0.20000000298023224D))) {
            if (e != rider && e.isPushable() && e instanceof MarisaBroomEntity) e.push(this);
        }
        if (rider != null) {
            rider.fallDistance = 0.0F;
            this.fallDistance = 0.0F;
        } else {
            mx *= 0.9D;
            my -= 0.03D;
            mz *= 0.9D;
            float pitch = getXRot();
            if (pitch > 1.0F) this.setXRot(pitch - 1);
            else if (pitch < -1.0F) this.setXRot(pitch + 1);
            if (this.onGround()) my += 0.06D;
        }
        this.setDeltaMovement(mx, my, mz);
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}
}
