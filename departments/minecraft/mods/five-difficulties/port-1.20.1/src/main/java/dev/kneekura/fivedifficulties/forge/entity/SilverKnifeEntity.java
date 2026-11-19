package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;
import java.util.Random;

/**
 * Port of X1 {@code EntitySilverKnife}. Thrown knives wait until their count passes 2 (one per tick once the
 * delay is over; white knives wait 30 more), then fly with acceleration, drag 0.95 (0.8 in water) and gravity
 * 0.008 × count. Hard blocks (stone-like, metal, glass, ice) bounce a fast knife (red keeps a quarter of its
 * speed, others almost stop); knives meeting knives scatter; soft blocks take the knife in, where it waits to
 * be picked up. Hits deal 4 (forced through hurt time by lowering health, as X1). A green knife sheds white
 * knives every other tick for its first 60 ticks. White knives vanish on their first hit.
 *
 * X1 materials are approximated with 1.20 block tags; X1 also reads the block at (0, 0, 0) for an entity hit
 * (its MovingObjectPosition carries zero block coordinates), which the port keeps.
 */
public class SilverKnifeEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_COUNT =
            SynchedEntityData.defineId(SilverKnifeEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Byte> DATA_COLOR =
            SynchedEntityData.defineId(SilverKnifeEntity.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<Integer> DATA_ZANGLE =
            SynchedEntityData.defineId(SilverKnifeEntity.class, EntityDataSerializers.INT);

    private BlockPos tile = new BlockPos(-1, -1, -1);
    private BlockState inState;
    private boolean inGround;
    private int ticksInAir;
    public LivingEntity shootingEntity;
    public LivingEntity playerEntity;
    private int ticksInGround;
    public double accelerationX, accelerationY, accelerationZ;
    private boolean hit;
    private boolean rockhit;
    private int lastTime;
    private double lastShotMotionX, lastShotMotionY, lastShotMotionZ;
    private int delay;
    private double motionX, motionY, motionZ;

    public SilverKnifeEntity(EntityType<? extends SilverKnifeEntity> type, Level level) {
        super(type, level);
    }

    public SilverKnifeEntity(Level level, Vec3d pos, Vec3d angle, double speed, int color) {
        this(level, null, pos, angle, speed, color);
    }

    public SilverKnifeEntity(Level level, LivingEntity user, Vec3d pos, Vec3d angle, double speed, int color) {
        this(PortRegistries.SILVER_KNIFE_ENTITY.get(), level);
        setKnifeColor(color);
        shootingEntity = user;
        playerEntity = user;
        motionX = angle.x() * speed;
        motionY = angle.y() * speed;
        motionZ = angle.z() * speed;
        lastShotMotionX = motionX;
        lastShotMotionY = motionY;
        lastShotMotionZ = motionZ;
        accelerationX = motionX / 2.0D;
        accelerationY = motionY / 2.0D;
        accelerationZ = motionZ / 2.0D;
        setKnifeZAngle(90.0F);
        float yaw = (float) Math.atan2(motionX, -motionZ) / 3.141593F * 180F;
        float pitch = (float) Math.atan2(motionY, Math.sqrt(motionX * motionX + motionZ * motionZ)) / 3.141593F * 180F;
        this.moveTo(pos.x() + angle.x() * speed, pos.y() + angle.y() * speed, pos.z() + angle.z() * speed, yaw, pitch);
        this.xo = getX();
        this.yo = getY();
        this.zo = getZ();
        lastTime = 0;
        delay = color == 3 ? -30 : 0;
        syncMotion();
    }

    /** THKaguyaLib.createSilverKnife: a white knife from {@code user} starting at {@code startCount}. */
    public static SilverKnifeEntity createSilverKnife(LivingEntity user, Vec3d pos, Vec3d angle, double speed, int startCount) {
        if (user == null) return null;
        SilverKnifeEntity knife = new SilverKnifeEntity(user.level(), user, pos, angle, speed, 3);
        knife.setKnifeCount(startCount);
        if (!user.level().isClientSide) {
            user.level().addFreshEntity(knife);
            return knife;
        }
        return null;
    }

    private void syncMotion() {
        this.setDeltaMovement(motionX, motionY, motionZ);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_COUNT, 0);
        this.entityData.define(DATA_COLOR, (byte) 0);
        this.entityData.define(DATA_ZANGLE, 0);
    }

    public void setKnifeCount(int c) { this.entityData.set(DATA_COUNT, c); }
    public int getKnifeCount() { return this.entityData.get(DATA_COUNT); }
    public void setKnifeColor(int c) { this.entityData.set(DATA_COLOR, (byte) c); }
    public byte getKnifeColor() { return this.entityData.get(DATA_COLOR); }
    public void setKnifeZAngle(float a) { this.entityData.set(DATA_ZANGLE, (int) (a * 10000.0F)); }
    public float getKnifeZAngle() { return (float) this.entityData.get(DATA_ZANGLE) / 10000.0F; }

    public double getEntitySpeed() {
        return Math.sqrt(motionX * motionX + motionY * motionY + motionZ * motionZ);
    }

    private void delete() {
        if (!this.level().isClientSide) this.discard();
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
    public float getPickRadius() {
        return 0.01F;
    }

    /** X1 materials rock / iron / glass / ice. */
    private static boolean hard(BlockState s) {
        return s.is(BlockTags.MINEABLE_WITH_PICKAXE) || s.is(BlockTags.IMPERMEABLE) || s.is(BlockTags.ICE);
    }

    private BlockHitResult trace(Vec3 from, Vec3 to) {
        return this.level().clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
    }

    @Override
    public void tick() {
        super.tick();
        boolean server = !this.level().isClientSide;
        if (this.tickCount > 1) {
            if (this.tickCount <= lastTime) {
                setKnifeCount(getKnifeCount());
                return;
            }
            motionX = lastShotMotionX;
            motionY = lastShotMotionY;
            motionZ = lastShotMotionZ;
            if (server) {
                delay++;
                if (delay >= 0) setKnifeCount(getKnifeCount() + 1);
            }
        }
        if (getKnifeCount() < 0) {
            setKnifeCount(getKnifeCount() + 1);
            return;
        }
        if (!hit && this.tickCount >= 300) delete();
        else if (hit && this.tickCount >= 6000) delete();
        if (getKnifeColor() == 3 && hit && this.tickCount >= 1) delete();
        rockhit = false;
        if (inGround) {
            if (this.level().getBlockState(tile) != inState) {
                inGround = false;
                motionX *= this.random.nextFloat() * 0.2F;
                motionY *= this.random.nextFloat() * 0.2F;
                motionZ *= this.random.nextFloat() * 0.2F;
                ticksInGround = 0;
                setKnifeCount(3);
            } else if (++ticksInGround == 3000) {
                delete();
            }
            return;
        }
        ticksInAir = 5;

        Vec3 posStart = this.position();
        Vec3 posEnd = posStart.add(motionX, motionY, motionZ);
        BlockHitResult blockHit = trace(posStart, posEnd);
        boolean blockFound = blockHit.getType() != HitResult.Type.MISS;
        if (blockFound) posEnd = blockHit.getLocation();

        Entity hitEntity = null;
        double nearDistance = 999.0D;
        AABB search = this.getBoundingBox().expandTowards(motionX, motionY, motionZ).inflate(0.01D);
        for (Entity check : this.level().getEntities(this, search)) {
            if (!check.isPickable() || check == shootingEntity || ticksInAir < 5 || check instanceof THShotEntity) continue;
            double extend = check instanceof SilverKnifeEntity ? 0.01D : 0.1D;
            if (check instanceof SilverKnifeEntity other && (getKnifeColor() == 3 || other.getKnifeColor() == 3)) continue;
            Optional<Vec3> at = dev.kneekura.fivedifficulties.forge.shot.X1Hit.intercept(check.getBoundingBox().inflate(extend), posStart, posEnd);
            if (at.isPresent()) {
                double d = posStart.distanceTo(at.get());
                if (d < nearDistance || nearDistance == 999.0D) {
                    hitEntity = check;
                    nearDistance = d;
                }
            }
        }
        // X1: players are never hit by knives.
        if (hitEntity instanceof Player) hitEntity = null;
        boolean anyHit = hitEntity != null || blockFound;

        if (anyHit) {
            if (hitEntity != null && !(hitEntity instanceof SilverKnifeEntity)) {
                onImpact(hitEntity);
                motionX *= -0.210000000149011612D;
                motionY *= -0.210000000149011612D;
                motionZ *= -0.210000000149011612D;
                accelerationX *= -0.01;
                accelerationY *= -0.01;
                accelerationZ *= -0.01;
                this.setYRot(this.getYRot() + 180F);
                this.yRotO += 180F;
                setKnifeCount(3);
                hit = true;
                setKnifeZAngle(0.0F);
            }
            // An entity hit carries block coordinates 0, 0, 0 in X1.
            tile = hitEntity != null ? BlockPos.ZERO : blockHit.getBlockPos();
            inState = this.level().getBlockState(tile);
            int side = hitEntity != null ? 0 : blockHit.getDirection().get3DDataValue();
            Vec3 hitVec = hitEntity != null ? hitEntity.position() : blockHit.getLocation();
            boolean air = inState.isAir();
            if (hard(inState)) {
                if (Math.abs(getEntitySpeed()) > 0.08F) {
                    if (hitEntity instanceof SilverKnifeEntity other && other.getKnifeColor() != 3 && getKnifeColor() != 3) {
                        this.level().playSound(null, getX(), getY(), getZ(), SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.NEUTRAL, 0.5F, 5.0F);
                        Random rand = new Random();
                        float randangle = (float) rand.nextInt(120);
                        this.setYRot(this.getYRot() + 165.0F - 15.0F + randangle);
                        motionX += Math.sin(randangle);
                        motionZ += Math.cos(randangle);
                        motionX *= -0.150000000149011612D * Math.sin(randangle);
                        motionY *= -0.150000000149011612D;
                        motionZ *= -0.150000000149011612D * Math.cos(randangle);
                        accelerationX *= -0.01;
                        accelerationZ *= -0.01;
                        if (getY() > other.getY()) accelerationY *= 0.01;
                        else accelerationY *= -1.2;
                    }
                    if (hitEntity == null) {
                        this.level().playSound(null, getX(), getY(), getZ(), SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.NEUTRAL, 0.5F, 5.0F);
                        bounce();
                    }
                    if (Math.abs(motionX) < 0.1D) motionX = 0.0D;
                    if (Math.abs(motionZ) < 0.1D) motionZ = 0.0D;
                    setKnifeCount(3);
                    hit = false;
                } else if (!air) {
                    motionX = hitVec.x - getX();
                    motionY = hitVec.y - getY();
                    motionZ = hitVec.z - getZ();
                    if (side == 1) {
                        this.setXRot(0F);
                        accelerationX = accelerationY = accelerationZ = 0.0D;
                        setKnifeCount(0);
                        setKnifeZAngle(0.0F);
                    } else {
                        accelerationX *= -0.01;
                        accelerationY *= -0.01;
                        accelerationZ *= -0.01;
                    }
                    stickBack();
                    rockhit = true;
                } else {
                    hit = false;
                }
            } else if (!air) {
                motionX = (float) (hitVec.x - getX());
                motionY = (float) (hitVec.y - getY());
                motionZ = (float) (hitVec.z - getZ());
                accelerationX *= -0.01;
                accelerationY *= -0.01;
                accelerationZ *= -0.01;
                stickBack();
                setKnifeCount(3);
            }
        }
        if (delay < 0) {
            syncMotion();
            return;
        }
        double x = getX(), y = getY(), z = getZ();
        if (server && getKnifeCount() > 2) {
            x += motionX;
            y += motionY;
            z += motionZ;
        }
        if (getKnifeColor() == 2 && Math.abs(getEntitySpeed()) > 0.08F && this.tickCount < 60 && this.tickCount > 2
                && this.tickCount % 2 == 1 && server) {
            double len = Math.sqrt(motionX * motionX + motionY * motionY + motionZ * motionZ);
            Vec3d angle = new Vec3d(motionX, motionY, motionZ); // X1 discards the normalized copy
            SilverKnifeEntity knife;
            if (shootingEntity == null || playerEntity == null) {
                knife = new SilverKnifeEntity(this.level(), new Vec3d(getX(), getY(), getZ()), angle, len, 3);
                this.level().addFreshEntity(knife);
            } else {
                knife = createSilverKnife(shootingEntity, new Vec3d(getX(), getY(), getZ()), angle, len, 0);
            }
            if (knife != null) {
                knife.accelerationX = accelerationX;
                knife.accelerationY = accelerationY;
                knife.accelerationZ = accelerationZ;
            }
        }
        float f = Mth.sqrt((float) (motionX * motionX + motionZ * motionZ));
        float yaw = (float) (Math.atan2(motionX, -motionZ) * 180D / Math.PI);
        float pitch = this.getXRot();
        if (server) pitch = (float) (Math.atan2(motionY, f) * 180D / Math.PI);
        while (pitch - this.xRotO < -180F) this.xRotO -= 360F;
        while (pitch - this.xRotO >= 180F) this.xRotO += 360F;
        while (yaw - this.yRotO < -180F) this.yRotO -= 360F;
        while (yaw - this.yRotO >= 180F) this.yRotO += 360F;
        if (rockhit) pitch = 0F;
        this.setYRot(yaw);
        this.setXRot(pitch);
        double slowDownRate = this.isInWater() ? 0.8F : 0.95F;
        motionX += accelerationX;
        motionY += accelerationY;
        motionZ += accelerationZ;
        motionY -= 0.008 * getKnifeCount();
        motionX *= slowDownRate;
        motionY *= slowDownRate;
        motionZ *= slowDownRate;
        this.setPos(x, y, z);
        if (this.tickCount > lastTime) {
            lastTime = this.tickCount;
            lastShotMotionX = motionX;
            lastShotMotionY = motionY;
            lastShotMotionZ = motionZ;
        }
        syncMotion();
    }

    /** Back off 0.05 from the hit point and stay in the block. */
    private void stickBack() {
        double f2 = Math.sqrt(motionX * motionX + motionY * motionY + motionZ * motionZ);
        if (f2 > 0) {
            this.setPos(getX() - (motionX / f2) * 0.05000000074505806D, getY() - (motionY / f2) * 0.05000000074505806D,
                    getZ() - (motionZ / f2) * 0.05000000074505806D);
        }
        inGround = true;
        hit = true;
    }

    /** X1's sub-trace loop off hard blocks (red keeps 0.25 × speed per bounce, the others ~0 and × 0.3). */
    private void bounce() {
        Vec3 from = this.position();
        Vec3 to = from.add(motionX, motionY, motionZ);
        BlockHitResult sub = trace(from, to);
        int guard = 0;
        while (sub.getType() != HitResult.Type.MISS && guard++ < 64) {
            double returnRate = 0.25D * getEntitySpeed();
            if (getKnifeColor() != 1) returnRate = 0.00001D;
            Direction d = sub.getDirection();
            switch (d) {
                case DOWN -> { motionY *= -returnRate; accelerationY *= -returnRate; }
                case UP -> {
                    motionY *= -returnRate;
                    accelerationY *= -returnRate;
                    setKnifeCount(0);
                    if (motionY < 0.2D) {
                        motionX *= 0.3D;
                        motionZ *= 0.3D;
                    }
                    setKnifeZAngle(getKnifeZAngle() > 0.0F ? getKnifeZAngle() - 21.0F : 0.0F);
                }
                case NORTH, SOUTH -> { motionZ *= -returnRate; accelerationZ *= -returnRate; }
                default -> { motionX *= -returnRate; accelerationX *= -returnRate; }
            }
            if (getKnifeColor() != 1) {
                motionX *= 0.3D; motionY *= 0.3D; motionZ *= 0.3D;
                accelerationX *= 0.3D; accelerationY *= 0.3D; accelerationZ *= 0.3D;
            }
            Vec3 h = sub.getLocation();
            from = new Vec3(from.x + (h.x - from.x) * 0.999D, from.y + (h.y - from.y) * 0.999D, from.z + (h.z - from.z) * 0.999D);
            to = from.add(motionX, motionY, motionZ);
            sub = trace(from, to);
        }
    }

    private void onImpact(Entity hit) {
        if (this.level().isClientSide || hit == shootingEntity) return;
        float damage = 4.0F;
        if (hit instanceof LivingEntity living) {
            if (living.hurtTime > 0) {
                boolean isLive = living.getHealth() > 0.0F;
                living.setHealth(living.getHealth() - damage); // X1 heal(-damage)
                if (living.getHealth() <= 0.0F && isLive) living.die(this.damageSources().mobAttack(shootingEntity));
                this.hit = true;
            } else {
                hit.hurt(this.damageSources().mobAttack(shootingEntity), damage);
            }
        }
    }

    @Override
    public void playerTouch(Player player) {
        if (!this.level().isClientSide && inGround
                && player.getInventory().add(new ItemStack(knifeItem(getKnifeColor())))) {
            this.level().playSound(null, getX(), getY(), getZ(), SoundEvents.ITEM_PICKUP, SoundSource.NEUTRAL, 4.0F,
                    ((this.random.nextFloat() - this.random.nextFloat()) * 0.7F + 1.0F) * 2.0F);
            player.take(this, 1);
            this.discard();
        }
    }

    public static net.minecraft.world.item.Item knifeItem(int color) {
        return switch (color) {
            case 1 -> PortRegistries.SILVER_KNIFE_RED.get();
            case 2 -> PortRegistries.SILVER_KNIFE_GREEN.get();
            case 3 -> PortRegistries.SILVER_KNIFE_WHITE.get();
            default -> PortRegistries.SILVER_KNIFE_BLUE.get();
        };
    }

    public boolean inGround() {
        return inGround;
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putShort("xTile", (short) tile.getX());
        tag.putShort("yTile", (short) tile.getY());
        tag.putShort("zTile", (short) tile.getZ());
        if (inState != null) tag.put("inState", NbtUtils.writeBlockState(inState));
        tag.putByte("inGround", (byte) (inGround ? 1 : 0));
        tag.putShort("color", getKnifeColor());
        tag.putShort("zAngle", (short) (getKnifeZAngle() * 10000.0F));
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        tile = new BlockPos(tag.getShort("xTile"), tag.getShort("yTile"), tag.getShort("zTile"));
        inState = tag.contains("inState")
                ? NbtUtils.readBlockState(this.level().holderLookup(net.minecraft.core.registries.Registries.BLOCK), tag.getCompound("inState"))
                : Blocks.AIR.defaultBlockState();
        inGround = tag.getByte("inGround") == 1;
        setKnifeColor(tag.getByte("color"));
        setKnifeZAngle((float) tag.getShort("zAngle") / 10000.0F);
    }
}
