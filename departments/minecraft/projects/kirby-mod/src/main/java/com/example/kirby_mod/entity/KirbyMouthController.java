package com.example.kirby_mod.entity;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.ai.KirbyHeldMobControl;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/**
 * Single authority for Mob ownership and state transitions inside Kirby's mouth.
 * AI goals request actions; this controller applies and recovers the actual state.
 */
public final class KirbyMouthController implements KirbyDebugInfoProvider {

    public enum CaptureResult {
        NONE,
        CAPTURED,
        ALREADY_HELD,
        CAPACITY_REJECTED,
        CONTROL_REJECTED,
        INVALID_PHASE
    }

    private static final int MAX_CONTROLLED_PER_TICK = KirbyEntity.MAX_SMALL_HOLD;

    private final KirbyEntity kirby;
    private KirbyMouthPhase lastKnownPhase = KirbyMouthPhase.EMPTY;
    private String lastTransition = "init";
    private String lastTransitionReason = "entity_created";
    private int lastTransitionTick;
    private CaptureResult lastCaptureResult = CaptureResult.NONE;
    private String lastWarning = "none";
    private int lastControlledCount;

    public KirbyMouthController(KirbyEntity kirby) {
        this.kirby = kirby;
    }

    public KirbyMouthPhase getPhase() {
        return KirbyMouthPhase.fromCombatState(this.kirby.getCombatState());
    }

    public void beginInhalePrep(String reason) {
        transitionTo(KirbyMouthPhase.INHALE_PREP, reason);
    }

    public void beginInhaling(String reason) {
        transitionTo(KirbyMouthPhase.INHALING, reason);
    }

    public void finishInhale(String reason) {
        transitionTo(KirbyMouthPhase.afterInhale(this.kirby.getHeldMobCount()), reason);
    }

    public void finishInhaleEnd(String reason) {
        transitionTo(KirbyMouthPhase.EMPTY, reason);
    }

    public void interruptInhale(String reason) {
        KirbyMouthPhase next = this.kirby.getHeldMobCount() > 0
                ? KirbyMouthPhase.HOLDING
                : KirbyMouthPhase.EMPTY;
        transitionTo(next, reason);
    }

    public CaptureResult tryCapture(LivingEntity mob) {
        if (getPhase() != KirbyMouthPhase.INHALING) {
            return recordCapture(CaptureResult.INVALID_PHASE);
        }
        if (mob == null || this.kirby.getHeldMobs().contains(mob)) {
            return recordCapture(CaptureResult.ALREADY_HELD);
        }
        KirbySize incoming = KirbyMouthFullness.animationSize(KirbyMouthFullness.capturePoints(mob));
        if (!this.kirby.canCaptureMore(incoming)) {
            return recordCapture(CaptureResult.CAPACITY_REJECTED);
        }

        // Apply containment before publishing the held UUID, so clients never hide a still-burning Mob.
        if (!KirbyHeldMobControl.capture(mob, this.kirby.getUUID())) {
            this.lastWarning = "capture rejected by active foreign owner id=" + shortId(mob);
            return recordCapture(CaptureResult.CONTROL_REJECTED);
        }
        if (!this.kirby.storeHeldMob(mob)) {
            return recordCapture(CaptureResult.ALREADY_HELD);
        }
        return recordCapture(CaptureResult.CAPTURED);
    }

    public void beginSwallowing(int sizeTransitionTicks, String reason) {
        transitionTo(KirbyMouthPhase.SWALLOWING, reason);
        this.kirby.beginMouthFullnessTransition(0.0D, sizeTransitionTicks);
    }

    public void completeSwallowing(String reason) {
        for (LivingEntity mob : this.kirby.getHeldMobs()) {
            mob.discard();
        }
        this.kirby.clearStoredHeldMobs();
        finishSizeTransition();
        transitionTo(KirbyMouthPhase.EMPTY, reason);
    }

    public void beginSpitting(int sizeTransitionTicks, String reason) {
        transitionTo(KirbyMouthPhase.SPITTING, reason);
        this.kirby.beginMouthFullnessTransition(0.0D, sizeTransitionTicks);
    }

    public boolean detachForSpit(LivingEntity mob) {
        if (getPhase() != KirbyMouthPhase.SPITTING || mob == null) return false;
        if (!KirbyHeldMobControl.beginSpit(mob, this.kirby.getUUID())) {
            this.lastWarning = "spit rejected by Mob control id=" + shortId(mob);
            return false;
        }
        this.kirby.removeStoredHeldMob(mob);
        return true;
    }

    public boolean refreshSpitMob(LivingEntity mob) {
        return KirbyHeldMobControl.refreshSpit(mob, this.kirby.getUUID());
    }

    public boolean releaseSpitMob(LivingEntity mob) {
        return mob != null && KirbyHeldMobControl.release(mob, this.kirby.getUUID());
    }

    public void completeSpitting(String reason) {
        for (LivingEntity mob : this.kirby.getHeldMobs()) {
            KirbyHeldMobControl.release(mob, this.kirby.getUUID());
        }
        this.kirby.clearStoredHeldMobs();
        finishSizeTransition();
        transitionTo(KirbyMouthPhase.EMPTY, reason);
    }

    public void abort(Collection<LivingEntity> extraControlledMobs, String reason) {
        List<LivingEntity> heldMobs = this.kirby.getHeldMobs();
        for (LivingEntity mob : heldMobs) {
            KirbyHeldMobControl.release(mob, this.kirby.getUUID());
        }
        if (extraControlledMobs != null) {
            for (LivingEntity mob : extraControlledMobs) {
                if (mob != null) KirbyHeldMobControl.release(mob, this.kirby.getUUID());
            }
        }
        this.kirby.clearStoredHeldMobs();
        this.kirby.cancelMouthFullnessTransition();
        this.kirby.setKirbySize(KirbySize.NORMAL);
        transitionTo(KirbyMouthPhase.EMPTY, reason);
    }

    public void recoverEmpty(String reason) {
        abort(List.of(), reason);
    }

    /** Reasserts at most five contained Mob invariants without any world scan. */
    public void tick() {
        KirbyMouthPhase phase = getPhase();
        if (phase != this.lastKnownPhase) {
            this.lastWarning = "external mouth transition " + this.lastKnownPhase + "->" + phase;
            recordTransition(this.lastKnownPhase, phase, "external_state_write");
        }

        List<LivingEntity> heldMobs = this.kirby.getHeldMobs();
        this.lastControlledCount = 0;
        if (heldMobs.isEmpty()) {
            if (phase == KirbyMouthPhase.HOLDING || phase == KirbyMouthPhase.SWALLOWING) {
                this.lastWarning = "phase=" + phase + " requires contents but list is empty";
            }
            return;
        }
        if (!phase.sealsContents()) {
            this.lastWarning = "orphaned contents in phase=" + phase;
            recoverEmpty("self_heal_orphaned_contents");
            return;
        }

        Vec3 mouth = this.kirby.position().add(0.0D, this.kirby.getBbHeight() * 0.5D, 0.0D);
        List<LivingEntity> lostControl = new ArrayList<>();
        for (LivingEntity mob : heldMobs) {
            if (this.lastControlledCount >= MAX_CONTROLLED_PER_TICK) {
                this.lastWarning = "held Mob count exceeded bounded tick budget";
                break;
            }
            if (!KirbyHeldMobControl.hold(mob, this.kirby.getUUID())) {
                lostControl.add(mob);
                this.lastWarning = "lost Mob ownership id=" + shortId(mob);
                continue;
            }
            mob.setPos(mouth.x, mouth.y, mouth.z);
            mob.setDeltaMovement(Vec3.ZERO);
            mob.fallDistance = 0.0F;
            this.lastControlledCount++;
        }
        for (LivingEntity mob : lostControl) {
            this.kirby.removeStoredHeldMob(mob);
        }
    }

    public void resetTracking(String reason) {
        this.lastKnownPhase = getPhase();
        this.lastTransition = "reset->" + this.lastKnownPhase;
        this.lastTransitionReason = reason;
        this.lastTransitionTick = this.kirby.tickCount;
        this.lastWarning = "none";
    }

    private CaptureResult recordCapture(CaptureResult result) {
        this.lastCaptureResult = result;
        return result;
    }

    private void finishSizeTransition() {
        this.kirby.finishMouthFullnessTransition();
        this.kirby.setKirbySize(KirbySize.NORMAL);
    }

    private void transitionTo(KirbyMouthPhase next, String reason) {
        KirbyMouthPhase previous = getPhase();
        int heldMobCount = this.kirby.getStoredHeldMobCountForDebug();
        if (!KirbyMouthTransitionPolicy.isAllowed(previous, next, heldMobCount)) {
            this.lastWarning = "invalid transition " + previous + "->" + next
                    + " contents=" + heldMobCount;
        }
        this.kirby.setCombatState(next.toCombatState());
        recordTransition(previous, next, reason);
    }

    private void recordTransition(KirbyMouthPhase previous, KirbyMouthPhase next, String reason) {
        this.lastKnownPhase = next;
        this.lastTransition = previous + "->" + next;
        this.lastTransitionReason = reason;
        this.lastTransitionTick = this.kirby.tickCount;
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        List<LivingEntity> heldMobs = this.kirby.getHeldMobs();
        lines.add("MouthState: phase=" + getPhase()
                + " contents=" + heldMobs.size()
                + " controlledThisTick=" + this.lastControlledCount + "/" + MAX_CONTROLLED_PER_TICK
                + " lastCapture=" + this.lastCaptureResult
                + " transition=" + this.lastTransition
                + " reason=" + this.lastTransitionReason
                + " age=" + Math.max(0, this.kirby.tickCount - this.lastTransitionTick));
        for (int i = 0; i < heldMobs.size() && i < MAX_CONTROLLED_PER_TICK; i++) {
            LivingEntity mob = heldMobs.get(i);
            lines.add("MouthState held[" + i + "] id=" + shortId(mob)
                    + " type=" + mob.getType()
                    + " onFire=" + mob.isOnFire()
                    + " control=" + KirbyHeldMobControl.debugSummary(mob));
            if (mob.isOnFire()) {
                lines.add("WARN MouthState held Mob is still burning id=" + shortId(mob));
            }
            if (!KirbyHeldMobControl.isControlledBy(mob, this.kirby.getUUID())) {
                lines.add("WARN MouthState held Mob has no matching owner id=" + shortId(mob));
            }
        }
        if (!"none".equals(this.lastWarning)) {
            lines.add("WARN MouthState " + this.lastWarning);
        }
        lines.add("MouthState thought=" + mouthThought());
    }

    private String mouthThought() {
        switch (getPhase()) {
            case INHALE_PREP: return "opening mouth for capture";
            case INHALING: return this.kirby.getStoredHeldMobCountForDebug() > 0
                    ? "keeping captured prey sealed while inhaling"
                    : "searching for prey to seal";
            case INHALE_END: return "closing empty mouth";
            case HOLDING: return "maintaining bounded contained Mob invariants";
            case SWALLOWING: return "consuming sealed contents";
            case SPITTING: return "transferring contents to projectile control";
            case EMPTY:
            default: return "mouth is empty";
        }
    }

    private static String shortId(LivingEntity mob) {
        return mob.getUUID().toString().substring(0, 8);
    }
}
