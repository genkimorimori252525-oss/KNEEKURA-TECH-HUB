package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.timestop.SakuyaTimeStopInstance;
import dev.kneekura.fivedifficulties.core.timestop.TimeDomainMode;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopFlags;
import dev.kneekura.fivedifficulties.core.timestop.TimeStopShape;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.core.x1.SakuyaWatchContract;
import dev.kneekura.fivedifficulties.core.x1.X1SakuyaControllerGeometry;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.timestop.SakuyaTimeStopRuntime;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import javax.annotation.Nullable;
import java.util.UUID;

/**
 * Network-synced, invisible 1.20.1 replacement for X1 EntitySakuyaWatch /
 * EntitySakuyaStopWatch.
 *
 * The entity itself is the synchronization primitive: source id, mode,
 * controller kind, start tick and duration are replicated through normal
 * entity data, so client tick-cancellation does not require a custom packet.
 */
public final class SakuyaTimeControllerEntity extends Entity {
    private boolean finishing;
    private static final EntityDataAccessor<Integer> DATA_SOURCE_ID =
            SynchedEntityData.defineId(SakuyaTimeControllerEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_MODE =
            SynchedEntityData.defineId(SakuyaTimeControllerEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_KIND =
            SynchedEntityData.defineId(SakuyaTimeControllerEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_START_TICK =
            SynchedEntityData.defineId(SakuyaTimeControllerEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_DURATION =
            SynchedEntityData.defineId(SakuyaTimeControllerEntity.class, EntityDataSerializers.INT);

    public SakuyaTimeControllerEntity(EntityType<? extends SakuyaTimeControllerEntity> type, Level level) {
        super(type, level);
        this.noPhysics = true;
        this.setNoGravity(true);
    }

    public SakuyaTimeControllerEntity(
            Level level,
            LivingEntity source,
            TimeDomainMode mode,
            int durationTicks,
            SakuyaControllerKind kind,
            int startTick
    ) {
        this(PortRegistries.SAKUYA_TIME_CONTROLLER.get(), level);
        configure(source, mode, durationTicks, kind, startTick);
    }

    public void configure(
            LivingEntity source,
            TimeDomainMode mode,
            int durationTicks,
            SakuyaControllerKind kind,
            int startTick
    ) {
        if (source == null || mode == null || kind == null) throw new NullPointerException();
        if (durationTicks == 0 || durationTicks < -1) throw new IllegalArgumentException("durationTicks");
        this.entityData.set(DATA_SOURCE_ID, source.getId());
        this.entityData.set(DATA_MODE, mode.ordinal());
        this.entityData.set(DATA_KIND, kind.ordinal());
        this.entityData.set(DATA_START_TICK, startTick);
        this.entityData.set(DATA_DURATION, durationTicks);
        followSource(source);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_SOURCE_ID, -1);
        this.entityData.define(DATA_MODE, TimeDomainMode.FULL_STOP.ordinal());
        this.entityData.define(DATA_KIND, SakuyaControllerKind.WATCH_LIMITED.ordinal());
        this.entityData.define(DATA_START_TICK, 0);
        this.entityData.define(DATA_DURATION, 1);
    }

    @Nullable
    public LivingEntity getSourceEntity() {
        int id = this.entityData.get(DATA_SOURCE_ID);
        if (id < 0) return null;
        Entity entity = this.level().getEntity(id);
        return entity instanceof LivingEntity living ? living : null;
    }

    public TimeDomainMode getTimeMode() {
        int value = this.entityData.get(DATA_MODE);
        TimeDomainMode[] values = TimeDomainMode.values();
        return value >= 0 && value < values.length ? values[value] : TimeDomainMode.FULL_STOP;
    }

    public SakuyaControllerKind getControllerKind() {
        int value = this.entityData.get(DATA_KIND);
        SakuyaControllerKind[] values = SakuyaControllerKind.values();
        return value >= 0 && value < values.length ? values[value] : SakuyaControllerKind.WATCH_LIMITED;
    }

    public int getStartTick() {
        return this.entityData.get(DATA_START_TICK);
    }

    public int getDurationTicks() {
        return this.entityData.get(DATA_DURATION);
    }

    public int elapsedTicks(int logicalTick) {
        return Math.max(0, logicalTick - getStartTick());
    }

    public boolean isActiveAt(int logicalTick) {
        int duration = getDurationTicks();
        if (logicalTick < getStartTick()) return false;
        return duration == -1 || ((long) logicalTick) < ((long) getStartTick() + duration);
    }

    public SakuyaTimeStopInstance toCoreInstance(LivingEntity source) {
        return new SakuyaTimeStopInstance(
                this.getUUID(),
                source.getUUID(),
                new Vec3d(this.getX(), this.getY(), this.getZ()),
                SakuyaWatchContract.FIELD_RANGE_BLOCKS,
                getStartTick(),
                getDurationTicks(),
                TimeStopFlags.x1EntityOnly(),
                TimeStopShape.AABB,
                getTimeMode()
        );
    }

    @Override
    public void tick() {
        super.tick();

        LivingEntity source = getSourceEntity();
        if (source == null || !source.isAlive()) {
            if (!this.level().isClientSide) finishX1();
            return;
        }

        followSource(source);

        if (!this.level().isClientSide) {
            int logicalTick = (int) (this.level().getGameTime() & 0x7fffffffL);

            if (!isActiveAt(logicalTick) || source.hurtTime > 0) {
                finishX1();
                return;
            }

            if (getControllerKind().endsOnSneakAfterGrace()
                    && elapsedTicks(logicalTick) >= SakuyaWatchContract.MANUAL_RELEASE_MIN_AGE_TICKS
                    && source.isShiftKeyDown()) {
                finishX1();
                return;
            }

            if (this.level().getEntitiesOfClass(
                    Player.class,
                    this.getBoundingBox().inflate(SakuyaWatchContract.FIELD_RANGE_BLOCKS)
            ).isEmpty()) {
                finishX1();
                return;
            }

            for (SakuyaTimeControllerEntity other : this.level().getEntitiesOfClass(
                    SakuyaTimeControllerEntity.class,
                    this.getBoundingBox().inflate(SakuyaWatchContract.FIELD_RANGE_BLOCKS),
                    candidate -> candidate != this && candidate.isAlive()
            )) {
                // X1 Watch only reacts to another Watch. StopWatch reacts to
                // either controller class, so a Watch+StopWatch pair is still
                // terminated when the StopWatch controller processes.
                boolean conflict = getControllerKind() == SakuyaControllerKind.STOPWATCH
                        || other.getControllerKind() != SakuyaControllerKind.STOPWATCH;
                if (!conflict) continue;

                other.finishX1();
                this.finishX1();
                return;
            }
        }
    }

    public void finishX1() {
        if (this.finishing) return;
        this.finishing = true;

        if (!this.level().isClientSide && getControllerKind() == SakuyaControllerKind.WATCH_LIMITED) {
            returnConsumedWatch();
        }

        this.discard();
    }

    private void returnConsumedWatch() {
        ItemStack returned = new ItemStack(PortRegistries.SAKUYA_WATCH.get());
        LivingEntity source = getSourceEntity();

        if (source instanceof Player player && player.getAbilities().instabuild) {
            return;
        }

        if (source instanceof Player player && player.isAlive() && player.getInventory().add(returned)) {
            return;
        }

        this.level().addFreshEntity(new ItemEntity(
                this.level(),
                this.getX(),
                this.getY(),
                this.getZ(),
                returned
        ));
    }

    private void followSource(LivingEntity source) {
        Vec3d center = X1SakuyaControllerGeometry.center(
                new Vec3d(source.getX(), source.getY(), source.getZ()),
                source.getEyeHeight(),
                source.getYRot(),
                source.getXRot()
        );
        this.setPos(center.x(), center.y(), center.z());
        this.setDeltaMovement(source.getDeltaMovement());
    }

    @Override
    public void onAddedToWorld() {
        super.onAddedToWorld();
        SakuyaTimeStopRuntime.registerController(this);
    }

    @Override
    public void onRemovedFromWorld() {
        SakuyaTimeStopRuntime.unregisterController(this);
        super.onRemovedFromWorld();
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean canBeCollidedWith() {
        return false;
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putInt("X1SourceId", this.entityData.get(DATA_SOURCE_ID));
        tag.putInt("X1Mode", this.entityData.get(DATA_MODE));
        tag.putInt("X1Kind", this.entityData.get(DATA_KIND));
        tag.putInt("X1StartTick", this.entityData.get(DATA_START_TICK));
        tag.putInt("X1Duration", this.entityData.get(DATA_DURATION));
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        this.entityData.set(DATA_SOURCE_ID, tag.getInt("X1SourceId"));
        this.entityData.set(DATA_MODE, tag.getInt("X1Mode"));
        this.entityData.set(DATA_KIND, tag.getInt("X1Kind"));
        this.entityData.set(DATA_START_TICK, tag.getInt("X1StartTick"));
        int duration = tag.getInt("X1Duration");
        this.entityData.set(DATA_DURATION, duration == 0 ? 1 : duration);
    }
}
