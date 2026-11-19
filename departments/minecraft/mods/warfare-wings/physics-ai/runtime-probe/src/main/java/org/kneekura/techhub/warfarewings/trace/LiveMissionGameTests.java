package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

/**
 * Exact-mod, non-weapon mission progress regressions. Separate GameTest batches
 * prevent unrelated aircraft from contaminating nearby collision/LOS sensors.
 * Movement + recorded mission phases must actually occur in the real server.
 */
@GameTestHolder(PhysicsTraceProbeMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class LiveMissionGameTests {
    private LiveMissionGameTests() {}

    @GameTest(template = "empty", batch = "ww_live_escort_mission", timeoutTicks = 280)
    public static void escortFollowsDistinctLeaderStation(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        Vec3 base = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 205, 0)));
        Entity bomber = LiveSquadronGameTests.spawn(level, "b17", base, 0f, .7);
        Entity escort = LiveSquadronGameTests.spawn(level, "p47n", base.add(65, 8, -65), 0f, .8);
        bomber.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);
        escort.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);
        var commander = new RuntimeTacticalPilot.LiveOrder("convoy",
                TacticalAirAI.Mission.PATROL, base.add(0, 0, 500), base,
                null, null, null);
        RuntimeTacticalPilot.startLive("mission-escort-b17", level, bomber,
                (ArmorStand) bomber.getFirstPassenger(), commander, 135);
        RuntimeTacticalPilot.startLive("mission-escort-p47", level, escort,
                (ArmorStand) escort.getFirstPassenger(),
                new RuntimeTacticalPilot.LiveOrder("convoy", TacticalAirAI.Mission.ESCORT,
                        base.add(0, 30, 500), escort.position(), null, null, bomber.getUUID()),
                135);
        helper.succeedWhen(() -> {
            var lead = RuntimeTacticalPilot.result("mission-escort-b17");
            var wing = RuntimeTacticalPilot.result("mission-escort-p47");
            if (lead == null || wing == null)
                throw new GameTestAssertException("escort formation still flying");
            try {
                if (!lead.complete() || !wing.complete())
                    throw new IllegalStateException("leader/follower failure: " + lead.failure() + "/" + wing.failure());
                if (lead.samples() != 135 || wing.samples() != 135
                        || lead.displacementBlocks() < 8 || wing.displacementBlocks() < 8
                        || wing.escortTicks() < 80)
                    throw new IllegalStateException("No convincing live escort station duty or movement");
            } finally {
                LiveSquadronGameTests.cleanupTestEntities(bomber, escort);
            }
        });
    }

    @GameTest(template = "empty", batch = "ww_live_strike_mission", timeoutTicks = 280)
    public static void il2ApproachesThenExitsWithoutFiring(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        Vec3 base = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 210, 0)));
        Entity plane = LiveSquadronGameTests.spawn(level, "il2", base, 0f, .75);
        var initial = new RuntimeTacticalPilot.LiveOrder("ground", TacticalAirAI.Mission.STRAFE,
                base.add(140, 0, 300), base.add(-60, 20, -150),
                null, null, null);
        RuntimeTacticalPilot.startLive("mission-strike-il2", level, plane,
                (ArmorStand) plane.getFirstPassenger(), initial, 140);
        // The owner changes the target coordinate in real time, after a
        // verified ingress phase, to force a near-range safe egress decision.
        helper.runAfterDelay(30, () -> RuntimeTacticalPilot.setLiveOrders(plane.getUUID(),
                new RuntimeTacticalPilot.LiveOrder("ground", TacticalAirAI.Mission.STRAFE,
                        plane.position().add(0, 0, 35), initial.home(),
                        null, null, null)));
        helper.succeedWhen(() -> {
            var result = RuntimeTacticalPilot.result("mission-strike-il2");
            if (result == null) throw new GameTestAssertException("Il-2 still on mission");
            try {
                if (!result.complete()) throw new IllegalStateException(result.failure());
                if (result.samples() != 140 || result.displacementBlocks() < 10
                        || result.strikeIngressTicks() < 15 || result.strikeEgressTicks() < 40)
                    throw new IllegalStateException("Real Il-2 did not follow ingress/egress phase sequence");
            } finally {
                LiveSquadronGameTests.cleanupTestEntities(plane);
            }
        });
    }

    @GameTest(template = "empty", batch = "ww_live_rtb_mission", timeoutTicks = 295)
    public static void p47BreaksPatrolForRtbHome(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        Vec3 base = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 210, 0)));
        Entity plane = LiveSquadronGameTests.spawn(level, "p47n", base, 0f, .8);
        var mission = new RuntimeTacticalPilot.LiveOrder("returning", TacticalAirAI.Mission.INTERCEPT,
                base.add(0, 0, 450), base.add(125, 5, -45),
                null, null, null);
        RuntimeTacticalPilot.startLive("mission-rtb-p47", level, plane,
                (ArmorStand) plane.getFirstPassenger(), mission, 160);
        helper.runAfterDelay(25, () -> RuntimeTacticalPilot.requestReturn(plane.getUUID()));
        helper.succeedWhen(() -> {
            var result = RuntimeTacticalPilot.result("mission-rtb-p47");
            if (result == null) throw new GameTestAssertException("P-47 RTB still active");
            try {
                if (!result.complete()) throw new IllegalStateException(result.failure());
                if (result.samples() != 160 || result.displacementBlocks() < 10
                        || result.returnTicks() < 100
                        || !Double.isFinite(result.returnStartDistance())
                        || !Double.isFinite(result.closestReturnDistance())
                        || result.closestReturnDistance() >= result.returnStartDistance() - 4)
                    throw new IllegalStateException("Real P-47 RTB did not reduce distance to home: "
                            + result.returnStartDistance() + " -> " + result.closestReturnDistance());
                if (plane.isRemoved() || !plane.getPassengers().isEmpty())
                    throw new IllegalStateException("RTB test retained an AI rider or removed aircraft");
            } finally {
                LiveSquadronGameTests.cleanupTestEntities(plane);
            }
        });
    }
}
