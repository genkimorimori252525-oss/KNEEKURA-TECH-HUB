package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.item.X1ItemEffects;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityMazinkyoukan} (魔人経巻): a scroll that unrolls around the player while the item is
 * held in use (count up to 114, turning after 50). When the use stops, {@code count / 3} becomes the buff time:
 * it costs {@code time / 8 + 1} levels (time shrinks by 8 per missing level) and gives Speed V, Strength I,
 * Jump Boost II and Resistance I for {@code time × 10} ticks.
 */
public class MazinkyoukanEntity extends Entity {
    public Player user;
    public int count;
    public float turnAngle;
    public int befUseCount;

    public MazinkyoukanEntity(EntityType<? extends MazinkyoukanEntity> type, Level level) {
        super(type, level);
    }

    public MazinkyoukanEntity(Level level, Player player) {
        this(PortRegistries.MAZINKYOUKAN_ENTITY.get(), level);
        this.user = player;
        this.xo = player.getX();
        this.yo = player.getY();
        this.zo = player.getZ();
        this.setPos(player.getX(), player.getY() + player.getEyeHeight(), player.getZ());
        this.setYRot(player.getYRot());
        this.setXRot(0.0F);
        this.count = 0;
        this.befUseCount = 0;
        this.turnAngle = 0F;
    }

    @Override
    protected void defineSynchedData() {}

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public void tick() {
        if (!this.level().isClientSide && (user == null || !user.isAlive())) {
            this.discard();
            return;
        }
        super.tick();
        if (user != null) {
            if (!user.isUsingItem()) {
                int time = count / 3;
                if (!this.level().isClientSide) {
                    int removeLevel = (int) ((float) time / 8.0F) + 1;
                    if (user.experienceLevel - removeLevel < 0) time += (user.experienceLevel - removeLevel) * 8F;
                    user.giveExperienceLevels(-removeLevel);
                    user.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, time * 10, 4));
                    user.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, time * 10, 0));
                    user.addEffect(new MobEffectInstance(MobEffects.JUMP, time * 10, 1));
                    user.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, time * 10, 0));
                    this.discard();
                }
            } else {
                X1ItemEffects.followUser(this, user, 0.5D, 0F);
                this.setYRot(user.getYRot());
                this.setXRot(0F);
            }
        }
        count++;
        if (count > 114) count = 114;
        else if (count > 50) turnAngle += 2.88F;
        float yaw = getYRot();
        if (yaw > 180F) setYRot(yaw - 360F);
        if (yaw < -180F) setYRot(yaw + 360F);
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {}

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {}
}
