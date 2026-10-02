package org.kneekura.bedrockwither.client;

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
    public static void register(EntityRenderersEvent.RegisterRenderers event) {
        // Boss renderer is intentionally non-authoritative/invisible until the
        // three-head Bedrock model is implemented. It prevents missing-renderer
        // crashes without pretending visual parity.
        EntityRenderers.register(ModEntities.BEDROCK_WITHER.get(), BedrockWitherPlaceholderRenderer::new);

        // The projectile geometry is compatible with Java's skull renderer; server
        // physics and dangerous/normal behavior remain owned by our custom entity.
        EntityRenderers.register(ModEntities.BEDROCK_WITHER_SKULL.get(), WitherSkullRenderer::new);
    }
}
