package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.timestop.TimeDomainMode;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.core.x1.SakuyaWatchContract;
import dev.kneekura.fivedifficulties.forge.timestop.SakuyaTimeStopRuntime;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

public final class SakuyaStopWatchItem extends Item {
    public SakuyaStopWatchItem(Properties properties) {
        super(properties.stacksTo(1));
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);

        if (!level.isClientSide && level instanceof ServerLevel serverLevel) {
            if (SakuyaTimeStopRuntime.startX1(
                    serverLevel,
                    player,
                    TimeDomainMode.FULL_STOP,
                    SakuyaWatchContract.STOPWATCH_PROCESSING_TICKS,
                    SakuyaControllerKind.STOPWATCH
            ) != null) {
                SakuyaWatchItem.playX1Click(serverLevel, player);
                if (!player.getAbilities().instabuild) {
                    stack.shrink(1);
                }
            }
        }

        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }
}
