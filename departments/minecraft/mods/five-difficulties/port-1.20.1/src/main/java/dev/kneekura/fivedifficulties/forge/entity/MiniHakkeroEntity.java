package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.item.X1ItemEffects;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityMiniHakkero}. It sits one block in front of the user's eyes and carries a
 * Master Spark set laser (ID 24, width 4.2, delay 30, end 120): the spell card's is 60 long with damage 8,
 * the item's 40 long and explosive (EXPLOSION01). It leaves at tick 109; the item's turns back into the
 * Mini Hakkero item.
 */
public class MiniHakkeroEntity extends Entity {

    public LivingEntity user;
    private LivingEntity tgEntity;
    public int count;
    private int damage;
    private float circleAngle;
    private int lastTime;
    private boolean isSpellCard;

    public MiniHakkeroEntity(EntityType<? extends MiniHakkeroEntity> type, Level level) {
        super(type, level);
        this.blocksBuilding = true; // preventEntitySpawning
    }

    /** Item constructor (ItemMiniHakkero): {@code da} is the item's damage value. */
    public MiniHakkeroEntity(Level level, LivingEntity user, int da) {
        this(PortRegistries.MINI_HAKKERO.get(), level);
        place(user);
        this.tgEntity = null;
        this.count = 0;
        this.circleAngle = 0F;
        this.damage = da;
        this.isSpellCard = false;
        level.playSound(null, this.getX(), this.getY(), this.getZ(), PortRegistries.SOUND_MASTERSPARK.get(),
                SoundSource.NEUTRAL, dev.kneekura.fivedifficulties.forge.X1Config.masterSparkVol(), 1.0F);
        this.lastTime = 0;
        X1Danmaku.createLaserB(user, this, X1Danmaku.pos_Entity(this), X1Danmaku.getVecFromAngle(getYRot(), getXRot()),
                X1Danmaku.rotate_Default(), 0.0F, 9999,
                X1LaserData.laser(24, 4.2F, 40.0F, 8.0F, 30, 120, X1ShotTables.EXPLOSION01), this, 1.0D, 0.0F);
    }

    private void place(LivingEntity user) {
        this.user = user;
        float yaw = user.getYRot(), pitch = user.getXRot();
        this.setPos(user.getX() - Math.sin(yaw / 180F * 3.141593F) * Math.cos(pitch / 180F * 3.141593F),
                user.getY() - Math.sin(pitch / 180F * 3.141593F) + (double) user.getEyeHeight() - 0.10000000149011612D,
                user.getZ() + Math.cos(yaw / 180F * 3.141593F) * Math.cos(pitch / 180F * 3.141593F));
        this.setYRot(yaw);
        this.setXRot(pitch);
        this.yRotO = yaw;
        this.xRotO = pitch;
    }

    public MiniHakkeroEntity(Level level, LivingEntity user, LivingEntity target) {
        this(PortRegistries.MINI_HAKKERO.get(), level);
        this.user = user;
        float yaw = user.getYRot(), pitch = user.getXRot();
        this.setPos(user.getX() - Math.sin(yaw / 180F * 3.141593F) * Math.cos(pitch / 180F * 3.141593F),
                user.getY() - Math.sin(pitch / 180F * 3.141593F) + (double) user.getEyeHeight() - 0.10000000149011612D,
                user.getZ() + Math.cos(yaw / 180F * 3.141593F) * Math.cos(pitch / 180F * 3.141593F));
        this.setYRot(yaw);
        this.setXRot(pitch);
        this.yRotO = yaw;
        this.xRotO = pitch;
        this.tgEntity = target;
        this.count = 0;
        this.circleAngle = 0F;
        level.playSound(null, this.getX(), this.getY(), this.getZ(), PortRegistries.SOUND_MASTERSPARK.get(),
                SoundSource.NEUTRAL, dev.kneekura.fivedifficulties.forge.X1Config.masterSparkVol(), 1.0F);
        this.lastTime = 0;
        this.isSpellCard = true;
        X1Danmaku.createLaserB(user, this, X1Danmaku.pos_Entity(this), X1Danmaku.getVecFromAngle(yaw, pitch),
                X1Danmaku.rotate_Default(), 0.0F, 9999, X1LaserData.laser(24, 4.2F, 60.0F, 8.0F, 30, 120, 0), this,
                1.0D, 0.0F);
    }

    @Override
    protected void defineSynchedData() {}

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide && user == null) {
            finish();
            return;
        }
        if (this.tickCount <= lastTime) return;
        circleAngle += 4.7F;
        if (this.tickCount > lastTime) lastTime = this.tickCount;
        if (this.tickCount >= 109 && !this.level().isClientSide) finish();
    }

    private void finish() {
        if (!isSpellCard) X1ItemEffects.itemEffectFinish(this, user, PortRegistries.MINI_HAKKERO_ITEM.get());
        else this.discard();
    }

    public float getCircleAngle() {
        return circleAngle;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean isPickable() {
        return true;
    }

    /** A reloaded hakkero has no user: the item's drops its item at once, the spell card's just leaves. */
    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        count = tag.getShort("count");
        damage = tag.getShort("damage");
        isSpellCard = tag.getBoolean("isSpellCard");
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putShort("count", (short) count);
        tag.putShort("damage", (short) damage);
        tag.putBoolean("isSpellCard", tgEntity != null); // X1 writes tgEntity != null
    }
}
