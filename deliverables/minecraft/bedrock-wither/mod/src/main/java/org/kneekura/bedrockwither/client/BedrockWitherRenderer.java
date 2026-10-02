package org.kneekura.bedrockwither.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.ResourceLocation;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;

public final class BedrockWitherRenderer extends MobRenderer<BedrockWitherEntity, BedrockWitherModel> {
    private static final ResourceLocation JAVA_WITHER_TEXTURE =
            new ResourceLocation("minecraft", "textures/entity/wither/wither.png");
    private static final ResourceLocation JAVA_WITHER_INVULNERABLE_TEXTURE =
            new ResourceLocation("minecraft", "textures/entity/wither/wither_invulnerable.png");

    public BedrockWitherRenderer(EntityRendererProvider.Context context) {
        super(context, new BedrockWitherModel(context.bakeLayer(BedrockWitherModel.LAYER_LOCATION)), 1.0F);
        this.addLayer(new BedrockWitherArmorLayer(this, context.getModelSet()));
    }

    @Override
    protected void scale(BedrockWitherEntity entity, PoseStack poseStack, float partialTick) {
        // Current Mojang Bedrock wither.entity.json:
        // base_scale = 2
        // swell_clamped = clamp(query.swell_amount, 0, 1)
        // wobble = 1 + sin(query.swell_amount * 5730deg) * query.swell_amount * 0.01
        // swell_adjustment = swell_clamped^4
        // scale_xz = (1 + swell_adjustment * 0.4) * wobble
        // scale_y  = (1 + swell_adjustment * 0.1) / wobble
        float swell = entity.getBedrockSwellAmount(partialTick);
        float swellClamped = Math.max(0.0F, Math.min(1.0F, swell));
        float wobble = 1.0F + (float) Math.sin(swell * 100.0F) * swell * 0.01F;
        float adjustment = swellClamped * swellClamped;
        adjustment *= adjustment;

        float scaleXZ = (1.0F + adjustment * 0.4F) * wobble;
        float scaleY = (1.0F + adjustment * 0.1F) / wobble;

        poseStack.scale(2.0F * scaleXZ, 2.0F * scaleY, 2.0F * scaleXZ);
    }

    @Override
    protected float getWhiteOverlayProgress(BedrockWitherEntity entity, float partialTick) {
        return entity.getDeathOverlayAlpha();
    }

    @Override
    public ResourceLocation getTextureLocation(BedrockWitherEntity entity) {
        // Current Mojang Bedrock entity script:
        // display_normal_skin = invulnerable_ticks <= 0
        //   || (invulnerable_ticks <= 80 && mod(invulnerable_ticks / 5, 2) == 1)
        //
        // Bedrock texture bytes are not redistributed; Java's bundled Mojang
        // normal/invulnerable Wither textures are used as asset substitutes while
        // preserving the Bedrock timing rule exactly.
        int invulnerableTicks = entity.runtimeState().spawningFrames();
        boolean displayNormal = invulnerableTicks <= 0
                || (invulnerableTicks <= 80 && (invulnerableTicks / 5) % 2 == 1);
        return displayNormal ? JAVA_WITHER_TEXTURE : JAVA_WITHER_INVULNERABLE_TEXTURE;
    }
}
