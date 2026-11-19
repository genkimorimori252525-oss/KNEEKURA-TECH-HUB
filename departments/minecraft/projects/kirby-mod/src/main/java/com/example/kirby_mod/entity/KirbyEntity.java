package com.example.kirby_mod.entity;

import com.example.kirby_mod.client.KirbyInhaleSoundInstance;
import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.debug.KirbyDebugInfoProviders;
import com.example.kirby_mod.entity.ai.KirbyAiAction;
import com.example.kirby_mod.entity.ai.KirbyAiBrain;
import com.example.kirby_mod.entity.ai.KirbyAutonomousFlightIntentGoal;
import com.example.kirby_mod.entity.ai.KirbyCrouchGoal;
import com.example.kirby_mod.entity.ai.KirbyDamageFacePolicy;
import com.example.kirby_mod.entity.ai.KirbyDecisionLane;
import com.example.kirby_mod.entity.ai.KirbyDigestGoal;
import com.example.kirby_mod.entity.ai.KirbyDodgeJumpGoal;
import com.example.kirby_mod.entity.ai.KirbyFlightGoal;
import com.example.kirby_mod.entity.ai.KirbyGroundTargetGoal;
import com.example.kirby_mod.entity.ai.KirbyInhaleGoal;
import com.example.kirby_mod.entity.ai.KirbyLocomotionMode;
import com.example.kirby_mod.entity.ai.KirbySwimGoal;
import com.example.kirby_mod.entity.ai.KirbySwimMotionPolicy;
import com.example.kirby_mod.entity.ai.KirbyThreatTargetGoal;
import com.example.kirby_mod.entity.ai.KirbyWanderGoal;
import com.example.kirby_mod.entity.ai.target.KirbyTargetMemory;
import com.example.kirby_mod.entity.ai.target.KirbyInterestRules;
import com.example.kirby_mod.entity.ai.target.KirbyTargetScanner;
import com.example.kirby_mod.network.KirbyHeldMobPresentationPacket;
import com.example.kirby_mod.network.KirbyTelemetryNetwork;
import net.minecraft.client.Minecraft;
import net.minecraft.sounds.SoundEvent;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

public class KirbyEntity extends PathfinderMob implements GeoEntity {

    public enum FlightState {
        GROUND, JUMPING, ASCEND_PREP, ASCEND_PUMP, DESCEND, DODGE_JUMP;

        public static FlightState byId(int id) {
            FlightState[] values = values();
            return id < 0 || id >= values.length ? GROUND : values[id];
        }
    }

    /**
     * @deprecated Flight takeoff now uses the purpose-driven KirbyJumpPolicy.
     */
    @Deprecated
    public static double getJumpImpulseForSize(KirbySize size) {
        switch (size) {
            case SMALL:  return 0.85D;
            case MIDDLE: return 0.70D;
            case BIG:    return 0.50D;
            case NORMAL:
            default:     return 0.95D;
        }
    }

    public enum HurtFace {
        NONE, HURT_1, HURT_2, HURT_3;

        public static HurtFace byId(int id) {
            HurtFace[] values = values();
            return id < 0 || id >= values.length ? NONE : values[id];
        }
    }

    private static final int HURT_FACE_DURATION = 10;

    private static final EntityDataAccessor<Integer> DATA_FLIGHT_STATE =
            SynchedEntityData.defineId(KirbyEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_KIRBY_SIZE =
            SynchedEntityData.defineId(KirbyEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_COMBAT_STATE =
            SynchedEntityData.defineId(KirbyEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> DATA_MOUTH_FULLNESS =
            SynchedEntityData.defineId(KirbyEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Integer> DATA_HURT_FACE =
            SynchedEntityData.defineId(KirbyEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> DATA_SWIMMING_ACTIVE =
            SynchedEntityData.defineId(KirbyEntity.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> DATA_GROUND_RUNNING =
            SynchedEntityData.defineId(KirbyEntity.class, EntityDataSerializers.BOOLEAN);

    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("animation.kirby.idle");
    private static final RawAnimation WALK = RawAnimation.begin().thenLoop("animation.kirby.walk");
    private static final RawAnimation RUN_START = RawAnimation.begin().thenPlay("animation.kirby.run_start");
    private static final RawAnimation RUN = RawAnimation.begin().thenLoop("animation.kirby.run");
    private static final RawAnimation FLY_START = RawAnimation.begin().thenPlay("animation.kirby.fly");
    private static final RawAnimation FLY_LOOP = RawAnimation.begin().thenLoop("animation.kirby.fly2");
    private static final RawAnimation FLY_END = RawAnimation.begin().thenPlay("animation.kirby.fly3");
    private static final RawAnimation FALL_START = RawAnimation.begin().thenPlay("animation.kirby.fall_start");
    private static final RawAnimation FALL = RawAnimation.begin().thenLoop("animation.kirby.fall");
    private static final RawAnimation LAND = RawAnimation.begin().thenLoop("animation.kirby.land");
    private static final RawAnimation SWIM = RawAnimation.begin().thenLoop("swim2");

    private static final RawAnimation BACUME_START = RawAnimation.begin().thenPlay("animation.kirby.Bacume_start");
    private static final RawAnimation BACUME_LOOP = RawAnimation.begin().thenLoop("animation.kirby.Bacume");
    private static final RawAnimation BACUME_END = RawAnimation.begin().thenPlay("animation.kirby.Bacume_end");

    private static final RawAnimation KEEP_SMALL_IDLE = RawAnimation.begin().thenLoop("kirby.keep.small.idle");
    private static final RawAnimation KEEP_MIDDLE_IDLE = RawAnimation.begin().thenLoop("kirby.keep.middle.idle");
    private static final RawAnimation KEEP_BIG_IDLE = RawAnimation.begin().thenLoop("kirby.keep.big.idle");
    private static final RawAnimation KEEP_SMALL_WALK = RawAnimation.begin().thenLoop("kirby.keep.small.walk");
    private static final RawAnimation KEEP_MIDDLE_WALK = RawAnimation.begin().thenLoop("kirby.keep.middle.walk");
    private static final RawAnimation KEEP_BIG_WALK = RawAnimation.begin().thenLoop("kirby.keep.big.walk");
    private static final RawAnimation KEEP_SMALL_NOMIKOMI = RawAnimation.begin().thenPlay("kirby.keep.small.nomikomi");
    private static final RawAnimation KEEP_MIDDLE_NOMIKOMI = RawAnimation.begin().thenPlay("kirby.keep.middle.nomikomi");
    private static final RawAnimation KEEP_BIG_NOMIKOMI = RawAnimation.begin().thenPlay("kirby.keep.big.nomikomi");
    private static final RawAnimation SMALL_REVERSE = RawAnimation.begin().thenPlay("kirby.small.reverse");
    private static final RawAnimation MIDDLE_REVERSE = RawAnimation.begin().thenPlay("kirby.middle.reverse");
    private static final RawAnimation BIG_REVERSE = RawAnimation.begin().thenPlay("kirby.big.reverse");
    private static final RawAnimation KEEP_SMALL_FALL_START = RawAnimation.begin().thenPlay("kirby.keep.small.fall_start");
    private static final RawAnimation KEEP_MIDDLE_FALL_START = RawAnimation.begin().thenPlay("kirby.keep.middle.fall_start");
    private static final RawAnimation KEEP_BIG_FALL_START = RawAnimation.begin().thenPlay("kirby.keep.big.fall_start");
    private static final RawAnimation KEEP_SMALL_FALL = RawAnimation.begin().thenLoop("kirby.keep.small.fall");
    private static final RawAnimation KEEP_MIDDLE_FALL = RawAnimation.begin().thenLoop("kirby.keep.middle.fall");
    private static final RawAnimation KEEP_BIG_FALL = RawAnimation.begin().thenLoop("kirby.keep.big.fall");
    private static final RawAnimation KEEP_SMALL_LAND = RawAnimation.begin().thenLoop("kirby.keep.small.land");
    private static final RawAnimation KEEP_MIDDLE_LAND = RawAnimation.begin().thenLoop("kirby.keep.middle.land");
    private static final RawAnimation KEEP_BIG_LAND = RawAnimation.begin().thenLoop("kirby.keep.big.land");
    private static final RawAnimation JAMP_MOLLY = RawAnimation.begin().thenPlay("animation.kirby.jamp.molly");
    private static final RawAnimation KEEP_SMALL_JAMP = RawAnimation.begin().thenPlay("kirby.keep.small.jamp");
    private static final RawAnimation KEEP_MIDDLE_JAMP = RawAnimation.begin().thenPlay("kirby.keep.middle.jamp");
    private static final RawAnimation KEEP_BIG_JAMP = RawAnimation.begin().thenPlay("kirby.keep.big.jamp");

    private static final RawAnimation HUSE  = RawAnimation.begin().thenPlay("animation.kirby.Huse");
    private static final RawAnimation HUSE2 = RawAnimation.begin().thenLoop("animation.kirby.Huse2");
    private static final RawAnimation HUSE3 = RawAnimation.begin().thenPlay("animation.kirby.Huse3");
    private static final RawAnimation SLIDE_START = RawAnimation.begin().thenPlay("animation.kirby.Sliding");
    private static final RawAnimation SLIDING = RawAnimation.begin().thenLoop("animation.kirby.Slidingkeep");
    private static final RawAnimation SLIDE_FINISH = RawAnimation.begin().thenPlay("animation.kirby.Slidingfinish");

    private static final int FALL_START_TICKS = 2;
    private static final int RUN_START_TICKS = 4;
    private static final int LAND_THRESHOLD_TICKS = 20;
    private static final double MIN_MOVEMENT_ANIMATION_SPEED = 0.05D;
    private static final double MAX_MOVEMENT_ANIMATION_SPEED = 3.0D;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final KirbyAiBrain aiBrain = new KirbyAiBrain();
    private final KirbyTargetScanner targetScanner = new KirbyTargetScanner(this);
    @Nullable private KirbyGroundTargetGoal groundTargetGoal;
    @Nullable private KirbyWanderGoal wanderGoal;

    @Nullable private BlockPos pendingHighTarget;
    private int airborneFallTicks;
    private int runTicks;
    private final KirbyWalkSoundSequence walkSoundSequence = new KirbyWalkSoundSequence();
    private final KirbyMouthController mouthController = new KirbyMouthController(this);

    private final List<UUID> heldMobUUIDs = new ArrayList<>();
    private final List<LivingEntity> heldMobsCache = new ArrayList<>();
    private final Map<UUID, Double> heldMobCapturePoints = new HashMap<>();
    private int heldMobPresentationRevision;
    @Nullable private List<KirbyDebugInfoProvider> debugInfoProviders;
    private int hurtFaceTicks;
    private float lastHurtRequestedAmount;
    private int lastHurtFaceTick = -1;
    private String lastHurtSource = "none";
    private boolean wasOnGround = true;
    private CombatState lastClientCombatState = CombatState.NONE;
    @Nullable private KirbyInhaleSoundInstance activeInhaleSound;
    private String lastDebugAnimationName = "unresolved";
    private double lastSwimInputStrength;
    private Vec3 lastSwimLookDirection = Vec3.ZERO;
    private Vec3 lastSwimVelocity = Vec3.ZERO;
    private float previousMouthRenderScale = Float.NaN;
    private float currentMouthRenderScale = Float.NaN;
    private boolean mouthFullnessTransitionLocked;
    private boolean mouthFullnessTransitionActive;
    private double mouthFullnessTransitionStart;
    private double mouthFullnessTransitionTarget;
    private int mouthFullnessTransitionTicks;
    private int mouthFullnessTransitionElapsedTicks;
    private OneShotAnimation latchedOneShotAnimation = OneShotAnimation.NONE;
    private KirbySize latchedOneShotAnimationSize = KirbySize.NORMAL;

    private static final int LAND_SOUND_AIR_THRESHOLD = 4;
    public static final int MAX_SMALL_HOLD = 5;

    public KirbyEntity(EntityType<? extends PathfinderMob> type, Level level) {
        super(type, level);
        this.aiBrain.setLaneEnforced(KirbyDecisionLane.LOCOMOTION, true);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_FLIGHT_STATE, 0);
        this.entityData.define(DATA_KIRBY_SIZE, 0);
        this.entityData.define(DATA_COMBAT_STATE, 0);
        this.entityData.define(DATA_MOUTH_FULLNESS, 0.0F);
        this.entityData.define(DATA_HURT_FACE, 0);
        this.entityData.define(DATA_SWIMMING_ACTIVE, false);
        this.entityData.define(DATA_GROUND_RUNNING, false);
    }

    @Override
    public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (this.level().isClientSide
                && (DATA_COMBAT_STATE.equals(key) || DATA_FLIGHT_STATE.equals(key))) {
            updateOneShotAnimationLatch();
        }
        if (this.level().isClientSide && DATA_COMBAT_STATE.equals(key)) {
            CombatState now = getCombatState();
            if (now == CombatState.INHALE && this.lastClientCombatState != CombatState.INHALE) {
                playInhaleSoundClient();
            }
            this.lastClientCombatState = now;
        }
    }

    @OnlyIn(Dist.CLIENT)
    private void playInhaleSoundClient() {
        if (this.activeInhaleSound != null
                && Minecraft.getInstance().getSoundManager().isActive(this.activeInhaleSound)) {
            return;
        }
        SoundEvent evt = getRandom().nextBoolean()
                ? ModSounds.KIRBY_BACUME_1.get()
                : ModSounds.KIRBY_BACUME_2.get();
        this.activeInhaleSound = new KirbyInhaleSoundInstance(this, evt);
        Minecraft.getInstance().getSoundManager().play(this.activeInhaleSound);
    }

    public HurtFace getHurtFace() {
        return HurtFace.byId(this.entityData.get(DATA_HURT_FACE));
    }

    public void setHurtFace(HurtFace face) {
        this.entityData.set(DATA_HURT_FACE, face.ordinal());
    }

    public FlightState getFlightState() {
        return FlightState.byId(this.entityData.get(DATA_FLIGHT_STATE));
    }

    public void setFlightState(FlightState state) {
        this.entityData.set(DATA_FLIGHT_STATE, state.ordinal());
        updateOneShotAnimationLatch();
    }

    public KirbySize getKirbySize() {
        return KirbySize.byId(this.entityData.get(DATA_KIRBY_SIZE));
    }

    public void setKirbySize(KirbySize size) {
        if (getKirbySize() != size) {
            this.entityData.set(DATA_KIRBY_SIZE, size.ordinal());
            this.refreshDimensions();
        }
    }

    public CombatState getCombatState() {
        return CombatState.byId(this.entityData.get(DATA_COMBAT_STATE));
    }

    public void setCombatState(CombatState state) {
        CombatState prev = getCombatState();
        this.entityData.set(DATA_COMBAT_STATE, state.ordinal());
        if (prev.usesLowProfileHitbox() != state.usesLowProfileHitbox()) {
            this.refreshDimensions();
        }
        updateOneShotAnimationLatch();
    }

    @Nullable
    public BlockPos getPendingHighTarget() {
        return this.pendingHighTarget;
    }

    public void setPendingHighTarget(@Nullable BlockPos pos) {
        this.pendingHighTarget = pos;
    }

    boolean storeHeldMob(LivingEntity mob) {
        if (mob == null) return false;
        UUID id = mob.getUUID();
        if (!this.heldMobUUIDs.contains(id)) {
            this.heldMobUUIDs.add(id);
            this.heldMobsCache.add(mob);
            this.heldMobCapturePoints.put(id, KirbyMouthFullness.capturePoints(mob));
            refreshMouthSize();
            syncHeldMobPresentation();
            return true;
        }
        return false;
    }

    void clearStoredHeldMobs() {
        this.heldMobUUIDs.clear();
        this.heldMobsCache.clear();
        this.heldMobCapturePoints.clear();
        refreshMouthSize();
        syncHeldMobPresentation();
    }

    void removeStoredHeldMob(LivingEntity mob) {
        if (mob == null) return;
        UUID id = mob.getUUID();
        this.heldMobUUIDs.remove(id);
        this.heldMobsCache.removeIf(cached -> cached == null || cached.getUUID().equals(id));
        this.heldMobCapturePoints.remove(id);
        refreshMouthSize();
        syncHeldMobPresentation();
    }

    public int getHeldMobPresentationRevisionForDebug() {
        return this.heldMobPresentationRevision;
    }

    public double getMouthFullness() {
        return this.entityData.get(DATA_MOUTH_FULLNESS);
    }

    public double getHeldMobCapturePoints(LivingEntity mob) {
        return mob == null ? 0.0D : this.heldMobCapturePoints.getOrDefault(mob.getUUID(), 0.0D);
    }

    public float getMouthRenderScale() {
        return KirbyMouthFullness.renderScale(getMouthFullness());
    }

    public float getMouthRenderScale(float partialTick) {
        if (!this.level().isClientSide
                || Float.isNaN(this.previousMouthRenderScale)
                || Float.isNaN(this.currentMouthRenderScale)) {
            return getMouthRenderScale();
        }
        return Mth.lerp(Mth.clamp(partialTick, 0.0F, 1.0F),
                this.previousMouthRenderScale, this.currentMouthRenderScale);
    }

    public String getOneShotAnimationLatchForDebug() {
        return this.latchedOneShotAnimation == OneShotAnimation.NONE
                ? "none"
                : this.latchedOneShotAnimation + ":" + this.latchedOneShotAnimationSize;
    }

    public String getMouthFullnessTransitionForDebug() {
        if (!this.mouthFullnessTransitionLocked) {
            return "none";
        }
        return (this.mouthFullnessTransitionActive ? "active" : "held")
                + " " + this.mouthFullnessTransitionElapsedTicks + "/" + this.mouthFullnessTransitionTicks
                + " start=" + this.mouthFullnessTransitionStart
                + " target=" + this.mouthFullnessTransitionTarget;
    }

    public void beginMouthFullnessTransition(double targetFullness, int durationTicks) {
        if (this.level().isClientSide) return;
        this.mouthFullnessTransitionLocked = true;
        this.mouthFullnessTransitionActive = durationTicks > 0;
        this.mouthFullnessTransitionStart = getMouthFullness();
        this.mouthFullnessTransitionTarget = KirbyMouthFullness.clamp(targetFullness);
        this.mouthFullnessTransitionTicks = Math.max(0, durationTicks);
        this.mouthFullnessTransitionElapsedTicks = 0;
        if (!this.mouthFullnessTransitionActive) {
            setMouthFullness(this.mouthFullnessTransitionTarget);
        }
    }

    public void finishMouthFullnessTransition() {
        if (this.level().isClientSide) return;
        this.mouthFullnessTransitionLocked = false;
        this.mouthFullnessTransitionActive = false;
        this.mouthFullnessTransitionElapsedTicks = 0;
        refreshMouthSize();
    }

    public void cancelMouthFullnessTransition() {
        finishMouthFullnessTransition();
    }

    private void refreshMouthSize() {
        if (this.mouthFullnessTransitionLocked) return;
        double fullness = KirbyMouthFullness.clamp(this.heldMobCapturePoints.values().stream()
                .mapToDouble(Double::doubleValue)
                .sum());
        setMouthFullness(fullness);
    }

    private void setMouthFullness(double fullness) {
        float clamped = (float) KirbyMouthFullness.clamp(fullness);
        if (this.entityData.get(DATA_MOUTH_FULLNESS) == clamped) return;
        this.entityData.set(DATA_MOUTH_FULLNESS, clamped);
        KirbySize targetSize = KirbyMouthFullness.animationSize(clamped);
        if (getKirbySize() == targetSize) {
            this.refreshDimensions();
        } else {
            setKirbySize(targetSize);
        }
    }

    private void tickMouthFullnessTransition() {
        if (!this.mouthFullnessTransitionActive) return;
        this.mouthFullnessTransitionElapsedTicks++;
        double progress = (double) this.mouthFullnessTransitionElapsedTicks / this.mouthFullnessTransitionTicks;
        double interpolated = this.mouthFullnessTransitionStart
                + (this.mouthFullnessTransitionTarget - this.mouthFullnessTransitionStart)
                * KirbyMouthFullness.easeOut(progress);
        setMouthFullness(interpolated);
        if (this.mouthFullnessTransitionElapsedTicks >= this.mouthFullnessTransitionTicks) {
            this.mouthFullnessTransitionActive = false;
            setMouthFullness(this.mouthFullnessTransitionTarget);
        }
    }

    public void sendHeldMobPresentationTo(ServerPlayer player) {
        if (this.level().isClientSide) return;
        KirbyTelemetryNetwork.sendHeldMobPresentationTo(player, heldMobPresentationPacket());
    }

    private void syncHeldMobPresentation() {
        if (this.level().isClientSide) return;
        this.heldMobPresentationRevision++;
        KirbyTelemetryNetwork.sendHeldMobPresentation(this, heldMobPresentationPacket());
    }

    private KirbyHeldMobPresentationPacket heldMobPresentationPacket() {
        return new KirbyHeldMobPresentationPacket(this.getId(), this.heldMobPresentationRevision,
                new ArrayList<>(this.heldMobUUIDs));
    }

    /** 解決済み LivingEntity のリストを返す。死亡や未ロードのものは除外。 */
    public List<LivingEntity> getHeldMobs() {
        pruneHeldMobs();
        List<LivingEntity> out = new ArrayList<>();
        if (this.heldMobUUIDs.isEmpty()) return out;
        // First-pass cache check
        for (UUID id : this.heldMobUUIDs) {
            LivingEntity cached = findInCache(id);
            if (isValidHeldMob(cached)) {
                out.add(cached);
                continue;
            }
            if (this.level() instanceof ServerLevel sl) {
                Entity e = sl.getEntity(id);
                if (e instanceof LivingEntity le && isValidHeldMob(le)) {
                    if (!this.heldMobsCache.contains(le)) this.heldMobsCache.add(le);
                    out.add(le);
                }
            }
        }
        return out;
    }

    private void pruneHeldMobs() {
        if (this.heldMobUUIDs.isEmpty()) {
            this.heldMobsCache.clear();
            return;
        }

        this.heldMobsCache.removeIf(mob ->
                !isValidHeldMob(mob) || !this.heldMobUUIDs.contains(mob.getUUID()));

        boolean removedHeldMob = false;
        Iterator<UUID> iter = this.heldMobUUIDs.iterator();
        while (iter.hasNext()) {
            UUID id = iter.next();
            LivingEntity held = findInCache(id);
            if (!isValidHeldMob(held) && this.level() instanceof ServerLevel sl) {
                Entity resolved = sl.getEntity(id);
                if (resolved instanceof LivingEntity le && isValidHeldMob(le)) {
                    held = le;
                    if (!this.heldMobsCache.contains(le)) this.heldMobsCache.add(le);
                }
            }
            if (!isValidHeldMob(held)) {
                iter.remove();
                this.heldMobCapturePoints.remove(id);
                removedHeldMob = true;
            }
        }
        if (removedHeldMob) {
            refreshMouthSize();
            syncHeldMobPresentation();
        }
    }

    private boolean isValidHeldMob(@Nullable LivingEntity mob) {
        return mob != null && mob.isAlive() && !mob.isRemoved();
    }

    @Nullable
    private LivingEntity findInCache(UUID id) {
        for (LivingEntity le : this.heldMobsCache) {
            if (le != null && le.getUUID().equals(id)) return le;
        }
        return null;
    }

    public int getHeldMobCount() {
        pruneHeldMobs();
        return this.heldMobUUIDs.size();
    }

    public int getStoredHeldMobCountForDebug() {
        return this.heldMobUUIDs.size();
    }

    public List<String> getDebugThoughtLines() {
        List<String> lines = new ArrayList<>();
        if (lastHurtFaceTick >= 0 || getHurtFace() != HurtFace.NONE) {
            lines.add(String.format(Locale.ROOT,
                    "DamageFace: face=%s remaining=%d requestedAmount=%.2f source=%s age=%d",
                    getHurtFace(), Math.max(0, this.hurtFaceTicks),
                    this.lastHurtRequestedAmount, this.lastHurtSource,
                    Math.max(0, this.tickCount - this.lastHurtFaceTick)));
            lines.add("DamageFace thought=showing_damage_expression_for_any_successful_damage");
        }
        if (this.isInWater() || isKirbySwimming()) {
            lines.add(String.format(Locale.ROOT,
                    "Swim: inWater=%s underwater=%s active=%s input=%.3f look=%s velocity=%s bodyYaw=%.1f pitch=%.1f air=%d/%d",
                    this.isInWater(), this.isUnderWater(), isKirbySwimming(),
                    this.lastSwimInputStrength, debugVec(this.lastSwimLookDirection),
                    debugVec(this.lastSwimVelocity), this.yBodyRot, this.getXRot(),
                    this.getAirSupply(), this.getMaxAirSupply()));
            lines.add("Swim thought=" + (isKirbySwimming()
                    ? "propelling along full-body look direction"
                    : "idle in water"));
        }
        if (!this.onGround() && !this.isInWater()) {
            lines.add(String.format(Locale.ROOT,
                    "FallPhysics: velocityY=%.3f fallDistance=%.2f gravityScale=%.3f maxFallSpeed=%.2f damage=false",
                    this.getDeltaMovement().y, this.fallDistance,
                    KirbyFallPhysics.FALL_GRAVITY / KirbyFallPhysics.VANILLA_GRAVITY,
                    KirbyFallPhysics.MAX_FALL_SPEED));
            lines.add("FallPhysics thought=soft_body_slow_fall_with_no_impact_damage");
        }
        lines.add(String.format(Locale.ROOT,
                "Footstep: moving=%s gait=%s phase=%.3f/%.3f speedScale=%.2f next=%s last=%s pitch=%.2f",
                this.walkSoundSequence.isMoving(), this.walkSoundSequence.getGait(),
                this.walkSoundSequence.getStepPhaseSeconds(),
                this.walkSoundSequence.getStepIntervalSeconds(),
                this.walkSoundSequence.getSpeedScale(),
                this.walkSoundSequence.getNextSoundName(),
                this.walkSoundSequence.getLastSoundName(),
                this.walkSoundSequence.getLastPitch()));
        lines.add("Footstep thought=matching_sound_cadence_to_gait_animation_and_movement_speed");
        KirbyDebugInfoProviders.append(this.debugInfoProviders, lines);
        return lines;
    }

    public boolean isKirbySwimming() {
        return this.entityData.get(DATA_SWIMMING_ACTIVE);
    }

    private void setKirbySwimming(boolean active) {
        if (!this.level().isClientSide && this.entityData.get(DATA_SWIMMING_ACTIVE) != active) {
            this.entityData.set(DATA_SWIMMING_ACTIVE, active);
        }
    }

    public KirbyAiBrain getAiBrain() {
        return this.aiBrain;
    }

    public KirbyMouthController getMouthController() {
        return this.mouthController;
    }

    public KirbyTargetMemory getTargetMemory() {
        return this.targetScanner.getMemory();
    }

    public String getDebugAnimationName() {
        return chooseDebugAnimation(isMovingHorizontally(), updateOneShotAnimationLatch()).name;
    }

    public String getLastDebugAnimationName() {
        return this.lastDebugAnimationName;
    }

    public KirbyWalkSoundSequence getWalkSoundSequenceForDebug() {
        return this.walkSoundSequence;
    }

    private void addDebugInfoProvider(KirbyDebugInfoProvider provider) {
        this.debugInfoProviders = KirbyDebugInfoProviders.add(this.debugInfoProviders, provider);
    }

    /** 新規 mob を取り込み可能か判定。
     *  - 未保持なら何でも OK
     *  - SMALL を保持中なら SMALL のみ最大 5 体まで
     *  - MIDDLE/BIG 保持中は不可 */
    public boolean canCaptureMore(KirbySize incomingSize) {
        pruneHeldMobs();
        if (this.heldMobUUIDs.isEmpty()) return true;
        KirbySize cur = getKirbySize();
        return cur == KirbySize.SMALL
                && incomingSize == KirbySize.SMALL
                && this.heldMobUUIDs.size() < MAX_SMALL_HOLD;
    }

    @Override
    public EntityDimensions getDimensions(Pose pose) {
        if (getKirbySize() == KirbySize.NORMAL && getCombatState().usesLowProfileHitbox()) {
            EntityDimensions normal = KirbySize.NORMAL.toDimensions();
            return EntityDimensions.scalable(normal.width, normal.height * 0.4F);
        }
        return KirbyMouthFullness.dimensions(getMouthFullness());
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("KirbySize", getKirbySize().ordinal());
        tag.putInt("CombatState", getCombatState().ordinal());
        if (!this.heldMobUUIDs.isEmpty()) {
            ListTag list = new ListTag();
            for (UUID id : this.heldMobUUIDs) {
                CompoundTag entry = new CompoundTag();
                entry.putUUID("UUID", id);
                list.add(entry);
            }
            tag.put("HeldMobs", list);
        }
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        KirbySize loadedSize = KirbySize.NORMAL;
        if (tag.contains("KirbySize")) {
            loadedSize = KirbySize.byId(tag.getInt("KirbySize"));
        }

        CombatState savedCombatState = CombatState.NONE;
        CombatState loadedCombatState = CombatState.NONE;
        if (tag.contains("CombatState")) {
            int savedCombatStateId = tag.getInt("CombatState");
            savedCombatState = CombatState.byId(savedCombatStateId);
            loadedCombatState = CombatState.loadSafeState(savedCombatStateId);
        }

        this.heldMobUUIDs.clear();
        this.heldMobsCache.clear();
        this.heldMobCapturePoints.clear();
        this.entityData.set(DATA_MOUTH_FULLNESS, 0.0F);
        boolean hasSavedHeldMobs = tag.contains("HeldMobs", Tag.TAG_LIST);
        boolean restoreHeldMobs = loadedCombatState.isHolding();
        if (restoreHeldMobs && hasSavedHeldMobs) {
            ListTag list = tag.getList("HeldMobs", Tag.TAG_COMPOUND);
            for (int i = 0; i < list.size(); i++) {
                CompoundTag entry = list.getCompound(i);
                if (entry.hasUUID("UUID")) {
                    this.heldMobUUIDs.add(entry.getUUID("UUID"));
                }
            }
        }

        if (!restoreHeldMobs && (savedCombatState != loadedCombatState || hasSavedHeldMobs)) {
            loadedSize = KirbySize.NORMAL;
        }
        this.entityData.set(DATA_KIRBY_SIZE, loadedSize.ordinal());
        this.entityData.set(DATA_COMBAT_STATE, loadedCombatState.ordinal());
        this.refreshDimensions();
        this.mouthController.resetTracking("entity_data_loaded");
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 20.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.25D)
                .add(Attributes.FOLLOW_RANGE, 36.0D);
    }

    @Override
    protected void registerGoals() {
        KirbyInhaleGoal inhaleGoal = new KirbyInhaleGoal(this);
        KirbyDigestGoal digestGoal = new KirbyDigestGoal(this);
        KirbyFlightGoal flightGoal = new KirbyFlightGoal(this);
        KirbyAutonomousFlightIntentGoal flightIntentGoal =
                new KirbyAutonomousFlightIntentGoal(this);
        KirbyCrouchGoal crouchGoal = new KirbyCrouchGoal(this);
        KirbySwimGoal swimGoal = new KirbySwimGoal(this);
        KirbyThreatTargetGoal threatTargetGoal = new KirbyThreatTargetGoal(this);
        this.groundTargetGoal = new KirbyGroundTargetGoal(this);
        this.wanderGoal = new KirbyWanderGoal(this, 1.0D);
        addDebugInfoProvider(aiBrain);
        addDebugInfoProvider(this.mouthController);
        addDebugInfoProvider(targetScanner);
        addDebugInfoProvider(threatTargetGoal);
        addDebugInfoProvider(inhaleGoal);
        addDebugInfoProvider(digestGoal);
        addDebugInfoProvider(flightGoal);
        addDebugInfoProvider(flightIntentGoal);
        addDebugInfoProvider(crouchGoal);
        addDebugInfoProvider(swimGoal);
        addDebugInfoProvider(this.groundTargetGoal);
        addDebugInfoProvider(this.wanderGoal);

        this.targetSelector.addGoal(0, threatTargetGoal);

        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, crouchGoal);
        this.goalSelector.addGoal(1, new KirbyDodgeJumpGoal(this));
        this.goalSelector.addGoal(1, inhaleGoal);
        this.goalSelector.addGoal(1, digestGoal);
        this.goalSelector.addGoal(2, flightGoal);
        this.goalSelector.addGoal(3, swimGoal);
        this.goalSelector.addGoal(3, this.groundTargetGoal);
        this.goalSelector.addGoal(4, flightIntentGoal);
        this.goalSelector.addGoal(5, this.wanderGoal);
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 6.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
    }

    @Override
    public void tick() {
        if (this.level().isClientSide) {
            tickClientMouthRenderScale();
        } else {
            tickMouthFullnessTransition();
        }
        super.tick();
        if (!this.level().isClientSide) {
            this.mouthController.tick();
        }
        if (this.isUnderWater()) {
            this.setAirSupply(this.getMaxAirSupply());
        }
        if (!this.isInWater()) {
            setKirbySwimming(false);
        }
        // Snapshot pre-update state for land detection
        int prevAirborneFallTicks = this.airborneFallTicks;

        if (!this.onGround() && this.getDeltaMovement().y < 0.0D) {
            this.airborneFallTicks++;
        } else {
            this.airborneFallTicks = 0;
        }
        if (!this.level().isClientSide) {
            setGroundRunning(isServerGroundRunGoal());
        }
        if (this.onGround() && isGroundRunMode() && isMovingHorizontally()) {
            this.runTicks++;
        } else {
            this.runTicks = 0;
        }
        if (!this.level().isClientSide) {
            syncAiBrainObservation();
            tickWalkSound();
        }
        if (!this.level().isClientSide && this.hurtFaceTicks > 0) {
            this.hurtFaceTicks--;
            if (this.hurtFaceTicks == 0) {
                setHurtFace(HurtFace.NONE);
            }
        }
        // Land sound: airborne -> grounded, only if was airborne long enough
        if (!this.level().isClientSide && !this.wasOnGround && this.onGround()
                && prevAirborneFallTicks >= LAND_SOUND_AIR_THRESHOLD) {
            this.level().playSound(null, this.getX(), this.getY(), this.getZ(),
                    ModSounds.KIRBY_LAND.get(), SoundSource.NEUTRAL, 1.0F, 1.0F);
        }
        this.wasOnGround = this.onGround();

        // Purpose-driven high target: tempt item-holding player above kirby
        if (!this.level().isClientSide && this.tickCount % 20 == 0
                && getCombatState() == CombatState.NONE
                && getFlightState() == FlightState.GROUND
                && this.pendingHighTarget == null
                && this.onGround()) {
            Player p = this.level().getNearestPlayer(this, 16.0D);
            if (p != null && KirbyInterestRules.isTempting(p) && (p.getY() - this.getY()) > 1.5D) {
                setPendingHighTarget(p.blockPosition());
            }
        }
        if (!this.level().isClientSide) {
            this.targetScanner.tick();
        }
    }

    @OnlyIn(Dist.CLIENT)
    private void tickClientMouthRenderScale() {
        float targetScale = getMouthRenderScale();
        if (Float.isNaN(this.currentMouthRenderScale)) {
            this.previousMouthRenderScale = targetScale;
            this.currentMouthRenderScale = targetScale;
            return;
        }
        this.previousMouthRenderScale = this.currentMouthRenderScale;
        this.currentMouthRenderScale = targetScale;
    }

    private void tickWalkSound() {
        boolean moving = shouldPlayWalkSound();
        boolean running = moving && isGroundRunMode();
        double speedScale = moving ? getMovementAnimationSpeedScale() : 0.0D;
        KirbyWalkSoundSequence.Gait gait = getWalkSoundGait(running);
        String soundName = this.walkSoundSequence.tick(moving, gait, speedScale);
        if (soundName != null) {
            this.level().playSound(null, this.getX(), this.getY(), this.getZ(),
                    walkSoundFor(soundName), SoundSource.NEUTRAL, 1.0F,
                    this.walkSoundSequence.getLastPitch());
        }
    }

    private KirbyWalkSoundSequence.Gait getWalkSoundGait(boolean running) {
        if (getCombatState() == CombatState.KEEP_HOLDING) {
            switch (getKirbySize()) {
                case MIDDLE: return KirbyWalkSoundSequence.Gait.HELD_MIDDLE;
                case BIG:    return KirbyWalkSoundSequence.Gait.HELD_BIG;
                case SMALL:
                case NORMAL:
                default:     return KirbyWalkSoundSequence.Gait.HELD_SMALL;
            }
        }
        return running ? KirbyWalkSoundSequence.Gait.RUN : KirbyWalkSoundSequence.Gait.WALK;
    }

    private double getMovementAnimationSpeedScale() {
        AttributeInstance movementSpeed = this.getAttribute(Attributes.MOVEMENT_SPEED);
        if (movementSpeed == null || movementSpeed.getBaseValue() <= 0.0D) {
            return 1.0D;
        }
        return clamp(movementSpeed.getValue() / movementSpeed.getBaseValue(),
                MIN_MOVEMENT_ANIMATION_SPEED, MAX_MOVEMENT_ANIMATION_SPEED);
    }

    private static double clamp(double value, double min, double max) {
        return Math.max(min, Math.min(max, value));
    }

    private boolean shouldPlayWalkSound() {
        CombatState combatState = getCombatState();
        return this.wasOnGround
                && this.onGround()
                && isMovingHorizontally()
                && getFlightState() == FlightState.GROUND
                && (combatState == CombatState.NONE || combatState == CombatState.KEEP_HOLDING);
    }

    private static SoundEvent walkSoundFor(String soundName) {
        switch (soundName) {
            case KirbyWalkSoundSequence.WALK_1:
                return ModSounds.KIRBY_WALK_1.get();
            case KirbyWalkSoundSequence.WALK_2:
                return ModSounds.KIRBY_WALK_2.get();
            case KirbyWalkSoundSequence.WALK_3:
            default:
                return ModSounds.KIRBY_WALK_3.get();
        }
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        boolean ok = super.hurt(source, amount);
        KirbyDamageFacePolicy.Severity severity = KirbyDamageFacePolicy.classify(amount);
        if (ok && !this.level().isClientSide
                && severity != KirbyDamageFacePolicy.Severity.NONE) {
            HurtFace pick = severity == KirbyDamageFacePolicy.Severity.CATASTROPHIC
                    ? HurtFace.HURT_2
                    : this.getRandom().nextBoolean() ? HurtFace.HURT_1 : HurtFace.HURT_3;
            setHurtFace(pick);
            this.hurtFaceTicks = HURT_FACE_DURATION;
            this.lastHurtRequestedAmount = amount;
            this.lastHurtSource = source.getMsgId();
            this.lastHurtFaceTick = this.tickCount;
        }
        return ok;
    }

    @Override
    public boolean causeFallDamage(float fallDistance, float multiplier, DamageSource source) {
        this.fallDistance = 0.0F;
        return false;
    }

    private boolean isMovingHorizontally() {
        Vec3 dm = this.getDeltaMovement();
        return (dm.x * dm.x + dm.z * dm.z) > 1.0E-5D;
    }

    private void syncAiBrainObservation() {
        this.aiBrain.observeActive(KirbyDecisionLane.BODY, currentBodyAction(), this.tickCount);
        this.aiBrain.observeActive(KirbyDecisionLane.LOCOMOTION, currentLocomotionAction(), this.tickCount);
        this.aiBrain.observeActive(KirbyDecisionLane.MOUTH, currentMouthAction(), this.tickCount);
        this.aiBrain.observeActive(KirbyDecisionLane.ATTENTION, currentAttentionAction(), this.tickCount);
        this.aiBrain.observeLocomotion(currentLocomotionMode(), this.tickCount);
    }

    private KirbyAiAction currentBodyAction() {
        CombatState combat = getCombatState();
        if (combat.isSliding()) return KirbyAiAction.SLIDE;
        if (combat.isCrouching()) return KirbyAiAction.CROUCH;
        if (getFlightState() == FlightState.DODGE_JUMP) return KirbyAiAction.DODGE_JUMP;
        if (isGoalRunning(FloatGoal.class)) return KirbyAiAction.FLOAT;
        return KirbyAiAction.IDLE;
    }

    private KirbyAiAction currentLocomotionAction() {
        if (this.isInWater()) {
            return isKirbySwimming() ? KirbyAiAction.SWIM : KirbyAiAction.IDLE;
        }
        switch (getFlightState()) {
            case JUMPING:
                return KirbyAiAction.JUMP;
            case ASCEND_PREP:
            case ASCEND_PUMP:
            case DESCEND:
                return KirbyAiAction.FLY;
            case GROUND:
            case DODGE_JUMP:
            default:
                break;
        }
        if (isGoalRunning(KirbySwimGoal.class)) return KirbyAiAction.SWIM;
        if (isGoalRunning(KirbyGroundTargetGoal.class)) return KirbyAiAction.FOLLOW;
        if (isGoalRunning(KirbyWanderGoal.class)) return KirbyAiAction.WANDER;
        return KirbyAiAction.IDLE;
    }

    private KirbyAiAction currentMouthAction() {
        switch (getCombatState()) {
            case INHALE_PREP:
            case INHALE:
            case INHALE_END:
                return KirbyAiAction.INHALE;
            case KEEP_HOLDING:
                return KirbyAiAction.HOLD;
            case KEEP_NOMIKOMI:
                return KirbyAiAction.SWALLOW;
            case KEEP_SPIT:
                return KirbyAiAction.SPIT;
            default:
                return KirbyAiAction.IDLE;
        }
    }

    private KirbyAiAction currentAttentionAction() {
        if (isGoalRunning(LookAtPlayerGoal.class)
                || isGoalRunning(RandomLookAroundGoal.class)) {
            return KirbyAiAction.OBSERVE;
        }
        return KirbyAiAction.IDLE;
    }

    private KirbyLocomotionMode currentLocomotionMode() {
        if (getCombatState().isSliding()) return KirbyLocomotionMode.SLIDE;
        if (this.isInWater()) {
            return isKirbySwimming() ? KirbyLocomotionMode.SWIM : KirbyLocomotionMode.IDLE;
        }
        switch (getFlightState()) {
            case JUMPING:
            case DODGE_JUMP:
                return KirbyLocomotionMode.JUMP;
            case ASCEND_PREP:
            case ASCEND_PUMP:
            case DESCEND:
                return KirbyLocomotionMode.FLY;
            case GROUND:
            default:
                break;
        }
        if (!this.onGround()) return KirbyLocomotionMode.FALL;
        if (!isMovingHorizontally()) return KirbyLocomotionMode.IDLE;
        return isGroundRunMode() && this.runTicks > RUN_START_TICKS
                ? KirbyLocomotionMode.RUN
                : KirbyLocomotionMode.WALK;
    }

    private boolean isGoalRunning(Class<? extends Goal> goalType) {
        return this.goalSelector.getRunningGoals()
                .anyMatch(wrapped -> goalType.isInstance(wrapped.getGoal()));
    }

    private boolean isGroundRunMode() {
        return this.level().isClientSide
                ? this.entityData.get(DATA_GROUND_RUNNING)
                : isServerGroundRunGoal();
    }

    private boolean isServerGroundRunGoal() {
        boolean targetRun = this.groundTargetGoal != null
                && isGoalRunning(KirbyGroundTargetGoal.class)
                && this.groundTargetGoal.isRunMode();
        boolean freeRun = this.wanderGoal != null
                && isGoalRunning(KirbyWanderGoal.class)
                && this.wanderGoal.isRunMode();
        return targetRun || freeRun;
    }

    private void setGroundRunning(boolean running) {
        if (!this.level().isClientSide
                && this.entityData.get(DATA_GROUND_RUNNING) != running) {
            this.entityData.set(DATA_GROUND_RUNNING, running);
        }
    }

    @Override
    public void travel(Vec3 vec) {
        if (this.isInWater() && !this.isPassenger() && getCombatState() == CombatState.NONE) {
            travelInWater(vec);
            return;
        }
        setKirbySwimming(false);
        FlightState fs = getFlightState();
        if (fs == FlightState.GROUND || fs == FlightState.DODGE_JUMP) {
            super.travel(vec);
            applyGentleFallAfterVanillaTravel();
            return;
        }
        if (this.isEffectiveAi() || this.isControlledByLocalInstance()) {
            this.moveRelative(this.getSpeed() * 0.1F, vec);
            Vec3 velocity = this.getDeltaMovement();
            if (velocity.y < -KirbyFallPhysics.MAX_FALL_SPEED) {
                velocity = new Vec3(velocity.x, -KirbyFallPhysics.MAX_FALL_SPEED, velocity.z);
                this.setDeltaMovement(velocity);
            }
            this.move(MoverType.SELF, velocity);
            Vec3 dm = this.getDeltaMovement();
            double nextY = KirbyFallPhysics.applyFlightFall(dm.y);
            this.setDeltaMovement(dm.x * 0.91D, nextY, dm.z * 0.91D);
        }
        this.calculateEntityAnimation(false);
    }

    private void applyGentleFallAfterVanillaTravel() {
        if (this.onGround()
                || this.isInWater()
                || this.isInLava()
                || this.isNoGravity()
                || this.hasEffect(MobEffects.SLOW_FALLING)) {
            return;
        }
        Vec3 dm = this.getDeltaMovement();
        if (dm.y < 0.0D) {
            this.setDeltaMovement(dm.x,
                    KirbyFallPhysics.adjustVanillaFallVelocity(dm.y),
                    dm.z);
        }
    }

    private void travelInWater(Vec3 input) {
        if (this.isEffectiveAi() || this.isControlledByLocalInstance()) {
            if (!this.level().isClientSide && getFlightState() != FlightState.GROUND) {
                setFlightState(FlightState.GROUND);
            }
            Vec3 look = this.getLookAngle();
            Vec3 current = this.getDeltaMovement();
            KirbySwimMotionPolicy.Decision decision = KirbySwimMotionPolicy.decide(
                    look.x, look.y, look.z,
                    current.x, current.y, current.z,
                    input.length(), this.getAttributeValue(Attributes.MOVEMENT_SPEED));
            Vec3 velocity = new Vec3(
                    decision.velocityX(), decision.velocityY(), decision.velocityZ());
            this.setDeltaMovement(velocity);
            this.move(MoverType.SELF, velocity);
            setKirbySwimming(decision.active());
            this.lastSwimInputStrength = decision.inputStrength();
            this.lastSwimLookDirection = look;
            this.lastSwimVelocity = velocity;
            if (decision.active()) {
                alignBodyToSwimDirection(look);
            }
        }
        this.calculateEntityAnimation(false);
    }

    private void alignBodyToSwimDirection(Vec3 direction) {
        double horizontal = Math.sqrt(direction.x * direction.x + direction.z * direction.z);
        if (horizontal < 1.0E-6D && Math.abs(direction.y) < 1.0E-6D) return;
        float yaw = (float) (Mth.atan2(direction.z, direction.x) * Mth.RAD_TO_DEG) - 90.0F;
        float pitch = (float) -(Mth.atan2(direction.y, horizontal) * Mth.RAD_TO_DEG);
        this.setYRot(yaw);
        this.yBodyRot = yaw;
        this.yHeadRot = yaw;
        this.setXRot(Mth.clamp(pitch, -75.0F, 75.0F));
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 4, this::predicate));
    }

    private <T extends KirbyEntity> PlayState predicate(AnimationState<T> state) {
        state.setControllerSpeed(1.0F);
        KirbySize oneShotAnimationSize = updateOneShotAnimationLatch();
        this.lastDebugAnimationName = chooseDebugAnimation(state.isMoving(), oneShotAnimationSize).name;
        CombatState cs = getCombatState();

        switch (cs) {
            case INHALE_PREP: return state.setAndContinue(BACUME_START);
            case INHALE:      return state.setAndContinue(BACUME_LOOP);
            case INHALE_END:  return state.setAndContinue(BACUME_END);
            case CROUCH_PREP: return state.setAndContinue(HUSE);
            case CROUCH_LOOP: return state.setAndContinue(HUSE2);
            case CROUCH_END:  return state.setAndContinue(HUSE3);
            case SLIDE_START: return state.setAndContinue(SLIDE_START);
            case SLIDING: return state.setAndContinue(SLIDING);
            case SLIDE_FINISH: return state.setAndContinue(SLIDE_FINISH);
            case KEEP_NOMIKOMI: return state.setAndContinue(nomikomiFor(oneShotAnimationSize));
            case KEEP_SPIT:     return state.setAndContinue(reverseFor(oneShotAnimationSize));
            case KEEP_HOLDING:
                // KEEP 中: 空中なら size 別 fall_start → fall → land、地上なら walk / idle
                if (!this.onGround() && this.getDeltaMovement().y < -0.05D) {
                    if (this.airborneFallTicks >= LAND_THRESHOLD_TICKS) {
                        return state.setAndContinue(keepLandFor(getKirbySize()));
                    }
                    if (this.airborneFallTicks <= FALL_START_TICKS) {
                        return state.setAndContinue(keepFallStartFor(getKirbySize()));
                    }
                    return state.setAndContinue(keepFallFor(getKirbySize()));
                }
                if (state.isMoving()) {
                    return setMovementAnimation(state, keepWalkFor(getKirbySize()));
                }
                return state.setAndContinue(keepIdleFor(getKirbySize()));
            case NONE:
            default:
                break;
        }

        if (this.isInWater()) {
            return isKirbySwimming()
                    ? state.setAndContinue(SWIM)
                    : state.setAndContinue(IDLE);
        }

        FlightState fs = getFlightState();
        switch (fs) {
            case JUMPING:
            case DODGE_JUMP:
                return state.setAndContinue(jampFor(oneShotAnimationSize));
            case ASCEND_PREP:
                return state.setAndContinue(FLY_START);
            case ASCEND_PUMP:
                return state.setAndContinue(FLY_LOOP);
            case DESCEND:
                if (this.airborneFallTicks < 10) {
                    return state.setAndContinue(FLY_END);
                }
                if (this.airborneFallTicks >= LAND_THRESHOLD_TICKS) {
                    return state.setAndContinue(LAND);
                }
                return state.setAndContinue(FALL);
            case GROUND:
            default:
                if (!this.onGround() && this.getDeltaMovement().y < -0.05D) {
                    if (this.airborneFallTicks >= LAND_THRESHOLD_TICKS) {
                        return state.setAndContinue(LAND);
                    }
                    if (this.airborneFallTicks <= FALL_START_TICKS) {
                        return state.setAndContinue(FALL_START);
                    }
                    return state.setAndContinue(FALL);
                }
                if (state.isMoving()) {
                    if (isGroundRunMode()) {
                        if (this.runTicks <= RUN_START_TICKS) {
                            return setMovementAnimation(state, RUN_START);
                        }
                        return setMovementAnimation(state, RUN);
                    }
                    return setMovementAnimation(state, WALK);
                }
                return state.setAndContinue(IDLE);
        }
    }

    private <T extends KirbyEntity> PlayState setMovementAnimation(AnimationState<T> state, RawAnimation animation) {
        state.setControllerSpeed((float) getMovementAnimationSpeedScale());
        return state.setAndContinue(animation);
    }

    private KirbySize updateOneShotAnimationLatch() {
        OneShotAnimation next = oneShotAnimation();
        if (next == OneShotAnimation.NONE) {
            this.latchedOneShotAnimation = OneShotAnimation.NONE;
            return getKirbySize();
        }
        if (this.latchedOneShotAnimation != next) {
            this.latchedOneShotAnimation = next;
            this.latchedOneShotAnimationSize = getKirbySize();
        }
        return this.latchedOneShotAnimationSize;
    }

    private OneShotAnimation oneShotAnimation() {
        switch (getCombatState()) {
            case KEEP_NOMIKOMI:
                return OneShotAnimation.NOMIKOMI;
            case KEEP_SPIT:
                return OneShotAnimation.SPIT;
            default:
                break;
        }
        switch (getFlightState()) {
            case JUMPING:
            case DODGE_JUMP:
                return OneShotAnimation.JAMP;
            default:
                return OneShotAnimation.NONE;
        }
    }

    private AnimationChoice chooseDebugAnimation(boolean moving, KirbySize oneShotAnimationSize) {
        CombatState cs = getCombatState();

        switch (cs) {
            case INHALE_PREP: return animationChoice(BACUME_START, "animation.kirby.Bacume_start");
            case INHALE:      return animationChoice(BACUME_LOOP, "animation.kirby.Bacume");
            case INHALE_END:  return animationChoice(BACUME_END, "animation.kirby.Bacume_end");
            case CROUCH_PREP: return animationChoice(HUSE, "animation.kirby.Huse");
            case CROUCH_LOOP: return animationChoice(HUSE2, "animation.kirby.Huse2");
            case CROUCH_END:  return animationChoice(HUSE3, "animation.kirby.Huse3");
            case KEEP_NOMIKOMI: return animationChoice(nomikomiFor(oneShotAnimationSize), nomikomiNameFor(oneShotAnimationSize));
            case KEEP_SPIT:     return animationChoice(reverseFor(oneShotAnimationSize), reverseNameFor(oneShotAnimationSize));
            case KEEP_HOLDING:
                if (!this.onGround() && this.getDeltaMovement().y < -0.05D) {
                    if (this.airborneFallTicks >= LAND_THRESHOLD_TICKS) {
                        return animationChoice(keepLandFor(getKirbySize()), keepLandNameFor(getKirbySize()));
                    }
                    if (this.airborneFallTicks <= FALL_START_TICKS) {
                        return animationChoice(keepFallStartFor(getKirbySize()), keepFallStartNameFor(getKirbySize()));
                    }
                    return animationChoice(keepFallFor(getKirbySize()), keepFallNameFor(getKirbySize()));
                }
                if (moving) {
                    return animationChoice(keepWalkFor(getKirbySize()), keepWalkNameFor(getKirbySize()));
                }
                return animationChoice(keepIdleFor(getKirbySize()), keepIdleNameFor(getKirbySize()));
            case NONE:
            default:
                break;
        }

        if (this.isInWater()) {
            return isKirbySwimming()
                    ? animationChoice(SWIM, "swim2")
                    : animationChoice(IDLE, "animation.kirby.idle");
        }

        FlightState fs = getFlightState();
        switch (fs) {
            case JUMPING:
            case DODGE_JUMP:
                return animationChoice(jampFor(oneShotAnimationSize), jampNameFor(oneShotAnimationSize));
            case ASCEND_PREP:
                return animationChoice(FLY_START, "animation.kirby.fly");
            case ASCEND_PUMP:
                return animationChoice(FLY_LOOP, "animation.kirby.fly2");
            case DESCEND:
                if (this.airborneFallTicks < 10) {
                    return animationChoice(FLY_END, "animation.kirby.fly3");
                }
                if (this.airborneFallTicks >= LAND_THRESHOLD_TICKS) {
                    return animationChoice(LAND, "animation.kirby.land");
                }
                return animationChoice(FALL, "animation.kirby.fall");
            case GROUND:
            default:
                if (!this.onGround() && this.getDeltaMovement().y < -0.05D) {
                    if (this.airborneFallTicks >= LAND_THRESHOLD_TICKS) {
                        return animationChoice(LAND, "animation.kirby.land");
                    }
                    if (this.airborneFallTicks <= FALL_START_TICKS) {
                        return animationChoice(FALL_START, "animation.kirby.fall_start");
                    }
                    return animationChoice(FALL, "animation.kirby.fall");
                }
                if (moving) {
                    if (isGroundRunMode()) {
                        if (this.runTicks <= RUN_START_TICKS) {
                            return animationChoice(RUN_START, "animation.kirby.run_start");
                        }
                        return animationChoice(RUN, "animation.kirby.run");
                    }
                    return animationChoice(WALK, "animation.kirby.walk");
                }
                return animationChoice(IDLE, "animation.kirby.idle");
        }
    }

    private static AnimationChoice animationChoice(RawAnimation animation, String name) {
        return new AnimationChoice(animation, name);
    }

    private static String debugVec(Vec3 value) {
        return String.format(Locale.ROOT, "(%.3f,%.3f,%.3f)", value.x, value.y, value.z);
    }

    private static final class AnimationChoice {
        private final RawAnimation animation;
        private final String name;

        private AnimationChoice(RawAnimation animation, String name) {
            this.animation = animation;
            this.name = name;
        }
    }

    private enum OneShotAnimation {
        NONE,
        NOMIKOMI,
        SPIT,
        JAMP
    }

    private static RawAnimation keepIdleFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return KEEP_MIDDLE_IDLE;
            case BIG:    return KEEP_BIG_IDLE;
            case SMALL:
            case NORMAL:
            default:     return KEEP_SMALL_IDLE;
        }
    }

    private static String keepIdleNameFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return "kirby.keep.middle.idle";
            case BIG:    return "kirby.keep.big.idle";
            case SMALL:
            case NORMAL:
            default:     return "kirby.keep.small.idle";
        }
    }

    private static RawAnimation keepWalkFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return KEEP_MIDDLE_WALK;
            case BIG:    return KEEP_BIG_WALK;
            case SMALL:
            case NORMAL:
            default:     return KEEP_SMALL_WALK;
        }
    }

    private static String keepWalkNameFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return "kirby.keep.middle.walk";
            case BIG:    return "kirby.keep.big.walk";
            case SMALL:
            case NORMAL:
            default:     return "kirby.keep.small.walk";
        }
    }

    private static RawAnimation nomikomiFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return KEEP_MIDDLE_NOMIKOMI;
            case BIG:    return KEEP_BIG_NOMIKOMI;
            case SMALL:
            case NORMAL:
            default:     return KEEP_SMALL_NOMIKOMI;
        }
    }

    private static String nomikomiNameFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return "kirby.keep.middle.nomikomi";
            case BIG:    return "kirby.keep.big.nomikomi";
            case SMALL:
            case NORMAL:
            default:     return "kirby.keep.small.nomikomi";
        }
    }

    private static RawAnimation reverseFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return MIDDLE_REVERSE;
            case BIG:    return BIG_REVERSE;
            case SMALL:
            case NORMAL:
            default:     return SMALL_REVERSE;
        }
    }

    private static String reverseNameFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return "kirby.middle.reverse";
            case BIG:    return "kirby.big.reverse";
            case SMALL:
            case NORMAL:
            default:     return "kirby.small.reverse";
        }
    }

    private static RawAnimation keepFallStartFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return KEEP_MIDDLE_FALL_START;
            case BIG:    return KEEP_BIG_FALL_START;
            case SMALL:
            case NORMAL:
            default:     return KEEP_SMALL_FALL_START;
        }
    }

    private static String keepFallStartNameFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return "kirby.keep.middle.fall_start";
            case BIG:    return "kirby.keep.big.fall_start";
            case SMALL:
            case NORMAL:
            default:     return "kirby.keep.small.fall_start";
        }
    }

    private static RawAnimation keepFallFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return KEEP_MIDDLE_FALL;
            case BIG:    return KEEP_BIG_FALL;
            case SMALL:
            case NORMAL:
            default:     return KEEP_SMALL_FALL;
        }
    }

    private static String keepFallNameFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return "kirby.keep.middle.fall";
            case BIG:    return "kirby.keep.big.fall";
            case SMALL:
            case NORMAL:
            default:     return "kirby.keep.small.fall";
        }
    }

    private static RawAnimation keepLandFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return KEEP_MIDDLE_LAND;
            case BIG:    return KEEP_BIG_LAND;
            case SMALL:
            case NORMAL:
            default:     return KEEP_SMALL_LAND;
        }
    }

    private static String keepLandNameFor(KirbySize size) {
        switch (size) {
            case MIDDLE: return "kirby.keep.middle.land";
            case BIG:    return "kirby.keep.big.land";
            case SMALL:
            case NORMAL:
            default:     return "kirby.keep.small.land";
        }
    }

    private static RawAnimation jampFor(KirbySize size) {
        switch (size) {
            case SMALL:  return KEEP_SMALL_JAMP;
            case MIDDLE: return KEEP_MIDDLE_JAMP;
            case BIG:    return KEEP_BIG_JAMP;
            case NORMAL:
            default:     return JAMP_MOLLY;
        }
    }

    private static String jampNameFor(KirbySize size) {
        switch (size) {
            case SMALL:  return "kirby.keep.small.jamp";
            case MIDDLE: return "kirby.keep.middle.jamp";
            case BIG:    return "kirby.keep.big.jamp";
            case NORMAL:
            default:     return "animation.kirby.jamp.molly";
        }
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
