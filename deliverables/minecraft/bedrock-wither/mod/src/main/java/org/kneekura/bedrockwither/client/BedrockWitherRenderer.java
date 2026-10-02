package org.kneekura.bedrockwither.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.ResourceLocation;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;

public final class BedrockWitherRenderer extends MobRenderer<BedrockWitherEntity, BedrockWitherModel> {
    private static final ResourceLocation JAVA_WITHER_TEXTURE =
            new ResourceLocation("minecraft", "textures/entity/wither/wither.png");

    public BedrockWitherRenderer(EntityRendererProvider.Context context) {
        super(context, new BedrockWitherModel(context.bakeLayer(BedrockWitherModel.LAYER_LOCATION)), 1.0F);
    }

    @Override
    protected void scale(BedrockWitherEntity entity, PoseStack poseStack, float partialTick) {
        // Mojang Bedrock client entity: variable.base_scale = 2.
        // Spawn/death swell is layered on top later once the exact Bedrock swell
        // lifecycle is reconstructed.
        poseStack.scale(2.0F, 2.0F, 2.0F);
    }

    @Override
    public ResourceLocation getTextureLocation(BedrockWitherEntity entity) {
        // Geometry/scale/animation come from Bedrock definitions. Texture bytes are
        // not redistributed; use the Java runtime's Mojang Wither texture for now.
        return JAVA_WITHER_TEXTURE;
    }
}
