package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.ai.target.KirbyTargetKind;
import com.example.kirby_mod.entity.ai.target.KirbyTargetObservation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

/**
 * Converts observation-only THREAT memory into Minecraft's canonical Mob target.
 *
 * <p>This goal selects a target but never performs a melee attack. Flight,
 * inhaling and spitting can share {@link KirbyEntity#getTarget()} without
 * independently scanning the world.</p>
 */
public final class KirbyThreatTargetGoal extends Goal implements KirbyDebugInfoProvider {

    private static final double TARGET_RANGE = 35.0D;

    private final KirbyEntity kirby;
    @Nullable private LivingEntity candidate;
    @Nullable private LivingEntity assignedTarget;
    private boolean active;
    private String lastReason = "waiting_for_threat";

    public KirbyThreatTargetGoal(KirbyEntity kirby) {
        this.kirby = kirby;
        this.setFlags(EnumSet.of(Flag.TARGET));
    }

    @Override
    public boolean canUse() {
        this.candidate = resolveRememberedThreat();
        this.lastReason = this.candidate == null
                ? "no_valid_threat"
                : "threat_available";
        return this.candidate != null;
    }

    @Override
    public boolean canContinueToUse() {
        this.candidate = resolveRememberedThreat();
        if (this.candidate == null) {
            this.lastReason = "threat_lost";
            return false;
        }
        return true;
    }

    @Override
    public void start() {
        this.active = true;
        assignCandidate("target_started");
    }

    @Override
    public void tick() {
        assignCandidate("target_refreshed");
    }

    @Override
    public void stop() {
        if (this.assignedTarget != null
                && this.kirby.getTarget() == this.assignedTarget) {
            this.kirby.setTarget(null);
        }
        this.active = false;
        this.candidate = null;
        this.assignedTarget = null;
        if (!"threat_lost".equals(this.lastReason)) {
            this.lastReason = "target_stopped";
        }
    }

    private void assignCandidate(String reason) {
        LivingEntity next = this.candidate;
        if (!isValidThreat(next)) return;
        if (this.kirby.getTarget() != next) {
            this.kirby.setTarget(next);
        }
        this.assignedTarget = next;
        this.lastReason = reason;
    }

    @Nullable
    private LivingEntity resolveRememberedThreat() {
        KirbyTargetObservation observation = this.kirby.getTargetMemory()
                .get(KirbyTargetKind.THREAT).orElse(null);
        if (observation == null
                || !(this.kirby.level() instanceof ServerLevel serverLevel)) {
            return null;
        }
        try {
            Entity entity = serverLevel.getEntity(
                    UUID.fromString(observation.targetKey()));
            return entity instanceof LivingEntity living && isValidThreat(living)
                    ? living
                    : null;
        } catch (IllegalArgumentException ignored) {
            this.lastReason = "invalid_threat_uuid";
            return null;
        }
    }

    private boolean isValidThreat(@Nullable LivingEntity target) {
        return target != null
                && target != this.kirby
                && target.isAlive()
                && !target.isRemoved()
                && target.level() == this.kirby.level()
                && !this.kirby.getHeldMobs().contains(target)
                && !this.kirby.isAlliedTo(target)
                && this.kirby.canAttack(target)
                && this.kirby.distanceTo(target) <= TARGET_RANGE;
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        LivingEntity target = this.kirby.getTarget();
        lines.add("ThreatTargetGoal active=" + this.active
                + " target=" + (target == null
                        ? "none"
                        : target.getUUID().toString().substring(0, 8))
                + " type=" + (target == null ? "none" : target.getType())
                + " distance=" + (target == null
                        ? "none"
                        : String.format(Locale.ROOT, "%.2f",
                                this.kirby.distanceTo(target)))
                + " reason=" + this.lastReason);
        lines.add("ThreatTargetGoal thought=" + (target == null
                ? "waiting for scanner to identify a threat"
                : "publishing one canonical combat target"));
    }
}
