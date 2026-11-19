package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.vehicle.Boat;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;

/**
 * Port of X1 {@code EntityKinkakuzi} (金閣寺の一枚天井): a 6 × 0.3 flying ceiling thrown up (0.7, sneak 1.0) and a
 * little forward. It falls 0.04 a tick (floats up in water), can be ridden and steered like a boat (speed up to
 * 0.35), and anything below it that it moves down onto takes {@code (int)(drop × 40) + 2} indirect magic
 * damage. Hits beyond 40 accumulated damage break it back into its item (creative: nothing).
 *
 * Moved by its controller as 1.20 boats are: the riding player's client, otherwise the server.
 */
public class KinkakuziEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_TIME_SINCE_HIT =
            SynchedEntityData.defineId(KinkakuziEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_FORWARD =
            SynchedEntityData.defineId(KinkakuziEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> DATA_DAMAGE =
            SynchedEntityData.defineId(KinkakuziEntity.class, EntityDataSerializers.FLOAT);
    private double speedMultiplier = 0.07D;
    private LivingEntity shootingEntity;
    private double serverLastY = Double.NaN;

    public KinkakuziEntity(EntityType<? extends KinkakuziEntity> type, Level level) {
        super(type, level);
        this.blocksBuilding = true;
    }

    public KinkakuziEntity(Level level, double x, double y, double z, LivingEntity user, double pow) {
        this(PortRegistries.KINKAKUZI_ENTITY.get(), level);
        this.setDeltaMovement(-Math.sin((float) Math.toRadians(user.getYRot())) * 0.2D, pow,
                Math.cos((float) Math.toRadians(user.getYRot())) * 0.2D);
        this.moveTo(x, y, z, user.getYRot(), 0.0F);
        this.xo = x;
        this.yo = y;
        this.zo = z;
        this.shootingEntity = user;
    }

    @Override
    protected AABB makeBoundingBox() {
        // 1.7.10 yOffset = height / 2: the box is centred on the position.
        return new AABB(getX() - 3.0D, getY() - 0.15D, getZ() - 3.0D, getX() + 3.0D, getY() + 0.15D, getZ() + 3.0D);
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
    public double getPassengersRidingOffset() {
        return 0.3D;
    }

    @Override
    public LivingEntity getControllingPassenger() {
        return this.getFirstPassenger() instanceof Player p ? p : null;
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
                if (!creative) this.spawnAtLocation(PortRegistries.KINKAKUZI.get());
                this.discard();
            }
        }
        return true;
    }

    @Override
    public void animateHurt(float yaw) {
        setForwardDirection(-getForwardDirection());
        setTimeSinceHit(10);
        setDamageTaken(getDamageTaken() * 11);
    }

    @Override
    public InteractionResult interact(Player player, InteractionHand hand) {
        Entity rider = this.getFirstPassenger();
        if (rider instanceof Player && rider != player) return InteractionResult.SUCCESS;
        if (!this.level().isClientSide) player.startRiding(this);
        return InteractionResult.sidedSuccess(this.level().isClientSide);
    }

    @Override
    protected void positionRider(Entity passenger, MoveFunction move) {
        double d = Math.cos(getYRot() * Math.PI / 180D) * 0.5D;
        double d1 = Math.sin(getYRot() * Math.PI / 180D) * 0.5D;
        move.accept(passenger, getX() + d, getY() + getPassengersRidingOffset() + passenger.getMyRidingOffset(), getZ() + d1);
    }

    @Override
    public void tick() {
        super.tick();
        if (getTimeSinceHit() > 0) setTimeSinceHit(getTimeSinceHit() - 1);
        if (getDamageTaken() > 0) setDamageTaken(getDamageTaken() - 1);
        if (this.isControlledByLocalInstance()) physics();
        if (!this.level().isClientSide) serverHits();
    }

    /** X1 onUpdate movement (on the controlling side). */
    private void physics() {
        double prevX = getX(), prevZ = getZ();
        AABB box = getBoundingBox();
        int slices = 5;
        double water = 0.0D;
        for (int j = 0; j < slices; j++) {
            double y0 = box.minY + (box.maxY - box.minY) * j / slices - 0.125D;
            double y1 = box.minY + (box.maxY - box.minY) * (j + 1) / slices - 0.125D;
            if (this.level().getBlockStates(new AABB(box.minX, y0, box.minZ, box.maxX, y1, box.maxZ))
                    .anyMatch(s -> s.getFluidState().is(FluidTags.WATER))) {
                water += 1.0D / slices;
            }
        }
        var m = getDeltaMovement();
        double mx = m.x, my = m.y, mz = m.z;
        double lengthXZ = Math.sqrt(mx * mx + mz * mz);
        if (water < 1.0D) {
            my += 0.039999999105930328D * (water * 2D - 1.0D);
        } else {
            if (my < 0.0D) my /= 2.0D;
            my += 0.0070000002160668373D;
        }
        if (getControllingPassenger() instanceof Player rider && rider.zza > 0.0F) {
            mx += -Math.sin(rider.getYRot() * Math.PI / 180.0F) * speedMultiplier * 0.05000000074505806D;
            mz += Math.cos(rider.getYRot() * Math.PI / 180.0F) * speedMultiplier * 0.05000000074505806D;
        }
        double speed = Math.sqrt(mx * mx + mz * mz);
        if (speed > 0.35D) {
            double r = 0.35D / speed;
            mx *= r;
            mz *= r;
            speed = 0.35D;
        }
        if (speed > lengthXZ && speedMultiplier < 0.35D) {
            speedMultiplier = Math.min(0.35D, speedMultiplier + (0.35D - speedMultiplier) / 35.0D);
        } else {
            speedMultiplier = Math.max(0.07D, speedMultiplier - (speedMultiplier - 0.07D) / 35.0D);
        }
        if (this.onGround()) {
            mx *= 0.5D;
            my *= 0.5D;
            mz *= 0.5D;
        }
        this.setDeltaMovement(mx, my, mz);
        this.move(MoverType.SELF, this.getDeltaMovement());
        var after = getDeltaMovement();
        mx = after.x;
        my = after.y;
        mz = after.z;
        if (!(this.horizontalCollision && lengthXZ > 0.2D)) {
            mx *= 0.99000000953674316D;
            my *= 0.94999998807907104D;
            mz *= 0.99000000953674316D;
        }
        this.setDeltaMovement(mx, my, mz);
        double yaw = getYRot();
        double dx = prevX - getX(), dz = prevZ - getZ();
        if (dx * dx + dz * dz > 0.001D) yaw = (float) (Math.atan2(dz, dx) * 180D / Math.PI);
        double shift = Mth.clamp(Mth.wrapDegrees(yaw - (double) getYRot()), -20D, 20D);
        this.setYRot((float) (getYRot() + shift));
        this.setXRot(0.0F);
    }

    /** X1's server-side pushes and landing hits; the drop is measured between server ticks. */
    private void serverHits() {
        double yMove = Double.isNaN(serverLastY) ? 0.0D : serverLastY - getY();
        serverLastY = getY();
        Entity rider = this.getFirstPassenger();
        for (Entity e : this.level().getEntities(this, getBoundingBox().inflate(0.20000000298023224D, 0.0D, 0.20000000298023224D))) {
            if (e != rider && e.isPushable() && e instanceof Boat) e.push(this);
        }
        for (Entity e : this.level().getEntities(this, getBoundingBox().inflate(0.0D, 0.5D, 0.1D) /* X1 boatYaw is 0 on the server */)) {
            if (e != rider && e.isPushable() && e instanceof KinkakuziEntity) e.push(this);
            if (e != rider && !(e instanceof KinkakuziEntity) && e.getY() < getY() && !(e instanceof ItemEntity)
                    && !(e instanceof ExperienceOrb) && !(e instanceof THShotEntity) && e != shootingEntity && yMove >= 0.0D) {
                int damage = (int) (yMove * 40.0D) + 2;
                e.hurt(this.damageSources().indirectMagic(this, shootingEntity), damage);
            }
        }
    }

    /** Test hook: one controller step and server step, as a server tick would run them. */
    public void stepForTest() {
        physics();
        serverHits();
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}
}
