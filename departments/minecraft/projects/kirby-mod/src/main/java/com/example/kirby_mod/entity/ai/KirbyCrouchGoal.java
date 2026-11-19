package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.KirbySize;
import com.example.kirby_mod.entity.ModSounds;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ThrownTrident;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.List;
import java.util.Locale;

public class KirbyCrouchGoal extends Goal implements KirbyDebugInfoProvider {

    private static final int PREP_TICKS = 3;
    private static final int END_TICKS = 3;
    private static final int LOOP_HARD_TIMEOUT = 60;
    private static final int LOOP_HARD_MIN = 10;
    private static final int RESCAN_PERIOD = 8;
    private static final int SIM_TICKS = 20;
    private static final double SCAN_HORIZ = 8.0D;
    private static final double SCAN_VERT = 4.0D;
    private static final double CROUCH_HEIGHT_RATIO = 0.4D;
    private static final double ARROW_GRAVITY_PER_TICK = 0.05D;
    private static final int SLIDE_DECISION_DELAY_TICKS = 2;
    private static final double SLIDE_MIN_TARGET_DISTANCE = 0.75D;
    private static final double SLIDE_MAX_TARGET_DISTANCE = 8.0D;
    private static final double SLIDE_FORWARD_DOT_MIN = 0.35D;
    private static final double SLIDE_HIT_INFLATE = 0.15D;
    private static final double SLIDE_KNOCKBACK = 2.0D;
    private static final double RECOIL_HORIZONTAL = 0.22D;
    private static final double RECOIL_VERTICAL = 0.42D;

    private final KirbyEntity kirby;
    private int phaseTicks;
    private int loopTicks;
    private int slideTicks;
    private Vec3 slideDirection = Vec3.ZERO;
    private Vec3 lastRecoil = Vec3.ZERO;
    @Nullable private LivingEntity slideCandidate;
    private String lastTrigger = "none";
    private String lastSlideDecision = "idle";
    private String lastSlideEndReason = "none";

    public KirbyCrouchGoal(KirbyEntity kirby) {
        this.kirby = kirby;
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        if (kirby.getKirbySize() != KirbySize.NORMAL) return false;
        if (!kirby.getHeldMobs().isEmpty()) return false;
        if (kirby.getCombatState() != CombatState.NONE) return false;
        if (kirby.getFlightState() != KirbyEntity.FlightState.GROUND) return false;
        if (!kirby.onGround()) return false;
        if (kirby.tickCount % 4 != 0) return false;
        Projectile threat = findAvoidableProjectile();
        if (threat == null) return false;
        captureSlideCandidate(threat);
        return true;
    }

    @Override
    public boolean canContinueToUse() {
        return kirby.getCombatState().usesLowProfileHitbox();
    }

    @Override
    public void start() {
        kirby.setCombatState(CombatState.CROUCH_PREP);
        phaseTicks = 0;
        loopTicks = 0;
        slideTicks = 0;
        slideDirection = Vec3.ZERO;
        lastRecoil = Vec3.ZERO;
        lastSlideDecision = slideCandidate == null ? "slide_skip:no_projectile_owner" : "crouch_ready";
        lastSlideEndReason = "none";
        if (!kirby.level().isClientSide) {
            kirby.level().playSound(null, kirby.getX(), kirby.getY(), kirby.getZ(),
                    ModSounds.KIRBY_LAND.get(), SoundSource.NEUTRAL, 1.0F, 1.0F);
        }
    }

    @Override
    public void tick() {
        kirby.getNavigation().stop();

        switch (kirby.getCombatState()) {
            case CROUCH_PREP:
                stopHorizontalMotion();
                faceSlideCandidate();
                if (!canRemainCrouched()) {
                    beginCrouchEnd("slide_skip:crouch_condition_lost");
                    break;
                }
                if (++phaseTicks >= PREP_TICKS) {
                    kirby.setCombatState(CombatState.CROUCH_LOOP);
                    loopTicks = 0;
                }
                break;
            case CROUCH_LOOP:
                stopHorizontalMotion();
                faceSlideCandidate();
                if (!canRemainCrouched()) {
                    beginCrouchEnd("slide_skip:crouch_condition_lost");
                    break;
                }
                loopTicks++;
                if (loopTicks >= SLIDE_DECISION_DELAY_TICKS && tryStartSlide()) {
                    break;
                }
                boolean reEval = (loopTicks % RESCAN_PERIOD == 0);
                boolean threatGone = loopTicks >= LOOP_HARD_MIN && reEval && !hasAvoidableProjectile();
                if (threatGone || loopTicks >= LOOP_HARD_TIMEOUT) {
                    if (canStandUp() || loopTicks >= LOOP_HARD_TIMEOUT + 20) {
                        beginCrouchEnd(threatGone ? "slide_skip:threat_gone" : "slide_skip:crouch_timeout");
                    }
                }
                break;
            case CROUCH_END:
                stopHorizontalMotion();
                if (++phaseTicks >= END_TICKS) {
                    kirby.setCombatState(CombatState.NONE);
                }
                break;
            case SLIDE_START:
                tickSlideStart();
                break;
            case SLIDING:
                tickSliding();
                break;
            case SLIDE_FINISH:
                lockSlideFacing();
                if (++phaseTicks >= KirbySlideMotion.FINISH_TICKS) {
                    kirby.setCombatState(CombatState.NONE);
                }
                break;
            default:
                break;
        }
    }

    @Override
    public void stop() {
        if (kirby.getCombatState().usesLowProfileHitbox()) {
            kirby.setCombatState(CombatState.NONE);
        }
        phaseTicks = 0;
        loopTicks = 0;
        slideTicks = 0;
        slideCandidate = null;
    }

    private boolean canStandUp() {
        net.minecraft.world.entity.EntityDimensions normal = KirbySize.NORMAL.toDimensions();
        double half = normal.width * 0.5D;
        double h = normal.height;
        AABB stand = new AABB(
                kirby.getX() - half, kirby.getY(), kirby.getZ() - half,
                kirby.getX() + half, kirby.getY() + h, kirby.getZ() + half);
        return kirby.level().noCollision(kirby, stand);
    }

    private boolean hasAvoidableProjectile() {
        return findAvoidableProjectile() != null;
    }

    @Nullable
    private Projectile findAvoidableProjectile() {
        AABB scan = kirby.getBoundingBox().inflate(SCAN_HORIZ, SCAN_VERT, SCAN_HORIZ);
        List<Projectile> projs = kirby.level().getEntitiesOfClass(Projectile.class, scan,
                p -> p.isAlive() && p.getOwner() != kirby
                        && p.getDeltaMovement().lengthSqr() > 0.01D);
        if (projs.isEmpty()) return null;

        AABB stand = kirby.getBoundingBox();
        double crouchH = KirbySize.NORMAL.toDimensions().height * CROUCH_HEIGHT_RATIO;
        AABB crouch = new AABB(stand.minX, stand.minY, stand.minZ,
                stand.maxX, stand.minY + crouchH, stand.maxZ);

        for (Projectile p : projs) {
            Vec3 pos = p.position();
            Vec3 vel = p.getDeltaMovement();
            boolean isArrowLike = (p instanceof AbstractArrow) || (p instanceof ThrownTrident);
            double gPerTick = isArrowLike ? ARROW_GRAVITY_PER_TICK : 0.0D;
            double vx = vel.x, vy = vel.y, vz = vel.z;
            double px = pos.x, py = pos.y, pz = pos.z;
            for (int t = 1; t <= SIM_TICKS; t++) {
                vy -= gPerTick;
                px += vx;
                py += vy;
                pz += vz;
                if (stand.contains(px, py, pz)) {
                    if (!crouch.contains(px, py, pz)) return p;
                    break;
                }
            }
        }
        return null;
    }

    private void captureSlideCandidate(Projectile threat) {
        Entity owner = threat.getOwner();
        lastTrigger = threat.getType() + " id=" + shortId(threat);
        if (owner instanceof LivingEntity living
                && living.isAlive()
                && !kirby.isAlliedTo(living)) {
            slideCandidate = living;
            lastTrigger += " owner=" + living.getType() + " id=" + shortId(living);
        } else {
            slideCandidate = null;
            lastTrigger += owner == null ? " owner=none" : " owner=ineligible";
        }
    }

    private boolean canRemainCrouched() {
        return kirby.getKirbySize() == KirbySize.NORMAL
                && kirby.getHeldMobs().isEmpty()
                && kirby.getFlightState() == KirbyEntity.FlightState.GROUND
                && kirby.onGround();
    }

    private void beginCrouchEnd(String reason) {
        kirby.setCombatState(CombatState.CROUCH_END);
        phaseTicks = 0;
        lastSlideDecision = reason;
    }

    private void stopHorizontalMotion() {
        kirby.setDeltaMovement(0.0D, kirby.getDeltaMovement().y, 0.0D);
    }

    private void faceSlideCandidate() {
        LivingEntity candidate = slideCandidate;
        if (candidate != null && candidate.isAlive()) {
            kirby.getLookControl().setLookAt(candidate, 45.0F, 30.0F);
        }
    }

    private boolean tryStartSlide() {
        LivingEntity candidate = slideCandidate;
        if (candidate == null || !candidate.isAlive()) {
            lastSlideDecision = "slide_skip:owner_unavailable";
            return false;
        }
        if (kirby.isAlliedTo(candidate)) {
            lastSlideDecision = "slide_skip:owner_allied";
            return false;
        }
        double distance = kirby.distanceTo(candidate);
        if (distance < SLIDE_MIN_TARGET_DISTANCE || distance > SLIDE_MAX_TARGET_DISTANCE) {
            lastSlideDecision = "slide_skip:distance=" + fmt(distance);
            return false;
        }
        if (!kirby.hasLineOfSight(candidate)) {
            lastSlideDecision = "slide_skip:blocked_line";
            return false;
        }

        Vec3 forward = horizontalUnit(kirby.getLookAngle());
        Vec3 toward = horizontalUnit(candidate.position().subtract(kirby.position()));
        if (forward == Vec3.ZERO || toward == Vec3.ZERO
                || forward.dot(toward) < SLIDE_FORWARD_DOT_MIN) {
            lastSlideDecision = "slide_skip:not_in_front";
            return false;
        }

        slideDirection = forward;
        phaseTicks = 0;
        slideTicks = 0;
        lastRecoil = Vec3.ZERO;
        lastSlideDecision = "slide_commit:owner=" + candidate.getType() + " distance=" + fmt(distance);
        lastSlideEndReason = "none";
        kirby.horizontalCollision = false;
        kirby.verticalCollision = false;
        kirby.setCombatState(CombatState.SLIDE_START);
        lockSlideFacing();
        return true;
    }

    private void tickSlideStart() {
        lockSlideFacing();
        if (!canContinueSliding()) {
            finishSlide("interrupted", false);
            return;
        }
        if (phaseTicks > 0 && finishForCollision()) return;

        applySlideSpeed(slideTicks);
        slideTicks++;
        phaseTicks++;
        if (phaseTicks >= 2) {
            kirby.setCombatState(CombatState.SLIDING);
        }
    }

    private void tickSliding() {
        lockSlideFacing();
        if (!canContinueSliding()) {
            finishSlide("interrupted", false);
            return;
        }
        if (finishForCollision()) return;
        if (slideTicks >= KirbySlideMotion.MOTION_TICKS) {
            finishSlide("timeout", false);
            return;
        }
        applySlideSpeed(slideTicks);
        slideTicks++;
    }

    private boolean canContinueSliding() {
        return kirby.getKirbySize() == KirbySize.NORMAL
                && kirby.getHeldMobs().isEmpty()
                && kirby.getFlightState() == KirbyEntity.FlightState.GROUND
                && kirby.onGround();
    }

    private void applySlideSpeed(int motionTick) {
        double walkSpeed = kirby.getAttributeValue(Attributes.MOVEMENT_SPEED);
        double speed = KirbySlideMotion.horizontalSpeed(walkSpeed, motionTick);
        kirby.setDeltaMovement(slideDirection.x * speed, kirby.getDeltaMovement().y,
                slideDirection.z * speed);
    }

    private boolean finishForCollision() {
        LivingEntity hit = findSlideHit();
        if (hit != null) {
            hit.knockback(SLIDE_KNOCKBACK,
                    kirby.getX() - hit.getX(), kirby.getZ() - hit.getZ());
            hit.hurtMarked = true;
            finishSlide("hit:" + hit.getType() + " id=" + shortId(hit), true);
            return true;
        }
        if (kirby.horizontalCollision) {
            finishSlide("wall", true);
            return true;
        }
        return false;
    }

    @Nullable
    private LivingEntity findSlideHit() {
        double lookAhead = Math.max(0.25D, kirby.getDeltaMovement().horizontalDistance());
        AABB swept = kirby.getBoundingBox().expandTowards(slideDirection.scale(lookAhead))
                .inflate(SLIDE_HIT_INFLATE, 0.05D, SLIDE_HIT_INFLATE);
        return kirby.level().getEntitiesOfClass(LivingEntity.class, swept,
                        entity -> entity != kirby
                                && entity.isAlive()
                                && !kirby.isAlliedTo(entity)
                                && (entity == slideCandidate || entity instanceof Enemy))
                .stream()
                .min((a, b) -> Double.compare(kirby.distanceToSqr(a), kirby.distanceToSqr(b)))
                .orElse(null);
    }

    private void finishSlide(String reason, boolean recoil) {
        lastSlideEndReason = reason;
        phaseTicks = 0;
        if (recoil) {
            lastRecoil = slideDirection.scale(-RECOIL_HORIZONTAL)
                    .add(0.0D, RECOIL_VERTICAL, 0.0D);
            kirby.setDeltaMovement(lastRecoil);
            kirby.fallDistance = 0.0F;
            kirby.hurtMarked = true;
        } else {
            lastRecoil = Vec3.ZERO;
            stopHorizontalMotion();
        }
        kirby.setCombatState(CombatState.SLIDE_FINISH);
    }

    private void lockSlideFacing() {
        if (slideDirection == Vec3.ZERO) return;
        float yaw = (float) (Math.toDegrees(Math.atan2(slideDirection.z, slideDirection.x)) - 90.0D);
        kirby.setYRot(yaw);
        kirby.yBodyRot = yaw;
        kirby.yHeadRot = yaw;
    }

    private static Vec3 horizontalUnit(Vec3 vector) {
        Vec3 horizontal = new Vec3(vector.x, 0.0D, vector.z);
        return horizontal.lengthSqr() < 1.0E-8D ? Vec3.ZERO : horizontal.normalize();
    }

    private static String shortId(Entity entity) {
        return entity.getUUID().toString().substring(0, 8);
    }

    private static String fmt(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }

    private static String vec(Vec3 value) {
        return fmt(value.x) + "," + fmt(value.y) + "," + fmt(value.z);
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        CombatState state = kirby.getCombatState();
        int remaining = Math.max(0, KirbySlideMotion.MOTION_TICKS - slideTicks);
        lines.add("CrouchGoal: state=" + state
                + " phaseTicks=" + phaseTicks
                + " loopTicks=" + loopTicks
                + " slideTicks=" + slideTicks + "/" + KirbySlideMotion.MOTION_TICKS
                + " remaining=" + remaining
                + " speed=" + fmt(kirby.getDeltaMovement().horizontalDistance())
                + " direction=" + vec(slideDirection));
        lines.add("CrouchGoal trigger=" + lastTrigger
                + " candidate=" + (slideCandidate == null ? "none" : slideCandidate.getType())
                + " endReason=" + lastSlideEndReason
                + " recoil=" + vec(lastRecoil));
        lines.add("CrouchGoal thought=" + lastSlideDecision);
    }
}
