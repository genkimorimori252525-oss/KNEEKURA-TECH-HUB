package dev.kneekura.fivedifficulties.forge.crafting;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraftforge.network.NetworkHooks;

/**
 * Port of X1 {@code BlockDanmakuCraftingTable}: metadata 0 (danmaku) and 1 (laser) become two blocks.
 * Hardness 1.5, resistance 1.0, wood sound, light 15; right-click opens its crafting menu.
 */
public class DanmakuCraftingTableBlock extends Block {
    private final boolean laser;

    public DanmakuCraftingTableBlock(boolean laser) {
        super(Properties.of().strength(1.5F, 1.0F).sound(SoundType.WOOD).lightLevel(s -> 15));
        this.laser = laser;
    }

    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand,
                                 BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (player instanceof ServerPlayer sp) {
            ContainerLevelAccess access = ContainerLevelAccess.create(level, pos);
            NetworkHooks.openScreen(sp, new SimpleMenuProvider((id, inv, p) -> new DanmakuCraftingMenu(
                    laser ? PortRegistries.LASER_CRAFTING_MENU.get() : PortRegistries.DANMAKU_CRAFTING_MENU.get(),
                    id, inv, access, laser),
                    Component.translatable(laser ? "laserCrafting.name" : "danmakuCrafting.name")), pos);
        }
        return InteractionResult.CONSUME;
    }
}
