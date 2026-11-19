package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;

/**
 * Records the real Forge client lifecycle boundary for G1 startup timing.
 *
 * <p>This class only exists in the dedicated KNEEKURA debug source set. Normal
 * TouhouLittleMaid builds never compile or package it.
 */
@Mod.EventBusSubscriber(
        modid = TouhouLittleMaid.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.MOD,
        value = Dist.CLIENT)
public final class KneekuraDebugForgeLifecycle {
    private KneekuraDebugForgeLifecycle() {
    }

    @SubscribeEvent
    public static void onClientSetup(FMLClientSetupEvent event) {
        KneekuraDebugClientBootstrap.markForgeInitialized();
    }
}
