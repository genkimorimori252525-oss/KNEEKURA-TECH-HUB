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
import org.kneekura.techhub.warfarewings.physics.RuntimeTacticalAtlas;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

import java.util.List;

/**
 * Source-roster-driven exact-binary smoke: all 24 real WW entity registrations.
 * Sequential execution guarantees only ONE airplane exists during each
 * 40-tick test phase, allowing reproducible real flight without a 24-plane
 * collision or 24x aircraft physics CPU spike.
 *
 * This is a bounded registry/controller/motion check, not parity/calibration.
 * 401-tick representative calibration remains a separate scenario.
 */
@GameTestHolder(PhysicsTraceProbeMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class AllAircraftRosterGameTests {
    private AllAircraftRosterGameTests() {}
    private static final int DURATION = 40;

    @GameTest(template = "empty", batch = "ww_roster_24_sequential", timeoutTicks = 1800)
    public static void everyAtlasAirframeMovesUnderRealIaController(GameTestHelper helper) {
        ServerLevel world = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        var data = RuntimeTacticalAtlas.load();
        if (data.size() != 24) throw new IllegalStateException("Missing any pinned Atlas airframe");
        List<String> keys = data.keySet().stream().sorted().toList();
        Vec3 spawn = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 215, 0)));
        final int[] index = {0};
        final Entity[] plane = {null};
        final String[] scenario = {null};
        // Stage the first aircraft immediately; each later craft is spawned
        // only after the previous completed run and its pilot were removed.
        startNext(world, spawn, data, keys, index, plane, scenario);
        helper.succeedWhen(() -> {
            var result = RuntimeTacticalPilot.result(scenario[0]);
            if (result == null)
                throw new GameTestAssertException("Sequential real-aircraft flight still sampling "
                        + scenario[0] + " (" + index[0] + "/24)");
            try {
                if (!result.complete())
                    throw new IllegalStateException("Real aircraft flight failure for " + scenario[0]
                            + ": " + result.failure());
                if (result.samples() != DURATION || result.displacementBlocks() < 4.0
                        || result.nonzeroLateralTicks() < 3 || result.yawTravelDeg() < .25)
                    throw new IllegalStateException("Real aircraft motion/control below physical smoke floor: "
                            + scenario[0] + " movement=" + result.displacementBlocks()
                            + " yaw=" + result.yawTravelDeg()
                            + " controlTicks=" + result.nonzeroLateralTicks());
            } finally {
                LiveSquadronGameTests.cleanupTestEntities(plane[0]);
            }
            index[0]++;
            if (index[0] == keys.size()) return; // last result validates all 24
            startNext(world, spawn, data, keys, index, plane, scenario);
            throw new GameTestAssertException("Completed " + index[0]
                    + "/24 real airframes; next aircraft now flying");
        });
    }

    private static void startNext(ServerLevel world, Vec3 position,
                                  java.util.Map<String, RuntimeTacticalAtlas.Airframe> data,
                                  List<String> keys,
                                  int[] index, Entity[] aircraft, String[] scenarios) {
        String id = keys.get(index[0]);
        ResourceLocation key = new ResourceLocation(id);
        EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getOptional(key)
                .orElseThrow(() -> new IllegalStateException("Missing exact WW registered aircraft: " + id));
        Entity plane = type.create(world);
        ArmorStand pilot = EntityType.ARMOR_STAND.create(world);
        if (plane == null || pilot == null)
            throw new IllegalStateException("Unable to spawn aircraft/pilot for " + id);
        plane.moveTo(position.x, position.y, position.z, 0, 0);
        plane.setInvulnerable(true);
        pilot.moveTo(position.x, position.y, position.z);
        pilot.setInvisible(true);
        pilot.setInvulnerable(true);
        pilot.setNoGravity(true);
        world.addFreshEntity(plane);
        world.addFreshEntity(pilot);
        if (!pilot.startRiding(plane, true)) {
            LiveSquadronGameTests.cleanupTestEntities(plane, pilot);
            throw new IllegalStateException("Pinned aircraft did not accept synthetic IA pilot: " + id);
        }
        plane.setDeltaMovement(0, 0, .7);
        IaRuntimeAccess.chill(plane);
        IaRuntimeAccess.setEngineTarget(plane, 1);
        TacticalAirAI.Mission mission = switch (data.get(id).profile().role()) {
            case "bomber" -> TacticalAirAI.Mission.LEVEL_BOMB;
            case "attacker" -> TacticalAirAI.Mission.STRAFE;
            case "torpedo_bomber" -> TacticalAirAI.Mission.TORPEDO;
            default -> TacticalAirAI.Mission.INTERCEPT;
        };
        String scenario = "roster-" + id.substring(id.indexOf(':') + 1);
        // With a non-hostile explicit route, all roles must steer toward the
        // same deliberately offset target to prove per-airframe yaw response.
        RuntimeTacticalPilot.start(scenario, world, plane, pilot, mission,
                position.add(105, 10, 175), position.add(-140, 10, -200),
                null, null, null, DURATION, true);
        aircraft[0] = plane;
        scenarios[0] = scenario;
    }
}
