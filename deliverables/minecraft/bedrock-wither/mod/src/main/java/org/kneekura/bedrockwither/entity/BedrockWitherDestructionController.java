package org.kneekura.bedrockwither.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

public final class BedrockWitherDestructionController {
    private final BedrockWitherEntity owner;

    public BedrockWitherDestructionController(BedrockWitherEntity owner) {
        this.owner = owner;
    }

    /**
     * Mirrors the current BDS _destroyBlocks(..., range, WitherAttackType) shape.
     *
     * Historical Bedrock passes range=1 for the hurt-reaction break and range=2
     * for charge. With the official 1x3 collision box and inclusive integer block
     * iteration, those become exactly 4x6x4 and 6x8x6, matching current Bedrock
     * runtime observation.
     */
    public DestructionResult destroyAroundSelf(int range, BedrockWitherAttackType attackType) {
        if (range < 0) {
            throw new IllegalArgumentException("range must be >= 0");
        }

        AABB volume = owner.getBoundingBox().inflate(range);
        int visited = candidateBlockCount(volume);

        if (!owner.level().getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)) {
            return new DestructionResult(visited, 0, visited);
        }

        int minX = Mth.floor(volume.minX);
        int minY = Mth.floor(volume.minY);
        int minZ = Mth.floor(volume.minZ);
        int maxX = Mth.floor(volume.maxX);
        int maxY = Mth.floor(volume.maxY);
        int maxZ = Mth.floor(volume.maxZ);

        int destroyed = 0;
        int skipped = 0;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();

        for (int x = minX; x <= maxX; x++) {
            for (int y = minY; y <= maxY; y++) {
                for (int z = minZ; z <= maxZ; z++) {
                    cursor.set(x, y, z);
                    BlockState state = owner.level().getBlockState(cursor);
                    if (!canDestroy(state, cursor, attackType)) {
                        skipped++;
                        continue;
                    }

                    if (owner.level().destroyBlock(cursor, true, owner)) {
                        destroyed++;
                    } else {
                        skipped++;
                    }
                }
            }
        }

        return new DestructionResult(visited, destroyed, skipped);
    }

    public int candidateBlockCount(int range) {
        if (range < 0) {
            throw new IllegalArgumentException("range must be >= 0");
        }
        return candidateBlockCount(owner.getBoundingBox().inflate(range));
    }

    private static int candidateBlockCount(AABB volume) {
        int width = Mth.floor(volume.maxX) - Mth.floor(volume.minX) + 1;
        int height = Mth.floor(volume.maxY) - Mth.floor(volume.minY) + 1;
        int depth = Mth.floor(volume.maxZ) - Mth.floor(volume.minZ) + 1;
        return width * height * depth;
    }

    private boolean canDestroy(
            BlockState state,
            BlockPos pos,
            BedrockWitherAttackType attackType
    ) {
        if (state.isAir()) {
            return false;
        }

        // Current Bedrock observations: liquids/waterlogged blocks and a bounded
        // set of unbreakable/system blocks survive these destructive Wither attacks.
        if (!state.getFluidState().isEmpty()) {
            return false;
        }
        if (state.getDestroySpeed(owner.level(), pos) < 0.0F) {
            return false;
        }

        if (state.is(Blocks.REINFORCED_DEEPSLATE)
                || state.is(Blocks.MOVING_PISTON)
                || state.is(Blocks.BARRIER)
                || state.is(Blocks.END_PORTAL)
                || state.is(Blocks.END_GATEWAY)
                || state.is(Blocks.END_PORTAL_FRAME)
                || state.is(Blocks.COMMAND_BLOCK)
                || state.is(Blocks.REPEATING_COMMAND_BLOCK)
                || state.is(Blocks.CHAIN_COMMAND_BLOCK)
                || state.is(Blocks.STRUCTURE_BLOCK)
                || state.is(Blocks.STRUCTURE_VOID)
                || state.is(Blocks.JIGSAW)
                || state.is(Blocks.LIGHT)) {
            return false;
        }

        // Current BDS canDestroy receives WitherAttackType, which proves that the
        // native predicate may differ by Charge/HurtExplosion/Projectile.
        // We intentionally keep the currently corroborated shared exclusions here
        // and do not invent attack-type differences without stronger evidence.
        return attackType == BedrockWitherAttackType.CHARGE
                || attackType == BedrockWitherAttackType.HURT_EXPLOSION;
    }

    public record DestructionResult(int visited, int destroyed, int skipped) {
    }
}
