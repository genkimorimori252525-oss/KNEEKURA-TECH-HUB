package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityMiniHakkero} (spell-card constructor). It sits one block in front of the
 * user's eyes and carries a Master Spark set laser (ID 24, width 4.2, length 60, damage 8, delay 30,
 * end 120); it disappears at tick 109. The item variant (ItemMiniHakkero) arrives with the items.
 */
public class MiniHakkeroEntity extends Entity {
    /** THKaguyaConfig "Master Spark Vol" default 50 / 100. */
    private static final float MASTER_SPARK_VOL = 0.5F;

    public LivingEntity user;
    private LivingEntity tgEntity;
    public int count;
    private float circleAngle;
    private int lastTime;
    private boolean isSpellCard;

    public MiniHakkeroEntity(EntityType<? extends MiniHakkeroEntity> type, Level level) {
        super(type, level);
        this.blocksBuilding = true; // preventEntitySpawning
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
                SoundSource.NEUTRAL, MASTER_SPARK_VOL, 1.0F);
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
            // !isSpellCard: itemEffectFinish (returns the Mini Hakkero item) arrives with the item.
            this.discard();
            return;
        }
        if (this.tickCount <= lastTime) return;
        circleAngle += 4.7F;
        if (this.tickCount > lastTime) lastTime = this.tickCount;
        if (this.tickCount >= 109 && !this.level().isClientSide) this.discard();
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

    /** X1 saves count / damage / isSpellCard, but a reloaded one has no user and dies at once. */
    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}
}
