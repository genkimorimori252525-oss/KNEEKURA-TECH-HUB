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
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;

public final class BedrockWitherEntity extends Monster {
    private static final EntityDataAccessor<Integer> DATA_STATE =
            SynchedEntityData.defineId(BedrockWitherEntity.class, EntityDataSerializers.INT);

    private final ServerBossEvent bossEvent =
            new ServerBossEvent(
                    Component.translatable("entity.kneekura_bedrock_wither.bedrock_wither"),
                    BossEvent.BossBarColor.PURPLE,
                    BossEvent.BossBarOverlay.PROGRESS
            );

    private boolean difficultyHealthInitialized;

    public BedrockWitherEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl(this, 10, true);
        this.setNoGravity(true);
        this.xpReward = 50;
    }

    public static AttributeSupplier.Builder createAttributes() {
        // 600 is the exposed Bedrock base/max value. Difficulty-specific runtime
        // values are a candidate contract until direct Bedrock measurement closes it.
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0D)
                .add(Attributes.FOLLOW_RANGE, 70.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.25D)
                .add(Attributes.FLYING_SPEED, 0.25D)
                .add(Attributes.ARMOR, 4.0D);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
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
        // Intentionally empty in the first scaffold.
        // Bedrock-specific movement, targeting and attacks are added explicitly.
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();

        if (!difficultyHealthInitialized) {
            applyCandidateDifficultyHealth();
            difficultyHealthInitialized = true;
        }

        this.bossEvent.setProgress(this.getHealth() / this.getMaxHealth());
    }

    private void applyCandidateDifficultyHealth() {
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

    public BedrockWitherState getBedrockState() {
        return BedrockWitherState.fromId(this.entityData.get(DATA_STATE));
    }

    public void setBedrockState(BedrockWitherState state) {
        this.entityData.set(DATA_STATE, state.id());
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
        tag.putBoolean("DifficultyHealthInitialized", difficultyHealthInitialized);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        setBedrockState(BedrockWitherState.fromId(tag.getInt("BedrockState")));
        difficultyHealthInitialized = tag.getBoolean("DifficultyHealthInitialized");
    }

    @Override
    public boolean isPushable() {
        return false;
    }
}
