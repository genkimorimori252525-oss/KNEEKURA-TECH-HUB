package com.example.kirby_mod.entity.ai.target;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.ai.KirbyInhaleEligibility;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** Observation-only target scanner. It never changes navigation, Goals, or entity state. */
public final class KirbyTargetScanner implements KirbyDebugInfoProvider {

    private static final int SCAN_INTERVAL_TICKS = 5;
    private static final int NORMAL_TTL_TICKS = 15;
    private static final int ATTACKER_TTL_TICKS = 60;
    private static final double SCAN_RANGE = 35.0D;

    private final KirbyEntity kirby;
    private final KirbyTargetMemory memory = new KirbyTargetMemory();
    private int scannedEntityCount;

    public KirbyTargetScanner(KirbyEntity kirby) {
        this.kirby = kirby;
    }

    public void tick() {
        if (kirby.level().isClientSide || kirby.tickCount % SCAN_INTERVAL_TICKS != 0) return;
        int scanTick = kirby.tickCount;
        AABB box = kirby.getBoundingBox().inflate(SCAN_RANGE);
        List<LivingEntity> nearby = kirby.level().getEntitiesOfClass(
                LivingEntity.class, box, entity -> entity != kirby && entity.isAlive());
        scannedEntityCount = nearby.size();

        Set<UUID> held = new HashSet<>();
        for (LivingEntity entity : kirby.getHeldMobs()) held.add(entity.getUUID());

        Map<String, Draft> uniqueDrafts = new HashMap<>();
        LivingEntity recentAttacker = kirby.getLastHurtByMob();
        int attackerTick = kirby.getLastHurtByMobTimestamp();
        int attackerAge = scanTick - attackerTick;
        if (recentAttacker != null && recentAttacker.isAlive()
                && !held.contains(recentAttacker.getUUID())
                && attackerAge >= 0 && attackerAge <= ATTACKER_TTL_TICKS) {
            double distance = kirby.distanceTo(recentAttacker);
            addDraft(uniqueDrafts, new Draft(KirbyTargetKind.THREAT, recentAttacker,
                    200.0D + (ATTACKER_TTL_TICKS - attackerAge) * 0.25D - distance,
                    attackerTick, ATTACKER_TTL_TICKS, "recent_attacker"));
        }

        for (LivingEntity entity : nearby) {
            double distance = kirby.distanceTo(entity);
            boolean ally = isAlly(entity);
            boolean heldByKirby = held.contains(entity.getUUID());
            if (ally) {
                addDraft(uniqueDrafts, new Draft(KirbyTargetKind.ALLY, entity,
                        60.0D - distance, scanTick, NORMAL_TTL_TICKS, allyReason(entity)));
            }
            if (entity instanceof Enemy && !heldByKirby) {
                addDraft(uniqueDrafts, new Draft(KirbyTargetKind.THREAT, entity,
                        100.0D - distance, scanTick, NORMAL_TTL_TICKS, "enemy_marker"));
            }
            if (!ally && !heldByKirby && KirbyInhaleEligibility.canInhale(entity)) {
                addDraft(uniqueDrafts, new Draft(KirbyTargetKind.PREY, entity,
                        80.0D - distance, scanTick, NORMAL_TTL_TICKS, "inhale_eligible"));
            }
            if (entity instanceof Player player && KirbyInterestRules.isTempting(player)) {
                addDraft(uniqueDrafts, new Draft(KirbyTargetKind.INTEREST, entity,
                        70.0D - distance, scanTick, NORMAL_TTL_TICKS, "tempt_item"));
            }
        }

        EnumMap<KirbyTargetKind, Integer> counts = new EnumMap<>(KirbyTargetKind.class);
        EnumMap<KirbyTargetKind, Draft> best = new EnumMap<>(KirbyTargetKind.class);
        for (Draft draft : uniqueDrafts.values()) {
            counts.merge(draft.kind(), 1, Integer::sum);
            Draft current = best.get(draft.kind());
            if (current == null || isBetter(draft, current)) best.put(draft.kind(), draft);
        }

        List<KirbyTargetObservation> observations = new ArrayList<>();
        Map<UUID, KirbyTargetVisibility> visibilityCache = new HashMap<>();
        for (Draft draft : best.values()) {
            LivingEntity entity = draft.entity();
            KirbyTargetVisibility visibility = visibilityCache.computeIfAbsent(entity.getUUID(), ignored ->
                    kirby.hasLineOfSight(entity)
                            ? KirbyTargetVisibility.CLEAR
                            : KirbyTargetVisibility.BLOCKED);
            observations.add(toObservation(draft, visibility));
        }

        BlockPos destination = kirby.getPendingHighTarget();
        if (destination != null) {
            double x = destination.getX() + 0.5D;
            double y = destination.getY() + 0.5D;
            double z = destination.getZ() + 0.5D;
            double distance = Math.sqrt(kirby.distanceToSqr(x, y, z));
            String dimension = kirby.level().dimension().location().toString();
            observations.add(new KirbyTargetObservation(KirbyTargetKind.DESTINATION,
                    dimension + ":" + destination.toShortString(), "block", x, y, z, distance,
                    KirbyTargetVisibility.UNKNOWN, 50.0D - distance, scanTick,
                    NORMAL_TTL_TICKS, "pending_high_target"));
            counts.put(KirbyTargetKind.DESTINATION, 1);
        }
        memory.observeScan(scanTick, observations, counts);
    }

    public KirbyTargetMemory getMemory() {
        return memory;
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        int scanTick = memory.getLastScanTick();
        lines.add("TargetScanner: mode=OBSERVE scanTick=" + scanTick
                + " interval=" + SCAN_INTERVAL_TICKS
                + " range=" + fmt(SCAN_RANGE)
                + " scanned=" + scannedEntityCount);
        for (KirbyTargetKind kind : KirbyTargetKind.values()) {
            KirbyTargetObservation target = memory.get(kind).orElse(null);
            if (target == null) {
                lines.add("Target kind=" + kind + " target=none candidates="
                        + memory.getCandidateCount(kind));
                continue;
            }
            lines.add("Target kind=" + kind
                    + " target=" + target.targetKey()
                    + " type=" + target.typeKey()
                    + " distance=" + fmt(target.distance())
                    + " los=" + target.visibility()
                    + " score=" + fmt(target.score())
                    + " age=" + Math.max(0, scanTick - target.seenTick())
                    + " candidates=" + memory.getCandidateCount(kind)
                    + " reason=" + target.reason());
        }
        for (String warning : memory.getWarnings()) {
            lines.add("WARN TargetScanner " + warning);
        }
        lines.add("TargetScanner thought=" + thought());
    }

    private String thought() {
        KirbyTargetObservation threat = memory.get(KirbyTargetKind.THREAT).orElse(null);
        if (threat != null) return "watching_threat:" + threat.typeKey();
        KirbyTargetObservation interest = memory.get(KirbyTargetKind.INTEREST).orElse(null);
        if (interest != null) return "watching_interest:" + interest.typeKey();
        KirbyTargetObservation prey = memory.get(KirbyTargetKind.PREY).orElse(null);
        if (prey != null) return "observing_prey:" + prey.typeKey();
        KirbyTargetObservation destination = memory.get(KirbyTargetKind.DESTINATION).orElse(null);
        if (destination != null) return "remembering_destination";
        return "no_actionable_target";
    }

    private boolean isAlly(LivingEntity entity) {
        return kirby.isAlliedTo(entity)
                || entity instanceof TamableAnimal tamable && tamable.isTame();
    }

    private String allyReason(LivingEntity entity) {
        return kirby.isAlliedTo(entity) ? "allied" : "tamed";
    }

    private void addDraft(Map<String, Draft> drafts, Draft candidate) {
        String key = candidate.kind() + ":" + candidate.entity().getUUID();
        Draft current = drafts.get(key);
        if (current == null || isBetter(candidate, current)) drafts.put(key, candidate);
    }

    private boolean isBetter(Draft candidate, Draft current) {
        int score = Double.compare(candidate.score(), current.score());
        if (score != 0) return score > 0;
        int distance = Double.compare(kirby.distanceTo(candidate.entity()),
                kirby.distanceTo(current.entity()));
        if (distance != 0) return distance < 0;
        return candidate.entity().getUUID().toString()
                .compareTo(current.entity().getUUID().toString()) < 0;
    }

    private KirbyTargetObservation toObservation(Draft draft, KirbyTargetVisibility visibility) {
        LivingEntity entity = draft.entity();
        ResourceLocation type = BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType());
        return new KirbyTargetObservation(draft.kind(), entity.getUUID().toString(),
                type == null ? "unknown" : type.toString(),
                entity.getX(), entity.getY(), entity.getZ(), kirby.distanceTo(entity), visibility,
                draft.score(), draft.seenTick(), draft.ttlTicks(), draft.reason());
    }

    private static String fmt(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }

    private record Draft(
            KirbyTargetKind kind,
            LivingEntity entity,
            double score,
            int seenTick,
            int ttlTicks,
            String reason) {}
}
