package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

import java.nio.file.Files;

/**
 * These only run with both pinned runtime dependency JARs.
 * Exercises the real non-player IA flight controller; no simulated bullet hit
 * or release operation and no implicit source-to-runtime parity assertion.
 */
@GameTestHolder(PhysicsTraceProbeMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class TacticalRuntimeGameTests {
    private TacticalRuntimeGameTests() {}
    private static final int DURATION = 180;

    // Forge runs tests in the same batch together. One test per batch keeps
    // their real aircraft out of each other's proximity/collision sensors.
    @GameTest(template = "empty", timeoutTicks = 320, batch = "ww_tactical_a6m")
    public static void a6mSteeredInterception(GameTestHelper helper) {
        start(helper, "a6m-steered-interception", "a6m",
                TacticalAirAI.Mission.INTERCEPT, true);
    }

    @GameTest(template = "empty", timeoutTicks = 320, batch = "ww_tactical_p47n")
    public static void p47nSteeredInterception(GameTestHelper helper) {
        start(helper, "p47n-steered-interception", "p47n",
                TacticalAirAI.Mission.INTERCEPT, true);
    }

    @GameTest(template = "empty", timeoutTicks = 320, batch = "ww_tactical_il2")
    public static void il2GroundApproachNoFire(GameTestHelper helper) {
        start(helper, "il2-ground-approach-no-fire", "il2",
                TacticalAirAI.Mission.STRAFE, false);
    }

    @GameTest(template = "empty", timeoutTicks = 320, batch = "ww_tactical_b17")
    public static void b17LevelBombGuidanceNoRelease(GameTestHelper helper) {
        start(helper, "b17-level-bomb-guidance-only", "b17",
                TacticalAirAI.Mission.LEVEL_BOMB, false);
    }

    @GameTest(template = "empty", timeoutTicks = 320, batch = "ww_tactical_g4m")
    public static void g4mTorpedoApproachNoRelease(GameTestHelper helper) {
        start(helper, "g4m-torpedo-guidance-only", "g4m",
                TacticalAirAI.Mission.TORPEDO, false);
    }

    private static void start(GameTestHelper helper, String scenario, String aircraftName,
                              TacticalAirAI.Mission mission, boolean contact) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        ResourceLocation id = new ResourceLocation("warfare_wings", aircraftName);
        EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getOptional(id)
                .orElseThrow(() -> new IllegalStateException("Pinned Warfare Wings entity absent: " + id));
        Entity aircraft = type.create(level);
        ArmorStand pilot = EntityType.ARMOR_STAND.create(level);
        if (aircraft == null || pilot == null)
            throw new IllegalStateException("Cannot spawn real tactical bridge test entities");

        BlockPos origin = helper.absolutePos(new BlockPos(0, 200, 0));
        Vec3 start = Vec3.atBottomCenterOf(origin);
        aircraft.moveTo(start.x, start.y, start.z, 0f, 0f);
        // The runtime driver fails explicitly if another test's aircraft
        // enters its 80-block obstacle query. This also catches accidental
        // concurrent execution by a runner outside GameTest's batch policy.
        aircraft.addTag(RuntimeTacticalPilot.GAME_TEST_ISOLATION_TAG);
        aircraft.setInvulnerable(true);
        pilot.moveTo(start.x, start.y, start.z, 0f, 0f);
        pilot.setInvisible(true);
        pilot.setInvulnerable(true);
        pilot.setNoGravity(true);

        level.addFreshEntity(aircraft);
        level.addFreshEntity(pilot);
        if (!pilot.startRiding(aircraft, true))
            throw new IllegalStateException("Cannot mount non-player IA controller pilot");

        aircraft.setDeltaMovement(0, 0, 0.7);
        IaRuntimeAccess.chill(aircraft);
        IaRuntimeAccess.setEngineTarget(aircraft, 1f);
        Entity hostile = null;
        if (contact) {
            ArmorStand observed = EntityType.ARMOR_STAND.create(level);
            if (observed == null) throw new IllegalStateException("Cannot spawn observed target");
            Vec3 p = start.add(140, 0, 245);
            observed.moveTo(p.x, p.y, p.z);
            observed.setNoGravity(true);
            observed.setInvisible(true);
            observed.setInvulnerable(true);
            level.addFreshEntity(observed);
            hostile = observed;
        }

        RuntimeTacticalPilot.start(scenario, level, aircraft, pilot, mission,
                start.add(140, 0, 245), start.add(-140, 0, -200),
                hostile, null, null, DURATION);
        helper.succeedWhen(() -> {
            RuntimeTacticalPilot.Result result = RuntimeTacticalPilot.result(scenario);
            if (result == null)
                throw new GameTestAssertException("Tactical aircraft bridge still sampling");
            if (!result.complete())
                throw new IllegalStateException("IA tactical bridge failed: " + result.failure());
            if (result.samples() != DURATION || result.nonzeroLateralTicks() < 10
                    || result.yawTravelDeg() < 2.0 || result.displacementBlocks() < 8.0)
                throw new IllegalStateException("No meaningful closed-loop lateral control: "
                        + result.samples() + " samples, " + result.nonzeroLateralTicks()
                        + " steering ticks, " + result.yawTravelDeg() + " yaw degrees, "
                        + result.displacementBlocks() + " blocks moved");
            if (result.firstCommandSample() < 1
                    || result.firstYawResponseSample() <= result.firstCommandSample())
                throw new IllegalStateException("IA expected one-physics-tick input delay, command sample="
                        + result.firstCommandSample() + " yaw response sample="
                        + result.firstYawResponseSample());
            if (!Files.isRegularFile(result.trace()))
                throw new IllegalStateException("Missing on-disk IA tactical control trace");
        });
    }
}
