package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityReimu} (博麗霊夢): 1 × 1.8, 74 HP, 250 XP, human, speed 0.4, flying height 4. She
 * starts in 「夢想封印」 (card 0); her death is final. Detection range 0, so she only fights whoever hits her.
 * {@code isEntityInvulnerable} is replaced wholesale: only {@code NOT_ATTACK} protects her, not the
 * between-phase {@code attackInterval}. Spell-card kills fan out 12 power and 12 point items. Never spawns
 * naturally and has no spawn egg in X1 (registered without egg colours).
 */
public class ReimuEntity extends DanmakuMobEntity {
    public ReimuEntity(EntityType<? extends ReimuEntity> type, Level level) {
        super(type, level);
        this.xpReward = 250;
        this.setDanmakuMobName("Reimu Hakurei");
        this.setSpecies(SPECIES_HUMAN);
        this.setDanmakuPattern(SPELLCARD_ATTACK01);
        this.setMaxHP(74.0F);
        this.setHealth(74.0F);
        this.setSpeed(0.4D);
        this.setAttackDistance(14.0D);
        this.setDetectionDistance(0.0D);
        this.setFlyingHeight(4);
        this.isFlyingMode = false;
        this.isSpellCardMode = false;
        this.attackInterval = 0;
    }

    @Override
    public int getUsingSpellCardNo() {
        return getDanmakuPattern() == SPELLCARD_ATTACK01 ? 0 /* SC_REIMU_MusouFuuin */ : -1;
    }

    @Override
    protected void tickDeath() {
        switch (getDanmakuPattern()) {
            case NORMAL_ATTACK01 -> {
                setFlyingHeight(2);
                moveDanmakuAttack(SPELLCARD_ATTACK01, 40, 60.0F, 160);
            }
            case SPELLCARD_ATTACK01 -> moveDanmakuAttack(ATTACK_END, 90, 40.0F, 160);
            default -> {
                if (deathTime % 6 == 0) explosionEffect(this.level(), getX(), getY(), getZ(), 1.0F + deathTime * 0.1F);
                super.tickDeath();
            }
        }
    }

    @Override
    protected void danmakuPattern(int level) {
        if (getDanmakuPattern() == SPELLCARD_ATTACK01) {
            if (attackCounter == 1) useSpellCard(0);
            else if (attackCounter >= 140) attackCounter = 0;
        }
    }

    @Override
    protected boolean canFairyCall() { return false; }

    /** isEntityInvulnerable: NOT_ATTACK only (X1 drops the base's attackInterval check here). */
    @Override
    public boolean isX1Invulnerable() {
        return getDanmakuPattern() == NOT_ATTACK;
    }

    @Override
    protected float getDamageAfterMagicAbsorb(DamageSource source, float damage) {
        damage = super.getDamageAfterMagicAbsorb(source, damage);
        if (getDanmakuPattern() == NOT_ATTACK) damage = (float) ((double) damage * 0.05D);
        return damage;
    }

    /** dropFewItems: on spell-card kills, 12 power items (yaw k·30, speed 0.5) and 12 point items (+15°, 0.3). */
    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean hitByPlayer) {
        super.dropCustomDeathLoot(source, looting, hitByPlayer);
        if (isSpellCardAttack()) {
            for (int k = 0; k < 12; ++k) fan(PortRegistries.POWER_ITEM_SMALL.get(), k * 30F, 0.5F);
            for (int k = 0; k < 12; ++k) fan(PortRegistries.POINT_ITEM.get(), k * 30F + 15F, 0.3F);
        }
    }

    private void fan(Item item, float yaw, float speed) {
        ItemEntity drop = this.spawnAtLocation(new ItemStack(item), 0.0F);
        if (drop == null) return;
        drop.setYRot(yaw);
        drop.setXRot(-60F);
        Vec3d v = X1Danmaku.getVecFromAngle(yaw, -60F, speed);
        drop.setPos(drop.getX() + v.x() * 2.0D, drop.getY(), drop.getZ() + v.z() * 2.0D);
        drop.setDeltaMovement(v.x(), v.y(), v.z());
    }

    @Override
    public int getMaxSpawnClusterSize() { return 1; }

    /** getCanSpawnHere is false: no natural or spawner spawns (1.7.10 spawners asked it too); commands only. */
    public static boolean checkNoSpawnRules(EntityType<? extends ReimuEntity> type, net.minecraft.world.level.ServerLevelAccessor level,
                                            net.minecraft.world.entity.MobSpawnType reason, net.minecraft.core.BlockPos pos,
                                            net.minecraft.util.RandomSource random) {
        return reason == net.minecraft.world.entity.MobSpawnType.COMMAND || reason == net.minecraft.world.entity.MobSpawnType.SPAWN_EGG;
    }
}
