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
        if (event.getTabKey() == CreativeModeTabs.FOOD_AND_DRINKS) { // P16a small items
            event.accept(PortRegistries.HEAVENLY_PEACH.get());
            event.accept(PortRegistries.SWALLOW_COWRIE_SHELL.get());
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) { // P16a small items
            event.accept(PortRegistries.CLOSED_THIRD_EYE.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16a small items
            event.accept(PortRegistries.TENGU_FAN.get());
            event.accept(PortRegistries.ONBASHIRA.get());
        }
        if (event.getTabKey() == CreativeModeTabs.INGREDIENTS) { // P16a small items
            event.accept(PortRegistries.HOURAI_PEARL_RED.get());
            event.accept(PortRegistries.HOURAI_PEARL_BLUE.get());
            event.accept(PortRegistries.HOURAI_PEARL_GREEN.get());
            event.accept(PortRegistries.HOURAI_PEARL_YELLOW.get());
            event.accept(PortRegistries.HOURAI_PEARL_PURPLE.get());
            event.accept(PortRegistries.HOURAI_PEARL_AQUA.get());
            event.accept(PortRegistries.HOURAI_PEARL_ORANGE.get());
        }
        // X1 getSubItems lists pearls 0..6 only: the white pearl is in no tab.
        if (event.getTabKey() == CreativeModeTabs.COMBAT) {
            event.accept(PortRegistries.HOMING_AMULET.get());
            event.accept(PortRegistries.DIFFUSION_AMULET.get());
            event.accept(PortRegistries.DRAGON_NECK_JEWEL_ITEM.get());
            event.accept(PortRegistries.MINI_HAKKERO_ITEM.get());
            event.accept(PortRegistries.NUCLEAR_CONTROL_ROD.get());
            event.accept(PortRegistries.HAKUREI_MIKO_STICK.get());
            event.accept(PortRegistries.WIND_MIKO_STICK.get());
        }
        if (event.getTabKey() == CreativeModeTabs.INGREDIENTS) { // X1 CreativeTabs.tabMaterials
            PortRegistries.SHOT_ITEMS.forEach(item -> event.accept(item.get()));
            PortRegistries.LASER_ITEMS.forEach(item -> event.accept(item.get()));
            event.accept(PortRegistries.SHOT_MATERIAL.get());
            event.accept(PortRegistries.POWER_ITEM_SMALL.get());
            event.accept(PortRegistries.POWER_ITEM_BIG.get());
            event.accept(PortRegistries.POINT_ITEM.get());
            event.accept(PortRegistries.BOMB_ITEM.get());
            event.accept(PortRegistries.EXTEND_ITEM.get());
        }
        if (event.getTabKey() == CreativeModeTabs.FUNCTIONAL_BLOCKS) { // X1 tabDecorations
            event.accept(PortRegistries.DANMAKU_CRAFTING_TABLE_ITEM.get());
            event.accept(PortRegistries.LASER_CRAFTING_TABLE_ITEM.get());
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) { // X1 tabMisc for the gaps
            event.accept(PortRegistries.GAP.get());
            event.accept(PortRegistries.GAP_FOLDING_UMBRELLA.get());
            event.accept(PortRegistries.SAKUYA_WATCH.get());
            event.accept(PortRegistries.SAKUYA_STOPWATCH.get());
        }
    }
}
