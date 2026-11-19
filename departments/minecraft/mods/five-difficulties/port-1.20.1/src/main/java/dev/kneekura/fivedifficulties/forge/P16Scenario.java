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
            runWeapons();
            runShotItems();
            runEffectItems();
            runAjaRedStone();
            runPendulum();
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
        require(dealt >= 4.6F || target.isDeadOrDying(), "onbashira extra damage (5..22 less zombie armor 2) " + dealt);
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

    private static Zombie zombie(double dx) {
        Zombie z = EntityType.ZOMBIE.create(level);
        z.moveTo(bx + dx, by, bz, 90F, 0F);
        z.setNoAi(true);
        level.addFreshEntity(z);
        return z;
    }

    private static void runWeapons() {
        FakePlayer p = player();
        p.experienceLevel = 30;

        // Gungnir: declares card 27 at a target ahead and throws the spear laser; the spear takes 1 damage.
        Zombie aim = zombie(10);
        ItemStack spear = new ItemStack(PortRegistries.SPEAR_THE_GUNGNIR.get());
        p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, spear);
        shots = 0;
        lastShot = null;
        counting = true;
        spear.getItem().use(level, p, net.minecraft.world.InteractionHand.MAIN_HAND);
        counting = false;
        require(lastShot instanceof dev.kneekura.fivedifficulties.forge.entity.THLaserEntity, "a gungnir laser, saw " + shots);
        require(spear.getDamageValue() == 1, "spear damage " + spear.getDamageValue() + " shots=" + shots + " creative=" + p.getAbilities().instabuild + " lvl=" + p.experienceLevel);
        lastShot.discard();
        aim.discard();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_GUNGNIR_PASS shots=" + shots);

        // Laevateinn: one sweeping set laser per player; a second use does nothing; hits set fire.
        ItemStack lae = new ItemStack(PortRegistries.LAEVATEINN.get());
        p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, lae);
        shots = 0;
        lastShot = null;
        counting = true;
        lae.getItem().use(level, p, net.minecraft.world.InteractionHand.MAIN_HAND);
        lae.getItem().use(level, p, net.minecraft.world.InteractionHand.MAIN_HAND);
        counting = false;
        require(shots == 1 && lastShot instanceof dev.kneekura.fivedifficulties.forge.entity.THSetLaserEntity s
                && s.source() == p, "one set laser owned by the player, saw " + shots);
        require(lae.getDamageValue() == 1, "laevateinn damage " + lae.getDamageValue());
        lastShot.discard();
        Zombie burn = zombie(2);
        lae.getItem().hurtEnemy(lae, burn, p);
        require(burn.getRemainingFireTicks() > 0, "the target burns");
        burn.discard();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_LAEVATEINN_PASS");

        // Roukanken: dash 10 ticks -> 3.0 forward; undead take 16 more; at speed > 3 it cuts what it passes.
        ItemStack rk = new ItemStack(PortRegistries.ROUKANKEN.get());
        p.setOnGround(true);
        p.setDeltaMovement(0, 0, 0);
        rk.getItem().releaseUsing(rk, level, p, 72000 - 10);
        Vec3 dash = p.getDeltaMovement();
        require(Math.abs(dash.x - 3.0D) < 1e-6 && Math.abs(dash.z) < 1e-6, "dash " + dash);
        require(rk.getDamageValue() == 1, "dash wears the sword");
        Zombie undead = zombie(2);
        float hp = undead.getHealth();
        rk.getItem().hurtEnemy(rk, undead, p);
        require(hp - undead.getHealth() >= 14F, "undead bonus " + (hp - undead.getHealth()));
        undead.discard();
        net.minecraft.world.entity.animal.Cow cow = EntityType.COW.create(level);
        cow.moveTo(bx + 1.5, by, bz, 0F, 0F);
        cow.setNoAi(true);
        level.addFreshEntity(cow);
        p.getInventory().selected = 0;
        p.getInventory().setItem(0, rk);
        p.setDeltaMovement(3.5D, 0.0D, 0.0D);
        int worn = rk.getDamageValue();
        rk.getItem().inventoryTick(rk, level, p, 0, true);
        require(cow.getHealth() <= 2.0F + 1e-4F, "the dash cut the cow to " + cow.getHealth());
        require(rk.getDamageValue() == worn + 1, "cutting wears the sword");
        cow.discard();
        p.getInventory().clearContent();
        p.setDeltaMovement(0, 0, 0);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_ROUKANKEN_PASS dash=" + dash.x);

        // Death scythe: pulls the zombie on the line 0.6 toward the player.
        Zombie pulled = zombie(6);
        pulled.setDeltaMovement(0, 0, 0);
        ItemStack scythe = new ItemStack(PortRegistries.DEATH_SCYTHE.get());
        require(scythe.getMaxDamage() == 444, "scythe durability 444");
        p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, scythe);
        scythe.getItem().use(level, p, net.minecraft.world.InteractionHand.MAIN_HAND);
        require(Math.abs(pulled.getDeltaMovement().x + 0.6D) < 1e-6, "pulled " + pulled.getDeltaMovement());
        require(scythe.getDamageValue() == 1, "scythe wears");
        pulled.discard();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_SCYTHE_PASS");

        // Remorse rod: knocks a healthy target to 3/4 once; an ink sac recharges it.
        Zombie z = zombie(2);
        ItemStack rod = new ItemStack(PortRegistries.REMORSE_ROD.get());
        rod.getItem().hurtEnemy(rod, z, p);
        require(z.getHealth() == 15F && dev.kneekura.fivedifficulties.forge.item.X1Weapons.Kaigo.used(rod), "rod hit " + z.getHealth());
        z.setHealth(20F);
        rod.getItem().hurtEnemy(rod, z, p);
        require(z.getHealth() == 20F, "a used rod does nothing");
        p.getInventory().setItem(5, new ItemStack(net.minecraft.world.item.Items.INK_SAC, 2));
        p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, rod);
        rod.getItem().use(level, p, net.minecraft.world.InteractionHand.MAIN_HAND);
        require(!dev.kneekura.fivedifficulties.forge.item.X1Weapons.Kaigo.used(rod)
                && p.getInventory().getItem(5).getCount() == 1, "ink recharges the rod");
        z.discard();
        p.stopUsingItem();
        p.getInventory().clearContent();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_KAIGO_PASS");
        // Leave nothing behind for the other scenarios (the declared Gungnir card keeps running otherwise).
        for (Entity e : level.getEntities((Entity) null, new net.minecraft.world.phys.AABB(bx - 64, by - 64, bz - 64, bx + 64, by + 64, bz + 64),
                e -> (e instanceof dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity c && c.user == p)
                        || (e instanceof THShotEntity shot && shot.getOwner() == p))) {
            e.discard();
        }
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16B_WEAPONS_PASS");
    }

    private static int fire(Runnable action) {
        shots = 0;
        lastShot = null;
        counting = true;
        action.run();
        counting = false;
        return shots;
    }

    private static void runShotItems() {
        FakePlayer p = player();
        var hand = net.minecraft.world.InteractionHand.MAIN_HAND;

        // Soul torch: three phantoms with special 352 (homing 16); one torch used.
        ItemStack torch = new ItemStack(PortRegistries.SOUL_TORCH.get(), 2);
        p.setItemInHand(hand, torch);
        int n = fire(() -> torch.getItem().finishUsingItem(torch, level, p));
        require(n == 3 && lastShot.motion().special == 352 && torch.getCount() == 1, "soul torch shots " + n);
        require(dev.kneekura.fivedifficulties.forge.shot.X1SpecialShotRegistry.get(352) != null, "special 352 registered");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_SOUL_TORCH_PASS shots=" + n);

        // Yuyuko fan: held 10 ticks -> 42 -> 14 per third; fans ahead = 2 x 15, rings (sneak) = 6 x 14.
        ItemStack fan = new ItemStack(PortRegistries.YUYUKO_FAN.get());
        p.setItemInHand(hand, fan);
        int wide = fire(() -> fan.getItem().releaseUsing(fan, level, p, 72000 - 10));
        p.setShiftKeyDown(true);
        int rings = fire(() -> fan.getItem().releaseUsing(fan, level, p, 72000 - 10));
        p.setShiftKeyDown(false);
        require(wide == 30 && rings == 84 && fan.getDamageValue() == 2, "fan wide " + wide + " rings " + rings);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_YUYUKO_FAN_PASS wide=" + wide + " rings=" + rings);

        // Kappa water pistol: three shots a click; the last charge never fires.
        ItemStack pistol = new ItemStack(PortRegistries.KAPPA_WATER_PISTOL.get());
        p.setItemInHand(hand, pistol);
        int three = fire(() -> pistol.getItem().use(level, p, hand));
        require(three == 3 && pistol.getDamageValue() == 1, "pistol shots " + three);
        pistol.setDamageValue(38);
        int none = fire(() -> pistol.getItem().use(level, p, hand));
        require(none == 0 && pistol.getDamageValue() == 38, "the last charge stays");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_WATER_PISTOL_PASS");

        // Ibuki gourd: two drinks of 5, then dry; Strength 15 s and Nausea III 20 s.
        ItemStack gourd = new ItemStack(PortRegistries.IBUKI_GOURD.get());
        p.setItemInHand(hand, gourd);
        p.removeAllEffects();
        gourd.getItem().finishUsingItem(gourd, level, p);
        var str = p.getEffect(MobEffects.DAMAGE_BOOST);
        var nau = p.getEffect(MobEffects.CONFUSION);
        require(gourd.getDamageValue() == 5 && str != null && str.getDuration() == 300 && nau != null
                && nau.getAmplifier() == 2 && nau.getDuration() == 400, "first drink " + gourd.getDamageValue());
        gourd.getItem().finishUsingItem(gourd, level, p);
        gourd.getItem().finishUsingItem(gourd, level, p);
        require(gourd.getDamageValue() == 10 && !gourd.isEmpty(), "two drinks then dry: " + gourd.getDamageValue());
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_IBUKI_GOURD_PASS");

        for (Entity e : level.getEntities((Entity) null, new net.minecraft.world.phys.AABB(bx - 64, by - 64, bz - 64, bx + 64, by + 64, bz + 64),
                e -> e instanceof THShotEntity shot && shot.getOwner() == p)) {
            e.discard();
        }
        p.getInventory().clearContent();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16C_SHOT_ITEMS_PASS");
    }

    private static void runEffectItems() {
        FakePlayer p = player();
        var hand = net.minecraft.world.InteractionHand.MAIN_HAND;

        // Spiritual strike talisman: one used; at tick 2 (range 8) a zombie is blown away and up, a cow is not.
        Zombie z = zombie(4);
        z.setDeltaMovement(0, 0, 0);
        net.minecraft.world.entity.animal.Cow cow = EntityType.COW.create(level);
        cow.moveTo(bx + 1.5, by, bz + 3, 0F, 0F);
        cow.setNoAi(true);
        level.addFreshEntity(cow);
        ItemStack tal = new ItemStack(PortRegistries.SPIRITUAL_STRIKE_TALISMAN.get(), 3);
        p.setItemInHand(hand, tal);
        tal.getItem().use(level, p, hand);
        require(tal.getCount() == 2, "one talisman used");
        var blasts = level.getEntitiesOfClass(dev.kneekura.fivedifficulties.forge.entity.SpiritualStrikeTalismanEntity.class,
                p.getBoundingBox().inflate(4.0D), e -> e.userEntity == p);
        require(blasts.size() == 1, "one blast entity, saw " + blasts.size());
        var blast = blasts.get(0);
        blast.tickCount = 2;
        blast.tick();
        Vec3 push = z.getDeltaMovement();
        require(push.x > 0.0D && push.y > 0.0D, "the zombie is blown away from the talisman: " + push);
        require(cow.getDeltaMovement().lengthSqr() == 0.0D, "animals are left alone");
        blast.tickCount = 4;
        blast.tick();
        require(blast.isRemoved(), "gone after tick 3");
        z.discard();
        cow.discard();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_TALISMAN_PASS push=" + String.format("%.3f,%.3f", push.x, push.y));

        // Sorcerer sutra scroll: released at count 60 -> 20 -> 3 levels, Speed V / Strength / Jump II / Resistance 200 ticks.
        p.removeAllEffects();
        p.experienceLevel = 5;
        var scroll = new dev.kneekura.fivedifficulties.forge.entity.MazinkyoukanEntity(level, p);
        level.addFreshEntity(scroll);
        scroll.count = 60;
        scroll.tick();
        var speed = p.getEffect(MobEffects.MOVEMENT_SPEED);
        require(p.experienceLevel == 2 && speed != null && speed.getAmplifier() == 4 && speed.getDuration() == 200
                && p.hasEffect(MobEffects.DAMAGE_BOOST) && p.getEffect(MobEffects.JUMP).getAmplifier() == 1
                && p.hasEffect(MobEffects.DAMAGE_RESISTANCE), "scroll buffs level=" + p.experienceLevel + " speed=" + speed);
        require(scroll.isRemoved(), "the scroll closes");
        p.removeAllEffects();
        p.getInventory().clearContent();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_SUTRA_SCROLL_PASS");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16D_EFFECT_ITEMS_PASS");
    }

    private static void runAjaRedStone() {
        FakePlayer p = player();
        // Not in use and no light gathered: nothing fires, the effect stays and gathers light.
        var idle = new dev.kneekura.fivedifficulties.forge.entity.AjaRedStoneEffectEntity(level, p);
        level.addFreshEntity(idle);
        int none = fire(idle::tick);
        require(none == 0 && !idle.isRemoved() && idle.lightLevel == idle.getLightPower(), "idle gathers " + idle.lightLevel);
        idle.discard();
        // 400 gathered -> damage 10: one red laser (width 0.1, length 3, damage 10, special 351), effect gone.
        var stone = new dev.kneekura.fivedifficulties.forge.entity.AjaRedStoneEffectEntity(level, p);
        level.addFreshEntity(stone);
        stone.lightLevel = 400;
        int n = fire(stone::tick);
        require(n == 1 && lastShot instanceof dev.kneekura.fivedifficulties.forge.entity.THLaserEntity
                && lastShot.motion().special == 351 && lastShot.shotDamage == 10F && stone.isRemoved(),
                "aja laser shots=" + n + " damage=" + (lastShot == null ? -1 : lastShot.shotDamage));
        // Special 351 sets undead on fire; others are untouched.
        Zombie undead = zombie(3);
        net.minecraft.world.entity.animal.Cow cow = EntityType.COW.create(level);
        cow.moveTo(bx + 3, by, bz + 3, 0F, 0F);
        level.addFreshEntity(cow);
        var special = dev.kneekura.fivedifficulties.forge.shot.X1SpecialShotRegistry.get(351);
        special.hitEntity(lastShot, lastShot.motion(), 351, undead);
        special.hitEntity(lastShot, lastShot.motion(), 351, cow);
        require(undead.getRemainingFireTicks() > 0 && cow.getRemainingFireTicks() <= 0, "only undead burn");
        undead.discard();
        cow.discard();
        lastShot.discard();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_AJA_RED_STONE_PASS idleLight=" + idle.lightLevel);
    }

    private static void runPendulum() {
        FakePlayer p = player();
        var hand = net.minecraft.world.InteractionHand.MAIN_HAND;
        // Five gold blocks 3 below the pendulum: the first search finds them.
        BlockPos base = BlockPos.containing(bx, by - 3, bz);
        for (int i = 0; i < 5; i++) level.setBlockAndUpdate(base.offset(i, 0, 0), net.minecraft.world.level.block.Blocks.GOLD_BLOCK.defaultBlockState());
        p.getInventory().selected = 0;
        p.getInventory().setItem(0, new ItemStack(PortRegistries.NAZRIN_PENDULUM.get()));
        p.getInventory().setItem(1, new ItemStack(net.minecraft.world.item.Items.GOLD_BLOCK));
        ItemStack held = p.getItemInHand(hand);
        held.getItem().use(level, p, hand);
        require(held.isEmpty(), "the pendulum leaves the inventory");
        var found = level.getEntitiesOfClass(dev.kneekura.fivedifficulties.forge.entity.PendulumEntity.class,
                p.getBoundingBox().inflate(4.0D), e -> e.user == p);
        require(found.size() == 1, "one pendulum, saw " + found.size());
        var pen = found.get(0);
        pen.tick();
        require(pen.getSearchCount() == 5 && Math.abs(pen.getSearchAngle() - 5F / 3F) < 0.01F,
                "found " + pen.getSearchCount() + " angle " + pen.getSearchAngle());
        // Sneaking after 10 ticks returns it to the inventory.
        pen.tickCount = 11;
        p.setShiftKeyDown(true);
        pen.tick();
        p.setShiftKeyDown(false);
        require(pen.isRemoved() && p.getInventory().countItem(PortRegistries.NAZRIN_PENDULUM.get()) == 1, "returned");
        for (int i = 0; i < 5; i++) level.setBlockAndUpdate(base.offset(i, 0, 0), net.minecraft.world.level.block.Blocks.AIR.defaultBlockState());
        p.getInventory().clearContent();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P16_PENDULUM_PASS found=5");
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P16 check failed: " + what);
    }
}
