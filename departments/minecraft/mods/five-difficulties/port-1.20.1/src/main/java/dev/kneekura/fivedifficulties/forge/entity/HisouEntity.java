package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.X1Config;
import dev.kneekura.fivedifficulties.forge.item.X1ItemEffects;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import dev.kneekura.fivedifficulties.forge.spellcard.cards.SimpleCards;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityHisou}: the eight swords of the Hisou sword's card. They follow the user 1.2 ahead
 * for 100 ticks, each turning by {@code num / 3 × 39} degrees a tick (X1's {@code count} never grows); sword 8
 * carries the item (its damage) back at the end and fires a random ring of {@code num} red kishitu shots each
 * tick (special 700).
 *
 * X1 also half-mounts the swords on the user; 1.7.10 undoes it on the first tick, so its {@code updateRidden}
 * (slowing the user) never runs. Not ported.
 */
public class HisouEntity extends Entity {
    private static final EntityDataAccessor<Integer> DATA_NUM =
            SynchedEntityData.defineId(HisouEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_ANGLE =
            SynchedEntityData.defineId(HisouEntity.class, EntityDataSerializers.INT);
    public LivingEntity userEntity;
    private Entity motherEntity;
    private int count;
    public int num;
    private int damage;
    private int spellCardUsedTime;

    public HisouEntity(EntityType<? extends HisouEntity> type, Level level) {
        super(type, level);
    }

    public HisouEntity(Level level, LivingEntity user, Entity mother, int n, int damage) {
        this(PortRegistries.HISOU_ENTITY.get(), level);
        this.userEntity = user;
        this.xo = user.getX();
        this.yo = user.getY();
        this.zo = user.getZ();
        float yaw = user.getYRot() / 180F * (float) Math.PI, pitch = user.getXRot() / 180F * (float) Math.PI;
        this.setPos(user.getX() - Math.sin(yaw) * Math.cos(pitch) * 1.2D,
                user.getY() - Math.sin(pitch) * 1.2D + user.getEyeHeight() - 0.7D,
                user.getZ() + Math.cos(yaw) * Math.cos(pitch) * 1.2D);
        this.setYRot(user.getYRot());
        this.motherEntity = mother;
        this.count = 0;
        this.num = n;
        setNum(n);
        this.damage = damage;
        this.spellCardUsedTime = 0;
        level.playSound(null, getX(), getY(), getZ(), PortRegistries.SOUND_MASTERSPARK.get(), SoundSource.NEUTRAL,
                X1Config.hisoutenVol(), 1.0F);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_NUM, 0);
        this.entityData.define(DATA_ANGLE, 0);
    }

    public void setNum(int n) { this.entityData.set(DATA_NUM, n); }
    public int getNum() { return this.entityData.get(DATA_NUM); }
    public void setAngle(float a) { this.entityData.set(DATA_ANGLE, (int) (a * 1000F)); }
    public float getAngle() { return (float) this.entityData.get(DATA_ANGLE) / 1000F; }

    @Override
    public boolean isPushable() {
        return false;
    }

    private void finish() {
        if (getNum() == 8) X1ItemEffects.itemEffectFinish(this, userEntity, PortRegistries.HISOU_SWORD.get(), damage);
        if (!this.level().isClientSide) this.discard();
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide && userEntity == null) {
            if (num == 8) X1ItemEffects.itemEffectFinish(this, userEntity, PortRegistries.HISOU_SWORD.get(), damage);
            else this.discard();
            return;
        }
        setAngle(getAngle() + ((float) count + (float) getNum() / 3.0F) * 39.0F);
        X1ItemEffects.followUser(this, userEntity, 1.2D, 0F);
        if (userEntity != null) {
            this.setYRot(userEntity.getYRot());
            this.setXRot(userEntity.getXRot());
        } else {
            finish();
        }
        if (this.tickCount > spellCardUsedTime && userEntity != null && getNum() == 8 && !this.level().isClientSide) {
            X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_KISHITU, X1ShotTables.RED, 0.5F, 6.0F, 3, 60,
                    SimpleCards.ZenzinruiNoHisouten.SPECIAL_HISOUTEN01);
            var look = userEntity.getLookAngle();
            X1Danmaku.createRandomRingShot(userEntity, this, new Vec3d(getX(), getY(), getZ()), new Vec3d(look.x, look.y, look.z),
                    0F, 9999, 0.1D, 0.8D, 0.05D, Vec3d.ZERO, shot, num, 0.1D, 30F);
        }
        if (this.tickCount > spellCardUsedTime) spellCardUsedTime = this.tickCount;
        if (this.tickCount >= 100) finish();
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putShort("count", (short) count);
        tag.putShort("damage", (short) damage);
        tag.putByte("number", (byte) num);
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        count = tag.getShort("count");
        damage = tag.getShort("damage");
        num = tag.getByte("number");
    }
}
