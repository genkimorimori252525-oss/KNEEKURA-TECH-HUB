package dev.kneekura.fivedifficulties.forge.block;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import javax.annotation.Nullable;

/**
 * Port of X1 {@code BlockDivineSpirit} (小神霊), metadata 0..7 flattened into one block per colour: red, blue,
 * green, yellow, purple, aqua, orange, white. Glass material, hardness 0.1, resistance 2000, snow sounds, light 8,
 * no collision (the outline stays a full block), not opaque, drops itself. X1's block renderer draws nothing;
 * the visible part is the tile-entity renderer (a glowing, bobbing billboard). The tile entity holds no data.
 */
public class DivineSpiritBlock extends BaseEntityBlock {
    public static final String[] COLORS = {"red", "blue", "green", "yellow", "purple", "aqua", "orange", "white"};
    private final int color;

    public DivineSpiritBlock(int color) {
        super(Properties.of().strength(0.1F, 2000.0F).sound(SoundType.SNOW).lightLevel(s -> 8).noCollission().noOcclusion());
        this.color = color;
    }

    public int color() { return color; }

    @Override
    public RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    @Override
    public VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return Shapes.empty();
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new DivineSpiritBlockEntity(pos, state);
    }

    /** TileEntityDivineSpirit: everything in it is commented out. */
    public static class DivineSpiritBlockEntity extends BlockEntity {
        public DivineSpiritBlockEntity(BlockPos pos, BlockState state) {
            super(PortRegistries.DIVINE_SPIRIT_BLOCK_ENTITY.get(), pos, state);
        }
    }
}
