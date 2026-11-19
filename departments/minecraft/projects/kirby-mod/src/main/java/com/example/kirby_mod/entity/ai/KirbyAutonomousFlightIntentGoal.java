package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/** Periodically queues a random flight destination for the existing FlightGoal. */
public final class KirbyAutonomousFlightIntentGoal extends Goal
        implements KirbyDebugInfoProvider {

    private static final int MIN_DECISION_DELAY = 240;
    private static final int DECISION_DELAY_RANGE = 361;
    private static final int MIN_HORIZONTAL_DISTANCE = 6;
    private static final int HORIZONTAL_DISTANCE_RANGE = 9;
    private static final int MIN_FLIGHT_HEIGHT = 3;
    private static final int FLIGHT_HEIGHT_RANGE = 5;
    private static final int MAX_CANDIDATE_ATTEMPTS = 8;
    private static final double MAX_TARGET_DISTANCE_SQ = 256.0D;

    private final KirbyEntity kirby;
    @Nullable private BlockPos preparedTarget;
    @Nullable private BlockPos lastQueuedTarget;
    private int nextDecisionTick;
    private int candidateAttempts;
    private int rejectedCandidates;
    private boolean active;
    private String lastReason = "initial_delay";

    public KirbyAutonomousFlightIntentGoal(KirbyEntity kirby) {
        this.kirby = kirby;
    }

    @Override
    public boolean canUse() {
        if (!canQueueFlight()) return false;
        if (nextDecisionTick == 0) {
            scheduleNextDecision();
            return false;
        }
        if (kirby.tickCount < nextDecisionTick) return false;

        scheduleNextDecision();
        preparedTarget = findFlightTarget();
        lastReason = preparedTarget == null
                ? "no_safe_random_flight_target"
                : "random_flight_target_ready";
        return preparedTarget != null;
    }

    @Override
    public void start() {
        active = true;
        BlockPos target = preparedTarget;
        preparedTarget = null;
        if (target == null || !canQueueFlight()) {
            lastReason = "flight_intent_cancelled";
            return;
        }
        kirby.setPendingHighTarget(target);
        lastQueuedTarget = target;
        lastReason = "autonomous_flight_queued";
    }

    @Override
    public boolean canContinueToUse() {
        return false;
    }

    @Override
    public void stop() {
        active = false;
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        lines.add("FlightIntentGoal: active=" + active
                + " nextIn=" + Math.max(0, nextDecisionTick - kirby.tickCount)
                + " prepared=" + debugPos(preparedTarget)
                + " lastQueued=" + debugPos(lastQueuedTarget)
                + " attempts=" + candidateAttempts
                + " rejected=" + rejectedCandidates
                + " reason=" + lastReason);
        if (candidateAttempts > 0 && rejectedCandidates >= candidateAttempts) {
            lines.add("WARN FlightIntentGoal no safe target attempts=" + candidateAttempts);
        }
        lines.add("FlightIntentGoal thought=" + thought());
    }

    private boolean canQueueFlight() {
        return kirby.getCombatState() == CombatState.NONE
                && kirby.getFlightState() == KirbyEntity.FlightState.GROUND
                && kirby.onGround()
                && !kirby.isInWater()
                && !kirby.isPassenger()
                && kirby.getStoredHeldMobCountForDebug() == 0
                && kirby.getPendingHighTarget() == null;
    }

    @Nullable
    private BlockPos findFlightTarget() {
        candidateAttempts = 0;
        rejectedCandidates = 0;
        if (!hasTakeoffClearance()) {
            lastReason = "takeoff_clearance_blocked";
            return null;
        }
        for (int attempt = 0; attempt < MAX_CANDIDATE_ATTEMPTS; attempt++) {
            candidateAttempts++;
            double angle = kirby.getRandom().nextDouble() * Math.PI * 2.0D;
            int distance = MIN_HORIZONTAL_DISTANCE
                    + kirby.getRandom().nextInt(HORIZONTAL_DISTANCE_RANGE);
            int x = (int) Math.floor(kirby.getX() + Math.cos(angle) * distance);
            int z = (int) Math.floor(kirby.getZ() + Math.sin(angle) * distance);
            BlockPos probe = new BlockPos(x, kirby.blockPosition().getY(), z);
            if (!kirby.level().hasChunkAt(probe)) {
                rejectedCandidates++;
                continue;
            }
            int landingY = kirby.level().getHeight(
                    Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
            BlockPos landing = new BlockPos(x, landingY, z);
            int flightHeight = MIN_FLIGHT_HEIGHT
                    + kirby.getRandom().nextInt(FLIGHT_HEIGHT_RANGE);
            int targetY = Math.max(landingY + flightHeight,
                    kirby.blockPosition().getY() + MIN_FLIGHT_HEIGHT);
            BlockPos target = new BlockPos(x, targetY, z);
            if (!isSafeLandingArea(landing)
                    || !kirby.level().getWorldBorder().isWithinBounds(target)
                    || target.distSqr(kirby.blockPosition()) > MAX_TARGET_DISTANCE_SQ) {
                rejectedCandidates++;
                continue;
            }
            return target;
        }
        return null;
    }

    private boolean hasTakeoffClearance() {
        AABB takeoffColumn = kirby.getBoundingBox()
                .expandTowards(0.0D, MIN_FLIGHT_HEIGHT, 0.0D)
                .inflate(-0.05D);
        return kirby.level().noCollision(kirby, takeoffColumn);
    }

    private boolean isSafeLandingArea(BlockPos landing) {
        BlockPos support = landing.below();
        return kirby.level().hasChunkAt(landing)
                && kirby.level().getWorldBorder().isWithinBounds(landing)
                && kirby.level().getBlockState(support)
                .isFaceSturdy(kirby.level(), support, Direction.UP)
                && kirby.level().getBlockState(landing).getCollisionShape(
                kirby.level(), landing).isEmpty()
                && kirby.level().getBlockState(landing.above()).getCollisionShape(
                kirby.level(), landing.above()).isEmpty()
                && kirby.level().getFluidState(landing).isEmpty()
                && kirby.level().getFluidState(landing.above()).isEmpty();
    }

    private void scheduleNextDecision() {
        nextDecisionTick = kirby.tickCount + MIN_DECISION_DELAY
                + kirby.getRandom().nextInt(DECISION_DELAY_RANGE);
    }

    private String thought() {
        if (active && "autonomous_flight_queued".equals(lastReason)) {
            return "queued_a_free_flight_for_existing_flight_ai";
        }
        if ("takeoff_clearance_blocked".equals(lastReason)) {
            return "waiting_for_open_sky_before_free_flight";
        }
        return "waiting_until_kirby_feels_like_flying";
    }

    private static String debugPos(@Nullable BlockPos pos) {
        return pos == null ? "none" : pos.toShortString();
    }
}
