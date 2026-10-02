package org.kneekura.bedrockwither.entity;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.BossEvent;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobType;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

public final class BedrockWitherEntity extends Monster {
    private static final EntityDataAccessor<Integer> DATA_STATE =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.INT);

    private final ServerBossEvent bossEvent =
            new ServerBossEvent(
                    Component.translatable("entity.kneekura_bedrock_wither.bedrock_wither"),
                    BossEvent.BossBarColor.PURPLE,
                    BossEvent.BossBarOverlay.PROGRESS
            );

    private final BedrockWitherStateMachine stateMachine;
    private final BedrockWitherThreatLedger threatLedger = new BedrockWitherThreatLedger();

    private boolean difficultyHealthInitialized;

    public BedrockWitherEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.stateMachine = new BedrockWitherStateMachine(this);
        // Bedrock wither.json exposes movement.basic max_turn 180. The Java
        // FlyingMoveControl is an adaptation layer, but the exposed turn cap is kept exact.
        this.moveControl = new FlyingMoveControl(this, 180, true);
        this.setNoGravity(true);
        this.xpReward = 50;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0D)
                .add(Attributes.FOLLOW_RANGE, 70.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.25D)
                .add(Attributes.FLYING_SPEED, 0.25D)
                .add(Attributes.ARMOR, 4.0D);
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
    }

    @Override
    protected void registerGoals() {
        // Goal wiring is added from Bedrock's exposed goal ordering, not from Java Wither.
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();

        if (!difficultyHealthInitialized) {
            applyCandidateDifficultyHealth();
            difficultyHealthInitialized = true;
        }

        this.stateMachine.tick();
        this.bossEvent.setProgress(this.getHealth() / this.getMaxHealth());
    }

    private void applyCandidateDifficultyHealth() {
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
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        Entity attacker = source.getEntity();

        // Bedrock wither.json damage_sensor: undead damage deals no damage.
        if (attacker instanceof LivingEntity livingAttacker
                && livingAttacker.getMobType() == MobType.UNDEAD) {
            return false;
        }

        boolean accepted = super.hurt(source, amount);
        if (accepted && attacker instanceof LivingEntity livingAttacker && livingAttacker != this) {
            threatLedger.recordDamage(livingAttacker, amount, this.level().getGameTime());
        }
        return accepted;
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

    public BedrockWitherDebugSnapshot debugSnapshot() {
        Vec3 velocity = this.getDeltaMovement();
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
                threatLedger.size()
        );
    }

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        this.bossEvent.addPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        this.bossEvent.removePlayer(player);
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("BedrockState", getBedrockState().id());
        tag.putLong("StateEnteredGameTime", stateMachine.enteredAtGameTime());
        tag.putBoolean("DifficultyHealthInitialized", difficultyHealthInitialized);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        BedrockWitherState restoredState = BedrockWitherState.fromId(tag.getInt("BedrockState"));
        stateMachine.restore(restoredState, tag.getLong("StateEnteredGameTime"));
        difficultyHealthInitialized = tag.getBoolean("DifficultyHealthInitialized");
    }
}
