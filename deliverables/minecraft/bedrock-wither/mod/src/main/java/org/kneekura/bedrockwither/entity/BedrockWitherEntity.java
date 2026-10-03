package org.kneekura.bedrockwither.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.BossEvent;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobType;
import net.minecraft.world.entity.PowerableMob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.entity.ai.BedrockFlyingMoveControl;
import org.kneekura.bedrockwither.entity.ai.BedrockHighestDamageTargetGoal;
import org.kneekura.bedrockwither.entity.ai.BedrockLookGoal;

import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

public final class BedrockWitherEntity extends Monster implements PowerableMob {
    private static final double BEDROCK_BOSS_HUD_RANGE = 55.0D;
    private static final double BEDROCK_BOSS_HUD_RANGE_SQR = BEDROCK_BOSS_HUD_RANGE * BEDROCK_BOSS_HUD_RANGE;
    private static final EntityDataAccessor<Integer> DATA_STATE =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> DATA_AERIAL_ATTACK =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> DATA_SPAWNING_FRAMES =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_DEATH_TICKS =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> DATA_DEATH_OLD_SWELL =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Float> DATA_DEATH_SWELL =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Float> DATA_DEATH_OVERLAY_ALPHA =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Integer> DATA_DEATH_SHIELD_FLICKER =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> DATA_HEAD_PITCH_0 =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Float> DATA_HEAD_PITCH_1 =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Float> DATA_HEAD_PITCH_2 =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Optional<UUID>> DATA_HEAD_TARGET_0 =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.OPTIONAL_UUID);
    private static final EntityDataAccessor<Optional<UUID>> DATA_HEAD_TARGET_1 =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.OPTIONAL_UUID);
    private static final EntityDataAccessor<Optional<UUID>> DATA_HEAD_TARGET_2 =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.OPTIONAL_UUID);

    private final ServerBossEvent bossEvent =
            new ServerBossEvent(
                    Component.translatable("entity.kneekura_bedrock_wither.bedrock_wither"),
                    BossEvent.BossBarColor.PURPLE,
                    BossEvent.BossBarOverlay.PROGRESS
            );

    private final BedrockWitherStateMachine stateMachine;
    private final BedrockWitherThreatLedger threatLedger = new BedrockWitherThreatLedger();
    private final BedrockWitherRuntimeState runtimeState = new BedrockWitherRuntimeState();
    private final BedrockWitherAttackController attackController;
    private final BedrockWitherPhaseController phaseController;
    private final BedrockWitherDestructionController destructionController;
    private final BedrockWitherHurtReactionController hurtReactionController;
    private final BedrockWitherDashController dashController;
    private final BedrockWitherVolleyController volleyController;
    private final BedrockWitherSpawnController spawnController;
    private final BedrockWitherDeathController deathController;
    private final BedrockWitherSpecialMovementController specialMovementController;
    private final BedrockWitherSideHeadController sideHeadController;
    private final BedrockWitherHeadTrackingController headTrackingController;
    private final Set<ServerPlayer> trackingBossPlayers = new HashSet<>();

    private boolean difficultyHealthInitialized;

    public BedrockWitherEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.stateMachine = new BedrockWitherStateMachine(this);
        this.attackController = new BedrockWitherAttackController(this);
        this.phaseController = new BedrockWitherPhaseController(this);
        this.destructionController = new BedrockWitherDestructionController(this);
        this.hurtReactionController = new BedrockWitherHurtReactionController(this);
        this.dashController = new BedrockWitherDashController(this);
        this.volleyController = new BedrockWitherVolleyController(this);
        this.spawnController = new BedrockWitherSpawnController(this);
        this.deathController = new BedrockWitherDeathController(this);
        this.specialMovementController = new BedrockWitherSpecialMovementController(this);
        this.sideHeadController = new BedrockWitherSideHeadController(this);
        this.headTrackingController = new BedrockWitherHeadTrackingController(this);
        this.runtimeState.setNativePhase(BedrockWitherPhaseController.firstPhaseNativeId());
        this.spawnController.initializeNewEntity();
        this.bossEvent.setDarkenScreen(true);
        // Pinned Bedrock movement.basic exposes max_turn=180 degrees/tick.
        // Vanilla FlyingMoveControl hard-codes yaw to 90, so use the bounded
        // KNEEKURA adapter that applies the public 180-degree cap to yaw and pitch.
        this.moveControl = new BedrockFlyingMoveControl(this);
        this.setNoGravity(true);
        this.xpReward = 50;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0D)
                .add(Attributes.FOLLOW_RANGE, 70.0D)
                // Public Bedrock JSON exposes 0.25, but Bedrock native hardcoded
                // reload historically overwrites runtime movement speed to 0.6.
                // Current Bedrock gameplay documentation independently reports 0.6.
                .add(Attributes.MOVEMENT_SPEED, 0.6D)
                .add(Attributes.FLYING_SPEED, 0.6D)
                .add(Attributes.ARMOR, 4.0D);
    }

    public static double maxHealthForDifficulty(Difficulty difficulty) {
        return switch (difficulty) {
            case HARD -> 600.0D;
            case NORMAL -> 450.0D;
            case EASY, PEACEFUL -> 300.0D;
        };
    }

    @Override
    public boolean isPushable() {
        // Pinned format 1.26.50 declares minecraft:pushable_by_entity {}.
        // LivingEntity disables pushing while on a climbable block; Bedrock's
        // pushability component is independent from can_climb, so preserve
        // entity pushing even while the Wither is on a ladder/scaffolding.
        return this.isAlive() && !this.isSpectator();
    }

    @Override
    public boolean requiresCustomPersistence() {
        // Pinned Mojang wither.json: minecraft:persistent {}. A species-level
        // rule also covers old NBT with PersistenceRequired=false. The inherited
        // checkDespawn still handles Peaceful removal before this natural-despawn gate.
        return true;
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        // Bedrock exposes can_fly plus native/unique Wither movement while its public
        // JSON still names navigation.walk. Java needs an actual airborne navigation
        // primitive, so FlyingPathNavigation remains an explicit adaptation, not a
        // claim about Bedrock's hidden native implementation.
        FlyingPathNavigation navigation = new FlyingPathNavigation(this, level);
        navigation.setCanOpenDoors(false);
        navigation.setCanFloat(true);
        navigation.setCanPassDoors(true);
        return navigation;
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_STATE, BedrockWitherState.SPAWN_SEQUENCE.id());
        this.entityData.define(DATA_AERIAL_ATTACK, true);
        // Identical server/client defaults matter for late tracking: completed
        // spawn (zero) must be included in the initial non-default snapshot.
        this.entityData.define(DATA_SPAWNING_FRAMES, BedrockWitherSpawnController.CURRENT_SPAWN_DURATION_TICKS);
        this.entityData.define(DATA_DEATH_TICKS, 0);
        this.entityData.define(DATA_DEATH_OLD_SWELL, 0.0F);
        this.entityData.define(DATA_DEATH_SWELL, 0.0F);
        this.entityData.define(DATA_DEATH_OVERLAY_ALPHA, 0.0F);
        this.entityData.define(DATA_DEATH_SHIELD_FLICKER, 0);
        this.entityData.define(DATA_HEAD_PITCH_0, 0.0F);
        this.entityData.define(DATA_HEAD_PITCH_1, 0.0F);
        this.entityData.define(DATA_HEAD_PITCH_2, 0.0F);
        this.entityData.define(DATA_HEAD_TARGET_0, Optional.empty());
        this.entityData.define(DATA_HEAD_TARGET_1, Optional.empty());
        this.entityData.define(DATA_HEAD_TARGET_2, Optional.empty());
    }

    @Override
    protected void registerGoals() {
        // Current Mojang Bedrock wither.json generic goal ordering.
        // behavior.float is an exposed priority-1 contract. It only owns JUMP,
        // leaving the Wither's dedicated MOVE/attack controllers authoritative.
        this.goalSelector.addGoal(1, new FloatGoal(this));

        // The special reposition controller owns movement whenever combat or a
        // lifecycle gate is active. Idle stroll must not overwrite its navigator.
        this.goalSelector.addGoal(5, new RandomStrollGoal(this, 1.0D) {
            @Override public boolean canUse() { return canRunIdleMovement() && super.canUse(); }
            @Override public boolean canContinueToUse() {
                return canRunIdleMovement() && super.canContinueToUse();
            }
        });
        // Pinned Bedrock Wither: look_at_target priority 5 and look_at_player
        // priority 6, explicit 1..2 second look_time. Public component defaults
        // provide look_distance=8 and probability=0.02.
        this.goalSelector.addGoal(5, new BedrockLookGoal(this, BedrockLookGoal.Source.CURRENT_TARGET));
        this.goalSelector.addGoal(6, new BedrockLookGoal(this, BedrockLookGoal.Source.NEAREST_PLAYER));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));

        // Current Mojang Bedrock target ordering:
        // 1 = wither_target_highest_damage
        // 2 = hurt_by_target
        // 3 = nearest_attackable_target
        this.targetSelector.addGoal(1, new BedrockHighestDamageTargetGoal(this));
        this.targetSelector.addGoal(2, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(
                3,
                new NearestAttackableTargetGoal<>(
                        this,
                        LivingEntity.class,
                        10,
                        true,
                        false,
                        this::isBedrockNearestTargetCandidate
                )
        );
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.WITHER_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.WITHER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.WITHER_DEATH;
    }

    private boolean canRunIdleMovement() {
        return isAlive() && getTarget() == null
                && getBedrockState() == BedrockWitherState.PHASE1_REPOSITION
                && !runtimeState.pathing() && !runtimeState.wantsMove()
                && !spawnController.isActive() && !deathController.isActive();
    }

    /** Guard active adapters before the next target-selector maintenance tick. */
    public boolean isValidCombatTarget(LivingEntity target) {
        return target != null && target.isAlive() && target.level() == this.level()
                && (!(target instanceof net.minecraft.world.entity.player.Player player)
                || (!player.isCreative() && !player.isSpectator() && this.canAttack(player)));
    }

    private boolean isBedrockNearestTargetCandidate(LivingEntity candidate) {
        // Bedrock target filter accepts players and non-undead/non-inanimate targets.
        // ArmorStand is a Java LivingEntity but is the clearest Java analogue of
        // Bedrock's inanimate family and must not enter the generic target branch.
        return candidate != this
                && !(candidate instanceof ArmorStand)
                && candidate.getMobType() != MobType.UNDEAD;
    }

    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide) dashController.afterEntityMovement();
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();

        if (!difficultyHealthInitialized) {
            applyBedrockDifficultyHealth();
            difficultyHealthInitialized = true;
        }

        this.spawnController.tick();
        this.stateMachine.tick();
        this.phaseController.tick();
        if (this.spawnController.isActive() || this.deathController.isActive()) {
            this.specialMovementController.cancelPath();
        } else if (this.getBedrockState() != BedrockWitherState.PHASE_TRANSITION) {
            this.hurtReactionController.tick();
            this.dashController.tick();
            this.specialMovementController.tick();
            this.volleyController.tick();
            this.sideHeadController.tick();
        }
        this.headTrackingController.tick();
        this.bossEvent.setProgress(this.getHealth() / this.getMaxHealth());
        updateBossBarPlayers();
    }

    private void applyBedrockDifficultyHealth() {
        // Public Bedrock JSON exposes 600. Difficulty-specific 300/450/600 remains
        // secondary-observation-backed until direct Bedrock measurement closes it.
        Difficulty difficulty = this.level().getDifficulty();
        double maxHealth = switch (difficulty) {
            case HARD -> 600.0D;
            case NORMAL -> 450.0D;
            case EASY, PEACEFUL -> 300.0D;
        };

        AttributeInstance maxHealthAttribute = this.getAttribute(Attributes.MAX_HEALTH);
        if (maxHealthAttribute != null) {
            maxHealthAttribute.setBaseValue(maxHealth);
        }
        this.setHealth((float) maxHealth);
        this.phaseController.initializeForCurrentDifficulty();
        this.volleyController.initializeForCurrentDifficulty();
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        Entity attacker = source.getEntity();

        // Modern Bedrock spawn sequence is invulnerable. Preserve bypass sources
        // so administrative/void-style damage semantics are not silently blocked.
        if (spawnController.isActive()
                && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return false;
        }

        // Current Bedrock phase 2 rejects projectile damage. Keep this separate
        // from the undead family damage sensor so each contract can be tested.
        if (phaseController.isSecondPhase() && source.getDirectEntity() instanceof Projectile) {
            return false;
        }

        // Bedrock wither.json damage_sensor: undead damage deals no damage.
        if (attacker instanceof LivingEntity livingAttacker
                && livingAttacker.getMobType() == MobType.UNDEAD) {
            return false;
        }

        boolean accepted = super.hurt(source, amount);
        if (accepted && attacker instanceof LivingEntity livingAttacker && livingAttacker != this) {
            threatLedger.recordDamage(livingAttacker, amount, this.level().getGameTime());
            hurtReactionController.onAcceptedDamage(livingAttacker);
        }
        if (accepted && this.isAlive()) volleyController.onAcceptedDamage();
        return accepted;
    }

    @Override
    public void die(DamageSource source) {
        // Forge may cancel semantic death (for example, a revival listener).
        // The inherited dead flag is set only after that event accepts death;
        // health-based isAlive/isDeadOrDying cannot distinguish the decision.
        super.die(source);
        if (this.dead
                && !this.isRemoved()
                && getBedrockState() != BedrockWitherState.DEATH_SEQUENCE
                && getDeathTicksRemaining() <= 0) {
            deathController.begin();
        }
    }

    @Override
    public net.minecraft.world.entity.item.ItemEntity spawnAtLocation(
            net.minecraft.world.item.ItemStack stack, float offset) {
        net.minecraft.world.entity.item.ItemEntity dropped = super.spawnAtLocation(stack, offset);
        if (dropped != null && stack.is(net.minecraft.world.item.Items.NETHER_STAR)) {
            // The retained Minecraft Wiki Bedrock drop contract specifies no
            // timed despawning. Java's unlimited-age flag also survives item NBT.
            // Preserve the ordinary Forge loot/event path and item count.
            dropped.setUnlimitedLifetime();
        }
        return dropped;
    }

    @Override
    public boolean killedEntity(ServerLevel level, LivingEntity victim) {
        boolean accepted = super.killedEntity(level, victim);
        if (accepted) {
            createBedrockWitherRose(level, victim);
        }
        return accepted;
    }

    /**
     * LivingEntity.createWitherRose is hard-wired to Java WitherBoss kill credit.
     * This independent Monster therefore bridges the same Java integration
     * contract explicitly: place when mobGriefing allows and the rose survives,
     * otherwise drop exactly one rose item at the victim.
     */
    private void createBedrockWitherRose(ServerLevel level, LivingEntity victim) {
        boolean placed = false;
        if (level.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)) {
            BlockPos pos = victim.blockPosition();
            BlockState rose = Blocks.WITHER_ROSE.defaultBlockState();
            if (level.getBlockState(pos).isAir() && rose.canSurvive(level, pos)) {
                level.setBlock(pos, rose, 3);
                placed = true;
            }
        }

        if (!placed) {
            level.addFreshEntity(new ItemEntity(
                    level,
                    victim.getX(),
                    victim.getY(),
                    victim.getZ(),
                    new ItemStack(Items.WITHER_ROSE)
            ));
        }
    }

    @Override
    protected void tickDeath() {
        if (this.level().isClientSide) {
            // Server-synchronized Wither death state drives visuals/removal.
            // Suppress Java's ordinary 20-tick side-fall removal timer.
            this.deathTime = 0;
            return;
        }
        deathController.tickServer();
    }

    @Override
    public boolean canBeAffected(MobEffectInstance effect) {
        // Current BDS exposes WitherBoss::canBeAffected, and historical Bedrock
        // native code accepts only Instant Health / Instant Damage. As an undead
        // mob Java applies their effects with the expected reversed semantics.
        return effect.getEffect() == MobEffects.HEAL
                || effect.getEffect() == MobEffects.HARM;
    }

    @Override
    public MobType getMobType() {
        // Bedrock type_family explicitly includes "undead".
        return MobType.UNDEAD;
    }

    @Override
    public boolean canBreatheUnderwater() {
        // Bedrock breathable component: breathes_water=true, suffocate_time=0.
        return true;
    }

    @Override
    public boolean canFreeze() {
        // Bedrock wither.json: minecraft:freezing_immune.
        return false;
    }

    public boolean isAerialAttack() {
        return this.entityData.get(DATA_AERIAL_ATTACK);
    }

    public void setAerialAttack(boolean value) {
        this.entityData.set(DATA_AERIAL_ATTACK, value);
    }

    @Override
    public boolean isPowered() {
        // Current Bedrock NBT/visual contract: AirAttack=1 -> first phase,
        // powered shield hidden; AirAttack=0 -> second phase, shield visible.
        return !isAerialAttack();
    }

    public int getVisualInvulnerableTicks() {
        if (getDeathTicksRemaining() > 0) {
            return getDeathTicksRemaining();
        }
        return this.entityData.get(DATA_SPAWNING_FRAMES);
    }

    void setSpawningFrames(int value) {
        int bounded = Math.max(0, value);
        runtimeState.setSpawningFrames(bounded);
        this.entityData.set(DATA_SPAWNING_FRAMES, bounded);
    }

    public int getDeathTicksRemaining() {
        return this.entityData.get(DATA_DEATH_TICKS);
    }

    public void setDeathTicksRemaining(int value) {
        this.entityData.set(DATA_DEATH_TICKS, Math.max(0, value));
    }

    public float getDeathOldSwell() {
        return this.entityData.get(DATA_DEATH_OLD_SWELL);
    }

    public void setDeathOldSwell(float value) {
        this.entityData.set(DATA_DEATH_OLD_SWELL, Math.max(0.0F, value));
    }

    public float getDeathSwell() {
        return this.entityData.get(DATA_DEATH_SWELL);
    }

    public void setDeathSwell(float value) {
        this.entityData.set(DATA_DEATH_SWELL, Math.max(0.0F, value));
    }

    public float getDeathOverlayAlpha() {
        return this.entityData.get(DATA_DEATH_OVERLAY_ALPHA);
    }

    public void setDeathOverlayAlpha(float value) {
        this.entityData.set(DATA_DEATH_OVERLAY_ALPHA, Math.max(0.0F, Math.min(1.0F, value)));
    }

    public int getDeathShieldFlicker() {
        return this.entityData.get(DATA_DEATH_SHIELD_FLICKER);
    }

    public void setDeathShieldFlicker(int value) {
        this.entityData.set(DATA_DEATH_SHIELD_FLICKER, Math.max(0, value));
    }

    public float getBedrockSwellAmount(float partialTick) {
        return deathController.swellAmount(partialTick);
    }

    public BedrockWitherState getBedrockState() {
        return BedrockWitherState.fromId(this.entityData.get(DATA_STATE));
    }

    public void setBedrockState(BedrockWitherState state) {
        this.entityData.set(DATA_STATE, state.id());
    }

    public BedrockWitherStateMachine stateMachine() {
        return stateMachine;
    }

    public BedrockWitherThreatLedger threatLedger() {
        return threatLedger;
    }

    public BedrockWitherRuntimeState runtimeState() {
        return runtimeState;
    }

    public float getSyncedHeadPitch(int headIndex) {
        return this.entityData.get(headPitchAccessor(headIndex));
    }

    public void setSyncedHeadPitch(int headIndex, float pitch) {
        this.entityData.set(headPitchAccessor(headIndex), pitch);
    }

    private static EntityDataAccessor<Float> headPitchAccessor(int headIndex) {
        return switch (headIndex) {
            case 0 -> DATA_HEAD_PITCH_0;
            case 1 -> DATA_HEAD_PITCH_1;
            case 2 -> DATA_HEAD_PITCH_2;
            default -> throw new IndexOutOfBoundsException("Wither head index must be 0..2: " + headIndex);
        };
    }

    public Optional<UUID> getAlternativeHeadTarget(int headIndex) {
        return this.entityData.get(headTargetAccessor(headIndex));
    }

    public void setAlternativeHeadTarget(int headIndex, UUID targetUuid) {
        this.entityData.set(headTargetAccessor(headIndex), Optional.ofNullable(targetUuid));
    }

    public void clearAlternativeHeadTarget(int headIndex) {
        this.entityData.set(headTargetAccessor(headIndex), Optional.empty());
    }

    private static EntityDataAccessor<Optional<UUID>> headTargetAccessor(int headIndex) {
        return switch (headIndex) {
            case 0 -> DATA_HEAD_TARGET_0;
            case 1 -> DATA_HEAD_TARGET_1;
            case 2 -> DATA_HEAD_TARGET_2;
            default -> throw new IndexOutOfBoundsException("Wither head index must be 0..2: " + headIndex);
        };
    }

    public BedrockWitherAttackController attackController() {
        return attackController;
    }

    public BedrockWitherPhaseController phaseController() {
        return phaseController;
    }

    public BedrockWitherDestructionController destructionController() {
        return destructionController;
    }

    public BedrockWitherHurtReactionController hurtReactionController() {
        return hurtReactionController;
    }

    public BedrockWitherDashController dashController() {
        return dashController;
    }

    public BedrockWitherVolleyController volleyController() {
        return volleyController;
    }

    public BedrockWitherSpawnController spawnController() {
        return spawnController;
    }

    public BedrockWitherDeathController deathController() {
        return deathController;
    }

    public BedrockWitherSpecialMovementController specialMovementController() {
        return specialMovementController;
    }

    public BedrockWitherSideHeadController sideHeadController() {
        return sideHeadController;
    }

    public BedrockWitherHeadTrackingController headTrackingController() {
        return headTrackingController;
    }

    public BedrockWitherDebugSnapshot debugSnapshot() {
        Vec3 velocity = this.getDeltaMovement();
        Vec3 chargeDirection = runtimeState.chargeDirection();
        return new BedrockWitherDebugSnapshot(
                this.getId(),
                getBedrockState(),
                stateMachine.ticksInState(),
                this.getHealth(),
                this.getMaxHealth(),
                this.level().getDifficulty().name(),
                this.getX(),
                this.getY(),
                this.getZ(),
                velocity.x,
                velocity.y,
                velocity.z,
                threatLedger.size(),
                List.of(
                        headSnapshot(0),
                        headSnapshot(1),
                        headSnapshot(2)
                ),
                runtimeState.nativePhase(),
                isAerialAttack(),
                isPowered(),
                getDeathTicksRemaining(),
                getDeathSwell(),
                getDeathOverlayAlpha(),
                getDeathShieldFlicker(),
                runtimeState.wantsToExplode(),
                runtimeState.charging(),
                chargeDirection.x,
                chargeDirection.y,
                chargeDirection.z,
                runtimeState.chargeFrames(),
                runtimeState.preparingCharge(),
                runtimeState.projectileCounter(),
                runtimeState.spawningFrames(),
                runtimeState.timeTillNextShot(),
                runtimeState.fireRate(),
                runtimeState.stunTimer(),
                runtimeState.framesTillMove(),
                runtimeState.wantsMove(),
                runtimeState.pathing(),
                runtimeState.numSkeletons(),
                runtimeState.maxSkeletons(),
                runtimeState.movementTime(),
                runtimeState.healthIntervals(),
                runtimeState.lastHealthValue(),
                runtimeState.delayShot(),
                runtimeState.timeSinceLastShot(),
                runtimeState.attackRange(),
                runtimeState.secondVolley(),
                runtimeState.mainHeadAttackCountdown(),
                runtimeState.lastFiredHead()
        );
    }

    private BedrockWitherHeadDebugSnapshot headSnapshot(int index) {
        BedrockWitherHeadRuntime head = runtimeState.head(index);
        return new BedrockWitherHeadDebugSnapshot(
                index,
                head.yaw(),
                head.pitch(),
                head.oldYaw(),
                head.oldPitch(),
                head.nextUpdate(),
                head.idleUpdates(),
                getAlternativeHeadTarget(index)
        );
    }

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        trackingBossPlayers.add(player);
        updateBossBarPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        trackingBossPlayers.remove(player);
        this.bossEvent.removePlayer(player);
    }

    private void updateBossBarPlayers() {
        for (ServerPlayer player : List.copyOf(trackingBossPlayers)) {
            if (player.isRemoved()) {
                trackingBossPlayers.remove(player);
                bossEvent.removePlayer(player);
                continue;
            }
            updateBossBarPlayer(player);
        }
    }

    private void updateBossBarPlayer(ServerPlayer player) {
        // Bedrock minecraft:boss exposes hud_range=55.
        if (player.level() == this.level()
                && player.isAlive()
                && this.distanceToSqr(player) <= BEDROCK_BOSS_HUD_RANGE_SQR) {
            bossEvent.addPlayer(player);
        } else {
            bossEvent.removePlayer(player);
        }
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("BedrockState", getBedrockState().id());
        tag.putLong("StateEnteredGameTime", stateMachine.enteredAtGameTime());
        tag.putBoolean("DifficultyHealthInitialized", difficultyHealthInitialized);
        tag.putInt("NativePhase", runtimeState.nativePhase());
        tag.putBoolean("AirAttack", isAerialAttack());
        tag.putInt("HealthThreshold", runtimeState.healthThreshold());
        tag.putBoolean("WantsToExplode", runtimeState.wantsToExplode());
        tag.putInt("NumSkeletons", runtimeState.numSkeletons());
        tag.putInt("MaxSkeletons", runtimeState.maxSkeletons());
        tag.putInt("DestroyBlocksTick", runtimeState.destroyBlocksTick());
        tag.putInt("ProjectileCounter", runtimeState.projectileCounter());
        tag.putInt("FireRate", runtimeState.fireRate());
        tag.putInt("HealthIntervals", runtimeState.healthIntervals());
        tag.putInt("HistoricalRateHealthCursor", runtimeState.historicalRateHealthCursor());
        tag.putBoolean("SecondVolley", runtimeState.secondVolley());
        tag.putInt("TransitionTicks", runtimeState.transitionTicks());
        tag.putInt("LastHealthValue", runtimeState.lastHealthValue());
        tag.putInt("DelayShot", runtimeState.delayShot());
        tag.putInt("TimeSinceLastShot", runtimeState.timeSinceLastShot());
        tag.putInt("MainHeadAttackCountdown", runtimeState.mainHeadAttackCountdown());
        tag.putInt("SpawningFrames", runtimeState.spawningFrames());
        tag.putInt("DyingFrames", getDeathTicksRemaining());
        tag.putFloat("DeathOldSwell", getDeathOldSwell());
        tag.putFloat("DeathSwell", getDeathSwell());
        tag.putFloat("DeathOverlayAlpha", getDeathOverlayAlpha());
        tag.putInt("DeathShieldFlicker", getDeathShieldFlicker());
        hurtReactionController.addAdditionalSaveData(tag);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        BedrockWitherState restoredState = BedrockWitherState.fromId(tag.getInt("BedrockState"));
        boolean interruptedCharge = restoredState == BedrockWitherState.PHASE2_DASH
                || restoredState == BedrockWitherState.PHASE2_DASH_PREP;
        // A live target and path cannot be serialized reliably. Cancel motion even
        // when load() reuses an existing object, then recover in a valid phase.
        dashController.stopDash();
        specialMovementController.cancelPath();
        if (interruptedCharge) restoredState = BedrockWitherState.PHASE2_RECOVER;
        if (restoredState == BedrockWitherState.PHASE1_HURT_REACTION) {
            // Hurt destruction has its own persisted countdown. This obsolete
            // transient state must not strand the ordinary center-head scheduler.
            restoredState = BedrockWitherState.PHASE1_REPOSITION;
        }
        stateMachine.restore(restoredState, tag.getLong("StateEnteredGameTime"));
        difficultyHealthInitialized = tag.getBoolean("DifficultyHealthInitialized");

        if (tag.contains("AirAttack")) {
            setAerialAttack(tag.getBoolean("AirAttack"));
        } else {
            setAerialAttack(restoredState != BedrockWitherState.PHASE2_DASH_PREP
                    && restoredState != BedrockWitherState.PHASE2_DASH
                    && restoredState != BedrockWitherState.PHASE2_RECOVER
                    && restoredState != BedrockWitherState.PHASE2_BURST
                    && restoredState != BedrockWitherState.PHASE2_COOLDOWN
                    && restoredState != BedrockWitherState.PHASE_TRANSITION
                    && restoredState != BedrockWitherState.DEATH_SEQUENCE);
        }

        if (tag.contains("NativePhase")) {
            runtimeState.setNativePhase(tag.getInt("NativePhase"));
        } else {
            runtimeState.setNativePhase(isAerialAttack()
                    ? BedrockWitherPhaseController.firstPhaseNativeId()
                    : BedrockWitherPhaseController.secondPhaseNativeId());
        }
        if (tag.contains("HealthThreshold")) {
            runtimeState.setHealthThreshold(tag.getInt("HealthThreshold"));
        } else {
            runtimeState.setHealthThreshold(Math.round(this.getMaxHealth()) / 2);
        }
        runtimeState.setWantsToExplode(tag.getBoolean("WantsToExplode"));
        runtimeState.setNumSkeletons(tag.getInt("NumSkeletons"));
        runtimeState.setMaxSkeletons(tag.getInt("MaxSkeletons"));
        runtimeState.setDestroyBlocksTick(tag.getInt("DestroyBlocksTick"));
        runtimeState.setProjectileCounter(tag.getInt("ProjectileCounter"));
        runtimeState.setFireRate(tag.contains("FireRate") ? Math.max(1, tag.getInt("FireRate"))
                : BedrockWitherVolleyController.PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS);
        runtimeState.setHealthIntervals(Math.max(1, Math.round(getMaxHealth()) / 6));
        runtimeState.setHistoricalRateHealthCursor(tag.contains("HistoricalRateHealthCursor")
                ? tag.getInt("HistoricalRateHealthCursor") : Math.round(getHealth()));
        runtimeState.setSecondVolley(tag.getBoolean("SecondVolley"));
        runtimeState.setTransitionTicks(Math.min(BedrockWitherPhaseController.ADAPTER_MAX_DESCENT_TICKS,
                tag.getInt("TransitionTicks")));
        volleyController.restoreLastHealthInterval(tag.getInt("LastHealthValue"));
        runtimeState.setDelayShot(interruptedCharge ? BedrockWitherDashController.HISTORICAL_RECOVERY_TICKS
                : Math.max(0, tag.getInt("DelayShot")));
        runtimeState.setTimeSinceLastShot(tag.getInt("TimeSinceLastShot"));
        runtimeState.setMainHeadAttackCountdown(Math.max(1, tag.getInt("MainHeadAttackCountdown")));
        runtimeState.setTimeTillNextShot(runtimeState.mainHeadAttackCountdown());
        int spawningFrames = tag.contains("SpawningFrames")
                ? tag.getInt("SpawningFrames")
                : 0;
        spawnController.restore(spawningFrames, restoredState);
        deathController.restore(
                tag.getInt("DyingFrames"),
                tag.getFloat("DeathOldSwell"),
                tag.getFloat("DeathSwell"),
                tag.getFloat("DeathOverlayAlpha"),
                tag.getInt("DeathShieldFlicker"),
                restoredState
        );
        hurtReactionController.readAdditionalSaveData(tag);
    }
}
