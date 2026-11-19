package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.ModSounds;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;

public class KirbyDigestGoal extends Goal implements KirbyDebugInfoProvider {

    private static final int HOLD_TICKS =
            KirbyDigestTimingPolicy.HOLD_DECISION_TICKS;
    private static final int NOMIKOMI_TICKS = 40;
    // The nomikomi animation returns its size keyframes to normal at 0.3 seconds (6 ticks).
    // Complete the continuous mouth scale in that same visual window so no shrink remains afterward.
    private static final int NOMIKOMI_SIZE_TRANSITION_TICKS = 6;
    private static final double TARGET_SCAN_RANGE = 35.0D;
    private static final double DISTANT_TARGET_RANGE = 8.0D;
    private static final double WALL_CHECK_RANGE = 4.0D;
    private static final double FRONT_DOT_MIN = 0.5D;
    private static final double FRIENDLY_LANE_RADIUS = 0.75D;
    private static final float FORCE_SPIT_MAX_HEALTH = 50.0F;
    private static final TagKey<EntityType<?>> ALWAYS_SPIT = TagKey.create(
            Registries.ENTITY_TYPE, id("always_spit"));
    private static final TagKey<EntityType<?>> SWALLOWABLE = TagKey.create(
            Registries.ENTITY_TYPE, id("swallowable"));

    private final KirbyEntity kirby;
    private final KirbySpitController spitController;
    private int holdTicks;
    private int phaseTicks;
    private double lastSwallowScore;
    private double lastSpitScore;
    private String lastDigestDecision = "WAITING";
    private String lastDigestDecisionReason = "hold timer not reached";
    private List<String> lastTrajectoryCandidates = List.of();
    @Nullable private LivingEntity trackedSpitTarget;
    private KirbySpitTargetPolicy.Selection lastTargetSelection =
            KirbySpitTargetPolicy.Selection.none("not_evaluated");
    private Vec3 lastPlannedSpitDirection = Vec3.ZERO;
    private String lastAimReason = "not_evaluated";

    public KirbyDigestGoal(KirbyEntity kirby) {
        this.kirby = kirby;
        this.spitController = new KirbySpitController(kirby);
        // Holding can coexist with locomotion, but owns LOOK so the selected threat stays aimed.
        this.setFlags(EnumSet.of(Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        return kirby.getCombatState().isHolding();
    }

    @Override
    public boolean canContinueToUse() {
        return kirby.getCombatState().isHolding();
    }

    @Override
    public void start() {
        holdTicks = 0;
        phaseTicks = 0;
        spitController.resetTracking();
        trackedSpitTarget = null;
        lastTargetSelection = KirbySpitTargetPolicy.Selection.none("hold_started");
        lastPlannedSpitDirection = Vec3.ZERO;
        lastAimReason = "hold_started";
    }

    @Override
    public void tick() {
        List<LivingEntity> heldMobs = kirby.getHeldMobs();
        // Safety: lost all held mobs outside of spit — clean reset.
        if (heldMobs.isEmpty() && kirby.getCombatState() != CombatState.KEEP_SPIT) {
            kirby.getMouthController().recoverEmpty("digest_goal_lost_contents");
            return;
        }

        switch (kirby.getCombatState()) {
            case KEEP_HOLDING:
                SpitTargetContext spitTarget = selectSpitTarget(heldMobs);
                trackSpitTarget(spitTarget);
                holdTicks++;
                if (KirbyDigestTimingPolicy.readyForDecision(holdTicks)) {
                    chooseDigestAction(heldMobs, spitTarget);
                    phaseTicks = 0;
                }
                break;

            case KEEP_NOMIKOMI:
                phaseTicks++;
                if (phaseTicks >= NOMIKOMI_TICKS) {
                    kirby.getMouthController().completeSwallowing("swallow_animation_completed");
                }
                break;

            case KEEP_SPIT:
                spitController.tick();
                break;

            default:
                break;
        }
    }

    @Override
    public void stop() {
        // The dedicated controller owns every in-flight terminal path.
        if (spitController.isActive()) {
            spitController.abort(KirbySpitFinishReason.GOAL_INTERRUPTED);
        }
        if (kirby.getMouthController().getPhase().isActive()
                || !kirby.getHeldMobs().isEmpty()) {
            kirby.getMouthController().abort(List.of(), "digest_goal_interrupted");
        }
        holdTicks = 0;
        phaseTicks = 0;
        trackedSpitTarget = null;
    }

    private void chooseDigestAction(
            List<LivingEntity> heldMobs,
            SpitTargetContext spitTarget) {
        DecisionContext context = inspectDecisionContext(heldMobs, spitTarget);
        double strongestHeldMaxHealth = heldMobs.stream()
                .mapToDouble(LivingEntity::getMaxHealth)
                .max()
                .orElse(0.0D);
        double jitter = kirby.getRandom().nextDouble() * 0.7D - 0.35D;
        KirbyDigestDecisionPolicy.Scores scores = KirbyDigestDecisionPolicy.evaluate(
                new KirbyDigestDecisionPolicy.Inputs(
                        context.clearTargetCount,
                        context.distantTargetCount,
                        context.wallAhead,
                        context.friendlyInLine,
                        heldMobs.size(),
                        kirby.getMouthFullness(),
                        strongestHeldMaxHealth,
                        jitter));

        String forcedReason = forcedSpitReason(heldMobs);
        boolean shouldSpit = forcedReason != null || scores.shouldSpit();
        this.lastSwallowScore = scores.swallowScore;
        this.lastSpitScore = scores.spitScore;
        this.lastDigestDecision = shouldSpit ? "SPIT" : "SWALLOW";
        this.lastDigestDecisionReason = forcedReason != null
                ? "forced:" + forcedReason
                : String.join(",", scores.reasons);
        this.lastTrajectoryCandidates = context.trajectoryCandidates;
        this.lastPlannedSpitDirection = context.aimDirection;
        this.lastAimReason = context.aimReason;

        if (shouldSpit) {
            spitController.start(heldMobs, context.aimDirection);
            SoundEvent[] reverses = new SoundEvent[] {
                    ModSounds.KIRBY_REVERSE_1.get(),
                    ModSounds.KIRBY_REVERSE_2A.get(),
                    ModSounds.KIRBY_REVERSE_2B.get(),
                    ModSounds.KIRBY_REVERSE_3.get()
            };
            playSound(reverses[kirby.getRandom().nextInt(reverses.length)]);
            return;
        }

        kirby.getMouthController().beginSwallowing(
                NOMIKOMI_SIZE_TRANSITION_TICKS, "digest_decision_swallow");
        SoundEvent nomi = kirby.getRandom().nextBoolean()
                ? ModSounds.KIRBY_NOMIKOMI_1.get()
                : ModSounds.KIRBY_NOMIKOMI_2.get();
        playSound(nomi);
    }

    private SpitTargetContext selectSpitTarget(List<LivingEntity> heldMobs) {
        LivingEntity target = kirby.getTarget();
        if (target == null) {
            return new SpitTargetContext(null,
                    KirbySpitTargetPolicy.Selection.none("no_combat_target"));
        }
        if (!target.isAlive()
                || target.isRemoved()
                || heldMobs.contains(target)
                || isFriendly(target)
                || !kirby.canAttack(target)
                || kirby.distanceTo(target) > TARGET_SCAN_RANGE) {
            return new SpitTargetContext(null,
                    KirbySpitTargetPolicy.Selection.none("invalid_combat_target"));
        }

        Vec3 offset = target.getBoundingBox().getCenter()
                .subtract(kirby.getEyePosition());
        KirbySpitTargetPolicy.Candidate candidate =
                new KirbySpitTargetPolicy.Candidate(
                        target.getUUID().toString(),
                        offset.x,
                        offset.z,
                        offset.length(),
                        kirby.hasLineOfSight(target),
                        true,
                        true);
        KirbySpitTargetPolicy.Selection selection =
                KirbySpitTargetPolicy.select(List.of(candidate));
        return new SpitTargetContext(
                selection.found() ? target : null,
                selection);
    }

    private void trackSpitTarget(SpitTargetContext context) {
        trackedSpitTarget = context.target;
        lastTargetSelection = context.selection;
        if (trackedSpitTarget != null) {
            lastPlannedSpitDirection = new Vec3(
                    context.selection.directionX(), 0.0D,
                    context.selection.directionZ());
            lastAimReason = context.selection.reason();
            kirby.getLookControl().setLookAt(trackedSpitTarget, 60.0F, 60.0F);
        } else {
            lastPlannedSpitDirection = Vec3.ZERO;
            lastAimReason = context.selection.reason();
        }
    }

    private String forcedSpitReason(List<LivingEntity> heldMobs) {
        for (LivingEntity mob : heldMobs) {
            ResourceLocation key = BuiltInRegistries.ENTITY_TYPE.getKey(mob.getType());
            String typeName = key == null ? "unknown" : key.toString();
            if (mob.getType().is(ALWAYS_SPIT)) {
                return "alwaysSpitTag mob=" + typeName;
            }
            if (mob.getMaxHealth() >= FORCE_SPIT_MAX_HEALTH) {
                return "maxHealth mob=" + typeName + " value=" + fmt(mob.getMaxHealth());
            }
            if (mob.hasCustomName()) {
                return "customName mob=" + typeName;
            }
            if (mob instanceof TamableAnimal tamable && tamable.isTame()) {
                return "tamed mob=" + typeName;
            }
            if (key != null && !"minecraft".equals(key.getNamespace())
                    && !mob.getType().is(SWALLOWABLE)) {
                return "moddedNamespace mob=" + typeName;
            }
        }
        return null;
    }

    private DecisionContext inspectDecisionContext(
            List<LivingEntity> heldMobs,
            SpitTargetContext spitTarget) {
        Vec3 origin = kirby.getEyePosition();
        Vec3 forward = spitTarget.selection.found()
                ? new Vec3(spitTarget.selection.directionX(), 0.0D,
                        spitTarget.selection.directionZ())
                : horizontalLookDirection();
        Vec3 wallEnd = origin.add(forward.scale(WALL_CHECK_RANGE));
        boolean wallAhead = kirby.level().clip(new ClipContext(
                origin, wallEnd, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, kirby))
                .getType() != HitResult.Type.MISS;

        int clearTargets = 0;
        int distantTargets = 0;
        boolean friendlyInLine = false;
        List<String> candidates = new ArrayList<>();
        AABB scanBox = kirby.getBoundingBox().inflate(TARGET_SCAN_RANGE);
        List<LivingEntity> nearby = kirby.level().getEntitiesOfClass(LivingEntity.class, scanBox,
                entity -> entity != kirby && entity.isAlive() && !heldMobs.contains(entity));

        for (LivingEntity entity : nearby) {
            Vec3 toEntity = entity.getBoundingBox().getCenter().subtract(origin);
            double distance = toEntity.length();
            if (distance < 1.0E-4D) continue;
            double forwardDistance = toEntity.dot(forward);
            if (forwardDistance <= 0.0D || forwardDistance > TARGET_SCAN_RANGE) continue;
            double lateralSq = Math.max(0.0D,
                    toEntity.lengthSqr() - forwardDistance * forwardDistance);
            double laneRadius = FRIENDLY_LANE_RADIUS + entity.getBbWidth() * 0.5D;
            if (isFriendly(entity) && lateralSq <= laneRadius * laneRadius) {
                friendlyInLine = true;
            }

            boolean inFront = forwardDistance / distance >= FRONT_DOT_MIN;
            boolean selectedThreat = entity.getUUID().toString()
                    .equals(spitTarget.selection.targetKey());
            if (!(entity instanceof Enemy) && !selectedThreat) continue;
            if (!inFront || !kirby.canAttack(entity) || isFriendly(entity)) continue;
            boolean clear = kirby.hasLineOfSight(entity);
            if (candidates.size() < 6) {
                ResourceLocation key = BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType());
                candidates.add((key == null ? "unknown" : key.toString())
                        + " dist=" + fmt(distance) + " clear=" + clear);
            }
            if (!clear) continue;
            clearTargets++;
            if (distance >= DISTANT_TARGET_RANGE) distantTargets++;
        }

        String aimReason = spitTarget.selection.found()
                ? spitTarget.selection.reason()
                : "current_view_fallback:" + spitTarget.selection.reason();
        return new DecisionContext(clearTargets, distantTargets, wallAhead,
                friendlyInLine, List.copyOf(candidates), forward, aimReason);
    }

    private Vec3 horizontalLookDirection() {
        Vec3 view = kirby.getViewVector(1.0F);
        double length = Math.sqrt(view.x * view.x + view.z * view.z);
        if (length >= 1.0E-4D) {
            return new Vec3(view.x / length, 0.0D, view.z / length);
        }
        double yaw = Math.toRadians(kirby.getYRot());
        return new Vec3(-Math.sin(yaw), 0.0D, Math.cos(yaw));
    }

    private boolean isFriendly(LivingEntity entity) {
        return entity instanceof Player
                || kirby.isAlliedTo(entity)
                || entity instanceof TamableAnimal tamable && tamable.isTame();
    }

    private void playSound(SoundEvent evt) {
        if (kirby.level().isClientSide) return;
        kirby.level().playSound(null, kirby.getX(), kirby.getY(), kirby.getZ(),
                evt, SoundSource.NEUTRAL, 1.0F, 1.0F);
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        CombatState state = kirby.getCombatState();
        lines.add("DigestGoal: state=" + state
                + " holdTicks=" + holdTicks + "/" + HOLD_TICKS
                + " phaseTicks=" + phaseTicks);
        spitController.appendDebugInfo(lines);
        lines.add("DigestRecovery " + KirbyHeldMobControl.recoveryDebugSummary());
        lines.add("DigestDecision result=" + lastDigestDecision
                + " swallowScore=" + fmt(lastSwallowScore)
                + " spitScore=" + fmt(lastSpitScore)
                + " reason=" + lastDigestDecisionReason);
        lines.add("DigestAim target=" + lastTargetSelection.targetKey()
                + " distance=" + (Double.isFinite(lastTargetSelection.distance())
                        ? fmt(lastTargetSelection.distance()) : "none")
                + " remembered=" + lastTargetSelection.rememberedThreat()
                + " targetAlive=" + (trackedSpitTarget != null && trackedSpitTarget.isAlive())
                + " direction=" + vec(lastPlannedSpitDirection)
                + " reason=" + lastAimReason);
        if (lastTrajectoryCandidates.isEmpty()) {
            lines.add("DigestDecision trajectory[0]=none");
        } else {
            for (int i = 0; i < lastTrajectoryCandidates.size(); i++) {
                lines.add("DigestDecision trajectory[" + i + "]=" + lastTrajectoryCandidates.get(i));
            }
        }
        lines.add("DigestGoal thought=" + digestThought(state));
    }

    private String digestThought(CombatState state) {
        switch (state) {
            case KEEP_HOLDING:
                if (lastTargetSelection.found()) {
                    return "aiming held prey at threat=" + lastTargetSelection.targetKey()
                            + " reason=" + lastTargetSelection.reason();
                }
                return holdTicks >= HOLD_TICKS
                        ? "ready to choose swallow or spit without clear threat"
                        : "keeping prey sealed while searching for threat";
            case KEEP_NOMIKOMI:
                return "swallowing held prey";
            case KEEP_SPIT:
                return lastTargetSelection.found()
                        ? "launching held prey at threat=" + lastTargetSelection.targetKey()
                        : "launching held prey along safe fallback direction";
            default:
                return "no prey in mouth";
        }
    }

    private static String fmt(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }

    private static String vec(Vec3 value) {
        return fmt(value.x) + "," + fmt(value.y) + "," + fmt(value.z);
    }

    private static ResourceLocation id(String path) {
        return Objects.requireNonNull(ResourceLocation.tryBuild("kirby_mod", path));
    }

    private static final class DecisionContext {
        private final int clearTargetCount;
        private final int distantTargetCount;
        private final boolean wallAhead;
        private final boolean friendlyInLine;
        private final List<String> trajectoryCandidates;
        private final Vec3 aimDirection;
        private final String aimReason;

        private DecisionContext(int clearTargetCount, int distantTargetCount,
                                boolean wallAhead, boolean friendlyInLine,
                                List<String> trajectoryCandidates,
                                Vec3 aimDirection, String aimReason) {
            this.clearTargetCount = clearTargetCount;
            this.distantTargetCount = distantTargetCount;
            this.wallAhead = wallAhead;
            this.friendlyInLine = friendlyInLine;
            this.trajectoryCandidates = trajectoryCandidates;
            this.aimDirection = aimDirection;
            this.aimReason = aimReason;
        }
    }

    private record SpitTargetContext(
            @Nullable LivingEntity target,
            KirbySpitTargetPolicy.Selection selection) {}
}
