package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.entity.KirbyEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.HashSet;
import java.util.Set;

/** Finds deterministic, collision-safe landing positions without controlling flight timing. */
public final class KirbyFlightLandingPlanner {

    private static final int[] DESTINATION_RADII = {0, 2, 4};
    private static final int[] COMBAT_RADII = {4, 6, 8};
    private static final int ANGLE_STEPS = 12;
    private static final int SEARCH_UP = 4;
    private static final int SEARCH_DOWN = 16;

    private final KirbyEntity kirby;

    public KirbyFlightLandingPlanner(KirbyEntity kirby) {
        this.kirby = kirby;
    }

    public Result findDestination(BlockPos focus, int maximumLandingY) {
        return find(focus, null, DESTINATION_RADII, false, maximumLandingY);
    }

    public Result findCombat(LivingEntity threat, int maximumLandingY) {
        return find(threat.blockPosition(), threat, COMBAT_RADII, true, maximumLandingY);
    }

    public boolean remainsValid(BlockPos position, @Nullable LivingEntity threat) {
        return isSafeLanding(position) && (threat == null || hasLineOfSight(position, threat));
    }

    private Result find(
            BlockPos focus,
            @Nullable LivingEntity threat,
            int[] radii,
            boolean requireLineOfSight,
            int maximumLandingY) {
        BlockPos best = null;
        double bestScore = -Double.MAX_VALUE;
        int safeCandidates = 0;
        Set<Long> visited = new HashSet<>();
        for (int radius : radii) {
            int steps = radius == 0 ? 1 : ANGLE_STEPS;
            for (int step = 0; step < steps; step++) {
                double angle = Math.PI * 2.0D * step / steps;
                int x = focus.getX() + (int) Math.round(Math.cos(angle) * radius);
                int z = focus.getZ() + (int) Math.round(Math.sin(angle) * radius);
                BlockPos candidate = findFeetPosition(x, z, focus.getY(), maximumLandingY);
                if (candidate == null || !visited.add(candidate.asLong())) continue;
                safeCandidates++;
                boolean clear = threat == null || hasLineOfSight(candidate, threat);
                if (requireLineOfSight && !clear) continue;
                double focusDistance = Math.sqrt(candidate.distSqr(focus));
                double currentDistance = Math.sqrt(candidate.distSqr(kirby.blockPosition()));
                double heightPenalty = Math.abs(candidate.getY() - focus.getY());
                double score = 100.0D - focusDistance * 4.0D
                        - heightPenalty * 1.5D - currentDistance * 0.1D
                        + (clear ? 25.0D : 0.0D);
                if (best == null || score > bestScore
                        || score == bestScore && candidate.asLong() < best.asLong()) {
                    best = candidate.immutable();
                    bestScore = score;
                }
            }
        }
        if (best == null) {
            return new Result(null, safeCandidates, 0.0D, false,
                    requireLineOfSight ? "no_safe_visible_landing" : "no_safe_landing");
        }
        return new Result(best, safeCandidates, bestScore,
                threat == null || hasLineOfSight(best, threat), "selected");
    }

    @Nullable
    private BlockPos findFeetPosition(int x, int z, int focusY, int maximumLandingY) {
        int top = Math.min(Math.min(kirby.level().getMaxBuildHeight() - 2,
                focusY + SEARCH_UP), maximumLandingY);
        int bottom = Math.max(kirby.level().getMinBuildHeight() + 1, focusY - SEARCH_DOWN);
        for (int y = top; y >= bottom; y--) {
            BlockPos feet = new BlockPos(x, y, z);
            if (isSafeLanding(feet)) return feet;
        }
        return null;
    }

    private boolean isSafeLanding(BlockPos feet) {
        if (!kirby.level().hasChunkAt(feet)
                || !kirby.level().getWorldBorder().isWithinBounds(feet)) return false;
        BlockPos support = feet.below();
        BlockPos head = feet.above();
        BlockState supportState = kirby.level().getBlockState(support);
        BlockState feetState = kirby.level().getBlockState(feet);
        BlockState headState = kirby.level().getBlockState(head);
        if (!supportState.isFaceSturdy(kirby.level(), support, Direction.UP)) return false;
        if (!feetState.getCollisionShape(kirby.level(), feet).isEmpty()
                || !headState.getCollisionShape(kirby.level(), head).isEmpty()) return false;
        if (!kirby.level().getFluidState(support).isEmpty()
                || !kirby.level().getFluidState(feet).isEmpty()
                || !kirby.level().getFluidState(head).isEmpty()) return false;
        if (isKnownHazard(supportState) || isKnownHazard(feetState) || isKnownHazard(headState)) {
            return false;
        }
        AABB current = kirby.getBoundingBox();
        double dx = feet.getX() + 0.5D - kirby.getX();
        double dy = feet.getY() - kirby.getY();
        double dz = feet.getZ() + 0.5D - kirby.getZ();
        return kirby.level().noCollision(kirby, current.move(dx, dy, dz).deflate(0.01D));
    }

    private boolean hasLineOfSight(BlockPos feet, LivingEntity threat) {
        Vec3 start = new Vec3(feet.getX() + 0.5D,
                feet.getY() + kirby.getBbHeight() * 0.7D, feet.getZ() + 0.5D);
        Vec3 end = threat.position().add(0.0D, threat.getBbHeight() * 0.5D, 0.0D);
        return kirby.level().clip(new ClipContext(start, end,
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, kirby)).getType()
                == HitResult.Type.MISS;
    }

    private static boolean isKnownHazard(BlockState state) {
        return state.is(Blocks.FIRE)
                || state.is(Blocks.SOUL_FIRE)
                || state.is(Blocks.CACTUS)
                || state.is(Blocks.MAGMA_BLOCK)
                || state.is(Blocks.CAMPFIRE)
                || state.is(Blocks.SOUL_CAMPFIRE)
                || state.is(Blocks.SWEET_BERRY_BUSH)
                || state.is(Blocks.POWDER_SNOW)
                || state.is(Blocks.WITHER_ROSE);
    }

    public record Result(
            @Nullable BlockPos position,
            int candidateCount,
            double score,
            boolean lineOfSight,
            String reason) {

        public boolean found() {
            return position != null;
        }
    }
}
