package org.kneekura.bedrockwither.client;

import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;

public final class BedrockWitherPlaceholderRenderer extends EntityRenderer<BedrockWitherEntity> {
    private static final ResourceLocation VANILLA_WITHER_TEXTURE =
            new ResourceLocation("minecraft", "textures/entity/wither/wither.png");

    public BedrockWitherPlaceholderRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public ResourceLocation getTextureLocation(BedrockWitherEntity entity) {
        return VANILLA_WITHER_TEXTURE;
    }
}
