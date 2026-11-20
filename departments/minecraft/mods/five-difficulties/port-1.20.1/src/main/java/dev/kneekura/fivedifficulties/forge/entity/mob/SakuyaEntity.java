package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntitySakuya} (十六夜咲夜): an invulnerable wandering trader (1 × 1.8, 44 HP, 250 XP, human,
 * speed 0.5). Sells a (blue) silver knife for 16 shot materials and Sakuya's stopwatch for 64. Her attack phases
 * (normal → 「殺人ドール」 card 8 at 60 HP → end) are kept but, as in X1, never reached.
 */
public class SakuyaEntity extends X1TraderMobEntity {
    public SakuyaEntity(EntityType<? extends SakuyaEntity> type, Level level) {
        super(type, level);
        this.xpReward = 250;
        this.setDanmakuMobName("Sakuya Izayoi");
        this.setSpecies(SPECIES_HUMAN);
        this.setDanmakuPattern(NOT_ATTACK);
        this.setMaxHP(44.0F);
        this.setHealth(44.0F);
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
        list.add(recipe(new ItemStack(PortRegistries.SHOT_MATERIAL.get(), 16), new ItemStack(PortRegistries.SILVER_KNIFE_BLUE.get())));
        list.add(recipe(new ItemStack(PortRegistries.SHOT_MATERIAL.get(), 64), new ItemStack(PortRegistries.SAKUYA_STOPWATCH.get())));
        return list;
    }

    @Override
    public int getUsingSpellCardNo() {
        return getDanmakuPattern() == SPELLCARD_ATTACK01 ? 8 /* SC_SAKUYA_SatuzinDoll */ : -1;
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
            if (attackCounter == 1) useSpellCard(getUsingSpellCardNo());
            else if (attackCounter >= 140) attackCounter = 0;
        }
    }
}
