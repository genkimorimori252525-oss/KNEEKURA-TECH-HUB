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
        if (event.getTabKey() == CreativeModeTabs.FUNCTIONAL_BLOCKS) { // P18a divine spirit (X1 tabDecorations)
            event.accept(PortRegistries.DIVINE_SPIRIT_RED_ITEM.get());
            event.accept(PortRegistries.DIVINE_SPIRIT_BLUE_ITEM.get());
            event.accept(PortRegistries.DIVINE_SPIRIT_GREEN_ITEM.get());
            event.accept(PortRegistries.DIVINE_SPIRIT_YELLOW_ITEM.get());
            event.accept(PortRegistries.DIVINE_SPIRIT_PURPLE_ITEM.get());
            event.accept(PortRegistries.DIVINE_SPIRIT_AQUA_ITEM.get());
            event.accept(PortRegistries.DIVINE_SPIRIT_ORANGE_ITEM.get());
            event.accept(PortRegistries.DIVINE_SPIRIT_WHITE_ITEM.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P18a
            event.accept(PortRegistries.TOYOSATOMIMI_SWORD.get());
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) { // P17j mallet and doll
            event.accept(PortRegistries.MIRACLE_MALLET.get());
            event.accept(PortRegistries.CURSED_DECOY_DOLL_ITEM.get());
        }
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) { // P17j
            event.accept(PortRegistries.DANMAKU_CREEPER_SPAWN_EGG.get());
        }
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) { // P17i
            event.accept(PortRegistries.RINNOSUKE_SPAWN_EGG.get());
        }
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) { // P17g
            event.accept(PortRegistries.SAKUYA_SPAWN_EGG.get());
            event.accept(PortRegistries.SANAE_SPAWN_EGG.get());
        }
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) { // P17f
            event.accept(PortRegistries.TOZIKO_SPAWN_EGG.get());
        }
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) { // P17e
            event.accept(PortRegistries.WRIGGLE_SPAWN_EGG.get());
        }
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) { // P17d
            event.accept(PortRegistries.CIRNO_SPAWN_EGG.get());
        }
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) { // P17c
            event.accept(PortRegistries.RUMIA_SPAWN_EGG.get());
        }
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) { // P17b
            event.accept(PortRegistries.TH_PHANTOM_SPAWN_EGG.get());
        }
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) { // P17a
            event.accept(PortRegistries.TH_FAIRY_SPAWN_EGG.get());
            event.accept(PortRegistries.SUNFLOWER_FAIRY_SPAWN_EGG.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16o broom
            event.accept(PortRegistries.MARISA_BROOM.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16n kinkakuzi
            event.accept(PortRegistries.KINKAKUZI.get());
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) { // P16m eye orb branch
            event.accept(PortRegistries.THIRD_EYE.get());
            event.accept(PortRegistries.BLOODTHIRSTY_YIN_YANG_ORB.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16m eye orb branch
            event.accept(PortRegistries.HOURAI_JEWELED_BRANCH.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16l hisou sword
            event.accept(PortRegistries.HISOU_SWORD.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16k parasol
            event.accept(PortRegistries.YUUKA_PARASOL.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16j silver knives
            event.accept(PortRegistries.SILVER_KNIFE_BLUE.get());
            event.accept(PortRegistries.SILVER_KNIFE_RED.get());
            event.accept(PortRegistries.SILVER_KNIFE_GREEN.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16i armour
            event.accept(PortRegistries.FIRE_RAT_ROBE.get());
            event.accept(PortRegistries.MARISA_HAT.get());
            event.accept(PortRegistries.KAPPA_CAP.get());
            event.accept(PortRegistries.SUWAKO_HAT.get());
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) { // P16h tools
            event.accept(PortRegistries.BUDDHA_STONE_BOWL.get());
            event.accept(PortRegistries.BYOUKIHEIYU_MAMORI.get());
            event.accept(PortRegistries.WALL_PASSING_CHISEL.get());
            event.accept(PortRegistries.SHIP_GHOST_DIPPER.get());
            event.accept(PortRegistries.SHIP_GHOST_DIPPER_EMPTY.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16g swords
            event.accept(PortRegistries.ICICLE_SWORD.get());
            event.accept(PortRegistries.HAKUROUKEN.get());
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) { // P16f pendulum
            event.accept(PortRegistries.NAZRIN_PENDULUM.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16e aja red stone
            event.accept(PortRegistries.AJA_RED_STONE.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16d effect items
            event.accept(PortRegistries.SPIRITUAL_STRIKE_TALISMAN.get());
        }
        if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES) { // P16d effect items
            event.accept(PortRegistries.SORCERER_SUTRA_SCROLL.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16c shot items
            event.accept(PortRegistries.SOUL_TORCH.get());
            event.accept(PortRegistries.YUYUKO_FAN.get());
            event.accept(PortRegistries.KAPPA_WATER_PISTOL.get());
        }
        if (event.getTabKey() == CreativeModeTabs.FOOD_AND_DRINKS) { // P16c shot items
            event.accept(PortRegistries.IBUKI_GOURD.get());
        }
        if (event.getTabKey() == CreativeModeTabs.COMBAT) { // P16b weapons
            event.accept(PortRegistries.SPEAR_THE_GUNGNIR.get());
            event.accept(PortRegistries.LAEVATEINN.get());
            event.accept(PortRegistries.ROUKANKEN.get());
            event.accept(PortRegistries.ROUKANKEN_SENPUUZIN.get());
            event.accept(PortRegistries.DEATH_SCYTHE.get());
            event.accept(PortRegistries.REMORSE_ROD.get());
        }
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
