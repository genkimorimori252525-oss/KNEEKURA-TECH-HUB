package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntitySanae} (東風谷早苗): an invulnerable wandering trader (0.6 × 1.7, 56 HP, 760 XP,
 * human / god, speed 0.5). Sells the illness-recovery charm for 64 shot materials. Her phase table (normal →
 * cards 14 / 17 / 18 / 16 → end) is kept for the spell-card numbers and transitions, but as in X1 she never
 * leaves NOT_ATTACK, so none of it runs; the normal-attack star pattern (danmaku01) is therefore not ported.
 */
public class SanaeEntity extends X1TraderMobEntity {
    public SanaeEntity(EntityType<? extends SanaeEntity> type, Level level) {
        super(type, level);
        this.xpReward = 760;
        this.setDanmakuMobName("Sanae Kochiya");
        this.setSpecies(SPECIES_HUMAN, SPECIES_GOD);
        this.setDanmakuPattern(NOT_ATTACK);
        this.setMaxHP(56.0F);
        this.setHealth(56.0F);
        this.setSpeed(0.5D);
        this.setAttackDistance(14.0D);
        this.setDetectionDistance(0.0D);
        this.setFlyingHeight(0);
        this.isFlyingMode = false;
        this.isSpellCardMode = false;
        this.attackInterval = 0;
    }

    @Override
    protected MerchantOffers createOffers() {
        MerchantOffers list = new MerchantOffers();
        list.add(recipe(new ItemStack(PortRegistries.SHOT_MATERIAL.get(), 64), new ItemStack(PortRegistries.BYOUKIHEIYU_MAMORI.get())));
        return list;
    }

    @Override
    public int getUsingSpellCardNo() {
        return switch (getDanmakuPattern()) {
            case SPELLCARD_ATTACK01 -> 14;
            case SPELLCARD_ATTACK02 -> 17;
            case SPELLCARD_ATTACK03 -> 18;
            case SPELLCARD_ATTACK04 -> 16;
            default -> -1;
        };
    }

    @Override
    protected void tickDeath() {
        if (this.tickCount <= lastTime) return;
        switch (getDanmakuPattern()) {
            case NORMAL_ATTACK01 -> {
                setFlyingHeight(2);
                moveDanmakuAttack(SPELLCARD_ATTACK01, 40, 60.0F, 160);
            }
            case SPELLCARD_ATTACK01, SPELLCARD_ATTACK02, SPELLCARD_ATTACK03, SPELLCARD_ATTACK04 ->
                    moveDanmakuAttack(ATTACK_END, 90, 40.0F, 160);
            default -> {
                if (deathTime % 6 == 0) explosionEffect(this.level(), getX(), getY(), getZ(), 1.0F + deathTime * 0.1F);
                super.tickDeath();
            }
        }
    }

    @Override
    protected void danmakuPattern(int level) {
        int card = getUsingSpellCardNo();
        if (card >= 0) {
            if (attackCounter == 1) useSpellCard(card);
            else if (attackCounter >= 140) attackCounter = 0;
        }
    }
}
