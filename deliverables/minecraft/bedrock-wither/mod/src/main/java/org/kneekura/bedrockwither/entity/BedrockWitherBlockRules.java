package org.kneekura.bedrockwither.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Bedrock Wither block-destruction eligibility boundary.
 *
 * Current BDS exposes canDestroy(Block, WitherAttackType), proving that block
 * eligibility is conceptually separate from explosion resistance and that the
 * attack category is part of the native decision.
 */
public final class BedrockWitherBlockRules {
    private BedrockWitherBlockRules() {
    }

    public static boolean canDestroy(
            BlockGetter level,
            BlockPos pos,
            BlockState state,
            BedrockWitherAttackType attackType
    ) {
        if (state.isAir()) {
            return false;
        }

        // Minecraft Wiki's retained 2025-11 Bedrock description distinguishes
        // charge from blue-skull explosions: charge cannot break obsidian.
        // Do not silently apply that exception to the projectile category.
        if (attackType == BedrockWitherAttackType.CHARGE && state.is(Blocks.OBSIDIAN)) {
            return false;
        }

        // Current dangerous-skull observation excludes waterlogged/liquid blocks.
        // Keep the shared exclusion conservative until per-attack differences are
        // recovered from the current BDS body.
        if (!state.getFluidState().isEmpty()) {
            return false;
        }

        if (state.getDestroySpeed(level, pos) < 0.0F) {
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

        return switch (attackType) {
            case CHARGE, HURT_EXPLOSION, PROJECTILE -> true;
        };
    }
}
