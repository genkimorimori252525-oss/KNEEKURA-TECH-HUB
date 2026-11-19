package com.example.kirby_mod.debug;

import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.KirbySize;
import com.example.kirby_mod.entity.KirbyWalkSoundSequence;
import com.example.kirby_mod.entity.ai.KirbyAiAction;
import com.example.kirby_mod.entity.ai.KirbyAiBrain;
import com.example.kirby_mod.entity.ai.KirbyDecisionLane;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

public final class KirbyTelemetryFormatter {

    private static final int MAX_LINES = 60;

    private KirbyTelemetryFormatter() {}

    public static List<String> format(KirbyEntity kirby) {
        List<String> lines = new ArrayList<>();
        int storedHeldBeforePrune = kirby.getStoredHeldMobCountForDebug();
        List<LivingEntity> heldMobs = kirby.getHeldMobs();
        int storedHeldAfterPrune = kirby.getStoredHeldMobCountForDebug();

        lines.add("[TLM] Kirby " + shortId(kirby.getUUID()));
        lines.add("dim=" + kirby.level().dimension().location()
                + " pos=" + pos(kirby.position())
                + " tick=" + kirby.tickCount);
        lines.add("health=" + fmt(kirby.getHealth()) + "/" + fmt(kirby.getMaxHealth())
                + " alive=" + kirby.isAlive()
                + " removed=" + kirby.isRemoved());
        lines.add("motion=" + vec(kirby.getDeltaMovement())
                + " onGround=" + kirby.onGround()
                + " fall=" + fmt(kirby.fallDistance));
        lines.add("state combat=" + kirby.getCombatState()
                + " flight=" + kirby.getFlightState()
                + " size=" + kirby.getKirbySize()
                + " aiMode=" + kirby.getAiBrain().getMode()
                + " locomotion=" + kirby.getAiBrain().getLocomotionMode()
                + " actionLatch=" + kirby.getOneShotAnimationLatchForDebug()
                + " hurtFace=" + kirby.getHurtFace());
        lines.add("animation=" + kirby.getDebugAnimationName());
        KirbyWalkSoundSequence walkSound = kirby.getWalkSoundSequenceForDebug();
        lines.add("walkSound moving=" + walkSound.isMoving()
                + " running=" + walkSound.isRunning()
                + " idleTicks=" + walkSound.getIdleTicks()
                + " phase=" + fmt(walkSound.getStepPhaseSeconds())
                + " interval=" + fmt(walkSound.getStepIntervalSeconds())
                + " speedScale=" + fmt(walkSound.getSpeedScale())
                + " next=" + walkSound.getNextSoundName()
                + " last=" + walkSound.getLastSoundName()
                + " pitch=" + fmt(walkSound.getLastPitch()));
        BlockPos highTarget = kirby.getPendingHighTarget();
        lines.add("target pendingHigh=" + (highTarget == null ? "none" : blockPos(highTarget)));

        lines.add("[Held]");
        lines.add("stored=" + storedHeldAfterPrune
                + " live=" + heldMobs.size()
                + " prunedThisSample=" + Math.max(0, storedHeldBeforePrune - storedHeldAfterPrune)
                + " presentationRevision=" + kirby.getHeldMobPresentationRevisionForDebug()
                + " fullness=" + fmt(kirby.getMouthFullness())
                + " scaleTarget=" + fmt(kirby.getMouthRenderScale())
                + " transition=" + kirby.getMouthFullnessTransitionForDebug()
                + " maxSmall=" + KirbyEntity.MAX_SMALL_HOLD);
        if (heldMobs.isEmpty()) {
            lines.add("held[0]=none");
        } else {
            for (int i = 0; i < heldMobs.size(); i++) {
                LivingEntity mob = heldMobs.get(i);
                lines.add("held[" + i + "] " + mobSummary(kirby, mob));
            }
        }

        lines.add("[Thoughts]");
        List<String> thoughts = kirby.getDebugThoughtLines();
        if (thoughts.isEmpty()) {
            lines.add("thought=idle scan");
        } else {
            lines.addAll(thoughts);
        }

        appendWarnings(lines, kirby, heldMobs, storedHeldBeforePrune, storedHeldAfterPrune);
        return trim(lines);
    }

    public static List<String> noKirby(String reason) {
        List<String> lines = new ArrayList<>();
        lines.add("[TLM] Kirby unavailable");
        lines.add("WARN " + reason);
        lines.add("thought=waiting for nearest Kirby");
        return lines;
    }

    private static void appendWarnings(List<String> lines, KirbyEntity kirby, List<LivingEntity> heldMobs,
                                       int storedHeldBeforePrune, int storedHeldAfterPrune) {
        List<String> warnings = new ArrayList<>();
        CombatState combatState = kirby.getCombatState();
        if (storedHeldBeforePrune != storedHeldAfterPrune) {
            warnings.add("WARN stale held mob entries were pruned");
        }
        if (combatState.isHolding() && combatState != CombatState.KEEP_SPIT && heldMobs.isEmpty()) {
            warnings.add("WARN holding state has no live held mobs");
        }
        if (kirby.getKirbySize() != KirbySize.NORMAL
                && combatState != CombatState.KEEP_SPIT && heldMobs.isEmpty()) {
            warnings.add("WARN non-normal size without live held mobs");
        }
        if (combatState.usesLowProfileHitbox()
                && (kirby.getKirbySize() != KirbySize.NORMAL || !heldMobs.isEmpty())) {
            warnings.add("WARN crouch/slide active outside empty normal form");
        }
        if ((combatState.isCrouching() || combatState == CombatState.SLIDE_START
                || combatState == CombatState.SLIDING) && !kirby.onGround()) {
            warnings.add("WARN ground-only crouch/slide state is airborne");
        }
        if (kirby.getAiBrain().getMode() != KirbyAiBrain.Mode.OBSERVE) {
            for (KirbyDecisionLane lane : KirbyDecisionLane.values()) {
                if (!kirby.getAiBrain().isLaneEnforced(lane)) continue;
                KirbyAiAction active = kirby.getAiBrain().getActiveAction(lane);
                KirbyAiAction recommended = kirby.getAiBrain().getLastDecision(lane).action();
                if (recommended != KirbyAiAction.IDLE && active != recommended) {
                    warnings.add("WARN AI lane mismatch lane=" + lane
                            + " active=" + active + " recommended=" + recommended);
                }
            }
        }
        for (LivingEntity mob : heldMobs) {
            if (mob.isOnFire()) {
                warnings.add("WARN held mob remains on fire id=" + shortId(mob.getUUID()));
            }
        }
        if (!warnings.isEmpty()) {
            lines.add("[Warnings]");
            lines.addAll(warnings);
        }
    }

    private static String mobSummary(KirbyEntity kirby, LivingEntity mob) {
        ResourceLocation key = BuiltInRegistries.ENTITY_TYPE.getKey(mob.getType());
        StringBuilder flags = new StringBuilder();
        flags.append("alive=").append(mob.isAlive());
        flags.append(" removed=").append(mob.isRemoved());
        flags.append(" invisible=").append(mob.isInvisible());
        flags.append(" invul=").append(mob.isInvulnerable());
        flags.append(" silent=").append(mob.isSilent());
        flags.append(" noGravity=").append(mob.isNoGravity());
        flags.append(" noPhysics=").append(mob.noPhysics);
        flags.append(" onFire=").append(mob.isOnFire());
        if (mob instanceof Mob m) {
            flags.append(" noAi=").append(m.isNoAi());
        }
        return key + " id=" + shortId(mob.getUUID())
                + " hp=" + fmt(mob.getHealth()) + "/" + fmt(mob.getMaxHealth())
                + " mouthPoints=" + fmt(kirby.getHeldMobCapturePoints(mob))
                + " pos=" + pos(mob.position())
                + " " + flags;
    }

    private static List<String> trim(List<String> lines) {
        if (lines.size() <= MAX_LINES) return lines;
        List<String> out = new ArrayList<>(lines.subList(0, MAX_LINES - 1));
        out.add("... " + (lines.size() - out.size()) + " lines truncated");
        return out;
    }

    private static String shortId(UUID uuid) {
        String text = uuid.toString();
        return text.substring(0, 8);
    }

    private static String pos(Vec3 vec) {
        return fmt(vec.x) + "," + fmt(vec.y) + "," + fmt(vec.z);
    }

    private static String vec(Vec3 vec) {
        return fmt(vec.x) + "," + fmt(vec.y) + "," + fmt(vec.z);
    }

    private static String blockPos(BlockPos pos) {
        return pos.getX() + "," + pos.getY() + "," + pos.getZ();
    }

    private static String fmt(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }
}
