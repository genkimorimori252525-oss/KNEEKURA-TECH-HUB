package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.InteractGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.LookAtTradingPlayerGoal;
import net.minecraft.world.entity.ai.goal.OpenDoorGoal;
import net.minecraft.world.entity.ai.goal.TradeWithPlayerGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.navigation.GroundPathNavigation;
import net.minecraft.world.entity.monster.Witch;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Port of X1 {@code EntityRinnosuke} (森近霖之助): an {@code EntityVillager} with X1's own profession, whose
 * trades come from {@code VillagerRinnosuke}. 1.7.10 villager trading is reproduced, not 1.20's:
 * <ul>
 * <li>the first look at the offers adds one random recipe from the eight (shuffle, take one,
 * {@code addToListWithCheck}: a recipe already listed is replaced by a fresh copy);</li>
 * <li>each trade uses up one of the default 7; trading the <em>last</em> listed recipe starts a 40-tick timer
 * (not while trading) after which, if more than one recipe is listed, every used-up recipe gains
 * 2–12 more uses, one more random recipe is added, and he gets Regeneration for 10 seconds;</li>
 * <li>no trade XP, no levels, no restock at a job site.</li>
 * </ul>
 * Never breeds, despawns like a monster, cluster size 1, turns into a witch when struck by lightning (as any
 * 1.7.10 villager).
 */
public class RinnosukeEntity extends AbstractVillager {
    private int timeUntilReset;
    private boolean needsInitilization;

    public RinnosukeEntity(EntityType<? extends RinnosukeEntity> type, Level level) {
        super(type, level);
        ((GroundPathNavigation) this.getNavigation()).setCanOpenDoors(true);
    }

    /** 1.7.10 EntityVillager: 20 HP, speed 0.5. */
    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 20.0D).add(Attributes.MOVEMENT_SPEED, 0.5D);
    }

    /** The 1.7.10 villager task list, minus village-only tasks (indoors, mating, golems, play). */
    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new AvoidEntityGoal<>(this, Zombie.class, 8.0F, 0.6D, 0.6D));
        this.goalSelector.addGoal(1, new TradeWithPlayerGoal(this));
        this.goalSelector.addGoal(1, new LookAtTradingPlayerGoal(this));
        this.goalSelector.addGoal(4, new OpenDoorGoal(this, true));
        this.goalSelector.addGoal(9, new InteractGoal(this, Player.class, 3.0F, 1.0F));
        this.goalSelector.addGoal(9, new WaterAvoidingRandomStrollGoal(this, 0.6D));
        this.goalSelector.addGoal(10, new LookAtPlayerGoal(this, Mob.class, 8.0F));
    }

    /** VillagerRinnosuke.manipulateTradesForVillager. */
    public static List<MerchantOffer> rinnosukeTrades() {
        List<MerchantOffer> list = new ArrayList<>();
        list.add(recipe(new ItemStack(PortRegistries.POWER_ITEM_SMALL.get(), 22), new ItemStack(PortRegistries.SPIRITUAL_STRIKE_TALISMAN.get())));
        list.add(recipe(new ItemStack(Items.IRON_INGOT, 20), new ItemStack(PortRegistries.MINI_HAKKERO_ITEM.get())));
        list.add(recipe(new ItemStack(Items.NETHER_STAR, 1), new ItemStack(PortRegistries.MARISA_BROOM.get())));
        list.add(recipe(new ItemStack(PortRegistries.POWER_ITEM_SMALL.get(), 10), new ItemStack(PortRegistries.POINT_ITEM.get(), 9)));
        list.add(recipe(new ItemStack(PortRegistries.POINT_ITEM.get(), 10), new ItemStack(PortRegistries.POWER_ITEM_SMALL.get(), 9)));
        list.add(recipe(new ItemStack(Items.REDSTONE, 1), new ItemStack(PortRegistries.POWER_ITEM_SMALL.get(), 64)));
        list.add(recipe(new ItemStack(Items.LAPIS_LAZULI, 1), new ItemStack(PortRegistries.POINT_ITEM.get(), 64)));
        list.add(recipe(new ItemStack(Items.GOLD_INGOT, 1), new ItemStack(Items.ENDER_PEARL, 1)));
        return list;
    }

    private static MerchantOffer recipe(ItemStack buy, ItemStack sell) {
        return new MerchantOffer(buy, sell, 7, 0, 0.0F);
    }

    /** addDefaultEquipmentAndRecipies(1). */
    @Override
    protected void updateTrades() {
        List<MerchantOffer> candidates = rinnosukeTrades();
        Collections.shuffle(candidates, new java.util.Random(this.random.nextLong()));
        MerchantOffers list = this.getOffers();
        for (int l = 0; l < 1 && l < candidates.size(); ++l) addToListWithCheck(list, candidates.get(l));
    }

    /** MerchantRecipeList.addToListWithCheck: same items replace (fresh uses), same ids otherwise keep, else add. */
    static void addToListWithCheck(MerchantOffers list, MerchantOffer offer) {
        for (int i = 0; i < list.size(); ++i) {
            MerchantOffer old = list.get(i);
            if (sameIds(offer, old)) {
                if (sameItems(offer, old)) list.set(i, offer);
                return;
            }
        }
        list.add(offer);
    }

    private static boolean sameIds(MerchantOffer a, MerchantOffer b) {
        return a.getBaseCostA().getItem() == b.getBaseCostA().getItem() && a.getResult().getItem() == b.getResult().getItem()
                && a.getCostB().getItem() == b.getCostB().getItem();
    }

    private static boolean sameItems(MerchantOffer a, MerchantOffer b) {
        return sameIds(a, b) && a.getBaseCostA().getCount() == b.getBaseCostA().getCount()
                && a.getCostB().getCount() == b.getCostB().getCount();
    }

    /** useRecipe: the last listed recipe starts the 40-tick reset. */
    @Override
    protected void rewardTradeXp(MerchantOffer offer) {
        MerchantOffers list = this.getOffers();
        if (!list.isEmpty() && sameIds(offer, list.get(list.size() - 1))) {
            this.timeUntilReset = 40;
            this.needsInitilization = true;
        }
    }

    /** updateAITasks reset branch. */
    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        if (!this.isTrading() && this.timeUntilReset > 0) {
            --this.timeUntilReset;
            if (this.timeUntilReset <= 0) resetStep();
        }
    }

    /** Public for the scenario: what happens when the timer runs out. */
    public void resetStep() {
        if (this.needsInitilization) {
            MerchantOffers list = this.getOffers();
            if (list.size() > 1) {
                for (int i = 0; i < list.size(); ++i) {
                    MerchantOffer o = list.get(i);
                    if (o.isOutOfStock()) {
                        int more = this.random.nextInt(6) + this.random.nextInt(6) + 2;
                        list.set(i, new MerchantOffer(o.getBaseCostA(), o.getCostB(), o.getResult(), o.getUses(),
                                o.getMaxUses() + more, o.getXp(), o.getPriceMultiplier()));
                    }
                }
            }
            this.updateTrades();
            this.needsInitilization = false;
        }
        this.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 0));
    }

    public void setResetTimerForTest(int ticks) { this.timeUntilReset = ticks; }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack held = player.getItemInHand(hand);
        boolean egg = held.getItem() instanceof SpawnEggItem;
        if (!egg && this.isAlive() && !this.isTrading() && !player.isShiftKeyDown()) {
            if (!this.level().isClientSide) {
                this.setTradingPlayer(player);
                this.openTradingScreen(player, this.getDisplayName(), 1);
            }
            return InteractionResult.sidedSuccess(this.level().isClientSide);
        }
        return super.mobInteract(player, hand);
    }

    @Override
    public boolean showProgressBar() { return false; }

    @Nullable
    @Override
    public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob other) { return null; }

    @Override
    public boolean removeWhenFarAway(double distance) { return true; }

    @Override
    public int getMaxSpawnClusterSize() { return 1; }

    /** EntityVillager.onStruckByLightning: becomes a witch. */
    @Override
    public void thunderHit(ServerLevel level, LightningBolt bolt) {
        Witch witch = EntityType.WITCH.create(level);
        if (witch == null) return;
        witch.moveTo(this.getX(), this.getY(), this.getZ(), this.getYRot(), this.getXRot());
        witch.finalizeSpawn(level, level.getCurrentDifficultyAt(witch.blockPosition()), MobSpawnType.CONVERSION, null, null);
        level.addFreshEntityWithPassengers(witch);
        this.discard();
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("X1ResetTime", this.timeUntilReset);
        tag.putBoolean("X1NeedsInit", this.needsInitilization);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.timeUntilReset = tag.getInt("X1ResetTime");
        this.needsInitilization = tag.getBoolean("X1NeedsInit");
    }

    /** getCanSpawnHere: 2 % of attempts, not on a spot whose four neighbours below match the block underfoot. */
    public static boolean checkRinnosukeSpawnRules(EntityType<? extends RinnosukeEntity> type, ServerLevelAccessor level,
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
