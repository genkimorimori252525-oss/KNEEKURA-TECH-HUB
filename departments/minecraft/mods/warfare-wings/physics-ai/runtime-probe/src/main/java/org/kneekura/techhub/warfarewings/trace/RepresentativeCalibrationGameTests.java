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

/**
 * Equal-envelope exact-jar acceleration experiments for the four representative
 * types which lacked the A6M's 401-sample physical calibration. No AI weapons,
 * combat parity or aircraft ranking is inferred from these neutral controls.
 *
 * All four match the original A6M experiment: (0,200,0) relative to each
 * GameTest, +Z 0.7 blocks/tick, 0 yaw/pitch, 1.0 engine target, neutral inputs,
 * no wind/fuel consumption/collision damage, 400 consecutive entity ticks.
 */
@GameTestHolder(PhysicsTraceProbeMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class RepresentativeCalibrationGameTests {
    private RepresentativeCalibrationGameTests() {}

    @GameTest(template = "empty", batch = "ww_calibration_p47n", timeoutTicks = 560)
    public static void p47nNeutralAcceleration401Samples(GameTestHelper helper) {
        neutralFlight(helper, "p47n");
    }

    @GameTest(template = "empty", batch = "ww_calibration_spitfire", timeoutTicks = 560)
    public static void spitfireNeutralAcceleration401Samples(GameTestHelper helper) {
        neutralFlight(helper, "spitfire");
    }

    @GameTest(template = "empty", batch = "ww_calibration_il2", timeoutTicks = 560)
    public static void il2NeutralAcceleration401Samples(GameTestHelper helper) {
        neutralFlight(helper, "il2");
    }

    @GameTest(template = "empty", batch = "ww_calibration_b17", timeoutTicks = 560)
    public static void b17NeutralAcceleration401Samples(GameTestHelper helper) {
        neutralFlight(helper, "b17");
    }

    private static void neutralFlight(GameTestHelper helper, String airframe) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        Vec3 position = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 200, 0)));
        var warmup = new GameTestFlightChunkLease(level);
        warmup.update(position, new Vec3(0, 0, 0.7));
        // For a remote high-altitude GameTest, force ticketing alone may not
        // synchronously promote the starting chunk to an Entity-ticking chunk.
        level.getChunkAt(BlockPos.containing(position));
        helper.runAfterDelay(10, () -> {
            Entity aircraft = null;
            ArmorStand pilot = null;
            try {
                ResourceLocation registryId = new ResourceLocation("warfare_wings", airframe);
                EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getOptional(registryId)
                        .orElseThrow(() -> new IllegalStateException("Missing pinned airframe " + registryId));
                aircraft = type.create(level);
                pilot = EntityType.ARMOR_STAND.create(level);
                if (aircraft == null || pilot == null)
                    throw new IllegalStateException("Could not instantiate actual airplane/pilot " + registryId);
                aircraft.moveTo(position.x, position.y, position.z, 0f, 0f);
                aircraft.setInvulnerable(true);
                pilot.moveTo(position.x, position.y, position.z, 0f, 0f);
                pilot.setInvisible(true);
                pilot.setInvulnerable(true);
                pilot.setNoGravity(true);
                if (!level.addFreshEntity(aircraft) || !level.addFreshEntity(pilot))
                    throw new IllegalStateException("Could not register actual calibration entities " + registryId);
                if (!pilot.startRiding(aircraft, true))
                    throw new IllegalStateException("Could not mount calibration pilot " + registryId);
                aircraft.setDeltaMovement(0, 0, 0.7);
                aircraft.setYRot(0);
                aircraft.setXRot(0);
                IaRuntimeAccess.chill(aircraft);
                IaRuntimeAccess.setEngineTarget(aircraft, 1f);
                String scenario = airframe + "-throttle-step-v1";
                RuntimeTraceManager.start(level, aircraft, pilot, scenario,
                        "warfare_wings:" + airframe);
                Entity verifiedPlane = aircraft;
                ArmorStand verifiedPilot = pilot;
                helper.succeedWhen(() -> {
                    if (RuntimeTraceManager.failure() != null) {
                        LiveSquadronGameTests.cleanupTestEntities(verifiedPlane, verifiedPilot);
                        throw new IllegalStateException("Incomplete actual " + airframe + " trace: "
                                + RuntimeTraceManager.failure());
                    }
                    if (!RuntimeTraceManager.complete())
                        throw new GameTestAssertException("Actual " + airframe + " 401-sample flight ongoing");
                    LiveSquadronGameTests.cleanupTestEntities(verifiedPlane, verifiedPilot);
                });
            } catch (RuntimeException failure) {
                LiveSquadronGameTests.cleanupTestEntities(aircraft, pilot);
                throw failure;
            } finally {
                warmup.close();
            }
        });
    }
}
