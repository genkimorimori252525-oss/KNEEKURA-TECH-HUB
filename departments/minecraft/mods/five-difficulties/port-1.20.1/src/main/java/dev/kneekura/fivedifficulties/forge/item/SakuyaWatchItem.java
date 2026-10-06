package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.timestop.TimeDomainMode;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.core.x1.SakuyaWatchContract;
import dev.kneekura.fivedifficulties.forge.timestop.SakuyaTimeStopRuntime;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;

public final class SakuyaWatchItem extends Item {
    private static final String TAG_MODE = "X1SakuyaWatchMode";

    public SakuyaWatchItem(Properties properties) {
        super(properties.stacksTo(1));
    }

    public static int getX1Mode(ItemStack stack) {
        return stack.getOrCreateTag().getInt(TAG_MODE) == 1 ? 1 : 0;
    }

    public static void setX1Mode(ItemStack stack, int mode) {
        if (mode != 0 && mode != 1) throw new IllegalArgumentException("X1 Watch mode");
        if (mode == 0) {
            if (stack.hasTag()) stack.getTag().remove(TAG_MODE);
        } else {
            stack.getOrCreateTag().putInt(TAG_MODE, 1);
        }
    }

    public static void toggleX1Mode(ItemStack stack) {
        setX1Mode(stack, SakuyaWatchContract.toggleModeDamage(getX1Mode(stack)));
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);

        // X1 uses sneak-right-click + even player age as a simple debounce.
        if (player.isShiftKeyDown() && player.tickCount % 2 == 0) {
            if (!level.isClientSide) {
                toggleX1Mode(stack);
            }
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
        }

        if (player.getAbilities().instabuild) {
            if (!level.isClientSide && level instanceof ServerLevel serverLevel) {
                activate(serverLevel, player, stack, true);
            }
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
        }

        if (player.getFoodData().getFoodLevel() <= 0) {
            return InteractionResultHolder.fail(stack);
        }

        player.startUsingItem(hand);
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return SakuyaWatchContract.resolveMode(getX1Mode(stack)).maxUseDurationTicks();
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.BOW;
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity living) {
        if (!level.isClientSide && level instanceof ServerLevel serverLevel && living instanceof Player player) {
            activate(serverLevel, player, stack, false);
        }
        return stack;
    }

    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity living, int timeLeft) {
        if (level.isClientSide || !(level instanceof ServerLevel serverLevel) || !(living instanceof Player player)) {
            return;
        }
        int used = getUseDuration(stack) - timeLeft;
        if (used >= getUseDuration(stack)) {
            activate(serverLevel, player, stack, false);
        }
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return getX1Mode(stack) == 1 || super.isFoil(stack);
    }

    private static boolean activate(ServerLevel level, Player player, ItemStack stack, boolean creativePersistent) {
        int mode = getX1Mode(stack);
        TimeDomainMode timeMode = mode == 0 ? TimeDomainMode.HALF_SPEED : TimeDomainMode.FULL_STOP;

        int duration;
        SakuyaControllerKind kind;
        if (creativePersistent) {
            duration = -1;
            kind = SakuyaControllerKind.WATCH_PERSISTENT;
        } else {
            duration = mode == 0
                    ? SakuyaWatchContract.LIMITED_HALF_PROCESSING_TICKS
                    : SakuyaWatchContract.LIMITED_STOP_PROCESSING_TICKS;
            kind = SakuyaControllerKind.WATCH_LIMITED;
        }

        if (SakuyaTimeStopRuntime.startX1(level, player, timeMode, duration, kind) == null) {
            return false;
        }

        playX1Click(level, player);
        if (!creativePersistent) {
            stack.shrink(1);
        }
        return true;
    }

    static void playX1Click(ServerLevel level, Player player) {
        float pitch = 0.4F / (player.getRandom().nextFloat() * 4.0F + 0.8F);
        level.playSound(
                null,
                player.blockPosition(),
                SoundEvents.UI_BUTTON_CLICK.value(),
                SoundSource.PLAYERS,
                0.5F,
                pitch
        );
    }
}
