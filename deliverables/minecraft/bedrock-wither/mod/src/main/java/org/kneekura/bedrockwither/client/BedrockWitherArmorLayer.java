package org.kneekura.bedrockwither.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.geom.EntityModelSet;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;
import org.kneekura.bedrockwither.entity.BedrockWitherPresentation;

/**
 * The pinned official armor controllers draw both white and blue passes, using
 * the same inflated geometry, independent UVs and ignore_lighting=true.
 * Java's bundled armor texture and an explicit blue tint are asset substitutes;
 * no Bedrock texture bytes are redistributed or texture parity claimed.
 */
public final class BedrockWitherArmorLayer extends RenderLayer<BedrockWitherEntity, BedrockWitherModel> {
    private static final ResourceLocation JAVA_WITHER_ARMOR_TEXTURE =
            new ResourceLocation("minecraft", "textures/entity/wither/wither_armor.png");

    private final BedrockWitherModel model;

    public BedrockWitherArmorLayer(
            RenderLayerParent<BedrockWitherEntity, BedrockWitherModel> parent,
            EntityModelSet modelSet
    ) {
        super(parent);
        this.model = new BedrockWitherModel(modelSet.bakeLayer(BedrockWitherModel.ARMOR_LAYER_LOCATION));
    }

    @Override
    public void render(PoseStack poses, MultiBufferSource buffers, int sceneLight,
                       BedrockWitherEntity entity, float limbSwing, float limbSwingAmount,
                       float partialTick, float ageInTicks, float netHeadYaw, float headPitch) {
        var passes = BedrockWitherPresentation.armorPasses(
                entity.isPowered(), entity.tickCount, partialTick, sceneLight);
        if (passes.isEmpty()) return;

        model.prepareMobModel(entity, limbSwing, limbSwingAmount, partialTick);
        getParentModel().copyPropertiesTo(model);
        model.setupAnim(entity, limbSwing, limbSwingAmount, ageInTicks, netHeadYaw, headPitch);
        for (var pass : passes) {
            // Java's energy-swirl shader ignores lighting and supplies the UV
            // texture transform. Repeating coordinates permits bounded offsets.
            var vertices = buffers.getBuffer(RenderType.energySwirl(
                    JAVA_WITHER_ARMOR_TEXTURE, pass.u() % 1.0F, pass.v() % 1.0F));
            model.renderToBuffer(poses, vertices, pass.packedLight(), OverlayTexture.NO_OVERLAY,
                    pass.red(), pass.green(), pass.blue(), 1.0F);
        }
    }
}
