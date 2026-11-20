package dev.kneekura.fivedifficulties.forge.entity.mob;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.trading.Merchant;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;

import javax.annotation.Nullable;

/**
 * The X1 {@code EntityDanmakuMob implements IMerchant} pattern shared by Sakuya and Sanae: they start (and, in
 * X1, stay) in {@code NOT_ATTACK}, where {@code isEntityInvulnerable} is true, so 1.7.10's
 * {@code attackEntityFrom} rejects every hit and nothing ever moves them to an attack phase. Right-click (not
 * with a spawn egg, not sneaking) opens the merchant screen titled with the mob's name. Offers are a fixed list
 * from {@code entityInit}, 1.7.10's default 7 uses each, never restocked (X1 commented the reset out), saved
 * as "Offers".
 */
public abstract class X1TraderMobEntity extends DanmakuMobEntity implements Merchant {
    @Nullable
    private Player tradingPlayer;
    private MerchantOffers offers = new MerchantOffers();

    protected X1TraderMobEntity(EntityType<? extends X1TraderMobEntity> type, Level level) {
        super(type, level);
        this.offers = createOffers();
    }

    /** X1 entityInit buyingList. */
    protected abstract MerchantOffers createOffers();

    /** 1.7.10 MerchantRecipe(buy, sell): maxTradeUses 7, no XP, no price multiplier. */
    protected static MerchantOffer recipe(ItemStack buy, ItemStack sell) {
        return new MerchantOffer(buy, sell, 7, 0, 0.0F);
    }

    /** isEntityInvulnerable: true exactly while NOT_ATTACK (X1 does not look at attackInterval here). */
    @Override
    public boolean isX1Invulnerable() {
        return getDanmakuPattern() == NOT_ATTACK;
    }

    /** applyPotionDamageCalculations × 0.05 while invulnerable (only reachable by bypassing damage). */
    @Override
    protected float getDamageAfterMagicAbsorb(DamageSource source, float damage) {
        damage = super.getDamageAfterMagicAbsorb(source, damage);
        if (getDanmakuPattern() == NOT_ATTACK) damage = (float) ((double) damage * 0.05D);
        return damage;
    }

    @Override
    protected boolean canFairyCall() { return false; }

    @Override
    public int getMaxSpawnClusterSize() { return 1; }

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack held = player.getItemInHand(hand);
        boolean egg = held.getItem() instanceof SpawnEggItem;
        if (!egg && this.isAlive() && !player.isShiftKeyDown()) {
            if (!this.level().isClientSide) {
                this.setTradingPlayer(player);
                this.openTradingScreen(player, Component.translatable(this.getType().getDescriptionId()), 1);
            }
            return InteractionResult.sidedSuccess(this.level().isClientSide);
        }
        return super.mobInteract(player, hand);
    }

    @Override
    public void setTradingPlayer(@Nullable Player player) { this.tradingPlayer = player; }

    @Nullable
    @Override
    public Player getTradingPlayer() { return this.tradingPlayer; }

    @Override
    public MerchantOffers getOffers() { return this.offers; }

    /** X1 setRecipes is empty. */
    @Override
    public void overrideOffers(MerchantOffers offers) {}

    /** useRecipe: incrementToolUses; the reset after the last recipe is commented out in X1. */
    @Override
    public void notifyTrade(MerchantOffer offer) {
        offer.increaseUses();
        this.ambientSoundTime = -this.getAmbientSoundInterval();
    }

    /** func_110297_a_: only resets the talk timer (the yes / no sounds are commented out in X1). */
    @Override
    public void notifyTradeUpdated(ItemStack stack) {
        if (!this.level().isClientSide && this.ambientSoundTime > -this.getAmbientSoundInterval() + 20) {
            this.ambientSoundTime = -this.getAmbientSoundInterval();
        }
    }

    @Override
    public int getVillagerXp() { return 0; }

    @Override
    public void overrideXp(int xp) {}

    @Override
    public boolean showProgressBar() { return false; }

    @Override
    public SoundEvent getNotifyTradeSound() { return SoundEvents.VILLAGER_YES; }

    @Override
    public boolean isClientSide() { return this.level().isClientSide; }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("Offers", 10)) this.offers = new MerchantOffers(tag.getCompound("Offers"));
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (this.offers != null) tag.put("Offers", this.offers.createTag());
    }

    /**
     * Sakuya / Sanae getCanSpawnHere: 2 % of attempts, and not when the four blocks around the one underfoot are
     * all the same block as it (keeps them off uniform ground).
     */
    public static boolean checkTraderSpawnRules(EntityType<? extends X1TraderMobEntity> type, ServerLevelAccessor level,
                                                MobSpawnType reason, BlockPos pos, RandomSource random) {
        if (reason == MobSpawnType.SPAWNER || reason == MobSpawnType.SPAWN_EGG || reason == MobSpawnType.COMMAND) return true;
        if (random.nextInt(100) < 98) return false;
        BlockPos below = pos.below();
        BlockState point = level.getBlockState(below);
        return !(level.getBlockState(below.west()).getBlock() == point.getBlock()
                && level.getBlockState(below.east()).getBlock() == point.getBlock()
                && level.getBlockState(below.north()).getBlock() == point.getBlock()
                && level.getBlockState(below.south()).getBlock() == point.getBlock());
    }
}
