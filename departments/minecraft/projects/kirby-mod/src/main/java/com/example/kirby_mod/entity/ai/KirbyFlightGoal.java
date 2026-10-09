package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.KirbyEntity.FlightState;
import com.example.kirby_mod.entity.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.List;
import java.util.Locale;

public class KirbyFlightGoal extends Goal implements KirbyDebugInfoProvider {

    private static final int JAMP_SOUND_DELAY = 4;       // ≒ 0.17s
    private static final int JUMP_TIMEOUT = 60;          // ジャンプ単体で居続ける最大 tick

    private static final int PREP_DURATION = 10;
    private static final int DESCEND_DURATION = 10;
    private static final int DESCEND_HARD_TIMEOUT = 200;
    private static final int PUMP_TIMEOUT = 100;
    private static final int MAX_DESCENT_HOVER_RECOVERIES = 3;
    private static final double PUMP_IMPULSE_Y = 0.4D;
    private static final double HOVER_LIFT_Y = 0.08D;
    private static final double GROUND_PROBE_MAX_DISTANCE = 4.0D;
    private static final double GROUND_PROBE_STEP = 0.25D;
    private static final double HORIZONTAL_NUDGE = 0.06D;
    private static final double STALE_TARGET_DIST_SQ = 256.0D;
    private static final double MAX_HORIZONTAL_SPEED = 0.30D;
    private static final double DESCEND_STEER_SPEED = 0.18D;
    private static final double INERTIA_WEIGHT = 0.25D;
    private static final double COLLISION_LOOKAHEAD_TICKS = 3.0D;
    private static final double ARRIVAL_HORIZONTAL_DISTANCE = 0.65D;
    private static final double THREAT_TRACK_RANGE = 35.0D;
    private static final int LANDING_REFRESH_TICKS = 10;
    private static final double THREAT_REPLAN_DIST_SQ = 16.0D;

    private final KirbyEntity kirby;
    private final KirbyFlightLandingPlanner landingPlanner;
    private BlockPos flightTarget;
    @Nullable private BlockPos destinationLandingTarget;
    @Nullable private BlockPos landingTarget;
    @Nullable private LivingEntity combatTarget;
    @Nullable private BlockPos combatFocus;
    private LandingPurpose landingPurpose = LandingPurpose.NONE;
    private int phaseTicks;
    private int pumpTicks;
    private int totalAscendTicks;
    private int nextLandingRefreshTick;
    private int landingCandidateCount;
    private int destinationLandingCandidateCount;
    private double landingScore;
    private double destinationLandingScore;
    private int originalDeltaY;
    private double plannedJumpHeight;
    private double plannedJumpImpulse;
    private double plannedJumpHorizontalDistance;
    private double availableJumpClearance;
    private boolean plannedJumpRequiresHover;
    private String lastJumpReason = "not_planned";
    private int fallingTicks;
    private int descentHoverRecoveries;
    private double groundDistance = Double.POSITIVE_INFINITY;
    private String lastHoverDecision = "not_evaluated";
    private boolean jumpImpulseApplied;
    private boolean landingLineOfSight;
    private boolean destinationLandingLineOfSight;
    private KirbyFlightSteeringPolicy.Decision lastSteering =
            new KirbyFlightSteeringPolicy.Decision(0.0D, 0.0D, -1, 0.0D, 0, false);
    private Vec3 lastHorizontalVelocity = Vec3.ZERO;
    private String lastLandingReason = "none";
    private String destinationLandingReason = "none";
    private String lastSteeringReason = "idle";

    private enum LandingPurpose {
        NONE,
        DESTINATION,
        COMBAT,
        ORIGINAL_TARGET
    }

    public KirbyFlightGoal(KirbyEntity kirby) {
        this.kirby = kirby;
        this.landingPlanner = new KirbyFlightLandingPlanner(kirby);
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        if (kirby.getCombatState() != CombatState.NONE) return false;
        if (kirby.getFlightState() != FlightState.GROUND) return false;
        if (!kirby.onGround()) return false; // ジャンプの起点は必ず地上
        BlockPos pending = kirby.getPendingHighTarget();
        if (pending == null) return false;
        if (pending.getY() <= kirby.getY() + 1) {
            kirby.setPendingHighTarget(null);
            return false;
        }
        if (pending.distSqr(kirby.blockPosition()) > STALE_TARGET_DIST_SQ) {
            kirby.setPendingHighTarget(null);
            return false;
        }
        return true;
    }

    @Override
    public boolean canContinueToUse() {
        return kirby.getFlightState() != FlightState.GROUND;
    }

    @Override
    public void start() {
        BlockPos pending = kirby.getPendingHighTarget();
        if (pending == null) return;
        flightTarget = pending.above(2); // +2 ブロック余裕
        originalDeltaY = pending.getY() - (int) Math.floor(kirby.getY());
        double targetX = pending.getX() + 0.5D - kirby.getX();
        double targetZ = pending.getZ() + 0.5D - kirby.getZ();
        plannedJumpHorizontalDistance = Math.sqrt(targetX * targetX + targetZ * targetZ);
        availableJumpClearance = measureJumpClearance();
        KirbyJumpPolicy.Decision jump = KirbyJumpPolicy.plan(
                originalDeltaY, plannedJumpHorizontalDistance, availableJumpClearance);
        plannedJumpHeight = jump.targetHeight();
        plannedJumpImpulse = jump.impulse();
        plannedJumpRequiresHover = jump.hoverRequired();
        lastJumpReason = jump.reason();
        phaseTicks = 0;
        pumpTicks = 0;
        totalAscendTicks = 0;
        fallingTicks = 0;
        descentHoverRecoveries = 0;
        groundDistance = Double.POSITIVE_INFINITY;
        lastHoverDecision = "jump_still_rising";
        jumpImpulseApplied = false;
        nextLandingRefreshTick = kirby.tickCount;
        combatTarget = null;
        combatFocus = null;
        lastSteering = new KirbyFlightSteeringPolicy.Decision(
                0.0D, 0.0D, -1, 0.0D, 0, false);
        lastHorizontalVelocity = Vec3.ZERO;
        lastSteeringReason = "idle";
        planDestinationLanding(pending);
        kirby.setFlightState(FlightState.JUMPING);
        kirby.setPendingHighTarget(null);
    }

    @Override
    public void tick() {
        if (flightTarget == null) return;
        updateVerticalContext();
        observeFlightDecision();
        refreshCombatLandingIfNeeded();
        BlockPos horizontalTarget = horizontalTarget();
        double lookY = kirby.getFlightState() == FlightState.DESCEND && landingTarget != null
                ? landingTarget.getY()
                : flightTarget.getY();
        kirby.getLookControl().setLookAt(
                horizontalTarget.getX() + 0.5,
                lookY,
                horizontalTarget.getZ() + 0.5);

        switch (kirby.getFlightState()) {
            case JUMPING:
                tickJumping();
                guardImmediateCollision(horizontalTarget);
                break;

            case ASCEND_PREP:
                maintainHover(horizontalTarget);
                phaseTicks++;
                if (phaseTicks >= PREP_DURATION) {
                    kirby.setFlightState(FlightState.ASCEND_PUMP);
                    phaseTicks = 0;
                    pumpTicks = 0;
                }
                break;

            case ASCEND_PUMP:
                boolean needsAltitude = kirby.getY() < flightTarget.getY();
                KirbyFlightRecoveryPolicy.Decision repump =
                        KirbyFlightRecoveryPolicy.ascentRepump(needsAltitude, fallingTicks);
                boolean firstPump = pumpTicks == 0;
                if (firstPump || repump.shouldHover()) {
                    Vec3 horizontal = chooseHorizontalVelocity(horizontalTarget,
                            requestedHorizontalSpeed(horizontalTarget, MAX_HORIZONTAL_SPEED));
                    kirby.setDeltaMovement(horizontal.x, PUMP_IMPULSE_Y, horizontal.z);
                    kirby.hasImpulse = true;
                    if (!firstPump) {
                        playSound(ModSounds.KIRBY_FLY_LOOP);
                    }
                    lastHoverDecision = firstPump ? "initial_air_pump" : repump.reason();
                } else {
                    guardImmediateCollision(horizontalTarget);
                    lastHoverDecision = repump.reason();
                }
                pumpTicks++;
                totalAscendTicks++;
                if (!needsAltitude || totalAscendTicks >= PUMP_TIMEOUT) {
                    kirby.setFlightState(FlightState.DESCEND);
                    phaseTicks = 0;
                    playSound(ModSounds.KIRBY_FLY_FINISH);
                }
                break;

            case DESCEND:
                if (!kirby.onGround()) {
                    boolean landingAligned = isHorizontallyAligned(horizontalTarget);
                    boolean landingSafe = landingTarget != null
                            && landingPlanner.remainsValid(landingTarget, combatTarget);
                    KirbyFlightRecoveryPolicy.Decision recovery =
                            KirbyFlightRecoveryPolicy.descentRecovery(
                                    descentHoverRecoveries < MAX_DESCENT_HOVER_RECOVERIES,
                                    landingSafe, landingAligned, fallingTicks, groundDistance);
                    lastHoverDecision = recovery.reason();
                    if (recovery.shouldHover()) {
                        descentHoverRecoveries++;
                        beginHoverPrep(recovery.reason());
                        break;
                    }
                    steerDuringDescent(horizontalTarget);
                }
                phaseTicks++;
                if (phaseTicks >= DESCEND_DURATION && kirby.onGround()) {
                    kirby.setFlightState(FlightState.GROUND);
                    flightTarget = null;
                } else if (phaseTicks >= DESCEND_HARD_TIMEOUT) {
                    kirby.setFlightState(FlightState.GROUND);
                    flightTarget = null;
                }
                break;

            case GROUND:
            default:
                break;
        }
    }

    private void tickJumping() {
        // tick 0: 目的地・距離・頭上空間から計画した初速を適用
        if (!jumpImpulseApplied) {
            double v = plannedJumpImpulse;
            Vec3 horizontal = chooseHorizontalVelocity(flightTarget,
                    requestedHorizontalSpeed(flightTarget, MAX_HORIZONTAL_SPEED));
            kirby.setDeltaMovement(horizontal.x, v, horizontal.z);
            kirby.hasImpulse = true;
            jumpImpulseApplied = true;
        }
        // tick 4: jamp サウンド
        if (phaseTicks == JAMP_SOUND_DELAY) {
            playSound(ModSounds.KIRBY_JAMP);
        }
        phaseTicks++;

        if (plannedJumpRequiresHover) {
            // 高所: falling time and ground clearance decide when hover must begin.
            KirbyFlightRecoveryPolicy.Decision hover =
                    KirbyFlightRecoveryPolicy.initialHover(
                            true,
                            !kirby.onGround(),
                            kirby.getDeltaMovement().y < 0.0D,
                            fallingTicks,
                            groundDistance);
            lastHoverDecision = hover.reason();
            if (hover.shouldHover()) {
                beginHoverPrep(hover.reason());
                return;
            }
            // タイムアウト: 飛行できない場合は終了
            if (phaseTicks >= JUMP_TIMEOUT) {
                kirby.setFlightState(FlightState.GROUND);
                flightTarget = null;
            }
        } else {
            // 低所: 適応ジャンプのみで完結。着地で終了
            if (kirby.onGround() && phaseTicks > 2) {
                kirby.setFlightState(FlightState.GROUND);
                flightTarget = null;
            } else if (phaseTicks >= JUMP_TIMEOUT) {
                kirby.setFlightState(FlightState.GROUND);
                flightTarget = null;
            }
        }
    }

    private double measureJumpClearance() {
        AABB probe = kirby.getBoundingBox().inflate(-0.05D, 0.0D, -0.05D);
        for (double distance = KirbyJumpPolicy.CLEARANCE_PROBE_STEP;
             distance <= KirbyJumpPolicy.MAX_JUMP_HEIGHT;
             distance += KirbyJumpPolicy.CLEARANCE_PROBE_STEP) {
            if (!kirby.level().noCollision(kirby, probe.move(0.0D, distance, 0.0D))) {
                return Math.max(0.0D, distance - KirbyJumpPolicy.CLEARANCE_PROBE_STEP);
            }
        }
        return KirbyJumpPolicy.MAX_JUMP_HEIGHT;
    }

    private void updateVerticalContext() {
        boolean descending = !kirby.onGround() && kirby.getDeltaMovement().y < -1.0E-3D;
        fallingTicks = descending ? fallingTicks + 1 : 0;
        groundDistance = measureGroundDistance();
    }

    private double measureGroundDistance() {
        if (kirby.onGround()) return 0.0D;
        AABB probe = kirby.getBoundingBox().inflate(-0.05D, 0.0D, -0.05D);
        for (double distance = GROUND_PROBE_STEP;
             distance <= GROUND_PROBE_MAX_DISTANCE;
             distance += GROUND_PROBE_STEP) {
            if (!kirby.level().noCollision(kirby, probe.move(0.0D, -distance, 0.0D))) {
                return Math.max(0.0D, distance - GROUND_PROBE_STEP);
            }
        }
        return Double.POSITIVE_INFINITY;
    }

    private void beginHoverPrep(String reason) {
        Vec3 current = kirby.getDeltaMovement();
        double lift = kirby.onGround() ? 0.20D : Math.max(current.y, HOVER_LIFT_Y);
        kirby.setDeltaMovement(current.x, lift, current.z);
        kirby.hasImpulse = true;
        kirby.setFlightState(FlightState.ASCEND_PREP);
        phaseTicks = 0;
        pumpTicks = 0;
        fallingTicks = 0;
        lastHoverDecision = reason;
        playSound(ModSounds.KIRBY_FLY_LOOP);
    }

    private void maintainHover(BlockPos target) {
        Vec3 horizontal = chooseHorizontalVelocity(target,
                requestedHorizontalSpeed(target, MAX_HORIZONTAL_SPEED));
        Vec3 current = kirby.getDeltaMovement();
        double lift = kirby.onGround() ? 0.20D : Math.max(current.y, HOVER_LIFT_Y);
        kirby.setDeltaMovement(horizontal.x, lift, horizontal.z);
        kirby.hasImpulse = true;
    }

    private boolean isHorizontallyAligned(BlockPos target) {
        double dx = target.getX() + 0.5D - kirby.getX();
        double dz = target.getZ() + 0.5D - kirby.getZ();
        return dx * dx + dz * dz
                <= ARRIVAL_HORIZONTAL_DISTANCE * ARRIVAL_HORIZONTAL_DISTANCE;
    }

    private void planDestinationLanding(BlockPos pending) {
        KirbyFlightLandingPlanner.Result result = landingPlanner.findDestination(
                pending, flightTarget.getY());
        destinationLandingTarget = result.position();
        landingTarget = result.position();
        destinationLandingCandidateCount = result.candidateCount();
        destinationLandingScore = result.score();
        destinationLandingLineOfSight = result.lineOfSight();
        destinationLandingReason = "destination:" + result.reason();
        landingCandidateCount = destinationLandingCandidateCount;
        landingScore = destinationLandingScore;
        landingLineOfSight = destinationLandingLineOfSight;
        lastLandingReason = destinationLandingReason;
        landingPurpose = result.found() ? LandingPurpose.DESTINATION : LandingPurpose.ORIGINAL_TARGET;
    }

    private void refreshCombatLandingIfNeeded() {
        FlightState state = kirby.getFlightState();
        if (state != FlightState.ASCEND_PREP
                && state != FlightState.ASCEND_PUMP
                && state != FlightState.DESCEND) return;
        if (kirby.tickCount < nextLandingRefreshTick) return;
        nextLandingRefreshTick = kirby.tickCount + LANDING_REFRESH_TICKS;

        LivingEntity threat = resolveThreat();
        if (threat == null) {
            if (combatTarget != null || landingPurpose == LandingPurpose.COMBAT) {
                restoreDestinationLanding("combat_target_lost");
            }
            return;
        }

        boolean sameTarget = combatTarget != null
                && combatTarget.getUUID().equals(threat.getUUID());
        boolean focusStable = combatFocus != null
                && combatFocus.distSqr(threat.blockPosition()) <= THREAT_REPLAN_DIST_SQ;
        if (sameTarget && focusStable && landingTarget != null
                && landingPlanner.remainsValid(landingTarget, threat)) return;

        KirbyFlightLandingPlanner.Result result = landingPlanner.findCombat(
                threat, flightTarget.getY());
        if (result.found()) {
            combatTarget = threat;
            combatFocus = threat.blockPosition();
            landingTarget = result.position();
            landingCandidateCount = result.candidateCount();
            landingScore = result.score();
            landingLineOfSight = result.lineOfSight();
            landingPurpose = LandingPurpose.COMBAT;
            lastLandingReason = "combat:" + result.reason();
        } else {
            restoreDestinationLanding("combat:" + result.reason());
        }
    }

    private void restoreDestinationLanding(String reason) {
        combatTarget = null;
        combatFocus = null;
        landingTarget = destinationLandingTarget;
        landingPurpose = landingTarget == null
                ? LandingPurpose.ORIGINAL_TARGET
                : LandingPurpose.DESTINATION;
        landingCandidateCount = destinationLandingCandidateCount;
        landingScore = destinationLandingScore;
        landingLineOfSight = destinationLandingLineOfSight;
        lastLandingReason = reason + ":fallback=" + landingPurpose;
    }

    @Nullable
    private LivingEntity resolveThreat() {
        LivingEntity target = kirby.getTarget();
        if (target == null
                || !target.isAlive()
                || target.isRemoved()
                || kirby.getHeldMobs().contains(target)
                || kirby.isAlliedTo(target)
                || !kirby.canAttack(target)
                || kirby.distanceTo(target) > THREAT_TRACK_RANGE) {
            return null;
        }
        return target;
    }

    private BlockPos horizontalTarget() {
        return landingTarget == null ? flightTarget : landingTarget;
    }

    private double requestedHorizontalSpeed(BlockPos target, double maximum) {
        double dx = target.getX() + 0.5D - kirby.getX();
        double dz = target.getZ() + 0.5D - kirby.getZ();
        return Math.min(maximum, Math.sqrt(dx * dx + dz * dz) * HORIZONTAL_NUDGE);
    }

    private void steerDuringDescent(BlockPos target) {
        double dx = target.getX() + 0.5D - kirby.getX();
        double dz = target.getZ() + 0.5D - kirby.getZ();
        if (dx * dx + dz * dz <= ARRIVAL_HORIZONTAL_DISTANCE * ARRIVAL_HORIZONTAL_DISTANCE) {
            Vec3 current = kirby.getDeltaMovement();
            kirby.setDeltaMovement(0.0D, current.y, 0.0D);
            lastHorizontalVelocity = Vec3.ZERO;
            lastSteeringReason = "above_landing_target";
            return;
        }
        Vec3 horizontal = chooseHorizontalVelocity(target,
                requestedHorizontalSpeed(target, DESCEND_STEER_SPEED));
        Vec3 current = kirby.getDeltaMovement();
        kirby.setDeltaMovement(horizontal.x, current.y, horizontal.z);
    }

    private void guardImmediateCollision(BlockPos target) {
        Vec3 current = kirby.getDeltaMovement();
        Vec3 horizontal = new Vec3(current.x, 0.0D, current.z);
        if (horizontal.lengthSqr() < 1.0E-8D || isCorridorClear(horizontal)) return;
        Vec3 detour = chooseHorizontalVelocity(target,
                Math.min(MAX_HORIZONTAL_SPEED, Math.max(0.08D, horizontal.length())));
        kirby.setDeltaMovement(detour.x, current.y, detour.z);
        lastSteeringReason = lastSteering.hasDirection()
                ? "corrected_blocked_momentum"
                : "blocked_holding_horizontal";
    }

    private Vec3 chooseHorizontalVelocity(BlockPos target, double requestedSpeed) {
        double desiredX = target.getX() + 0.5D - kirby.getX();
        double desiredZ = target.getZ() + 0.5D - kirby.getZ();
        if (desiredX * desiredX + desiredZ * desiredZ
                <= ARRIVAL_HORIZONTAL_DISTANCE * ARRIVAL_HORIZONTAL_DISTANCE) {
            lastSteering = new KirbyFlightSteeringPolicy.Decision(
                    0.0D, 0.0D, -1, 0.0D, 0, false);
            lastHorizontalVelocity = Vec3.ZERO;
            lastSteeringReason = "horizontal_target_reached";
            return Vec3.ZERO;
        }

        boolean[] clear = new boolean[KirbyFlightSteeringPolicy.candidateCount()];
        for (int i = 0; i < clear.length; i++) {
            KirbyFlightSteeringPolicy.Direction direction =
                    KirbyFlightSteeringPolicy.candidateDirection(desiredX, desiredZ, i);
            clear[i] = isCorridorClear(blendedVelocity(direction, requestedSpeed));
        }
        lastSteering = KirbyFlightSteeringPolicy.select(desiredX, desiredZ, clear);
        if (!lastSteering.hasDirection()) {
            lastHorizontalVelocity = Vec3.ZERO;
            lastSteeringReason = "all_directions_blocked";
            return Vec3.ZERO;
        }
        Vec3 velocity = blendedVelocity(new KirbyFlightSteeringPolicy.Direction(
                lastSteering.x(), lastSteering.z()), requestedSpeed);
        lastHorizontalVelocity = velocity;
        lastSteeringReason = lastSteering.avoidingObstacle()
                ? "detouring_around_obstacle"
                : "direct_horizontal_route";
        return velocity;
    }

    private Vec3 blendedVelocity(
            KirbyFlightSteeringPolicy.Direction direction,
            double requestedSpeed) {
        Vec3 current = kirby.getDeltaMovement();
        double x = current.x * INERTIA_WEIGHT
                + direction.x() * requestedSpeed * (1.0D - INERTIA_WEIGHT);
        double z = current.z * INERTIA_WEIGHT
                + direction.z() * requestedSpeed * (1.0D - INERTIA_WEIGHT);
        double length = Math.sqrt(x * x + z * z);
        if (length > MAX_HORIZONTAL_SPEED) {
            x = x / length * MAX_HORIZONTAL_SPEED;
            z = z / length * MAX_HORIZONTAL_SPEED;
        }
        return new Vec3(x, 0.0D, z);
    }

    private boolean isCorridorClear(Vec3 horizontalVelocity) {
        if (horizontalVelocity.lengthSqr() < 1.0E-8D) return true;
        Vec3 displacement = horizontalVelocity.scale(COLLISION_LOOKAHEAD_TICKS);
        BlockPos end = BlockPos.containing(kirby.position().add(displacement));
        if (!kirby.level().getWorldBorder().isWithinBounds(end)) return false;
        AABB swept = kirby.getBoundingBox()
                .expandTowards(displacement.x, 0.0D, displacement.z)
                .inflate(0.05D, 0.0D, 0.05D);
        return kirby.level().noCollision(kirby, swept);
    }

    private void observeFlightDecision() {
        String targetKey = combatTarget == null
                ? blockPos(horizontalTarget())
                : combatTarget.getUUID().toString();
        kirby.getAiBrain().evaluate(KirbyDecisionLane.LOCOMOTION, kirby.tickCount, List.of(
                new KirbyAiCandidate(KirbyAiAction.FLY, KirbyDecisionLane.LOCOMOTION,
                        100.0D, true, 0, targetKey,
                        "flight_state=" + kirby.getFlightState()),
                new KirbyAiCandidate(KirbyAiAction.IDLE, KirbyDecisionLane.LOCOMOTION,
                        0.0D, true, 1, "none", "flight_fallback")));
    }

    private void playSound(net.minecraftforge.registries.RegistryObject<net.minecraft.sounds.SoundEvent> evt) {
        if (kirby.level().isClientSide) return;
        kirby.level().playSound(null, kirby.getX(), kirby.getY(), kirby.getZ(),
                evt.get(), SoundSource.NEUTRAL, 1.0F, 1.0F);
    }

    @Override
    public void stop() {
        kirby.setFlightState(FlightState.GROUND);
        flightTarget = null;
        phaseTicks = 0;
        pumpTicks = 0;
        totalAscendTicks = 0;
        fallingTicks = 0;
        descentHoverRecoveries = 0;
        groundDistance = Double.POSITIVE_INFINITY;
        lastHoverDecision = "stopped";
        jumpImpulseApplied = false;
        destinationLandingTarget = null;
        landingTarget = null;
        combatTarget = null;
        combatFocus = null;
        landingPurpose = LandingPurpose.NONE;
        lastHorizontalVelocity = Vec3.ZERO;
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        FlightState state = kirby.getFlightState();
        lines.add("FlightGoal: state=" + state
                + " phaseTicks=" + phaseTicks
                + " pumpTicks=" + pumpTicks
                + " totalAscend=" + totalAscendTicks
                + " target=" + (flightTarget == null ? "none" : blockPos(flightTarget))
                + " pending=" + (kirby.getPendingHighTarget() == null ? "none" : blockPos(kirby.getPendingHighTarget())));
        lines.add("FlightGoal jump: deltaY=" + originalDeltaY
                + " horizontalDistance=" + fmt(plannedJumpHorizontalDistance)
                + " availableClearance=" + fmt(availableJumpClearance)
                + " targetHeight=" + fmt(plannedJumpHeight)
                + " impulse=" + fmt(plannedJumpImpulse)
                + " hoverRequired=" + plannedJumpRequiresHover
                + " reason=" + lastJumpReason);
        lines.add("FlightGoal hover: fallingTicks=" + fallingTicks
                + " groundDistance=" + groundDistanceText()
                + " descentRecoveries=" + descentHoverRecoveries + "/" + MAX_DESCENT_HOVER_RECOVERIES
                + " reason=" + lastHoverDecision);
        lines.add("FlightGoal landing: purpose=" + landingPurpose
                + " target=" + (landingTarget == null ? "none" : blockPos(landingTarget))
                + " combatTarget=" + (combatTarget == null ? "none" : combatTarget.getUUID())
                + " candidates=" + landingCandidateCount
                + " score=" + fmt(landingScore)
                + " los=" + landingLineOfSight
                + " reason=" + lastLandingReason);
        lines.add("FlightGoal steering: offset=" + fmt(lastSteering.offsetDegrees())
                + " candidate=" + lastSteering.candidateIndex()
                + " rejectedBefore=" + lastSteering.blockedDirections()
                + " avoiding=" + lastSteering.avoidingObstacle()
                + " velocity=" + vec(lastHorizontalVelocity)
                + " reason=" + lastSteeringReason);
        if (state == FlightState.ASCEND_PREP && kirby.onGround()) {
            lines.add("WARN FlightGoal hover preparation touched ground");
        }
        if (lastJumpReason.contains("limited_by_headroom")) {
            lines.add("WARN FlightGoal jump height limited by overhead clearance");
        }
        if (state != FlightState.GROUND && landingTarget == null) {
            lines.add("WARN FlightGoal no safe landing target; using original horizontal target");
        }
        if (state != FlightState.GROUND && "all_directions_blocked".equals(lastSteeringReason)) {
            lines.add("WARN FlightGoal all horizontal steering directions blocked");
        }
        if (state != FlightState.GROUND && lastLandingReason.startsWith("combat:no_safe")) {
            lines.add("WARN FlightGoal no safe combat landing; using destination fallback");
        }
        lines.add("FlightGoal thought=" + flightThought(state));
    }

    private String flightThought(FlightState state) {
        switch (state) {
            case JUMPING:
                return "adaptive jump height=" + fmt(plannedJumpHeight)
                        + " reason=" + lastJumpReason;
            case ASCEND_PREP:
                return "holding altitude before air pump reason=" + lastHoverDecision;
            case ASCEND_PUMP:
                if (fallingTicks > 0) {
                    return "evaluating another hover pump reason=" + lastHoverDecision;
                }
                return landingPurpose == LandingPurpose.COMBAT
                        ? "pumping upward toward combat landing"
                        : "pumping upward toward destination landing";
            case DESCEND:
                return landingPurpose == LandingPurpose.COMBAT
                        ? "descending to engage threat from safe ground"
                        : "descending to selected safe ground";
            case DODGE_JUMP:
                return "dodging incoming projectile";
            case GROUND:
            default:
                return kirby.getPendingHighTarget() == null ? "grounded" : "waiting to jump";
        }
    }

    private String groundDistanceText() {
        return Double.isFinite(groundDistance)
                ? fmt(groundDistance)
                : ">" + fmt(GROUND_PROBE_MAX_DISTANCE);
    }

    private static String blockPos(BlockPos pos) {
        return pos.getX() + "," + pos.getY() + "," + pos.getZ();
    }

    private static String vec(Vec3 vec) {
        return fmt(vec.x) + "," + fmt(vec.y) + "," + fmt(vec.z);
    }

    private static String fmt(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }
}
