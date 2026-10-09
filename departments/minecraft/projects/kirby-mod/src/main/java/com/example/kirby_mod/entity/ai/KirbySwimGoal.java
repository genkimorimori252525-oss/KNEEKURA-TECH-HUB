package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.ai.target.KirbyInterestRules;
import com.example.kirby_mod.entity.ai.target.KirbyTargetKind;
import com.example.kirby_mod.entity.ai.target.KirbyTargetObservation;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.navigation.AmphibiousPathNavigation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

/** Water-only 3D path following without changing Kirby's normal ground navigation. */
public final class KirbySwimGoal extends Goal implements KirbyDebugInfoProvider {

    private static final double MAX_FOLLOW_DISTANCE = 16.0D;
    private static final double HOLD_DISTANCE = 2.5D;
    private static final double SWIM_SPEED = 1.0D;
    private static final double TARGET_REPATH_DISTANCE = 1.5D;
    private static final double WAYPOINT_LOOKAHEAD_DISTANCE_SQ = 1.0D;
    private static final int REPATH_INTERVAL_TICKS = 10;
    private static final int MAX_PATH_FAILURES = 3;
    private static final int PATH_FAILURE_COOLDOWN_TICKS = 40;
    private static final int SHORE_EXIT_GRACE_TICKS = 10;
    private static final int SURFACE_RECOVERY_TIMEOUT_TICKS = 80;
    private static final int SURFACE_HORIZONTAL_RADIUS = 4;
    private static final int SURFACE_VERTICAL_RANGE = 16;
    private static final int MAX_SURFACE_PATH_ATTEMPTS = 8;
    private static final int FREE_ROAM_MIN_DELAY_TICKS = 80;
    private static final int FREE_ROAM_DELAY_RANGE_TICKS = 81;
    private static final int FREE_ROAM_TIMEOUT_TICKS = 160;
    private static final int FREE_ROAM_HORIZONTAL_RADIUS = 8;
    private static final int FREE_ROAM_VERTICAL_RADIUS = 4;
    private static final int FREE_ROAM_CANDIDATE_ATTEMPTS = 16;
    private static final double FREE_ROAM_MIN_DISTANCE_SQ = 9.0D;

    private enum Purpose {
        NONE,
        TARGET_WATER,
        SHORE_EXIT,
        SURFACE_RECOVERY,
        FREE_ROAM
    }

    private record FreeRoamPlan(BlockPos target, Path path) {}

    private final KirbyEntity kirby;
    private final AmphibiousPathNavigation waterNavigation;

    @Nullable private Player target;
    @Nullable private FreeRoamPlan preparedFreeRoam;
    private Purpose purpose = Purpose.NONE;
    private boolean active;
    private boolean turning;
    private boolean lastPathSuccess = true;
    private boolean lastPathReachable = true;
    private int repathTicks;
    private int pathFailures;
    private int replanCount;
    private int shoreExitTicks;
    private int surfaceRecoveryTicks;
    private int surfaceCandidateCount;
    private int surfacePathAttempts;
    private int nextFreeRoamTick;
    private int freeRoamTicks;
    private int freeRoamCandidates;
    private double plannedTargetX = Double.NaN;
    private double plannedTargetY = Double.NaN;
    private double plannedTargetZ = Double.NaN;
    private double lastDistance = Double.NaN;
    private Vec3 lastWaypoint = Vec3.ZERO;
    private String lastTargetKey = "none";
    private String lastReason = "idle";

    public KirbySwimGoal(KirbyEntity kirby) {
        this.kirby = kirby;
        this.waterNavigation = new AmphibiousPathNavigation(kirby, kirby.level());
        this.waterNavigation.setCanFloat(true);
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        if (!canFreeRoamNow()) return false;
        KirbyTargetObservation observation = interestObservation();
        Player candidate = resolvePlayer(observation);
        if (!isValidTarget(candidate)) candidate = null;
        if (kirby.isInWater()) {
            boolean selected = evaluateSwim(candidate != null && observation != null,
                    candidate == null ? MAX_FOLLOW_DISTANCE : kirby.distanceTo(candidate),
                    observation == null ? "none" : observation.targetKey(),
                    "water_interest_in_range");
            if (selected) {
                this.target = candidate;
                this.preparedFreeRoam = null;
                return true;
            }
        } else if (candidate != null) {
            return false;
        }
        if (candidate != null || !freeRoamDecisionReady()) return false;

        scheduleNextFreeRoam();
        preparedFreeRoam = findFreeRoamPlan();
        if (preparedFreeRoam == null) {
            lastReason = "no_safe_free_roam_path";
            return false;
        }
        target = null;
        return evaluateSwim(true,
                Math.sqrt(preparedFreeRoam.target().distSqr(kirby.blockPosition())),
                "water:" + preparedFreeRoam.target().toShortString(),
                "free_roam_path_ready");
    }

    @Override
    public boolean canContinueToUse() {
        if (kirby.getCombatState() != CombatState.NONE
                || kirby.getFlightState() != KirbyEntity.FlightState.GROUND
                || kirby.isPassenger()) {
            return false;
        }
        if (purpose == Purpose.FREE_ROAM) {
            return freeRoamTicks < FREE_ROAM_TIMEOUT_TICKS
                    && kirby.getAiBrain().cooldownRemaining(
                    KirbyAiAction.SWIM, kirby.tickCount) == 0;
        }
        if (!kirby.isInWater()
                && (purpose != Purpose.SHORE_EXIT
                || kirby.onGround()
                || shoreExitTicks >= SHORE_EXIT_GRACE_TICKS)) {
            return false;
        }
        KirbyTargetObservation observation = interestObservation();
        Player candidate = resolvePlayer(observation);
        if (!isValidTarget(candidate)) return false;
        this.target = candidate;
        return kirby.getAiBrain().cooldownRemaining(KirbyAiAction.SWIM, kirby.tickCount) == 0;
    }

    @Override
    public void start() {
        kirby.getNavigation().stop();
        active = true;
        turning = false;
        FreeRoamPlan freeRoam = preparedFreeRoam;
        if (target != null) {
            purpose = target.isInWater() ? Purpose.TARGET_WATER : Purpose.SHORE_EXIT;
        } else if (freeRoam != null) {
            purpose = Purpose.FREE_ROAM;
        } else {
            purpose = Purpose.NONE;
        }
        repathTicks = 0;
        pathFailures = 0;
        replanCount = 0;
        shoreExitTicks = 0;
        surfaceRecoveryTicks = 0;
        surfaceCandidateCount = 0;
        surfacePathAttempts = 0;
        freeRoamTicks = 0;
        plannedTargetX = Double.NaN;
        plannedTargetY = Double.NaN;
        plannedTargetZ = Double.NaN;
        lastPathSuccess = true;
        lastPathReachable = true;
        if (freeRoam != null) {
            lastTargetKey = "water:" + freeRoam.target().toShortString();
            lastDistance = Math.sqrt(freeRoam.target().distSqr(kirby.blockPosition()));
            lastPathReachable = freeRoam.path().canReach();
            lastPathSuccess = waterNavigation.moveTo(freeRoam.path(), SWIM_SPEED);
            lastReason = lastPathSuccess ? "free_roam_started" : "free_roam_start_failed";
            if (!lastPathSuccess) freeRoamTicks = FREE_ROAM_TIMEOUT_TICKS;
            preparedFreeRoam = null;
        } else {
            lastReason = "target_swim_started";
        }
    }

    @Override
    public void tick() {
        if (purpose == Purpose.FREE_ROAM) {
            tickFreeRoam();
            return;
        }
        Player currentTarget = this.target;
        if (!isValidTarget(currentTarget)) {
            lastReason = "target_invalid";
            waterNavigation.stop();
            return;
        }

        lastTargetKey = currentTarget.getUUID().toString();
        lastDistance = kirby.distanceTo(currentTarget);
        if (kirby.isInWater()) {
            shoreExitTicks = 0;
        } else {
            shoreExitTicks++;
        }

        if (lastDistance <= HOLD_DISTANCE && purpose != Purpose.SURFACE_RECOVERY) {
            waterNavigation.stop();
            turning = false;
            pathFailures = 0;
            lastPathSuccess = true;
            lastPathReachable = true;
            lastWaypoint = currentTarget.position();
            lastReason = "holding_swim_distance";
            clearMoveInput();
            kirby.getLookControl().setLookAt(currentTarget, 30.0F, 30.0F);
            return;
        }

        if (purpose == Purpose.SURFACE_RECOVERY) {
            surfaceRecoveryTicks++;
            if (waterNavigation.isDone() || waterNavigation.isStuck()
                    || surfaceRecoveryTicks >= SURFACE_RECOVERY_TIMEOUT_TICKS) {
                waterNavigation.stop();
                purpose = currentTarget.isInWater()
                        ? Purpose.TARGET_WATER
                        : Purpose.SHORE_EXIT;
                repathTicks = 0;
                pathFailures = 0;
                lastReason = "surface_recovery_completed";
            }
        }

        if (purpose != Purpose.SURFACE_RECOVERY) {
            purpose = currentTarget.isInWater()
                    ? Purpose.TARGET_WATER
                    : Purpose.SHORE_EXIT;
            boolean moved = KirbySwimNavigationPolicy.targetMoved(
                    plannedTargetX, plannedTargetY, plannedTargetZ,
                    currentTarget.getX(), currentTarget.getY(), currentTarget.getZ(),
                    TARGET_REPATH_DISTANCE);
            boolean pathEnded = waterNavigation.getPath() != null && waterNavigation.isDone();
            if (--repathTicks <= 0 || moved || pathEnded || waterNavigation.isStuck()) {
                planTargetPath(currentTarget, moved ? "target_moved" :
                        pathEnded ? "path_ended" :
                                waterNavigation.isStuck() ? "path_stuck" : "repath_interval");
            }
        }

        followCurrentPath();
    }

    @Override
    public void stop() {
        Purpose stoppedPurpose = purpose;
        waterNavigation.stop();
        clearMoveInput();
        active = false;
        turning = false;
        target = null;
        preparedFreeRoam = null;
        purpose = Purpose.NONE;
        shoreExitTicks = 0;
        surfaceRecoveryTicks = 0;
        freeRoamTicks = 0;
        if ("path_failed_cooldown".equals(lastReason)) return;
        if (stoppedPurpose == Purpose.FREE_ROAM
                && ("free_roam_arrived".equals(lastReason)
                || "free_roam_yielding_to_interest".equals(lastReason)
                || "free_roam_stuck".equals(lastReason)
                || "free_roam_start_failed".equals(lastReason))) {
            return;
        }
        lastReason = stoppedPurpose == Purpose.FREE_ROAM
                ? "free_roam_stopped"
                : "swim_stopped";
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        Path path = waterNavigation.getPath();
        int pathIndex = path == null ? -1 : path.getNextNodeIndex();
        int pathNodes = path == null ? 0 : path.getNodeCount();
        lines.add("SwimGoal: active=" + active
                + " purpose=" + purpose
                + " target=" + lastTargetKey
                + " distance=" + (Double.isFinite(lastDistance) ? fmt(lastDistance) : "none")
                + " turning=" + turning
                + " repathIn=" + Math.max(0, repathTicks)
                + " replans=" + replanCount
                + " pathFailures=" + pathFailures
                + " swimCooldown=" + kirby.getAiBrain().cooldownRemaining(
                        KirbyAiAction.SWIM, kirby.tickCount)
                + " reason=" + lastReason);
        lines.add("SwimPath: success=" + lastPathSuccess
                + " reachable=" + lastPathReachable
                + " done=" + (path == null || path.isDone())
                + " stuck=" + waterNavigation.isStuck()
                + " index=" + pathIndex + "/" + pathNodes
                + " next=" + debugVec(lastWaypoint)
                + " surfaceCandidates=" + surfaceCandidateCount
                + " surfaceAttempts=" + surfacePathAttempts
                + " freeRoamTicks=" + freeRoamTicks
                + " freeRoamNextIn=" + Math.max(0, nextFreeRoamTick - kirby.tickCount)
                + " freeRoamCandidates=" + freeRoamCandidates);
        if (pathFailures > 0 || waterNavigation.isStuck()) {
            lines.add("WARN SwimGoal pathFailures=" + pathFailures
                    + " stuck=" + waterNavigation.isStuck()
                    + " target=" + lastTargetKey
                    + " purpose=" + purpose);
        }
        lines.add("SwimGoal thought=" + thought());
    }

    private void tickFreeRoam() {
        freeRoamTicks++;
        KirbyTargetObservation observation = interestObservation();
        Player interest = resolvePlayer(observation);
        if (isValidTarget(interest)) {
            waterNavigation.stop();
            clearMoveInput();
            freeRoamTicks = FREE_ROAM_TIMEOUT_TICKS;
            lastReason = "free_roam_yielding_to_interest";
            return;
        }
        if (waterNavigation.isDone()) {
            clearMoveInput();
            freeRoamTicks = FREE_ROAM_TIMEOUT_TICKS;
            lastReason = "free_roam_arrived";
            return;
        }
        if (waterNavigation.isStuck()) {
            waterNavigation.stop();
            clearMoveInput();
            freeRoamTicks = FREE_ROAM_TIMEOUT_TICKS;
            lastPathSuccess = false;
            lastReason = "free_roam_stuck";
            return;
        }
        followCurrentPath();
        if (!turning) lastReason = "swimming_freely";
    }

    private boolean freeRoamDecisionReady() {
        if (nextFreeRoamTick == 0) {
            scheduleNextFreeRoam();
            lastReason = "free_roam_initial_delay";
            return false;
        }
        return kirby.tickCount >= nextFreeRoamTick;
    }

    private void scheduleNextFreeRoam() {
        nextFreeRoamTick = kirby.tickCount + FREE_ROAM_MIN_DELAY_TICKS
                + kirby.getRandom().nextInt(FREE_ROAM_DELAY_RANGE_TICKS);
    }

    @Nullable
    private FreeRoamPlan findFreeRoamPlan() {
        freeRoamCandidates = 0;
        BlockPos origin = kirby.blockPosition();
        for (int attempt = 0; attempt < FREE_ROAM_CANDIDATE_ATTEMPTS; attempt++) {
            BlockPos candidate = origin.offset(
                    kirby.getRandom().nextInt(FREE_ROAM_HORIZONTAL_RADIUS * 2 + 1)
                            - FREE_ROAM_HORIZONTAL_RADIUS,
                    kirby.getRandom().nextInt(FREE_ROAM_VERTICAL_RADIUS * 2 + 1)
                            - FREE_ROAM_VERTICAL_RADIUS,
                    kirby.getRandom().nextInt(FREE_ROAM_HORIZONTAL_RADIUS * 2 + 1)
                            - FREE_ROAM_HORIZONTAL_RADIUS);
            if (candidate.distSqr(origin) < FREE_ROAM_MIN_DISTANCE_SQ
                    || !isSafeWaterCandidate(candidate)) {
                continue;
            }
            freeRoamCandidates++;
            Path path = waterNavigation.createPath(candidate, 0);
            if (path == null || !path.canReach() || path.getNodeCount() == 0) continue;
            return new FreeRoamPlan(candidate.immutable(), path);
        }
        return null;
    }

    private boolean isSafeWaterCandidate(BlockPos candidate) {
        if (!kirby.level().hasChunkAt(candidate)
                || !kirby.level().getWorldBorder().isWithinBounds(candidate)
                || !kirby.level().getFluidState(candidate).is(FluidTags.WATER)) {
            return false;
        }
        Vec3 candidatePosition = new Vec3(
                candidate.getX() + 0.5D,
                candidate.getY() + 0.1D,
                candidate.getZ() + 0.5D);
        AABB candidateBounds = kirby.getBoundingBox().move(
                candidatePosition.x - kirby.getX(),
                candidatePosition.y - kirby.getY(),
                candidatePosition.z - kirby.getZ());
        return kirby.level().noCollision(kirby, candidateBounds);
    }

    private void planTargetPath(Player currentTarget, String replanReason) {
        repathTicks = REPATH_INTERVAL_TICKS;
        replanCount++;
        Path path = waterNavigation.createPath(currentTarget, 0);
        lastPathReachable = path != null && path.canReach();
        lastPathSuccess = path != null && path.getNodeCount() > 0
                && lastPathReachable && waterNavigation.moveTo(path, SWIM_SPEED);
        if (lastPathSuccess) {
            pathFailures = 0;
            plannedTargetX = currentTarget.getX();
            plannedTargetY = currentTarget.getY();
            plannedTargetZ = currentTarget.getZ();
            lastReason = replanReason;
            return;
        }

        pathFailures++;
        lastReason = "target_path_failed";
        if (pathFailures < MAX_PATH_FAILURES) return;
        if (startSurfaceRecovery()) {
            lastReason = "surface_recovery_started";
            return;
        }
        lastReason = "path_failed_cooldown";
        kirby.getAiBrain().startCooldown(KirbyAiAction.SWIM,
                kirby.tickCount, PATH_FAILURE_COOLDOWN_TICKS);
        waterNavigation.stop();
        clearMoveInput();
    }

    private boolean startSurfaceRecovery() {
        List<BlockPos> candidates = findSurfaceCandidates();
        surfaceCandidateCount = candidates.size();
        surfacePathAttempts = 0;
        for (BlockPos candidate : candidates) {
            if (surfacePathAttempts >= MAX_SURFACE_PATH_ATTEMPTS) break;
            surfacePathAttempts++;
            Path path = waterNavigation.createPath(candidate, 0);
            if (path == null || !path.canReach() || path.getNodeCount() == 0) continue;
            if (!waterNavigation.moveTo(path, SWIM_SPEED)) continue;
            purpose = Purpose.SURFACE_RECOVERY;
            surfaceRecoveryTicks = 0;
            lastPathSuccess = true;
            lastPathReachable = true;
            return true;
        }
        lastPathSuccess = false;
        return false;
    }

    private List<BlockPos> findSurfaceCandidates() {
        BlockPos origin = kirby.blockPosition();
        List<BlockPos> candidates = new ArrayList<>();
        for (int dy = 0; dy <= SURFACE_VERTICAL_RANGE; dy++) {
            for (int dx = -SURFACE_HORIZONTAL_RADIUS; dx <= SURFACE_HORIZONTAL_RADIUS; dx++) {
                for (int dz = -SURFACE_HORIZONTAL_RADIUS; dz <= SURFACE_HORIZONTAL_RADIUS; dz++) {
                    BlockPos water = origin.offset(dx, dy, dz);
                    if (!isSafeSurfaceCandidate(water)) continue;
                    candidates.add(water.immutable());
                }
            }
        }
        candidates.sort(Comparator
                .comparingDouble((BlockPos pos) -> pos.distSqr(origin))
                .thenComparingInt(BlockPos::getY)
                .thenComparingInt(BlockPos::getX)
                .thenComparingInt(BlockPos::getZ));
        return candidates;
    }

    private boolean isSafeSurfaceCandidate(BlockPos water) {
        BlockPos above = water.above();
        if (!kirby.level().hasChunkAt(water)
                || !kirby.level().hasChunkAt(above)
                || !kirby.level().getWorldBorder().isWithinBounds(water)
                || !kirby.level().getFluidState(water).is(FluidTags.WATER)
                || !kirby.level().getFluidState(above).isEmpty()
                || !kirby.level().getBlockState(above).isAir()) {
            return false;
        }
        Vec3 candidatePosition = new Vec3(
                water.getX() + 0.5D, water.getY() + 0.1D, water.getZ() + 0.5D);
        AABB candidateBounds = kirby.getBoundingBox().move(
                candidatePosition.x - kirby.getX(),
                candidatePosition.y - kirby.getY(),
                candidatePosition.z - kirby.getZ());
        return kirby.level().noCollision(kirby, candidateBounds);
    }

    private void followCurrentPath() {
        Path path = waterNavigation.getPath();
        if (path == null || path.isDone()) {
            turning = false;
            clearMoveInput();
            return;
        }
        Vec3 waypoint = lookaheadWaypoint(path);
        lastWaypoint = waypoint;
        Vec3 toWaypoint = waypoint.subtract(kirby.position());
        kirby.getLookControl().setLookAt(
                waypoint.x, waypoint.y, waypoint.z, 45.0F, 45.0F);
        Vec3 look = kirby.getLookAngle();
        turning = !KirbySwimNavigationPolicy.canPropel(
                look.x, look.y, look.z,
                toWaypoint.x, toWaypoint.y, toWaypoint.z);
        waterNavigation.setSpeedModifier(turning ? 0.0D : SWIM_SPEED);
        waterNavigation.tick();
        if (turning) lastReason = "turning_to_waypoint";
    }

    private Vec3 lookaheadWaypoint(Path path) {
        int index = path.getNextNodeIndex();
        Vec3 waypoint = path.getEntityPosAtNode(kirby, index);
        if (index + 1 < path.getNodeCount()
                && kirby.distanceToSqr(waypoint) <= WAYPOINT_LOOKAHEAD_DISTANCE_SQ) {
            waypoint = path.getEntityPosAtNode(kirby, index + 1);
        }
        return waypoint;
    }

    private void clearMoveInput() {
        kirby.getMoveControl().setWantedPosition(
                kirby.getX(), kirby.getY(), kirby.getZ(), 0.0D);
    }

    private boolean canFreeRoamNow() {
        return kirby.getCombatState() == CombatState.NONE
                && kirby.getFlightState() == KirbyEntity.FlightState.GROUND
                && !kirby.isPassenger()
                && (kirby.isInWater() || kirby.onGround());
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

    private boolean evaluateSwim(
            boolean eligible,
            double distance,
            String targetKey,
            String eligibleReason) {
        eligible = eligible
                && kirby.getAiBrain().cooldownRemaining(KirbyAiAction.SWIM, kirby.tickCount) == 0;
        KirbyAiDecision decision = kirby.getAiBrain().evaluate(KirbyDecisionLane.LOCOMOTION,
                kirby.tickCount, List.of(
                        new KirbyAiCandidate(KirbyAiAction.SWIM, KirbyDecisionLane.LOCOMOTION,
                                10.0D + Math.min(4.0D, distance / 4.0D), eligible, 0,
                                targetKey, eligible ? eligibleReason : "no_water_destination"),
                        new KirbyAiCandidate(KirbyAiAction.IDLE, KirbyDecisionLane.LOCOMOTION,
                                0.0D, true, 1, "none", "swim_fallback")));
        return decision.action() == KirbyAiAction.SWIM;
    }

    private String thought() {
        if ("path_failed_cooldown".equals(lastReason)) return "waiting_before_swim_path_retry";
        if (!active) return "waiting_for_target_or_free_roam_impulse";
        if (turning) return "turning_before_propulsion";
        switch (purpose) {
            case TARGET_WATER:
                return "following_water_target_in_3d";
            case SHORE_EXIT:
                return "swimming_to_shore_for_land_target";
            case SURFACE_RECOVERY:
                return "recovering_to_safe_water_surface";
            case FREE_ROAM:
                return "swimming_freely_without_a_target";
            case NONE:
            default:
                return "idle_in_water";
        }
    }

    private static String fmt(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }

    private static String debugVec(Vec3 value) {
        return String.format(Locale.ROOT, "(%.2f,%.2f,%.2f)", value.x, value.y, value.z);
    }
}
