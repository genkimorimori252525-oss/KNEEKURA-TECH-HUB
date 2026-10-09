package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.ai.target.KirbyInterestRules;
import com.example.kirby_mod.entity.ai.target.KirbyTargetKind;
import com.example.kirby_mod.entity.ai.target.KirbyTargetObservation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.player.Player;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

/** Target-memory-driven ground following. Flight and combat Goals retain priority. */
public final class KirbyGroundTargetGoal extends Goal implements KirbyDebugInfoProvider {

    private static final double MAX_FOLLOW_DISTANCE = 16.0D;
    private static final double WALK_SPEED = 1.0D;
    private static final double RUN_SPEED = 1.35D;
    private static final int REPATH_INTERVAL_TICKS = 10;
    private static final int MAX_PATH_FAILURES = 3;
    private static final int PATH_FAILURE_COOLDOWN_TICKS = 40;

    private final KirbyEntity kirby;
    @Nullable private Player target;
    private KirbyLocomotionMode moveMode = KirbyLocomotionMode.IDLE;
    private int repathTicks;
    private int pathFailures;
    private boolean lastPathSuccess = true;
    private boolean active;
    private double lastDistance = Double.NaN;
    private double lastSpeed;
    private String lastTargetKey = "none";
    private String lastReason = "idle";

    public KirbyGroundTargetGoal(KirbyEntity kirby) {
        this.kirby = kirby;
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        if (!canMoveOnGround()) return evaluateFollow(null, null);
        KirbyTargetObservation observation = interestObservation();
        Player candidate = resolvePlayer(observation);
        if (!isValidTarget(candidate)) candidate = null;
        boolean selected = evaluateFollow(candidate, observation);
        if (selected) this.target = candidate;
        return selected;
    }

    @Override
    public boolean canContinueToUse() {
        if (!canMoveOnGround()) return false;
        if (kirby.getAiBrain().cooldownRemaining(KirbyAiAction.FOLLOW, kirby.tickCount) > 0) {
            return false;
        }
        KirbyTargetObservation observation = interestObservation();
        Player candidate = resolvePlayer(observation);
        if (!isValidTarget(candidate)) return false;
        this.target = candidate;
        return true;
    }

    @Override
    public void start() {
        active = true;
        moveMode = KirbyLocomotionMode.IDLE;
        repathTicks = 0;
        pathFailures = 0;
        lastPathSuccess = true;
        lastReason = "follow_started";
    }

    @Override
    public void tick() {
        Player currentTarget = this.target;
        if (!isValidTarget(currentTarget)) {
            lastReason = "target_invalid";
            return;
        }
        lastTargetKey = currentTarget.getUUID().toString();
        lastDistance = kirby.distanceTo(currentTarget);
        KirbyLocomotionMode previous = moveMode;
        moveMode = KirbyGroundMovementPolicy.select(true, lastDistance, moveMode);
        kirby.getLookControl().setLookAt(currentTarget, 30.0F, 30.0F);

        if (moveMode == KirbyLocomotionMode.IDLE) {
            kirby.getNavigation().stop();
            lastSpeed = 0.0D;
            pathFailures = 0;
            lastPathSuccess = true;
            lastReason = "holding_follow_distance";
            return;
        }

        lastSpeed = moveMode == KirbyLocomotionMode.RUN ? RUN_SPEED : WALK_SPEED;
        if (--repathTicks <= 0 || previous != moveMode) {
            repathTicks = REPATH_INTERVAL_TICKS;
            lastPathSuccess = kirby.getNavigation().moveTo(currentTarget, lastSpeed);
            if (lastPathSuccess) {
                pathFailures = 0;
            } else {
                pathFailures++;
                if (pathFailures >= MAX_PATH_FAILURES) {
                    lastReason = "path_failed_cooldown";
                    kirby.getAiBrain().startCooldown(KirbyAiAction.FOLLOW,
                            kirby.tickCount, PATH_FAILURE_COOLDOWN_TICKS);
                    kirby.getNavigation().stop();
                    return;
                }
            }
        }
        lastReason = moveMode == KirbyLocomotionMode.RUN
                ? "running_to_interest"
                : "walking_to_interest";
    }

    @Override
    public void stop() {
        kirby.getNavigation().stop();
        active = false;
        target = null;
        moveMode = KirbyLocomotionMode.IDLE;
        lastSpeed = 0.0D;
        if (!"path_failed_cooldown".equals(lastReason)) lastReason = "follow_stopped";
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    public boolean isRunMode() {
        return active && moveMode == KirbyLocomotionMode.RUN;
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        lines.add("GroundTargetGoal: active=" + active
                + " mode=" + moveMode
                + " target=" + lastTargetKey
                + " distance=" + (Double.isFinite(lastDistance) ? fmt(lastDistance) : "none")
                + " speed=" + fmt(lastSpeed)
                + " repathIn=" + Math.max(0, repathTicks)
                + " pathSuccess=" + lastPathSuccess
                + " pathFailures=" + pathFailures
                + " followCooldown=" + kirby.getAiBrain().cooldownRemaining(
                        KirbyAiAction.FOLLOW, kirby.tickCount)
                + " reason=" + lastReason);
        if (pathFailures > 0) {
            lines.add("WARN GroundTargetGoal pathFailures=" + pathFailures
                    + " target=" + lastTargetKey);
        }
        lines.add("GroundTargetGoal thought=" + thought());
    }

    private boolean canMoveOnGround() {
        return kirby.getCombatState() == CombatState.NONE
                && kirby.getFlightState() == KirbyEntity.FlightState.GROUND
                && !kirby.isInWater()
                && kirby.onGround();
    }

    @Nullable
    private KirbyTargetObservation interestObservation() {
        return kirby.getTargetMemory().get(KirbyTargetKind.INTEREST).orElse(null);
    }

    @Nullable
    private Player resolvePlayer(@Nullable KirbyTargetObservation observation) {
        if (observation == null || !(kirby.level() instanceof ServerLevel serverLevel)) return null;
        try {
            Entity entity = serverLevel.getEntity(UUID.fromString(observation.targetKey()));
            return entity instanceof Player player ? player : null;
        } catch (IllegalArgumentException ignored) {
            return null;
        }
    }

    private boolean isValidTarget(@Nullable Player player) {
        return player != null
                && player.isAlive()
                && !player.isSpectator()
                && KirbyInterestRules.isTempting(player)
                && kirby.distanceTo(player) <= MAX_FOLLOW_DISTANCE;
    }

    private boolean evaluateFollow(
            @Nullable Player candidate,
            @Nullable KirbyTargetObservation observation) {
        boolean eligible = candidate != null && observation != null
                && kirby.getAiBrain().cooldownRemaining(KirbyAiAction.FOLLOW, kirby.tickCount) == 0;
        double distance = eligible ? kirby.distanceTo(candidate) : MAX_FOLLOW_DISTANCE;
        String targetKey = observation == null ? "none" : observation.targetKey();
        KirbyAiDecision decision = kirby.getAiBrain().evaluate(KirbyDecisionLane.LOCOMOTION,
                kirby.tickCount, List.of(
                        new KirbyAiCandidate(KirbyAiAction.FOLLOW, KirbyDecisionLane.LOCOMOTION,
                                10.0D + Math.min(4.0D, distance / 4.0D), eligible, 0,
                                targetKey, eligible ? "interest_in_range" : "no_valid_interest"),
                        new KirbyAiCandidate(KirbyAiAction.IDLE, KirbyDecisionLane.LOCOMOTION,
                                0.0D, true, 1, "none", "ground_follow_fallback")));
        return decision.action() == KirbyAiAction.FOLLOW;
    }

    private String thought() {
        if ("path_failed_cooldown".equals(lastReason)) return "waiting_before_path_retry";
        if (!active) return "waiting_for_interest_target";
        switch (moveMode) {
            case RUN:
                return "closing_long_distance_quickly";
            case WALK:
                return "approaching_interest_carefully";
            case IDLE:
            default:
                return "staying_near_interest";
        }
    }

    private static String fmt(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }
}
