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

    /** X1's 64-block look trace: blocks from the eyes to a far end measured from the feet, then the nearest living thing. */
    static net.minecraft.world.entity.Entity lookTarget(Level level, Player player, double range) {
        var look = player.getLookAngle();
        var from = new net.minecraft.world.phys.Vec3(player.getX(), player.getY() + player.getEyeHeight(), player.getZ());
        var to = new net.minecraft.world.phys.Vec3(player.getX() + look.x * range, player.getY() + look.y * range, player.getZ() + look.z * range);
        HitResult block = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
        if (block.getType() != HitResult.Type.MISS) to = block.getLocation();
        net.minecraft.world.entity.Entity entity = null;
        double d = 0.0D;
        for (var e : level.getEntities(player, player.getBoundingBox().expandTowards(look.scale(range)).inflate(1.0D))) {
            if (!(e instanceof LivingEntity)) continue;
            var at = dev.kneekura.fivedifficulties.forge.shot.X1Hit.intercept(e.getBoundingBox().inflate(0.3D), from, to);
            if (at.isPresent()) {
                double d1 = from.distanceTo(at.get());
                if (d1 < d || d == 0.0D) {
                    entity = e;
                    d = d1;
                }
            }
        }
        return entity;
    }

    static boolean lookHitsSomething(Level level, Player player, double range) {
        var look = player.getLookAngle();
        var from = new net.minecraft.world.phys.Vec3(player.getX(), player.getY() + player.getEyeHeight(), player.getZ());
        var to = new net.minecraft.world.phys.Vec3(player.getX() + look.x * range, player.getY() + look.y * range, player.getZ() + look.z * range);
        return level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player)).getType()
                != HitResult.Type.MISS || lookTarget(level, player, range) != null;
    }

    /**
     * ItemThirdEye (サードアイ, durability 150, mending 1 a tick): right-click reads the living thing on a 64-block
     * line; the next inventory tick reports its name, HP (in hearts) and a tame animal's owner in chat. As in X1
     * the target is kept on the item itself, shared by every holder and by both sides of an integrated server.
     */
    public static final class ThirdEye extends Item {
        private LivingEntity hitEntity = null;
        private boolean check = false;

        public ThirdEye(Properties p) {
            super(p.stacksTo(1).durability(150));
        }

        public LivingEntity pendingTarget() {
            return check ? hitEntity : null;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            var target = lookTarget(level, player, 64.0D);
            if (target != null || lookHitsSomething(level, player, 64.0D)) {
                check = true;
                hitEntity = target instanceof LivingEntity l ? l : null;
            }
            return InteractionResultHolder.pass(player.getItemInHand(hand));
        }

        @Override
        public void inventoryTick(ItemStack stack, Level level, net.minecraft.world.entity.Entity entity, int slot, boolean selected) {
            if (stack.isDamaged()) stack.setDamageValue(stack.getDamageValue() - 1);
            if (check && hitEntity != null) {
                if (entity instanceof Player player) {
                    float hp = hitEntity.getHealth() / 2F;
                    hp = (float) Math.round(hp * 100F) / 100F;
                    String strHP = " HP \uff1a " + hp + "/" + hitEntity.getMaxHealth() / 2F;
                    String name = hitEntity instanceof Player other ? other.getDisplayName().getString() : hitEntity.getName().getString();
                    if (!level.isClientSide) {
                        player.sendSystemMessage(net.minecraft.network.chat.Component.literal(name));
                        player.sendSystemMessage(net.minecraft.network.chat.Component.literal(strHP));
                    }
                    if (hitEntity instanceof net.minecraft.world.entity.TamableAnimal tame && tame.isTame() && tame.getOwner() != null
                            && !level.isClientSide) {
                        player.sendSystemMessage(net.minecraft.network.chat.Component.literal("  Owner : " + tame.getOwner().getName().getString()));
                    }
                }
                check = false;
                hitEntity = null;
            }
        }
    }

    /**
     * ItemBloodthirstyOnmyoudama (吸血の陰陽玉, durability 150, glint): hold and release to jump next to the living
     * thing on a 64-block line (2 short of it, feet snapped to a block + 0.1); 1 durability per use, and as in
     * 1.7.10 it breaks only once the damage goes past 150.
     */
    public static final class BloodthirstyOnmyoudama extends Item {
        public BloodthirstyOnmyoudama(Properties p) {
            super(p.stacksTo(1).durability(150));
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.startUsingItem(hand);
            return InteractionResultHolder.consume(player.getItemInHand(hand));
        }

        @Override
        public void releaseUsing(ItemStack stack, Level level, LivingEntity living, int timeLeft) {
            if (!(living instanceof Player player)) return;
            var entity = lookTarget(level, player, 64.0D);
            if (entity != null && player instanceof ServerPlayer mp && !level.isClientSide) {
                var eye = dev.kneekura.fivedifficulties.forge.shot.X1Danmaku.pos_Living(player);
                double tx = entity.getX() - eye.x(), ty = entity.getY() - eye.y(), tz = entity.getZ() - eye.z();
                double len = Math.sqrt(tx * tx + ty * ty + tz * tz);
                double vx = len == 0 ? 0 : tx / len, vy = len == 0 ? 0 : ty / len, vz = len == 0 ? 0 : tz / len;
                double x = player.getX() + tx - vx * 2.0D;
                double y = (int) (player.getY() + ty - vy * 2.0D + 1.0D) + 0.1D;
                double z = player.getZ() + tz - vz * 2.0D;
                player.setPos(x, y, z);
                mp.connection.teleport(x, y, z, player.getYRot(), player.getXRot());
            }
            stack.setDamageValue(stack.getDamageValue() + 1);
            if (stack.getDamageValue() > stack.getMaxDamage()) stack.shrink(1);
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return UseAnim.BOW;
        }

        @Override
        public int getUseDuration(ItemStack stack) {
            return 72000;
        }

        @Override
        public boolean isFoil(ItemStack stack) {
            return true;
        }
    }

    /**
     * ItemHouraiJeweledBranch (蓬莱の玉の枝, glint): a guard released while sneaking fires rings of rainbow pearls
     * (one ring per 3 of 32 + held ticks, capped at 72, each ring 0.2 faster and turned 9 degrees) and uses 50 of
     * its 200 "Charge"; it recovers 50 every 50 ticks. A plain release only plays the sound and uses the charge
     * (X1's forward volley was left empty). The icon shows the charge in five steps.
     */
    public static final class HouraiJeweledBranch extends Item {
        public HouraiJeweledBranch(Properties p) {
            super(p.stacksTo(1).durability(301).setNoRepair());
        }

        public static int getCharge(ItemStack stack) {
            return stack.getTag() == null ? 0 : stack.getTag().getShort("Charge");
        }

        private static void addCharge(ItemStack stack, int charge) {
            var nbt = stack.getTag();
            if (nbt == null) {
                stack.getOrCreateTag().putShort("Charge", (short) -charge);
            } else if (nbt.getShort("Charge") >= 0) {
                nbt.putShort("Charge", (short) (nbt.getShort("Charge") - charge));
            }
        }

        private static void setCharge(ItemStack stack, int charge) {
            var nbt = stack.getTag();
            if (nbt == null) stack.getOrCreateTag().putShort("Charge", (short) charge);
            else if (nbt.getShort("Charge") >= 0) nbt.putShort("Charge", (short) charge);
        }

        /** getIconFromDamage(charge): 0, ≤50, ≤100, ≤150, ≤200, more. */
        public static float iconStep(ItemStack stack) {
            int c = getCharge(stack);
            return c <= 0 ? 0 : c <= 50 ? 1 : c <= 100 ? 2 : c <= 150 ? 3 : c <= 200 ? 4 : 5;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.startUsingItem(hand);
            return InteractionResultHolder.consume(player.getItemInHand(hand));
        }

        @Override
        public void releaseUsing(ItemStack stack, Level level, LivingEntity living, int timeLeft) {
            if (!(living instanceof Player player)) return;
            int shotNum = 32 + getUseDuration(stack) - timeLeft;
            if (shotNum > 72) shotNum = 72;
            shotNum /= 3;
            if (getCharge(stack) <= 200) {
                var shot = dev.kneekura.fivedifficulties.core.x1.X1ShotData.shot(
                        dev.kneekura.fivedifficulties.core.x1.X1ShotTables.FORM_PEARL,
                        dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RAINBOW, 0.3F, 5.0F, 1, 80);
                if (player.isShiftKeyDown() && !level.isClientSide) {
                    for (int i = 0; i < shotNum; i += 3) {
                        dev.kneekura.fivedifficulties.forge.shot.X1Danmaku.createCircleShot(player, player,
                                dev.kneekura.fivedifficulties.forge.shot.X1Danmaku.pos_Living(player),
                                dev.kneekura.fivedifficulties.forge.shot.X1Danmaku.angle(player.getYRot(), player.getXRot()),
                                0.3D + (double) i * 0.2D, 2.0D, 0.03D,
                                dev.kneekura.fivedifficulties.core.math.Vec3d.ZERO, shot, shotNum, 0.2D, i * 3F);
                    }
                }
                level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.EXPERIENCE_ORB_PICKUP,
                        SoundSource.PLAYERS, 0.5F, 0.4F / (level.random.nextFloat() * 4F + 0.8F));
                addCharge(stack, -50);
            }
        }

        @Override
        public void inventoryTick(ItemStack stack, Level level, net.minecraft.world.entity.Entity entity, int slot, boolean selected) {
            if (getCharge(stack) > 0 && entity.tickCount % 50 == 0) {
                addCharge(stack, 50);
                if (getCharge(stack) < 0) setCharge(stack, 0);
            }
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return UseAnim.BLOCK;
        }

        @Override
        public int getUseDuration(ItemStack stack) {
            return 72000;
        }

        @Override
        public boolean isFoil(ItemStack stack) {
            return true;
        }

        @Override
        public int getEnchantmentValue() {
            return 0;
        }

        @Override
        public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
            return false;
        }
    }
}
