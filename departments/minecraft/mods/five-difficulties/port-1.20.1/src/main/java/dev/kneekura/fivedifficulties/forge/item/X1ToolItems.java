package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.X1Config;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.DiggerItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraftforge.common.TierSortingRegistry;

/** Ports of the X1 tool-like items (P16h). */
public final class X1ToolItems {
    private X1ToolItems() {}

    /**
     * ItemBuddhaStoneBowl (仏の御石の鉢, stone, glint): digs everything at 4 and harvests like a stone pickaxe;
     * X1 never wears it (hits and digs both skip the damage).
     */
    public static final class BuddhaStoneBowl extends DiggerItem {
        public BuddhaStoneBowl(Properties p) {
            super(4.0F, -2.8F, Tiers.STONE, BlockTags.MINEABLE_WITH_PICKAXE, p);
        }

        @Override
        public float getDestroySpeed(ItemStack stack, BlockState state) {
            return 4F;
        }

        @Override
        public boolean isCorrectToolForDrops(ItemStack stack, BlockState state) {
            return state.is(BlockTags.MINEABLE_WITH_PICKAXE) && TierSortingRegistry.isCorrectTierForDrops(Tiers.STONE, state);
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
            return true;
        }

        @Override
        public boolean mineBlock(ItemStack stack, Level level, BlockState state, BlockPos pos, LivingEntity miner) {
            return true;
        }

        @Override
        public boolean isFoil(ItemStack stack) {
            return true;
        }
    }

    /**
     * ItemByoukiheiyuMamori (病気平癒守, stack 16): after 24 ticks clears every effect and gives Regeneration IV for
     * 3 s; nothing happens while hurt. A creative click works at once as well.
     */
    public static final class ByoukiheiyuMamori extends Item {
        public ByoukiheiyuMamori(Properties p) {
            super(p.stacksTo(16));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (player.getAbilities().instabuild) cure(stack, level, player);
            player.startUsingItem(hand);
            return InteractionResultHolder.consume(stack);
        }

        @Override
        public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
            if (entity instanceof Player player) cure(stack, level, player);
            return stack;
        }

        static void cure(ItemStack stack, Level level, Player player) {
            if (player.hurtTime > 0) return;
            player.removeAllEffects();
            if (!level.isClientSide) player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 3 * 20, 3));
            if (!player.getAbilities().instabuild) stack.shrink(1);
        }

        @Override
        public int getUseDuration(ItemStack stack) {
            return 24;
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return UseAnim.BOW;
        }
    }

    /**
     * ItemKabenuke (壁抜けの鑿, durability 122, config "Can Use Wall-Passing Chisel"): used on a block face, walks
     * up to 16 blocks into the wall and puts the player in the first two-high air gap (or one-high with air
     * below, a block lower); bedrock stops it.
     */
    public static final class Kabenuke extends Item {
        public Kabenuke(Properties p) {
            super(p.stacksTo(1).durability(122));
        }

        @Override
        public InteractionResult onItemUseFirst(ItemStack stack, UseOnContext context) {
            if (!X1Config.canUseWallPassingChisel()) return InteractionResult.PASS;
            Level level = context.getLevel();
            if (!(context.getPlayer() instanceof ServerPlayer player) || level.isClientSide) return InteractionResult.PASS;
            Direction face = context.getClickedFace();
            BlockPos.MutableBlockPos at = context.getClickedPos().mutable();
            for (int i = 0; i < 16; i++) {
                if (level.isEmptyBlock(at)) {
                    if (level.isEmptyBlock(at.above())) {
                        teleport(level, player, stack, at.getX() + 0.5D, at.getY(), at.getZ() + 0.5D);
                        return InteractionResult.PASS;
                    } else if (level.isEmptyBlock(at.below())) {
                        teleport(level, player, stack, at.getX() + 0.5D, at.getY() - 1.0D, at.getZ() + 0.5D);
                        return InteractionResult.PASS;
                    }
                }
                if (level.getBlockState(at).is(Blocks.BEDROCK)) return InteractionResult.PASS;
                at.move(face.getOpposite());
            }
            return InteractionResult.PASS;
        }

        private static void teleport(Level level, ServerPlayer player, ItemStack stack, double x, double y, double z) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS,
                    0.5F, 1.0F);
            player.setPos(x, y, z); // X1 sets posX..Z directly, then setPlayerLocation
            player.setDeltaMovement(0.0D, 0.0D, 0.0D);
            player.connection.teleport(x, y, z, player.getYRot(), player.getXRot());
            stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(player.getUsedItemHand()));
        }
    }

    /**
     * ItemHisyaku (船幽霊の柄杓, durability 60): two items, full and empty, swapped by a sneak click. The full dipper
     * pours a water source where it points (even into a solid block there, X1's {@code isBlockSolid} check),
     * costing 2; the nether only fizzes. The empty one removes the water source it points at and stays empty.
     */
    public static final class Hisyaku extends Item {
        private final boolean empty;

        public Hisyaku(Properties p, boolean empty) {
            super(p.stacksTo(1).durability(60));
            this.empty = empty;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (player.isShiftKeyDown()) {
                Item other = empty ? PortRegistries.SHIP_GHOST_DIPPER.get() : PortRegistries.SHIP_GHOST_DIPPER_EMPTY.get();
                ItemStack swapped = new ItemStack(other);
                swapped.setDamageValue(stack.getDamageValue());
                return InteractionResultHolder.success(swapped);
            }
            BlockHitResult hit = getPlayerPOVHitResult(level, player, empty ? ClipContext.Fluid.SOURCE_ONLY : ClipContext.Fluid.NONE);
            if (empty) {
                if (hit.getType() == HitResult.Type.BLOCK) {
                    BlockPos pos = hit.getBlockPos();
                    if (level.getFluidState(pos).is(FluidTags.WATER) && level.getFluidState(pos).isSource()) {
                        level.setBlockAndUpdate(pos, Blocks.AIR.defaultBlockState());
                    }
                }
                return InteractionResultHolder.pass(stack);
            }
            BlockPos pos;
            if (hit.getType() != HitResult.Type.BLOCK) {
                pos = BlockPos.containing((int) (player.getX() - 0.5D), (int) (player.getY() + 0.5D), (int) (player.getZ() - 0.5D));
            } else {
                pos = hit.getBlockPos().relative(hit.getDirection());
            }
            BlockState state = level.getBlockState(pos);
            if (level.isEmptyBlock(pos) || state.isSolid() || state.is(Blocks.WATER)) {
                if (level.dimensionType().ultraWarm()) {
                    level.playSound(null, pos, SoundEvents.FIRE_EXTINGUISH, SoundSource.BLOCKS, 0.5F,
                            2.6F + (level.random.nextFloat() - level.random.nextFloat()) * 0.8F);
                } else {
                    level.setBlockAndUpdate(pos, Blocks.WATER.defaultBlockState());
                    stack.hurtAndBreak(2, player, p -> p.broadcastBreakEvent(hand));
                }
            }
            return InteractionResultHolder.pass(stack);
        }
    }
}
