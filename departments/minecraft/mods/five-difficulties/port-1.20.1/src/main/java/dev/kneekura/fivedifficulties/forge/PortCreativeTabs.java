package dev.kneekura.fivedifficulties.forge;

import net.minecraft.world.item.CreativeModeTabs;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Preserves X1 ItemHomingAmulet's old CreativeTabs.tabCombat placement. */
@Mod.EventBusSubscriber(
        modid = FiveDifficultiesPort.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.MOD
)
public final class PortCreativeTabs {
    private PortCreativeTabs() {}

    @SubscribeEvent
    public static void buildContents(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.COMBAT) {
            event.accept(PortRegistries.HOMING_AMULET.get());
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) {
            event.accept(PortRegistries.SAKUYA_WATCH.get());
            event.accept(PortRegistries.SAKUYA_STOPWATCH.get());
        }
    }
}
