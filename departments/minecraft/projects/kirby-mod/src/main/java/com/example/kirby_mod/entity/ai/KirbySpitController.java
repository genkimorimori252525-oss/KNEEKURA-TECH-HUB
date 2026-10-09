package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.KirbyEntity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Single authority for the runtime portion of a spit attack.
 *
 * <p>The digest goal chooses an action and direction. This controller owns the
 * atomic mouth handoff, scripted flight, collision damage, every terminal path,
 * and restoration of the physical Mob.</p>
 */
public final class KirbySpitController implements KirbyDebugInfoProvider {

    private static final int SPIT_ANIMATION_TICKS = 10;
    private static final double SPIT_SPEED = 1.0D;
    private static final int SPIT_MIN_TICKS = 20;
    private static final int SPIT_MAX_TICKS = 30;
    private static final float SPIT_DAMAGE = 100.0F;
    private static final int SPIT_PIERCE_THRESHOLD = 15;
    private static final double KNOCKBACK_STRENGTH = 1.2D;
    private static final double SPIT_EXIT_MARGIN = 0.2D;

    private final KirbyEntity kirby;
    private final Map<UUID, SpitProjectile> projectiles = new LinkedHashMap<>();
    private KirbySpitState state = KirbySpitState.IDLE;
    private int totalFlightTicks;
    private int flightTicks;
    private KirbySpitFinishReason lastSessionReason = KirbySpitFinishReason.NONE;
    private KirbySpitFinishReason lastProjectileReason = KirbySpitFinishReason.NONE;
    private String lastResult = "none";
    private String lastTransition = "init->IDLE";
    private String lastWarning = "none";

    public KirbySpitController(KirbyEntity kirby) {
        this.kirby = kirby;
    }

    public KirbySpitState getState() {
        return this.state;
    }

    public boolean isActive() {
        return this.state.isActive();
    }

    public String getLastResult() {
        return this.lastResult;
    }

    public void resetTracking() {
        if (isActive()) {
            abort(KirbySpitFinishReason.GOAL_INTERRUPTED);
        }
        this.lastSessionReason = KirbySpitFinishReason.NONE;
        this.lastProjectileReason = KirbySpitFinishReason.NONE;
        this.lastResult = "none";
        this.lastWarning = "none";
    }

    public boolean start(List<LivingEntity> heldMobs, Vec3 plannedDirection) {
        if (isActive()) {
            this.lastWarning = "start requested while state=" + this.state;
            return false;
        }
        if (heldMobs == null || heldMobs.isEmpty()) {
            this.lastSessionReason = KirbySpitFinishReason.LAUNCH_FAILED;
            this.lastResult = "launch failed: empty mouth";
            this.kirby.getMouthController().recoverEmpty("spit_launch_empty");
            return false;
        }

        transitionTo(KirbySpitState.STARTING, "digest_decision_spit");
        this.projectiles.clear();
        this.flightTicks = 0;
        this.totalFlightTicks = SPIT_MIN_TICKS + this.kirby.getRandom().nextInt(
                SPIT_MAX_TICKS - SPIT_MIN_TICKS + 1);
        this.lastSessionReason = KirbySpitFinishReason.NONE;
        this.lastProjectileReason = KirbySpitFinishReason.NONE;
        this.lastWarning = "none";
        this.kirby.getMouthController().beginSpitting(
                SPIT_ANIMATION_TICKS, "spit_controller_start");

        Vec3 baseDirection = normalizedHorizontal(plannedDirection);
        List<LivingEntity> launchMobs = List.copyOf(heldMobs);
        int count = launchMobs.size();
        for (int i = 0; i < count; i++) {
            LivingEntity mob = launchMobs.get(i);
            Vec3 direction = spreadDirection(baseDirection, i, count);
            Vec3 velocity = direction.scale(SPIT_SPEED);
            positionAtMouthExit(mob, direction, velocity);

            if (!this.kirby.getMouthController().detachForSpit(mob)) {
                this.lastWarning = "control transfer failed id=" + shortId(mob);
                continue;
            }
            this.projectiles.put(mob.getUUID(), new SpitProjectile(mob, velocity));
        }

        if (this.projectiles.isEmpty()) {
            this.lastResult = "launch failed: no Mob accepted projectile control";
            finishSession(KirbySpitFinishReason.LAUNCH_FAILED);
            return false;
        }

        transitionTo(KirbySpitState.FLYING, "projectiles_launched");
        this.lastResult = "launched count=" + this.projectiles.size()
                + " duration=" + this.totalFlightTicks;
        return true;
    }

    public void tick() {
        if (this.state != KirbySpitState.FLYING) {
            this.lastWarning = "tick requested while state=" + this.state;
            recoverStateDesync();
            return;
        }
        if (this.kirby.isRemoved() || !this.kirby.isAlive()) {
            finishSession(KirbySpitFinishReason.KIRBY_REMOVED);
            return;
        }

        this.flightTicks++;
        List<SpitProjectile> active = activeProjectiles();
        if (active.isEmpty()) {
            finishSession(KirbySpitFinishReason.PROJECTILE_MISSING);
            return;
        }

        Set<LivingEntity> activeMobs = new HashSet<>();
        for (SpitProjectile projectile : active) {
            activeMobs.add(projectile.mob);
        }
        for (SpitProjectile projectile : active) {
            tickProjectile(projectile, activeMobs);
        }

        if (this.state != KirbySpitState.FLYING) return;
        if (this.flightTicks >= this.totalFlightTicks) {
            finishSession(KirbySpitFinishReason.TIMEOUT);
            return;
        }
        if (allProjectilesFinished()) {
            finishSession(KirbySpitFinishReason.ALL_PROJECTILES_FINISHED);
        }
    }

    public void abort(KirbySpitFinishReason reason) {
        KirbySpitFinishReason effective = reason == null
                ? KirbySpitFinishReason.GOAL_INTERRUPTED
                : reason;
        if (!isActive()) return;
        finishSession(effective);
    }

    private void tickProjectile(
            SpitProjectile projectile, Set<LivingEntity> activeMobs) {
        if (projectile.finished) return;
        LivingEntity mob = projectile.mob;
        if (mob == null || !mob.isAlive() || mob.isRemoved()) {
            finishProjectile(projectile, KirbySpitFinishReason.PROJECTILE_MISSING);
            return;
        }

        if (!this.kirby.getMouthController().refreshSpitMob(mob)) {
            this.lastResult = "lost projectile control id=" + shortId(mob);
            finishProjectile(projectile, KirbySpitFinishReason.CONTROL_LOST);
            return;
        }

        mob.setDeltaMovement(projectile.velocity);
        mob.hurtMarked = true;

        if (mob.horizontalCollision || mob.verticalCollision) {
            this.lastResult = "wall id=" + shortId(mob)
                    + " tick=" + this.flightTicks
                    + " horizontal=" + mob.horizontalCollision
                    + " vertical=" + mob.verticalCollision;
            finishProjectile(projectile, KirbySpitFinishReason.WALL_HIT);
            return;
        }

        List<LivingEntity> hits = this.kirby.level().getEntitiesOfClass(
                LivingEntity.class,
                mob.getBoundingBox().inflate(0.1D),
                entity -> entity != this.kirby
                        && entity != mob
                        && entity.isAlive()
                        && !projectile.damagedTargets.contains(entity.getUUID())
                        && !activeMobs.contains(entity));

        if (hits.isEmpty()) return;

        Vec3 push = new Vec3(
                projectile.velocity.x, 0.15D, projectile.velocity.z)
                .normalize().scale(KNOCKBACK_STRENGTH);
        for (LivingEntity hit : hits) {
            hit.hurt(hit.damageSources().mobAttack(mob), SPIT_DAMAGE);
            hit.setDeltaMovement(hit.getDeltaMovement().add(push));
            hit.hurtMarked = true;
            projectile.damagedTargets.add(hit.getUUID());
        }
        mob.setDeltaMovement(mob.getDeltaMovement().add(push));

        if (this.flightTicks >= SPIT_PIERCE_THRESHOLD) {
            this.lastResult = "late entity hit id=" + shortId(mob)
                    + " tick=" + this.flightTicks;
            finishProjectile(projectile, KirbySpitFinishReason.ENTITY_HIT);
        }
    }

    private void finishProjectile(
            SpitProjectile projectile, KirbySpitFinishReason reason) {
        if (projectile.finished) return;
        projectile.finished = true;
        projectile.finishReason = reason;
        this.lastProjectileReason = reason;
        boolean restored = this.kirby.getMouthController()
                .releaseSpitMob(projectile.mob);
        this.lastResult = this.lastResult
                + " projectile=" + shortId(projectile.mob)
                + " reason=" + reason
                + (restored ? " release=restored" : " release=already_recovered");
    }

    private void finishSession(KirbySpitFinishReason reason) {
        if (!isActive()) return;
        transitionTo(KirbySpitState.FINISHING, "finish:" + reason);

        for (SpitProjectile projectile : this.projectiles.values()) {
            if (!projectile.finished) {
                finishProjectile(projectile, reason);
            }
        }

        Collection<LivingEntity> projectileMobs = projectileMobs();
        if (reason.abortsMouth()) {
            this.kirby.getMouthController().abort(
                    projectileMobs, "spit_abort:" + reason);
        } else {
            this.kirby.getMouthController().completeSpitting(
                    "spit_completed:" + reason);
        }

        this.lastSessionReason = reason;
        this.lastResult = this.lastResult + " session=" + reason;
        this.projectiles.clear();
        this.flightTicks = 0;
        this.totalFlightTicks = 0;
        transitionTo(KirbySpitState.IDLE, "cleanup_completed");
    }

    private void recoverStateDesync() {
        Collection<LivingEntity> projectileMobs = projectileMobs();
        for (LivingEntity mob : projectileMobs) {
            this.kirby.getMouthController().releaseSpitMob(mob);
        }
        this.kirby.getMouthController().abort(
                projectileMobs, "spit_state_desync");
        this.projectiles.clear();
        this.flightTicks = 0;
        this.totalFlightTicks = 0;
        this.lastSessionReason = KirbySpitFinishReason.STATE_DESYNC;
        this.lastResult = "recovered state desync from=" + this.state;
        this.state = KirbySpitState.IDLE;
        this.lastTransition = "desync->IDLE";
    }

    private List<SpitProjectile> activeProjectiles() {
        List<SpitProjectile> active = new ArrayList<>();
        for (SpitProjectile projectile : this.projectiles.values()) {
            if (!projectile.finished
                    && projectile.mob != null
                    && projectile.mob.isAlive()
                    && !projectile.mob.isRemoved()) {
                active.add(projectile);
            }
        }
        return active;
    }

    private boolean allProjectilesFinished() {
        if (this.projectiles.isEmpty()) return false;
        for (SpitProjectile projectile : this.projectiles.values()) {
            if (!projectile.finished) return false;
        }
        return true;
    }

    private Collection<LivingEntity> projectileMobs() {
        List<LivingEntity> mobs = new ArrayList<>();
        for (SpitProjectile projectile : this.projectiles.values()) {
            if (projectile.mob != null) mobs.add(projectile.mob);
        }
        return mobs;
    }

    private Vec3 normalizedHorizontal(Vec3 plannedDirection) {
        double length = plannedDirection == null ? 0.0D : Math.sqrt(
                plannedDirection.x * plannedDirection.x
                        + plannedDirection.z * plannedDirection.z);
        if (length >= 1.0E-4D) {
            return new Vec3(
                    plannedDirection.x / length, 0.0D,
                    plannedDirection.z / length);
        }

        Vec3 view = this.kirby.getViewVector(1.0F);
        double viewLength = Math.sqrt(view.x * view.x + view.z * view.z);
        if (viewLength >= 1.0E-4D) {
            return new Vec3(
                    view.x / viewLength, 0.0D,
                    view.z / viewLength);
        }
        double yaw = Math.toRadians(this.kirby.getYRot());
        return new Vec3(-Math.sin(yaw), 0.0D, Math.cos(yaw));
    }

    private static Vec3 spreadDirection(Vec3 base, int index, int count) {
        double spreadDegrees = count <= 1
                ? 0.0D
                : -15.0D + 30.0D * index / Math.max(1, count - 1);
        double radians = Math.toRadians(spreadDegrees);
        double cos = Math.cos(radians);
        double sin = Math.sin(radians);
        return new Vec3(
                base.x * cos - base.z * sin,
                0.0D,
                base.x * sin + base.z * cos);
    }

    private void positionAtMouthExit(
            LivingEntity mob, Vec3 direction, Vec3 velocity) {
        double exitDistance = (this.kirby.getBbWidth() + mob.getBbWidth())
                * 0.5D + SPIT_EXIT_MARGIN;
        Vec3 origin = this.kirby.position().add(
                direction.x * exitDistance,
                this.kirby.getBbHeight() * 0.5D,
                direction.z * exitDistance);
        mob.setPos(origin.x, origin.y, origin.z);
        mob.horizontalCollision = false;
        mob.verticalCollision = false;
        mob.setOnGround(false);
        mob.fallDistance = 0.0F;
        mob.setDeltaMovement(velocity);
    }

    private void transitionTo(KirbySpitState next, String reason) {
        KirbySpitState previous = this.state;
        if (!KirbySpitTransitionPolicy.isAllowed(previous, next)) {
            this.lastWarning = "invalid transition " + previous + "->" + next
                    + " reason=" + reason;
        }
        this.state = next;
        this.lastTransition = previous + "->" + next + " reason=" + reason;
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        lines.add("SpitController state=" + this.state
                + " flightTicks=" + this.flightTicks + "/" + this.totalFlightTicks
                + " projectiles=" + this.projectiles.size()
                + " active=" + activeProjectiles().size()
                + " lastSessionReason=" + this.lastSessionReason
                + " lastProjectileReason=" + this.lastProjectileReason);
        lines.add("SpitController transition=" + this.lastTransition);
        lines.add("SpitController result=" + this.lastResult);

        int index = 0;
        for (SpitProjectile projectile : this.projectiles.values()) {
            LivingEntity mob = projectile.mob;
            lines.add("SpitController projectile[" + index + "] id=" + shortId(mob)
                    + " finished=" + projectile.finished
                    + " reason=" + projectile.finishReason
                    + " pos=" + mob.position()
                    + " velocity=" + mob.getDeltaMovement()
                    + " horizontalCollision=" + mob.horizontalCollision
                    + " verticalCollision=" + mob.verticalCollision
                    + " control=" + KirbyHeldMobControl.debugSummary(mob));
            index++;
        }

        if (this.lastResult.startsWith("wall ")
                && this.lastResult.contains("tick=1 ")) {
            lines.add("WARN SpitController projectile collided on its first flight tick");
        }
        if (!"none".equals(this.lastWarning)) {
            lines.add("WARN SpitController " + this.lastWarning);
        }
        lines.add("SpitController thought=" + thought());
    }

    private String thought() {
        return switch (this.state) {
            case IDLE -> "no active spit session";
            case STARTING -> "transferring mouth contents into projectile control";
            case FLYING -> "owning all scripted projectile movement and collision";
            case FINISHING -> "restoring every projectile through one terminal path";
        };
    }

    private static String shortId(LivingEntity mob) {
        return mob == null
                ? "null"
                : mob.getUUID().toString().substring(0, 8);
    }

    private static final class SpitProjectile {
        private final LivingEntity mob;
        private final Vec3 velocity;
        private final Set<UUID> damagedTargets = new HashSet<>();
        private boolean finished;
        private KirbySpitFinishReason finishReason = KirbySpitFinishReason.NONE;

        private SpitProjectile(LivingEntity mob, Vec3 velocity) {
            this.mob = mob;
            this.velocity = velocity;
        }
    }
}
