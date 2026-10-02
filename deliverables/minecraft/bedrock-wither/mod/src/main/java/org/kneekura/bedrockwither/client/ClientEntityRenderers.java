package org.kneekura.bedrockwither.client;

import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.renderer.entity.EntityRenderers;
import net.minecraft.client.renderer.entity.WitherSkullRenderer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.registry.ModEntities;

@Mod.EventBusSubscriber(
        modid = BedrockWitherMod.MOD_ID,
        value = Dist.CLIENT,
        bus = Mod.EventBusSubscriber.Bus.MOD
)
public final class ClientEntityRenderers {
    private ClientEntityRenderers() {
    }

    @SubscribeEvent
    public static void registerLayerDefinitions(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(
                BedrockWitherModel.LAYER_LOCATION,
                () -> BedrockWitherModel.createBodyLayer(CubeDeformation.NONE)
        );
        event.registerLayerDefinition(
                BedrockWitherModel.ARMOR_LAYER_LOCATION,
                () -> BedrockWitherModel.createBodyLayer(new CubeDeformation(2.0F))
        );
    }

    @SubscribeEvent
    public static void register(EntityRenderersEvent.RegisterRenderers event) {
        EntityRenderers.register(ModEntities.BEDROCK_WITHER.get(), BedrockWitherRenderer::new);

        // The projectile geometry is compatible with Java's skull renderer; server
        // physics and dangerous/normal behavior remain owned by our custom entity.
        EntityRenderers.register(ModEntities.BEDROCK_WITHER_SKULL.get(), WitherSkullRenderer::new);
    }
}
