package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.item.X1ItemEffects;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.decoration.ItemFrame;
import net.minecraft.world.entity.decoration.Painting;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

import javax.annotation.Nullable;
import java.util.List;

/**
 * Port of X1 {@code EntityCursedDecoyDoll} (呪いのデコイ人形): a still danmaku mob (40 HP, 1 XP, shikigami doll,
 * speed 0) left where its user stood. Every tick, for every entity within 40 except the user (and anything the
 * user rides on), item frames and paintings: a creature that already has a target re-targets the doll, and every
 * living thing takes the doll as its revenge target. Another doll in range is finished (its item goes back to its
 * user), and so is this one. With no player within 40 it is finished; after 180 ticks it simply vanishes
 * (no item back). Finishing gives the user a fresh doll item (X1 {@code itemEffectFinish}), so a doll that ends
 * by finishing hands back an extra one; kept.
 */
public class CursedDecoyDollEntity extends DanmakuMobEntity {
    @Nullable
    public LivingEntity userEntity;

    public CursedDecoyDollEntity(EntityType<? extends CursedDecoyDollEntity> type, Level level) {
        super(type, level);
        this.xpReward = 1;
        this.setDanmakuMobName("");
        this.setSpecies(SPECIES_SHIKIGAMI_DOLL);
        this.setDanmakuPattern(NOT_ATTACK);
        this.setMaxHP(40.0F);
        this.setHealth(40.0F);
        this.setSpeed(0.0D);
        this.setAttackDistance(0.0D);
        this.setDetectionDistance(0.0D);
        this.setFlyingHeight(0);
        this.isFlyingMode = false;
        this.isSpellCardMode = false;
        this.attackInterval = 0;
    }

    public CursedDecoyDollEntity(Level level, LivingEntity user) {
        this(PortRegistries.CURSED_DECOY_DOLL.get(), level);
        this.userEntity = user;
        this.setPos(user.getX(), user.getY(), user.getZ());
    }

    @Override
    protected boolean canFairyCall() { return false; }

    @Override
    public void tick() {
        super.tick();
        if (this.isRemoved()) return;
        if (this.tickCount > 180 && !this.level().isClientSide) this.discard();
        int playerCount = 0;
        boolean dubbleWatch = false;
        List<Entity> list = this.level().getEntities(this, this.getBoundingBox().inflate(40.0D));
        for (Entity entity : list) {
            if (entity instanceof Player) playerCount++;
            if (entity != userEntity && !isRiddenByUser(entity) && !(entity instanceof ItemFrame) && !(entity instanceof Painting)) {
                if (entity instanceof CursedDecoyDollEntity decoy) {
                    if (!this.level().isClientSide) {
                        X1ItemEffects.itemEffectFinish(decoy, decoy.userEntity, PortRegistries.CURSED_DECOY_DOLL_ITEM.get());
                    }
                    dubbleWatch = true;
                }
                inDecoyEffectedArea(entity);
            }
        }
        if (playerCount == 0 && !this.level().isClientSide) {
            X1ItemEffects.itemEffectFinish(this, userEntity, PortRegistries.CURSED_DECOY_DOLL_ITEM.get());
        }
        if (dubbleWatch && !this.level().isClientSide) {
            X1ItemEffects.itemEffectFinish(this, userEntity, PortRegistries.CURSED_DECOY_DOLL_ITEM.get());
        }
        this.setYRot(this.yRotO);
        this.setXRot(this.xRotO);
    }

    /** 1.7.10 entityHit.riddenByEntity != userEntity: the user's mount is left alone. */
    private boolean isRiddenByUser(Entity entity) {
        return userEntity != null && entity.getPassengers().contains(userEntity);
    }

    /** inDecoyEffectedArea. */
    public void inDecoyEffectedArea(Entity hit) {
        if (hit instanceof PathfinderMob creature && creature.getTarget() != null) creature.setTarget(this);
        if (hit instanceof LivingEntity living) living.setLastHurtByMob(this);
    }

    @Nullable
    @Override
    protected SoundEvent getAmbientSound() { return null; }

    @Nullable
    @Override
    protected SoundEvent getHurtSound(DamageSource source) { return null; }

    @Nullable
    @Override
    protected SoundEvent getDeathSound() { return null; }
}
