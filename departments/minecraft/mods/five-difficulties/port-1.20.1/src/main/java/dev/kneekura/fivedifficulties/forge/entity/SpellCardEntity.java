package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCard;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardRegistry;
import dev.kneekura.fivedifficulties.forge.timestop.X1TimeStopMovable;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntitySpellCard}: the declared card that floats beside its user and runs the
 * spell card's {@code spellcard_main} once per (non-stopped) tick until its end time.
 */
public final class SpellCardEntity extends Entity implements X1TimeStopMovable {
    private static final EntityDataAccessor<Integer> DATA_NUMBER =
            SynchedEntityData.defineId(SpellCardEntity.class, EntityDataSerializers.INT);

    public LivingEntity user;
    public LivingEntity target;
    public int level;
    public SpellCardCircleEntity circle;
    public boolean canMoveInTimeStop;
    private X1SpellCard useSpellCard;
    private int spellCardUsedTime;
    private int lastTime;

    public SpellCardEntity(EntityType<? extends SpellCardEntity> type, Level level) {
        super(type, level);
    }

    public SpellCardEntity(ServerLevel world, LivingEntity user, LivingEntity target, int number, int spLevel) {
        this(PortRegistries.SPELL_CARD.get(), world);
        float yaw = user.getYRot(), pitch = user.getXRot();
        this.setPos(
                user.getX() - (double) Mth.sin((yaw + 30F) / 180F * 3.141593F) * (double) Mth.cos(pitch / 180F * 3.141593F),
                user.getY() - (double) Mth.sin(pitch / 180F * 3.141593F) + (double) user.getEyeHeight() - 0.10000000149011612D,
                user.getZ() + (double) Mth.cos((yaw + 30F) / 180F * 3.141593F) * (double) Mth.cos(pitch / 180F * 3.141593F));
        this.setYRot(yaw);
        this.setXRot(pitch);
        this.user = user;
        this.target = target;
        this.level = spLevel;
        this.entityData.set(DATA_NUMBER, number);
        X1SpellCardRegistry.Entry entry = X1SpellCardRegistry.get(number);
        if (entry != null) {
            useSpellCard = entry.create();
            useSpellCard.init(world, this, user, target, spLevel);
            canMoveInTimeStop = useSpellCard.canMoveInTimeStop();
            if (user instanceof Player) {
                circle = new SpellCardCircleEntity(world, user, useSpellCard.getSpellCardCircleColor(),
                        useSpellCard.getEndTime());
                world.addFreshEntity(circle);
            }
        } else {
            this.discard();
        }
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_NUMBER, 0);
    }

    public int getSpellCardNumber() {
        return this.entityData.get(DATA_NUMBER);
    }

    public X1SpellCard spellCard() {
        return useSpellCard;
    }

    private void finish() {
        if (this.level().isClientSide) return;
        this.discard();
        if (circle != null) circle.discard();
    }

    @Override
    public void tick() {
        if (this.tickCount <= lastTime) return;
        super.tick();
        if (this.level().isClientSide) return;
        if (user == null || !user.isAlive()) {
            finish();
            return;
        }
        // EntityDanmakuMob "spell card mode" ends its card: arrives with the X1 mobs.
        if (this.tickCount > spellCardUsedTime) {
            if (useSpellCard == null) return;
            if (target == null || !target.isAlive()) target = target == null ? user : target;
            useSpellCard.target = target;
            useSpellCard.onUpdate();
            if (user instanceof Player && this.tickCount < useSpellCard.getRemoveTime()) {
                X1Danmaku.danmakuRemove(user, 40.0F, "Other", true);
            }
            if (useSpellCard.time >= useSpellCard.getEndTime()) {
                finish();
                return;
            }
        }
        if (spellCardUsedTime < this.tickCount) spellCardUsedTime = this.tickCount;
        if (this.tickCount >= 9999) finish();
        if (this.tickCount > lastTime) lastTime = this.tickCount;
    }

    // X1 EntitySakuyaWatch lets a card through when canMoveInTimeStop and its user owns the watch.
    @Override
    public boolean canMoveInX1TimeStop(LivingEntity source) {
        return canMoveInTimeStop && user != null && user.equals(source);
    }

    @Override
    public void onX1TimeStopFieldTick(LivingEntity source) {
        if (useSpellCard != null) useSpellCard.specialProcessInTimeStop();
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
    public boolean shouldBeSaved() {
        return false; // X1 saves nothing
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}
}
