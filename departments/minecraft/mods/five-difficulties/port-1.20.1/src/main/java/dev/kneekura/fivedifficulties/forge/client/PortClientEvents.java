package dev.kneekura.fivedifficulties.forge.client;

import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(
        modid = FiveDifficultiesPort.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.MOD,
        value = Dist.CLIENT
)
public final class PortClientEvents {
    private PortClientEvents() {}

    @SubscribeEvent
    public static void registerEntityRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(
                PortRegistries.HOMING_AMULET_PROJECTILE.get(),
                HomingAmuletRenderer::new
        );
        event.registerEntityRenderer(
                PortRegistries.SAKUYA_TIME_CONTROLLER.get(),
                SakuyaTimeControllerRenderer::new
        );
    }

    @SubscribeEvent
    public static void registerLayerDefinitions(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(
                SakuyaTimeControllerModel.LAYER_LOCATION,
                SakuyaTimeControllerModel::createBodyLayer
        );
    }
}
