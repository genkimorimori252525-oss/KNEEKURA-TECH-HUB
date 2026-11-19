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

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Long real-entity two-aircraft mission: independent IL2 strafe and B17 level
 * bombing ingress/egress, followed by condition-triggered RTB commands.
 * The predeclared waypoint is never moved near the plane during flight;
 * successful geometric approach must arise from observed actual positions.
 * Weapons stay permanently disabled; an approach window is not a hit.
 */
@GameTestHolder(PhysicsTraceProbeMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class OperationalStrikeRtbGameTests {
    private static final int FLIGHT_TICKS = 840;
    private OperationalStrikeRtbGameTests() {}

    @GameTest(template = "empty", batch = "ww_operational_long_strike_rtb", timeoutTicks = 1160)
    public static void il2AndB17MustReallyApproachEgressAndReturn(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        Vec3 base = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 205, 0)));
        Vec3 il2Start = base.add(-96, 0, 0);
        Vec3 b17Start = base.add(96, 12, 0);
        var warmupIl2 = new GameTestFlightChunkLease(level);
        var warmupB17 = new GameTestFlightChunkLease(level);
        warmupIl2.update(il2Start, new Vec3(0, 0, .72));
        warmupB17.update(b17Start, new Vec3(0, 0, .72));
        level.getChunkAt(BlockPos.containing(il2Start));
        level.getChunkAt(BlockPos.containing(b17Start));
        helper.runAfterDelay(10, () -> {
            Entity il2 = null, b17 = null;
            try {
                il2 = LiveSquadronGameTests.spawn(level, "il2", il2Start, 0, .72);
                b17 = LiveSquadronGameTests.spawn(level, "b17", b17Start, 0, .72);
                il2.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);
                b17.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);
                RuntimeTacticalPilot.startLive("operational-strike-il2", level, il2,
                        (ArmorStand) il2.getFirstPassenger(),
                        new RuntimeTacticalPilot.LiveOrder("strike", TacticalAirAI.Mission.STRAFE,
                                il2Start.add(0, 0, 185), il2Start.add(0, 0, -130),
                                null, null, null), FLIGHT_TICKS);
                RuntimeTacticalPilot.startLive("operational-strike-b17", level, b17,
                        (ArmorStand) b17.getFirstPassenger(),
                        new RuntimeTacticalPilot.LiveOrder("strike", TacticalAirAI.Mission.LEVEL_BOMB,
                                b17Start.add(0, 0, 185), b17Start.add(0, 0, -130),
                                null, null, null), FLIGHT_TICKS);
                Entity capturedIl2 = il2, capturedB17 = b17;
                int[] sharedEgressTicks = {0};
                boolean[] requestedReturn = {false};
                boolean[] missionPassed = {false};
                String[] operationalFailure = {null};
                helper.runAfterDelay(FLIGHT_TICKS + 35, () -> {
                    if (missionPassed[0]) return;
                    RuntimeTacticalPilot.stop(capturedIl2.getUUID());
                    RuntimeTacticalPilot.stop(capturedB17.getUUID());
                    LiveSquadronGameTests.cleanupTestEntities(capturedIl2, capturedB17);
                    helper.fail("REAL_LONG_STRIKE_RTB_FAILED: "
                            + (operationalFailure[0] == null
                                ? "TEST_DID_NOT_COMPLETE" : operationalFailure[0]));
                });
                helper.succeedWhen(() -> {
                    if (operationalFailure[0] != null)
                        throw new GameTestAssertException("REAL_LONG_STRIKE_RTB_FAILED: " + operationalFailure[0]);
                    var resultsA = RuntimeTacticalPilot.result("operational-strike-il2");
                    var resultsB = RuntimeTacticalPilot.result("operational-strike-b17");
                    if (resultsA == null && resultsB == null && !requestedReturn[0]) {
                        Map<UUID, RuntimeTacticalPilot.LiveStatus> byId = new HashMap<>();
                        for (var status : RuntimeTacticalPilot.liveStatus())
                            byId.put(status.aircraft(), status);
                        var a = byId.get(capturedIl2.getUUID());
                        var b = byId.get(capturedB17.getUUID());
                        if (a != null && b != null
                                && a.phase() == LiveMissionPlanner.Phase.STRIKE_EGRESS
                                && b.phase() == LiveMissionPlanner.Phase.STRIKE_EGRESS) {
                            if (++sharedEgressTicks[0] >= 12) {
                                // The server command verifies actual live
                                // enrollment and throws on an invalid order.
                                RuntimeTacticalPilot.requestReturn(capturedIl2.getUUID());
                                RuntimeTacticalPilot.requestReturn(capturedB17.getUUID());
                                requestedReturn[0] = true;
                            }
                        } else {
                            sharedEgressTicks[0] = 0;
                        }
                    }
                    if (resultsA == null || resultsB == null)
                        throw new GameTestAssertException("Real two-plane attack/egress/RTB mission still flying");
                    try {
                        if (!resultsA.complete() || !resultsB.complete())
                            throw new IllegalStateException("REAL_LONG_STRIKE_INCOMPLETE "
                                    + resultsA.failure() + " / " + resultsB.failure());
                        if (resultsA.samples() != FLIGHT_TICKS || resultsB.samples() != FLIGHT_TICKS)
                            throw new IllegalStateException("REAL_LONG_STRIKE_MISSING_840_ENTITY_TICKS");
                        if (!requestedReturn[0])
                            throw new IllegalStateException("REAL_LONG_STRIKE_EGRESS_NOT_BOTH_OBSERVED");
                        for (var outcome : new RuntimeTacticalPilot.Result[]{resultsA, resultsB}) {
                            if (outcome.displacementBlocks() < 60
                                    || outcome.strikeIngressTicks() < 50
                                    || outcome.strikeEgressTicks() < 12
                                    || outcome.returnTicks() < 50
                                    || !Double.isFinite(outcome.closestReturnDistance())
                                    || !Double.isFinite(outcome.returnStartDistance())
                                    || outcome.closestReturnDistance() >= outcome.returnStartDistance() - 4)
                                throw new IllegalStateException("REAL_LONG_STRIKE_RTB_GEOMETRY_FAILED: "
                                        + "displacement=" + outcome.displacementBlocks()
                                        + " ingress=" + outcome.strikeIngressTicks()
                                        + " egress=" + outcome.strikeEgressTicks()
                                        + " return=" + outcome.returnTicks()
                                        + " home=" + outcome.returnStartDistance()
                                        + "->" + outcome.closestReturnDistance());
                        }
                        missionPassed[0] = true;
                    } catch (RuntimeException failingMission) {
                        operationalFailure[0] = failingMission.getMessage();
                        throw new GameTestAssertException("REAL_LONG_STRIKE_RTB_FAILED: " + operationalFailure[0]);
                    } finally {
                        LiveSquadronGameTests.cleanupTestEntities(capturedIl2, capturedB17);
                    }
                });
            } catch (RuntimeException failure) {
                LiveSquadronGameTests.cleanupTestEntities(il2, b17);
                throw failure;
            } finally {
                warmupIl2.close();
                warmupB17.close();
            }
        });
    }
}
