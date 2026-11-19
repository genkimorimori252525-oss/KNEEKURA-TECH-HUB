package dev.kneekura.fivedifficulties.forge;

import com.mojang.authlib.GameProfile;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.UUID;

/** P16 dedicated-server scenario: the remaining X1 items (FIVE_DIFFICULTIES_P16_RUNTIME_SCENARIO=1). */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P16Scenario {
    public static final String ENV = "FIVE_DIFFICULTIES_P16_RUNTIME_SCENARIO";
    private static ServerLevel level;
    private static double bx, by, bz;
    private static int shots;
    private static THShotEntity lastShot;
    private static boolean counting;

    private P16Scenario() {}

    private static boolean enabled() {
        return "1".equals(System.getenv(ENV));
    }

    @SubscribeEvent
    public static void onJoin(EntityJoinLevelEvent event) {
        if (!enabled() || event.getLevel().isClientSide || !counting) return;
        Entity e = event.getEntity();
        if (e instanceof THShotEntity shot && Math.abs(e.getX() - bx) < 48 && Math.abs(e.getZ() - bz) < 48) {
            shots++;
            lastShot = shot;
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        bx = spawn.getX() + 70 + 0.5D;
        bz = spawn.getZ() - 70 + 0.5D;
        by = level.getHeight(Heightmap.Types.MOTION_BLOCKING, spawn.getX() + 70, spawn.getZ() - 70);
        try {
            runSmallItems();
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_RUNTIME_SCENARIO_PASS");
            ScenarioShutdown.finished(level.getServer(), ENV);
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P16_RUNTIME_SCENARIO_FAIL", failure);
            ScenarioShutdown.failed(level.getServer());
        }
    }

    private static FakePlayer player() {
        FakePlayer p = FakePlayerFactory.get(level, new GameProfile(UUID.fromString("00000000-0000-0000-0000-0000f9160001"), "[FDP16]"));
        p.moveTo(bx, by, bz, -90F, 0F);
        p.getInventory().clearContent();
        p.removeAllEffects();
        return p;
    }

    private static void runSmallItems() {
        FakePlayer p = player();

        // Heavenly Peach: eaten (one used), Resistance level 2 for 400 ticks.
        ItemStack peach = new ItemStack(PortRegistries.HEAVENLY_PEACH.get(), 3);
        require(peach.getMaxStackSize() == 10, "peach stacks to 10");
        peach = peach.getItem().finishUsingItem(peach, level, p);
        MobEffectInstance res = p.getEffect(MobEffects.DAMAGE_RESISTANCE);
        require(res != null && res.getAmplifier() == 2 && res.getDuration() == 400, "peach resistance " + res);
        require(peach.getCount() == 2, "one peach eaten, left " + peach.getCount());

        // Swallow Cowrie Shell: 30 levels, food 10, standing -> 5 levels to 10 hunger, Regeneration II 300; never used up.
        p.removeAllEffects();
        p.experienceLevel = 30;
        p.getFoodData().setFoodLevel(10);
        ItemStack shell = new ItemStack(PortRegistries.SWALLOW_COWRIE_SHELL.get());
        ItemStack after = shell.getItem().finishUsingItem(shell, level, p);
        MobEffectInstance regen = p.getEffect(MobEffects.REGENERATION);
        require(p.experienceLevel == 25 && p.getFoodData().getFoodLevel() == 20, "levels " + p.experienceLevel
                + " food " + p.getFoodData().getFoodLevel());
        require(regen != null && regen.getAmplifier() == 1 && regen.getDuration() == 300, "shell regeneration " + regen);
        require(after.getCount() == 1 && after.is(PortRegistries.SWALLOW_COWRIE_SHELL.get()), "the shell is not used up");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_FOOD_PASS resistance=2 levels=25 food=20");

        // Closed Third Eye: a zombie 12 away that targets the player forgets them.
        p.removeAllEffects();
        Zombie far = EntityType.ZOMBIE.create(level);
        far.moveTo(bx + 12, by, bz, 0F, 0F);
        level.addFreshEntity(far);
        far.setTarget(p);
        Zombie near = EntityType.ZOMBIE.create(level);
        near.moveTo(bx + 2, by, bz, 0F, 0F);
        level.addFreshEntity(near);
        near.setTarget(p);
        boolean nearSees = near.hasLineOfSight(p);
        ItemStack eye = new ItemStack(PortRegistries.CLOSED_THIRD_EYE.get());
        eye.getItem().use(level, p, net.minecraft.world.InteractionHand.MAIN_HAND);
        require(p.hasEffect(MobEffects.INVISIBILITY) && p.getEffect(MobEffects.INVISIBILITY).getDuration() == 20,
                "one second of invisibility");
        require(far.getTarget() == null, "the far zombie forgets the player");
        require(!nearSees || near.getTarget() == p, "a near zombie that sees the player keeps them");
        far.discard();
        near.discard();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_EYE_PASS nearSees=" + nearSees);

        // Tengu Fan: released after 14 ticks of 24 -> one wind shot at 14 / 7 = 2.0, one durability used.
        ItemStack fan = new ItemStack(PortRegistries.TENGU_FAN.get());
        require(fan.getMaxDamage() == 40, "fan durability 40");
        shots = 0;
        lastShot = null;
        counting = true;
        fan.getItem().releaseUsing(fan, level, p, 10);
        counting = false;
        require(shots == 1 && lastShot != null, "one wind shot, saw " + shots);
        double speed = lastShot.getDeltaMovement().length();
        require(Math.abs(speed - 2.0D) < 0.05D, "wind shot speed 2.0, was " + speed);
        require(fan.getDamageValue() == 1, "one durability used");
        lastShot.discard();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_FAN_PASS speed=" + String.format("%.3f", speed));

        // Onbashira: a hit adds 5..22 mob damage; carrying it slows sideways and upward motion by 0.9.
        ItemStack pillar = new ItemStack(PortRegistries.ONBASHIRA.get());
        Zombie target = EntityType.ZOMBIE.create(level);
        target.moveTo(bx + 3, by, bz, 0F, 0F);
        level.addFreshEntity(target);
        float before = target.getHealth();
        pillar.getItem().hurtEnemy(pillar, target, p);
        float dealt = before - target.getHealth();
        require(dealt >= 5F || target.isDeadOrDying(), "onbashira extra damage " + dealt);
        target.discard();
        p.setDeltaMovement(1.0D, 1.0D, -1.0D);
        pillar.getItem().inventoryTick(pillar, level, p, 3, false);
        Vec3 v = p.getDeltaMovement();
        require(Math.abs(v.x - 0.9) < 1e-9 && Math.abs(v.y - 0.9) < 1e-9 && Math.abs(v.z + 0.9) < 1e-9, "slowed " + v);
        p.setDeltaMovement(0.0D, -1.0D, 0.0D);
        pillar.getItem().inventoryTick(pillar, level, p, 3, false);
        require(p.getDeltaMovement().y == -1.0D, "falling is not slowed");
        require(pillar.getDestroySpeed(net.minecraft.world.level.block.Blocks.STONE.defaultBlockState()) == 3F, "digs at 3");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_ONBASHIRA_PASS dealt=" + dealt);

        // Hourai pearls: eight colours registered.
        require(PortRegistries.HOURAI_PEARL_WHITE.get() != PortRegistries.HOURAI_PEARL_RED.get(), "pearls registered");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16A_ITEMS_PASS");
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P16 check failed: " + what);
    }
}
