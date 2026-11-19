package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.KirbyMouthFullness;
import com.example.kirby_mod.entity.KirbyMouthController;
import com.example.kirby_mod.entity.KirbySize;
import com.example.kirby_mod.entity.ModSounds;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

public class KirbyInhaleGoal extends Goal implements KirbyDebugInfoProvider {

    private static final double DETECT_RANGE = 35.0D;
    private static final double INHALE_RANGE = 50.0D;
    private static final double INHALE_CONE_DOT = 0.7D;
    private static final double PULL_BASE = 0.4D;
    private static final double CAPTURE_MOUTH_MARGIN = 0.15D;
    private static final int PREP_TICKS = 3;
    private static final int END_TICKS = 3;
    private static final int EMPTY_INHALE_TIMEOUT = 100; // give up if no captures within 5s
    private static final int INHALE_MAX_TICKS = 252;     // 12.6s 最大継続
    private static final double KEEP_TRANSITION_RADIUS = 20.0D;
    private final KirbyEntity kirby;
    private int phaseTicks;
    private int emptyTicks;
    private int inhaleTotalTicks;
    private KirbyMouthController.CaptureResult lastCaptureResult =
            KirbyMouthController.CaptureResult.NONE;

    public KirbyInhaleGoal(KirbyEntity kirby) {
        this.kirby = kirby;
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        if (kirby.getCombatState() != CombatState.NONE) return false;
        if (kirby.getFlightState() != KirbyEntity.FlightState.GROUND) return false;
        return findClosestVanillaMob(DETECT_RANGE) != null;
    }

    @Override
    public boolean canContinueToUse() {
        return kirby.getMouthController().getPhase().isInhaleLifecycle();
    }

    @Override
    public void start() {
        kirby.getMouthController().beginInhalePrep("inhale_goal_started");
        phaseTicks = 0;
        emptyTicks = 0;
        inhaleTotalTicks = 0;
        lastCaptureResult = KirbyMouthController.CaptureResult.NONE;
        LivingEntity target = findClosestVanillaMob(DETECT_RANGE);
        if (target == null) {
            // race condition: target despawned between canUse and start
            kirby.getMouthController().finishInhaleEnd("target_lost_before_prep");
            return;
        }
        snapToTarget(target);
    }

    private void snapToTarget(LivingEntity target) {
        double dx = target.getX() - kirby.getX();
        double dz = target.getZ() - kirby.getZ();
        float yaw = (float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0);
        kirby.setYRot(yaw);
        kirby.setYHeadRot(yaw);
        kirby.setYBodyRot(yaw);
        kirby.getLookControl().setLookAt(target, 60F, 60F);
    }

    @Override
    public void tick() {
        switch (kirby.getCombatState()) {
            case INHALE_PREP:
                phaseTicks++;
                LivingEntity prepTarget = findClosestVanillaMob(DETECT_RANGE);
                if (prepTarget != null) {
                    snapToTarget(prepTarget);
                }
                if (phaseTicks >= PREP_TICKS) {
                    kirby.getMouthController().beginInhaling("inhale_prep_completed");
                    phaseTicks = 0;
                    // bacume サウンドはクライアント側 onSyncedDataUpdated で再生する
                }
                break;

            case INHALE:
                inhaleTotalTicks++;
                // 12.6 秒のハードタイムアウト
                if (inhaleTotalTicks >= INHALE_MAX_TICKS) {
                    kirby.getMouthController().finishInhale("inhale_hard_timeout");
                    phaseTicks = 0;
                    break;
                }

                Vec3 kirbyPos = kirby.position().add(0, kirby.getBbHeight() * 0.5D, 0);
                Vec3 mouthPos = captureMouthPosition(kirbyPos);
                spawnMouthParticles(kirbyPos);

                List<LivingEntity> coneMobs = findMobsInCone();
                if (coneMobs.isEmpty()) {
                    emptyTicks++;
                    if (emptyTicks >= EMPTY_INHALE_TIMEOUT) {
                        kirby.getMouthController().finishInhale("inhale_empty_timeout");
                        phaseTicks = 0;
                    }
                    break;
                }
                emptyTicks = 0;

                for (LivingEntity mob : coneMobs) {
                    Vec3 mobCenter = mob.position().add(0, mob.getBbHeight() * 0.5D, 0);
                    double dist = mobCenter.distanceTo(mouthPos);
                    if (isAtCaptureMouth(mob, mouthPos)) {
                        lastCaptureResult = consume(mob);
                        if (lastCaptureResult != KirbyMouthController.CaptureResult.CAPTURED) {
                            phaseTicks = 0;
                            kirby.getMouthController().finishInhale(
                                    "capture_stopped:" + lastCaptureResult);
                            return;
                        }
                        if (kirby.getCombatState() != CombatState.INHALE) return;
                        continue;
                    }
                    Vec3 toKirby = mouthPos.subtract(mobCenter).normalize();
                    double pull = PULL_BASE * Math.max(0, 1.0D - dist / INHALE_RANGE);
                    mob.setDeltaMovement(mob.getDeltaMovement().add(toKirby.scale(pull)));
                    mob.hurtMarked = true;
                    if (mob == coneMobs.get(0)) {
                        snapToTarget(mob);
                    }
                    spawnSuctionParticles(mobCenter, mouthPos, dist);
                }

                // 早期 KEEP_HOLDING: 既に保持中で 20 ブロック内に他 mob がいなければ即遷移
                if (kirby.getCombatState() == CombatState.INHALE
                        && kirby.getHeldMobCount() > 0
                        && !anyVanillaMobWithin(KEEP_TRANSITION_RADIUS)) {
                    kirby.getMouthController().finishInhale("no_nearby_follow_up");
                }
                break;

            case INHALE_END:
                phaseTicks++;
                if (phaseTicks >= END_TICKS) {
                    kirby.getMouthController().finishInhaleEnd("inhale_end_completed");
                }
                break;

            default:
                break;
        }
    }

    @Override
    public void stop() {
        // A committed capture remains sealed even if another goal interrupts inhaling.
        if (kirby.getMouthController().getPhase().isInhaleLifecycle()) {
            kirby.getMouthController().interruptInhale("inhale_goal_interrupted");
        }
        phaseTicks = 0;
        emptyTicks = 0;
        inhaleTotalTicks = 0;
    }

    /** mob を取り込み、サイズ・容量に応じて INHALE 継続か KEEP_HOLDING 遷移を決める。 */
    private KirbyMouthController.CaptureResult consume(LivingEntity mob) {
        KirbySize incoming = KirbyMouthFullness.animationSize(KirbyMouthFullness.capturePoints(mob));
        KirbyMouthController.CaptureResult result = kirby.getMouthController().tryCapture(mob);
        if (result != KirbyMouthController.CaptureResult.CAPTURED) return result;

        playSound(ModSounds.KIRBY_SUICOMIED.get());

        // SMALL 容量未満なら INHALE 継続。それ以外(MIDDLE/BIG/SMALL満杯)は KEEP_HOLDING へ。
        if (incoming != KirbySize.SMALL || kirby.getHeldMobCount() >= KirbyEntity.MAX_SMALL_HOLD) {
            kirby.getMouthController().finishInhale("mouth_capacity_reached");
        }
        return result;
    }

    private Vec3 captureMouthPosition(Vec3 kirbyCenter) {
        Vec3 forward = kirby.getViewVector(1.0F).normalize();
        return kirbyCenter.add(forward.scale(kirby.getBbWidth() * 0.5D));
    }

    private boolean isAtCaptureMouth(LivingEntity mob, Vec3 mouthPos) {
        return mob.getBoundingBox().inflate(CAPTURE_MOUTH_MARGIN).contains(mouthPos);
    }

    /** 半径内に取り込み済みでない vanilla mob がいるか。 */
    private boolean anyVanillaMobWithin(double radius) {
        AABB box = kirby.getBoundingBox().inflate(radius);
        List<LivingEntity> heldMobs = kirby.getHeldMobs();
        return !kirby.level().getEntitiesOfClass(LivingEntity.class, box,
                e -> e != kirby && e.isAlive() && isVanillaMob(e)
                        && !heldMobs.contains(e)).isEmpty();
    }

    private void playSound(SoundEvent evt) {
        if (kirby.level().isClientSide) return;
        kirby.level().playSound(null, kirby.getX(), kirby.getY(), kirby.getZ(),
                evt, SoundSource.NEUTRAL, 1.0F, 1.0F);
    }

    /** mob → kirby 口の間にパフ粒を散布。距離が近いほど密度高め。 */
    private void spawnSuctionParticles(Vec3 mobCenter, Vec3 kirbyPos, double dist) {
        if (!(kirby.level() instanceof ServerLevel sl)) return;
        // 距離に応じて 1〜6 個の POOF を路上にランダム配置
        int count = (int) Math.max(1, Math.min(6, Math.round(6.0D * (1.0D - dist / INHALE_RANGE))));
        for (int i = 0; i < count; i++) {
            double t = kirby.getRandom().nextDouble();
            double px = mobCenter.x + (kirbyPos.x - mobCenter.x) * t;
            double py = mobCenter.y + (kirbyPos.y - mobCenter.y) * t;
            double pz = mobCenter.z + (kirbyPos.z - mobCenter.z) * t;
            sl.sendParticles(ParticleTypes.POOF, px, py, pz, 1, 0.1, 0.1, 0.1, 0.0);
        }
        // mob 直近で吸い込まれる感を強調する追加 CLOUD
        sl.sendParticles(ParticleTypes.CLOUD, mobCenter.x, mobCenter.y, mobCenter.z,
                2, 0.2, 0.2, 0.2, 0.02);
    }

    /** kirby の口元に螺旋・渦・風リングを撒いて吸引演出を派手にする。 */
    private void spawnMouthParticles(Vec3 kirbyPos) {
        if (!(kirby.level() instanceof ServerLevel sl)) return;
        Vec3 forward = kirby.getViewVector(1.0F).normalize();
        Vec3 right = new Vec3(-forward.z, 0, forward.x).normalize();
        Vec3 mouth = kirbyPos.add(forward.scale(0.6D));
        long tick = kirby.tickCount;
        // 螺旋: tick で角度進行、左右側面+上下に粒を散らす → 口に吸い込まれる速度
        for (int i = 0; i < 4; i++) {
            double phase = (tick + i * 5) * 0.4D;
            double r = 0.4D + 0.1D * (i % 2);
            double offX = Math.cos(phase) * r;
            double offY = Math.sin(phase) * r;
            double depth = 0.4D + i * 0.25D;
            Vec3 src = kirbyPos.add(forward.scale(depth))
                    .add(right.scale(offX))
                    .add(0, offY, 0);
            Vec3 vel = mouth.subtract(src).normalize().scale(0.15D);
            sl.sendParticles(ParticleTypes.CLOUD,
                    src.x, src.y, src.z, 1, vel.x, vel.y, vel.z, 0.0D);
        }
        // 4 tick 周期で「風リング」: 前方 2.5m で 6 点のリング状に放出
        if (tick % 4 == 0) {
            for (int i = 0; i < 6; i++) {
                double angle = i * (Math.PI * 2.0D / 6.0D) + tick * 0.1D;
                double ringR = 0.8D;
                double rx = Math.cos(angle) * ringR;
                double ry = Math.sin(angle) * ringR;
                Vec3 ringSrc = kirbyPos.add(forward.scale(2.5D))
                        .add(right.scale(rx))
                        .add(0, ry, 0);
                Vec3 ringVel = mouth.subtract(ringSrc).normalize().scale(0.2D);
                sl.sendParticles(ParticleTypes.CLOUD,
                        ringSrc.x, ringSrc.y, ringSrc.z, 1,
                        ringVel.x, ringVel.y, ringVel.z, 0.0D);
            }
        }
    }

    @Nullable
    private LivingEntity findClosestVanillaMob(double range) {
        AABB box = kirby.getBoundingBox().inflate(range);
        List<LivingEntity> heldMobs = kirby.getHeldMobs();
        List<LivingEntity> candidates = kirby.level().getEntitiesOfClass(LivingEntity.class, box,
                e -> e != kirby && e.isAlive() && isVanillaMob(e)
                        && !heldMobs.contains(e)
                        && kirby.hasLineOfSight(e));
        LivingEntity closest = null;
        double bestDistSq = Double.MAX_VALUE;
        for (LivingEntity e : candidates) {
            double d = e.distanceToSqr(kirby);
            if (d < bestDistSq) {
                bestDistSq = d;
                closest = e;
            }
        }
        return closest;
    }

    private List<LivingEntity> findMobsInCone() {
        AABB box = kirby.getBoundingBox().inflate(INHALE_RANGE);
        Vec3 viewDir = kirby.getViewVector(1.0F).normalize();
        Vec3 origin = kirby.position().add(0, kirby.getBbHeight() * 0.5D, 0);
        List<LivingEntity> heldMobs = kirby.getHeldMobs();
        return kirby.level().getEntitiesOfClass(LivingEntity.class, box, e -> {
            if (e == kirby || !e.isAlive() || !isVanillaMob(e) || heldMobs.contains(e)) return false;
            Vec3 toMob = e.position().add(0, e.getBbHeight() * 0.5D, 0).subtract(origin);
            double dist = toMob.length();
            if (dist > INHALE_RANGE || dist < 1.0E-3D) return false;
            double dot = toMob.normalize().dot(viewDir);
            return dot >= INHALE_CONE_DOT;
        });
    }

    private static boolean isVanillaMob(Entity entity) {
        return KirbyInhaleEligibility.canInhale(entity);
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        CombatState state = kirby.getCombatState();
        LivingEntity target = state.isInhaling() ? findClosestVanillaMob(DETECT_RANGE) : null;
        LivingEntity coneCandidate = state == CombatState.INHALE ? findClosestConeMob() : null;
        LivingEntity oversized = findClosestOversizedMob(DETECT_RANGE);
        lines.add("InhaleGoal: state=" + state
                + " phaseTicks=" + phaseTicks
                + " emptyTicks=" + emptyTicks
                + " totalTicks=" + inhaleTotalTicks
                + " lastCapture=" + lastCaptureResult
                + " target=" + (target == null ? "none" : target.getType().toString())
                + " coneCandidate=" + (coneCandidate == null ? "none" : coneCandidate.getType().toString()));
        if (coneCandidate != null) {
            lines.add("InhaleGoal candidate=" + candidateSummary(coneCandidate));
        }
        if (oversized != null) {
            lines.add("InhaleGoal warning=oversized candidate=" + oversized.getType()
                    + " points=" + fmt(KirbyMouthFullness.capturePoints(oversized)));
        }
        lines.add("InhaleGoal thought=" + inhaleThought(state, target));
    }

    @Nullable
    private LivingEntity findClosestConeMob() {
        Vec3 kirbyPos = kirby.position().add(0, kirby.getBbHeight() * 0.5D, 0);
        LivingEntity closest = null;
        double bestDistSq = Double.MAX_VALUE;
        for (LivingEntity mob : findMobsInCone()) {
            Vec3 mobCenter = mob.position().add(0, mob.getBbHeight() * 0.5D, 0);
            double distSq = mobCenter.distanceToSqr(kirbyPos);
            if (distSq < bestDistSq) {
                bestDistSq = distSq;
                closest = mob;
            }
        }
        return closest;
    }

    @Nullable
    private LivingEntity findClosestOversizedMob(double range) {
        AABB box = kirby.getBoundingBox().inflate(range);
        LivingEntity closest = null;
        double bestDistSq = Double.MAX_VALUE;
        for (LivingEntity mob : kirby.level().getEntitiesOfClass(LivingEntity.class, box,
                e -> e != kirby && e.isAlive() && KirbyInhaleEligibility.isEligibleMob(e)
                        && !KirbyMouthFullness.fitsInMaximumMouth(e))) {
            double distSq = mob.distanceToSqr(kirby);
            if (distSq < bestDistSq) {
                bestDistSq = distSq;
                closest = mob;
            }
        }
        return closest;
    }

    private String candidateSummary(LivingEntity mob) {
        KirbySize incoming = KirbyMouthFullness.animationSize(KirbyMouthFullness.capturePoints(mob));
        Vec3 kirbyPos = kirby.position().add(0, kirby.getBbHeight() * 0.5D, 0);
        Vec3 mouthPos = captureMouthPosition(kirbyPos);
        Vec3 mobCenter = mob.position().add(0, mob.getBbHeight() * 0.5D, 0);
        return mob.getType()
                + " id=" + shortId(mob.getUUID())
                + " mouthDist=" + fmt(mobCenter.distanceTo(mouthPos))
                + " atMouth=" + isAtCaptureMouth(mob, mouthPos)
                + " incoming=" + incoming
                + " mouthPoints=" + fmt(KirbyMouthFullness.capturePoints(mob))
                + " canCapture=" + kirby.canCaptureMore(incoming)
                + " invisible=" + mob.isInvisible()
                + " invul=" + mob.isInvulnerable()
                + " silent=" + mob.isSilent()
                + " noGravity=" + mob.isNoGravity()
                + " noPhysics=" + mob.noPhysics
                + (mob instanceof Mob m ? " noAi=" + m.isNoAi() : "")
                + " control=" + KirbyHeldMobControl.debugSummary(mob);
    }

    private static String shortId(UUID uuid) {
        return uuid.toString().substring(0, 8);
    }

    private static String fmt(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }

    private String inhaleThought(CombatState state, @Nullable LivingEntity target) {
        switch (state) {
            case INHALE_PREP:
                return target == null ? "lost target during prep" : "locking mouth direction";
            case INHALE:
                if (kirby.getHeldMobCount() > 0 && !anyVanillaMobWithin(KEEP_TRANSITION_RADIUS)) {
                    return "captured prey and no nearby follow-up";
                }
                if (target == null) return "searching cone for prey";
                return "pulling target into mouth";
            case INHALE_END:
                return "ending inhale animation";
            default:
                return target == null ? "waiting for vanilla mob" : "ready to inhale nearest mob";
        }
    }
}
