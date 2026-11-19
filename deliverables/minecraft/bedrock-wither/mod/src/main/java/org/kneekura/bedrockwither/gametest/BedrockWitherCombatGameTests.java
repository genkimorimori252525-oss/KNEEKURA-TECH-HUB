package org.kneekura.bedrockwither.gametest;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.*;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;
import org.kneekura.bedrockwither.registry.ModEntities;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/** Real server entity-tick integration tests; explicit adapters have separate safety tests. */
@GameTestHolder(BedrockWitherMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BedrockWitherCombatGameTests {
    private BedrockWitherCombatGameTests() {}

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_move_hover_volley")
    public static void ordinaryTicksReachRepositionHoverAndOrderedVolley(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            Vec3 start = f.wither.position();
            boolean sawMovement = false;
            boolean sawHover = false;
            for (int tick = 0; tick < 320 && f.shots.size() < 4; tick++) {
                f.tick();
                sawMovement |= f.wither.runtimeState().pathing();
                sawHover |= !f.wither.runtimeState().pathing()
                        && f.wither.runtimeState().delayShot() > 0 && f.shots.isEmpty();
            }
            helper.assertTrue(sawMovement && f.wither.position().distanceToSqr(start) > 0.1D,
                    "Ordinary AI never executed the phase-1 reposition path: path=" + sawMovement
                            + ", displacement=" + f.wither.position().distanceTo(start)
                            + ", shots=" + f.shots.size() + ", state=" + f.wither.getBedrockState());
            helper.assertTrue(sawHover, "Reposition did not stop for the historical 20-tick hover");
            helper.assertTrue(f.shots.equals(List.of(false, false, false, true)),
                    "Ordinary center volley was not three normal skulls then one dangerous skull: " + f.shots);
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_aerial_height")
    public static void ordinaryFirstPhaseRisesBeyondMeleeReachBeforeFiring(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            BlockPos floor = f.wither.blockPosition().below();
            for (int x = -3; x <= 3; x++) for (int z = -3; z <= 3; z++) {
                helper.getLevel().setBlockAndUpdate(floor.offset(x, 0, z), Blocks.BEDROCK.defaultBlockState());
            }
            try {
                for (int tick = 0; tick < 240 && f.shots.isEmpty(); tick++) f.tick();
                helper.assertTrue(!f.shots.isEmpty(), "Ordinary first-phase aerial cycle never fired");
                helper.assertTrue(f.wither.getY() - f.target.getY() >= 4.0D,
                        "Phase-1 combat never rose beyond ground-target melee reach; vertical gap="
                                + (f.wither.getY() - f.target.getY()));
                helper.succeed();
            } finally {
                for (int x = -3; x <= 3; x++) for (int z = -3; z <= 3; z++) {
                    helper.getLevel().setBlockAndUpdate(floor.offset(x, 0, z), Blocks.AIR.defaultBlockState());
                }
            }
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_phase2_alternate_charge")
    public static void ordinarySecondPhaseFiresTwoBurstsThenChargesAndResumes(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            f.enterSecondPhase();
            int firstChargeShots = -1;
            boolean sawRecovery = false;
            Vec3 chargeStart = null;
            double chargeDistance = 0;
            for (int tick = 0; tick < 900; tick++) {
                f.tick();
                if (f.wither.runtimeState().charging() && firstChargeShots < 0) {
                    firstChargeShots = f.shots.size();
                    chargeStart = f.wither.position();
                }
                if (chargeStart != null) {
                    chargeDistance = Math.max(chargeDistance, f.wither.position().distanceTo(chargeStart));
                }
                sawRecovery |= f.wither.getBedrockState() == BedrockWitherState.PHASE2_RECOVER;
                if (sawRecovery && f.shots.size() >= 12) break;
            }
            helper.assertTrue(firstChargeShots == 8, "First ordinary charge must follow the second four-shot burst; saw " + firstChargeShots);
            helper.assertTrue(chargeDistance > 2.0D && sawRecovery, "Ordinary charge never moved and recovered");
            helper.assertTrue(f.shots.size() >= 12, "Phase 2 stalled instead of resuming skull volleys after recovery");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_targetloss")
    public static void lostTargetDuringChargePreparationRecoversAndReacquires(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            f.enterSecondPhase();
            for (int tick = 0; tick < 500 && f.wither.getBedrockState() != BedrockWitherState.PHASE2_DASH_PREP; tick++) f.tick();
            helper.assertTrue(f.shots.size() == 8, "Charge preparation was not reached after two ordinary volleys");
            f.wither.setTarget(null);
            f.target.discard();
            for (int tick = 0; tick < 100; tick++) f.tick();
            helper.assertTrue(!f.wither.runtimeState().charging()
                            && f.wither.getBedrockState() != BedrockWitherState.PHASE2_DASH_PREP,
                    "Losing target left charge preparation waiting permanently");
            f.replaceTarget();
            for (int tick = 0; tick < 250 && f.shots.size() < 12; tick++) f.tick();
            helper.assertTrue(f.shots.size() >= 12, "Reacquiring a target did not resume phase-2 volleys");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_halfhealth_lands_once")
    public static void halfHealthTransitionDescendsBeforeExactlyOneExplosion(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            BlockPos floor = f.wither.blockPosition().below(8);
            for (int x = -3; x <= 3; x++) for (int z = -3; z <= 3; z++) {
                helper.getLevel().setBlockAndUpdate(floor.offset(x, 0, z), Blocks.BEDROCK.defaultBlockState());
            }
            double initialY = f.wither.getY();
            int[] explosions = {0};
            Consumer<net.minecraftforge.event.level.ExplosionEvent.Start> listener = event -> {
                if (event.getExplosion().getExploder() == f.wither) explosions[0]++;
            };
            var bus = net.minecraftforge.common.MinecraftForge.EVENT_BUS;
            bus.addListener(net.minecraftforge.eventbus.api.EventPriority.NORMAL, false,
                    net.minecraftforge.event.level.ExplosionEvent.Start.class, listener);
            try {
                f.wither.setHealth(f.wither.getMaxHealth() / 2.0F);
                f.tick();
                helper.assertTrue(explosions[0] == 0 && f.wither.getBedrockState() == BedrockWitherState.PHASE_TRANSITION,
                        "Half-health explosion fired before descending to ground");
                for (int tick = 0; tick < 200; tick++) f.tick();
                helper.assertTrue(f.wither.getY() < initialY - 4.0D && explosions[0] == 1,
                        "Half-health descent did not culminate in exactly one explosion: initialY=" + initialY
                                + ", finalY=" + f.wither.getY() + ", explosions=" + explosions[0]
                                + ", state=" + f.wither.getBedrockState());
                helper.assertTrue(!f.wither.runtimeState().wantsToExplode(), "Completed transition left explosion armed");
                helper.succeed();
            } finally {
                bus.unregister(listener);
                for (int x = -3; x <= 3; x++) for (int z = -3; z <= 3; z++) {
                    helper.getLevel().setBlockAndUpdate(floor.offset(x, 0, z), Blocks.AIR.defaultBlockState());
                }
            }
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_reload_transients")
    public static void saveLoadCancelsStaleChargeAndPreservesVolleyAlternation(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            f.enterSecondPhase();
            for (int tick = 0; tick < 500 && !f.wither.runtimeState().charging(); tick++) f.tick();
            helper.assertTrue(f.wither.runtimeState().charging(), "Ordinary charge never became saveable");
            CompoundTag saved = new CompoundTag();
            f.wither.saveWithoutId(saved);
            f.wither.load(saved);
            helper.assertTrue(!f.wither.runtimeState().charging() && f.wither.getDeltaMovement().lengthSqr() == 0.0D,
                    "Loading active charge retained stale velocity or transient charging");
            f.wither.setTarget(f.target);
            int shotsBefore = f.shots.size();
            boolean repeatedChargeTooEarly = false;
            for (int tick = 0; tick < 600 && f.shots.size() < shotsBefore + 8; tick++) {
                f.tick();
                repeatedChargeTooEarly |= f.wither.runtimeState().charging() && f.shots.size() < shotsBefore + 8;
            }
            helper.assertTrue(f.shots.size() >= shotsBefore + 8 && !repeatedChargeTooEarly,
                    "Reloaded phase 2 stalled or lost every-second-volley charge alternation");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_historical_acceleration")
    public static void provisionalAccelerationIsIndependentFromNbtBucketAndVolleyPause(GameTestHelper helper) {
        Difficulty previous = helper.getLevel().getDifficulty();
        helper.getLevel().getServer().setDifficulty(Difficulty.NORMAL, true);
        try (Fixture f = new Fixture(helper)) {
            // Explicit historical fallback: integer maxHealth/6 and half cadence,
            // not an equation combining the modern 75-HP NBT bucket with Wiki HP points.
            f.wither.setHealth(f.wither.getMaxHealth() - f.wither.getMaxHealth() / 6.0F - 1.0F);
            f.wither.volleyController().onAcceptedDamage();
            if (helper.getLevel().getDifficulty() != Difficulty.EASY) {
                helper.assertTrue(f.wither.runtimeState().fireRate() == 10,
                        "Historical acceleration fallback never halves the base 20-tick rate");
            }
            for (int tick = 0; tick < 320 && f.shots.size() < 4; tick++) f.tick();
            helper.assertTrue(f.shots.size() == 4 && f.wither.runtimeState().delayShot() == 140,
                    "A completed volley did not arm its independent 140-tick pause");
            f.wither.runtimeState().setFireRate(1);
            for (int tick = 0; tick < 139; tick++) f.tick();
            helper.assertTrue(f.shots.size() == 4, "Changing fireRate shortened the inter-volley pause");
            helper.succeed();
        } finally {
            helper.getLevel().getServer().setDifficulty(previous, true);
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_phase2_actual_volley_gap")
    public static void phaseTwoActualProjectileGapDoesNotAddFireRate(GameTestHelper helper) {
        for (int fireRate : new int[] {20, 10}) {
            try (Fixture f = new Fixture(helper)) {
                f.enterSecondPhase();
                f.wither.runtimeState().setFireRate(fireRate);
                for (int tick = 0; tick < 200 && f.shots.size() < 4; tick++) f.tick();
                helper.assertTrue(f.shots.size() == 4, "Phase-2 first burst never completed");
                int elapsed = 0;
                while (f.shots.size() < 5 && elapsed < 200) { f.tick(); elapsed++; }
                helper.assertTrue(elapsed == 140,
                        "Actual dangerous-to-normal inter-volley gap must be140 independently of fireRate="
                                + fireRate + "; got " + elapsed);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_reload_move_burst")
    public static void reloadDuringMovementAndBurstResumesWithoutStaleMotion(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            f.tick();
            helper.assertTrue(f.wither.runtimeState().pathing(), "Ordinary reposition path never began");
            CompoundTag saved = new CompoundTag();
            f.wither.saveWithoutId(saved);
            f.wither.load(saved);
            helper.assertTrue(!f.wither.runtimeState().pathing() && f.wither.getDeltaMovement().lengthSqr() == 0,
                    "Movement reload retained a stale navigation path or velocity");
            f.wither.setTarget(f.target);
            for (int tick = 0; tick < 300 && f.shots.size() < 2; tick++) f.tick();
            helper.assertTrue(f.shots.size() == 2, "Reloaded reposition never reached an ordinary volley");
            saved = new CompoundTag();
            f.wither.saveWithoutId(saved);
            f.wither.load(saved);
            f.wither.setTarget(f.target);
            for (int tick = 0; tick < 100 && f.shots.size() < 4; tick++) f.tick();
            helper.assertTrue(f.shots.equals(List.of(false, false, false, true)),
                    "Burst reload duplicated or lost the ordered center projectile counter");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_reload_transition")
    public static void transitionReloadPreservesOneShotAndCannotWaitForever(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            int[] explosions = {0};
            Consumer<net.minecraftforge.event.level.ExplosionEvent.Start> listener = event -> {
                if (event.getExplosion().getExploder() == f.wither) explosions[0]++;
            };
            var bus = net.minecraftforge.common.MinecraftForge.EVENT_BUS;
            bus.addListener(net.minecraftforge.eventbus.api.EventPriority.NORMAL, false,
                    net.minecraftforge.event.level.ExplosionEvent.Start.class, listener);
            try {
                f.wither.setHealth(f.wither.getMaxHealth() / 2.0F);
                f.tick();
                helper.assertTrue(f.wither.runtimeState().wantsToExplode(), "Transition was not pending before save");
                CompoundTag saved = new CompoundTag();
                f.wither.saveWithoutId(saved);
                f.wither.load(saved);
                f.wither.setTarget(f.target);
                for (int tick = 0; tick < 120; tick++) f.tick();
                helper.assertTrue(explosions[0] == 1 && !f.wither.runtimeState().wantsToExplode(),
                        "Reloaded unsupported descent did not finish once within the bounded adapter budget");
                int skeletonCount = f.wither.runtimeState().numSkeletons();
                saved = new CompoundTag();
                f.wither.saveWithoutId(saved);
                f.wither.load(saved);
                f.wither.setTarget(f.target);
                for (int tick = 0; tick < 160; tick++) f.tick();
                helper.assertTrue(explosions[0] == 1 && f.wither.runtimeState().numSkeletons() == skeletonCount,
                        "Completed transition replayed explosion or skeletons after reload");
                helper.succeed();
            } finally { bus.unregister(listener); }
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_invalid_dash_vectors")
    public static void dashAdapterRejectsNonfiniteVectorsWithoutCorruptingEntity(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            f.enterSecondPhase();
            for (Vec3 vector : new Vec3[] {new Vec3(Double.NaN, 0, 0),
                    new Vec3(Double.POSITIVE_INFINITY, 0, 0), Vec3.ZERO}) {
                boolean rejected = false;
                try { f.wither.dashController().beginMeasuredDash(vector, 2.0D); }
                catch (IllegalArgumentException expected) { rejected = true; }
                helper.assertTrue(rejected && !f.wither.runtimeState().charging(),
                        "Invalid dash direction was accepted or partially corrupted charge state: " + vector);
            }
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_phase2_sideheads")
    public static void secondPhaseSideHeadsFireOutsideChargeGates(GameTestHelper helper) {
        Difficulty previous = helper.getLevel().getDifficulty();
        helper.getLevel().getServer().setDifficulty(Difficulty.NORMAL, true);
        try (Fixture f = new Fixture(helper)) {
            f.enterSecondPhase();
            Cow sideTarget = EntityType.COW.create(helper.getLevel());
            if (sideTarget == null) throw new IllegalStateException("Failed to create side target");
            sideTarget.setPos(f.wither.getX() + 8, f.wither.getY(), f.wither.getZ());
            sideTarget.setInvulnerable(true);
            sideTarget.setNoAi(true);
            helper.getLevel().addFreshEntity(sideTarget);
            try {
                f.wither.setAlternativeHeadTarget(1, sideTarget.getUUID());
                f.wither.runtimeState().head(1).setNextUpdate(f.wither.tickCount + 1);
                int before = f.spawned.size();
                f.tick();
                helper.assertTrue(f.spawned.size() == before + 1,
                        "Historical phase-independent side-head scheduler did not fire in phase2");
                f.wither.dashController().prepareTargetCharge();
                f.wither.runtimeState().head(1).setNextUpdate(f.wither.tickCount + 1);
                f.wither.runtimeState().head(1).setIdleUpdates(16);
                before = f.spawned.size();
                for (int tick = 0; tick < 25; tick++) f.tick();
                helper.assertTrue(f.spawned.size() == before,
                        "Side-head scheduler fired targeted or passive skulls during charge preparation/execution");
                helper.succeed();
            } finally { sideTarget.discard(); }
        } finally { helper.getLevel().getServer().setDifficulty(previous, true); }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_lifecycle_dash_gates")
    public static void publicDashAdaptersCannotOverrideSpawnOrDeath(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            f.enterSecondPhase();
            f.wither.spawnController().initializeNewEntity();
            boolean rejected = false;
            try { f.wither.dashController().beginMeasuredDash(new Vec3(1, 0, 0), 2.0D); }
            catch (IllegalStateException expected) { rejected = true; }
            helper.assertTrue(rejected && f.wither.getBedrockState() == BedrockWitherState.SPAWN_SEQUENCE,
                    "Dash adapter overrode active spawn state");
            f.wither.spawnController().restore(0, BedrockWitherState.PHASE2_RECOVER);
            f.wither.stateMachine().enter(BedrockWitherState.PHASE1_REPOSITION);
            f.wither.runtimeState().setNativePhase(BedrockWitherPhaseController.firstPhaseNativeId());
            f.wither.setAerialAttack(true);
            f.wither.setHealth(f.wither.getMaxHealth() / 2.0F);
            f.tick();
            helper.assertTrue(f.wither.getBedrockState() == BedrockWitherState.PHASE_TRANSITION
                            && f.wither.runtimeState().wantsToExplode(),
                    "Ordinary half-health transition was not pending before adapter validation");
            rejected = false;
            try { f.wither.dashController().beginMeasuredDash(new Vec3(1, 0, 0), 2.0D); }
            catch (IllegalStateException expected) { rejected = true; }
            helper.assertTrue(rejected && f.wither.getBedrockState() == BedrockWitherState.PHASE_TRANSITION
                            && f.wither.runtimeState().wantsToExplode() && !f.wither.runtimeState().charging(),
                    "Dash adapter interrupted half-health transition and stranded its one-shot explosion");
            f.wither.hurt(helper.getLevel().damageSources().genericKill(), Float.MAX_VALUE);
            rejected = false;
            try { f.wither.dashController().beginMeasuredDash(new Vec3(1, 0, 0), 2.0D); }
            catch (IllegalStateException expected) { rejected = true; }
            helper.assertTrue(rejected && f.wither.getBedrockState() == BedrockWitherState.DEATH_SEQUENCE,
                    "Dash adapter overrode semantic death state");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_targetless_shot_delays")
    public static void lostTargetDoesNotFreezeCooldownHoverOrPassiveSideHeads(GameTestHelper helper) {
        Difficulty previous = helper.getLevel().getDifficulty();
        helper.getLevel().getServer().setDifficulty(Difficulty.NORMAL, true);
        try {
            for (boolean completeVolley : new boolean[] {true, false}) {
                try (Fixture f = new Fixture(helper)) {
                    for (int tick = 0; tick < 320; tick++) {
                        f.tick();
                        if (completeVolley ? f.shots.size() == 4
                                : f.wither.getBedrockState() == BedrockWitherState.PHASE1_BURST
                                && f.shots.isEmpty() && f.wither.runtimeState().delayShot() > 0) break;
                    }
                    int expectedCenterCount = completeVolley ? 4 : 0;
                    int delay = f.wither.runtimeState().delayShot();
                    helper.assertTrue(f.wither.runtimeState().projectileCounter() == expectedCenterCount
                                    && delay > 0 && (completeVolley ? delay == 140 : delay <= 20),
                            "Ordinary cycle never reached the requested cooldown/hover gate");
                    long dangerousBefore = f.spawned.stream()
                            .filter(entity -> entity instanceof BedrockWitherSkullEntity skull && skull.isDangerous()).count();
                    f.wither.setTarget(null);
                    f.target.discard();
                    for (int tick = 0; tick < delay - 1; tick++) f.tick();
                    helper.assertTrue(f.wither.runtimeState().delayShot() == 1,
                            "Lost target froze or double-decremented the shared shot delay");
                    f.tick();
                    helper.assertTrue(f.wither.runtimeState().delayShot() == 0
                                    && f.wither.runtimeState().mainHeadAttackCountdown() == 0,
                            "Targetless cooldown/hover did not expire both firing timers");
                    for (int tick = delay; tick < 500; tick++) f.tick();
                    long dangerousAfter = f.spawned.stream()
                            .filter(entity -> entity instanceof BedrockWitherSkullEntity skull && skull.isDangerous()).count();
                    helper.assertTrue(dangerousAfter > dangerousBefore,
                            "Passive dangerous side-head firing never resumed after target loss");
                    helper.assertTrue(f.wither.runtimeState().projectileCounter() == expectedCenterCount,
                            "Center head fired while its target was missing");
                    f.replaceTarget();
                    for (int tick = 0; tick < 350
                            && f.wither.runtimeState().projectileCounter() < expectedCenterCount + 4; tick++) f.tick();
                    helper.assertTrue(f.wither.runtimeState().projectileCounter() >= expectedCenterCount + 4,
                            "Center-head volley failed to resume after target reacquisition");
                }
            }
        } finally { helper.getLevel().getServer().setDifficulty(previous, true); }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_legacy_hurt_reload")
    public static void legacyTransientHurtStateReloadReturnsToOrdinaryCombat(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            CompoundTag saved = new CompoundTag();
            f.wither.saveWithoutId(saved);
            saved.putInt("BedrockState", BedrockWitherState.PHASE1_HURT_REACTION.id());
            f.wither.load(saved);
            f.wither.setTarget(f.target);
            for (int tick = 0; tick < 320 && f.shots.size() < 4; tick++) f.tick();
            helper.assertTrue(f.shots.size() >= 4, "Legacy saved hurt state remained permanently outside the firing cycle");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_actual_dash_ticks")
    public static void ordinaryDashMovesForTwentyActiveTicksAndStopsAtBedrock(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            f.enterSecondPhase();
            for (int tick = 0; tick < 500 && !f.wither.runtimeState().charging(); tick++) f.tick();
            helper.assertTrue(f.wither.runtimeState().charging(), "Ordinary dash was never reached");
            Vec3 start = f.wither.position();
            for (int tick = 0; tick < 20; tick++) f.tick();
            helper.assertTrue(!f.wither.runtimeState().charging(), "Dash exceeded its 20 active ticks");
            helper.assertTrue(Math.abs(f.wither.position().distanceTo(start) - 40.0D) < 0.01D,
                    "Twenty provisional 2-block motion ticks did not move 40 blocks: "
                            + f.wither.position().distanceTo(start));
            // Force another ordinary alternate volley to aim at a new live target.
            f.replaceTarget();
            for (int tick = 0; tick < 600 && !f.wither.runtimeState().charging(); tick++) f.tick();
            helper.assertTrue(f.wither.runtimeState().charging(), "Second ordinary dash was never reached");
            BlockPos obstacle = BlockPos.containing(f.wither.position().add(f.wither.runtimeState().chargeDirection().scale(2)));
            helper.getLevel().setBlockAndUpdate(obstacle, Blocks.BEDROCK.defaultBlockState());
            try {
                f.tick();
                helper.assertTrue(!f.wither.runtimeState().charging()
                                && helper.getLevel().getBlockState(obstacle).is(Blocks.BEDROCK),
                        "Unbreakable obstruction did not terminate ordinary charge safely");
            } finally {
                helper.getLevel().setBlockAndUpdate(obstacle, Blocks.AIR.defaultBlockState());
            }
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_threat_eligibility")
    public static void highestDamageGoalRejectsCreativeAndSpectatorPlayers(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            List<net.minecraft.server.level.ServerPlayer> players = new ArrayList<>();
            try {
                for (int i = 0; i < 3; i++) {
                    // Forge's supplied no-network ServerPlayer fixture avoids
                    // the vanilla helper's unsupported null-channel login path.
                    var player = new net.minecraftforge.common.util.FakePlayer(helper.getLevel(),
                            new com.mojang.authlib.GameProfile(java.util.UUID.randomUUID(), "BwrFixture" + i));
                    players.add(player);
                    player.setPos(f.wither.getX() + 4 + i, f.wither.getY(), f.wither.getZ());
                    helper.getLevel().addNewPlayer(player);
                    player.setGameMode(i == 0 ? net.minecraft.world.level.GameType.CREATIVE
                            : i == 1 ? net.minecraft.world.level.GameType.SPECTATOR
                            : net.minecraft.world.level.GameType.SURVIVAL);
                    f.wither.threatLedger().recordDamage(player, 100 - 40 * i, helper.getLevel().getGameTime());
                }
                var goal = new org.kneekura.bedrockwither.entity.ai.BedrockHighestDamageTargetGoal(f.wither);
                helper.assertTrue(goal.canUse(), "No eligible survival threat was selected");
                goal.start();
                helper.assertTrue(f.wither.getTarget() == players.get(2),
                        "Creative or spectator high-damage player displaced the eligible survival player");
                players.get(2).setGameMode(net.minecraft.world.level.GameType.CREATIVE);
                helper.assertTrue(!goal.canContinueToUse(), "Goal retained a player after switching to creative");
                goal.stop();
                helper.assertTrue(f.wither.getTarget() == null, "Invalid priority-one target was not cleared");
                helper.succeed();
            } finally {
                for (var player : players) player.discard();
            }
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_invalid_player_entry")
    public static void combatControllersRejectCreativeTargetsImmediately(GameTestHelper helper) {
        try (Fixture f = new Fixture(helper)) {
            var creative = new net.minecraftforge.common.util.FakePlayer(helper.getLevel(),
                    new com.mojang.authlib.GameProfile(java.util.UUID.randomUUID(), "BwrCreative"));
            creative.setPos(f.wither.getX() + 4, f.wither.getY(), f.wither.getZ());
            helper.getLevel().addNewPlayer(creative);
            try {
                creative.setGameMode(net.minecraft.world.level.GameType.CREATIVE);
                f.wither.setTarget(creative);
                f.wither.stateMachine().enter(BedrockWitherState.PHASE1_BURST);
                f.wither.runtimeState().setMainHeadAttackCountdown(1);
                f.wither.volleyController().tick();
                helper.assertTrue(f.wither.runtimeState().projectileCounter() == 0,
                        "Volley accepted an ineligible creative target before target-selector cleanup");
                f.wither.specialMovementController().requestMove();
                helper.assertTrue(!f.wither.specialMovementController().canBegin(),
                        "Special reposition accepted an ineligible creative target");
                f.enterSecondPhase();
                f.wither.dashController().prepareTargetCharge();
                helper.assertTrue(f.wither.getBedrockState() != BedrockWitherState.PHASE2_DASH_PREP,
                        "Charge preparation accepted an ineligible creative target");
                helper.succeed();
            } finally { creative.discard(); }
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_combat_rate_boundaries")
    public static void historicalRateThresholdsResetAtPhaseAndSurviveHealingAndReload(GameTestHelper helper) {
        Difficulty previous = helper.getLevel().getDifficulty();
        helper.getLevel().getServer().setDifficulty(Difficulty.HARD, true);
        try {
            try (Fixture f = new Fixture(helper)) {
                int[][] cases = {{500, 20}, {499, 10}, {400, 10}, {399, 5}};
                for (int[] c : cases) {
                    f.wither.setHealth(c[0]);
                    f.wither.volleyController().onAcceptedDamage();
                    helper.assertTrue(f.wither.runtimeState().fireRate() == c[1],
                            "Historical strict-threshold rate mismatch at " + c[0]);
                }
                f.wither.setHealth(300);
                f.tick(); // actual half-health transition must reset rate and stage cursor
                helper.assertTrue(f.wither.runtimeState().fireRate() == 20, "Phase transition did not reset base rate");
                f.wither.setHealth(299);
                f.wither.volleyController().onAcceptedDamage();
                helper.assertTrue(f.wither.runtimeState().fireRate() == 20,
                        "First damage just below half health reused the first-phase cursor and accelerated too early");
                f.wither.setHealth(199);
                f.wither.volleyController().onAcceptedDamage();
                helper.assertTrue(f.wither.runtimeState().fireRate() == 10, "Second-phase historical interval did not halve rate");
                f.wither.setHealth(99);
                f.wither.volleyController().onAcceptedDamage();
                helper.assertTrue(f.wither.runtimeState().fireRate() == 5, "Second phase did not reach the second rate stage");
                int bucket = f.wither.runtimeState().lastHealthValue();
                f.wither.setHealth(250);
                f.wither.volleyController().onAcceptedDamage();
                helper.assertTrue(f.wither.runtimeState().fireRate() == 5 && f.wither.runtimeState().lastHealthValue() == bucket,
                        "Healing increased the persisted minimum bucket or reversed acceleration");
                CompoundTag saved = new CompoundTag();
                f.wither.saveWithoutId(saved);
                f.wither.load(saved);
                f.wither.setHealth(98);
                f.wither.volleyController().onAcceptedDamage();
                helper.assertTrue(f.wither.runtimeState().fireRate() == 5,
                        "Reload lost the independent historical rate cursor and halved the same interval twice");
            }
            try (Fixture f = new Fixture(helper)) {
                f.wither.setHealth(90);
                f.wither.volleyController().onAcceptedDamage();
                helper.assertTrue(f.wither.runtimeState().fireRate() == 10,
                        "A large single hit must perform only one historical halving, not one per crossed interval");
            }
        } finally { helper.getLevel().getServer().setDifficulty(previous, true); }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_official_persistence")
    public static void officialPersistencePreventsNaturalDespawnForNewAndLegacySavedBosses(GameTestHelper helper) {
        Difficulty previous = helper.getLevel().getDifficulty();
        BedrockWitherEntity fresh = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        BedrockWitherEntity legacy = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (fresh == null || legacy == null) throw new IllegalStateException("Failed to create persistence fixtures");
        var farPlayer = new net.minecraftforge.common.util.FakePlayer(helper.getLevel(),
                new com.mojang.authlib.GameProfile(java.util.UUID.randomUUID(), "BwrPersistent"));
        try {
            helper.getLevel().getServer().setDifficulty(Difficulty.NORMAL, true);
            BlockPos position = helper.absolutePos(new BlockPos(2, 0, 2))
                    .atY(helper.getLevel().getMaxBuildHeight() - 64);
            fresh.setPos(position.getX() + 0.5D, position.getY(), position.getZ() + 0.5D);
            CompoundTag saved = new CompoundTag();
            fresh.saveWithoutId(saved);
            saved.putBoolean("PersistenceRequired", false); // old product saves used the inherited false value
            legacy.load(saved);
            int despawnDistance = fresh.getType().getCategory().getDespawnDistance();
            farPlayer.setPos(fresh.getX() + despawnDistance + 32.0D, fresh.getY(), fresh.getZ());
            helper.getLevel().addNewPlayer(farPlayer);
            farPlayer.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
            helper.assertTrue(!farPlayer.isCreative() && !farPlayer.isSpectator()
                            && helper.getLevel().getNearestPlayer(fresh, -1.0D) == farPlayer
                            && fresh.distanceToSqr(farPlayer) > (double) despawnDistance * despawnDistance,
                    "Persistence fixture did not establish an eligible distant nearest player");
            helper.assertTrue(!legacy.isPersistenceRequired(), "Legacy NBT fixture lost its explicit false persistence flag");
            fresh.checkDespawn();
            legacy.checkDespawn();
            helper.assertTrue(!fresh.isRemoved() && !legacy.isRemoved(),
                    "Official minecraft:persistent boss naturally despawned, new=" + fresh.isRemoved()
                            + ", legacy=" + legacy.isRemoved());
            // Keep the inherited Peaceful branch, which precedes persistence.
            helper.getLevel().getServer().setDifficulty(Difficulty.PEACEFUL, true);
            fresh.checkDespawn();
            legacy.checkDespawn();
            helper.assertTrue(fresh.isRemoved() && legacy.isRemoved(),
                    "Persistence override incorrectly bypassed ordinary Peaceful removal");
            helper.succeed();
        } finally {
            fresh.discard();
            legacy.discard();
            farPlayer.discard();
            helper.getLevel().getServer().setDifficulty(previous, true);
        }
    }

    private static final class Fixture implements AutoCloseable {
        private final GameTestHelper helper;
        private final BedrockWitherEntity wither;
        private Cow target;
        private final List<Boolean> shots = new ArrayList<>();
        private final List<net.minecraft.world.entity.Entity> spawned = new ArrayList<>();
        private final Consumer<net.minecraftforge.event.entity.EntityJoinLevelEvent> listener;

        private Fixture(GameTestHelper helper) {
            this.helper = helper;
            wither = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
            if (wither == null) throw new IllegalStateException("Failed to create Wither");
            BlockPos p = helper.absolutePos(new BlockPos(2, 0, 2))
                    .atY(helper.getLevel().getMaxBuildHeight() - 64);
            wither.setPos(p.getX() + 0.5D, p.getY(), p.getZ() + 0.5D);
            // The shared world has actual terrain near Y64. Use clear high air,
            // separate from reward fixtures at maxBuildHeight-32, rather than
            // accidentally testing movement inside terrain/trees at Y68.
            wither.getRandom().setSeed(42L);
            helper.getLevel().tickNonPassenger(wither); // difficulty initialization, still in spawn
            wither.spawnController().restore(0, BedrockWitherState.PHASE1_REPOSITION);
            wither.stateMachine().enter(BedrockWitherState.PHASE1_REPOSITION);
            replaceTarget();
            listener = event -> {
                // No world ticks run while a synchronous fixture is active, so
                // every skeleton/reward emitted here belongs to this fixture.
                if (event.getEntity() instanceof net.minecraft.world.entity.monster.WitherSkeleton
                        || event.getEntity() instanceof net.minecraft.world.entity.ExperienceOrb
                        || event.getEntity() instanceof net.minecraft.world.entity.item.ItemEntity) {
                    spawned.add(event.getEntity());
                }
                if (event.getEntity() instanceof BedrockWitherSkullEntity skull && skull.getOwner() == wither) {
                    spawned.add(skull);
                    if (wither.runtimeState().projectileCounter() > shots.size()) shots.add(skull.isDangerous());
                }
            };
            net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener(
                    net.minecraftforge.eventbus.api.EventPriority.NORMAL, false,
                    net.minecraftforge.event.entity.EntityJoinLevelEvent.class, listener);
        }

        private void replaceTarget() {
            if (target != null) target.discard();
            target = EntityType.COW.create(helper.getLevel());
            if (target == null) throw new IllegalStateException("Failed to create target");
            target.setPos(wither.getX() + 16.0D, wither.getY(), wither.getZ());
            // A real, eligible target: invulnerable/unregistered cows are
            // eventually rejected by the ordinary nearest-target goal.
            target.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(10000);
            target.setHealth(10000);
            target.setNoAi(true);
            helper.getLevel().addFreshEntity(target);
            wither.setTarget(target);
        }

        private void enterSecondPhase() {
            wither.runtimeState().setNativePhase(BedrockWitherPhaseController.secondPhaseNativeId());
            wither.setAerialAttack(false);
            // Legacy saved phase-2 idle/prep is a supported ordinary-AI entry.
            wither.stateMachine().enter(BedrockWitherState.PHASE2_RECOVER);
        }

        private void tick() {
            // Use the actual server entity-tick entry: it advances tickCount and
            // old transforms before invoking Mob.tick, unlike a bare tick call.
            helper.getLevel().tickNonPassenger(wither);
        }

        @Override public void close() {
            net.minecraftforge.common.MinecraftForge.EVENT_BUS.unregister(listener);
            for (net.minecraft.world.entity.Entity entity : spawned) entity.discard();
            wither.discard();
            target.discard();
        }
    }
}
