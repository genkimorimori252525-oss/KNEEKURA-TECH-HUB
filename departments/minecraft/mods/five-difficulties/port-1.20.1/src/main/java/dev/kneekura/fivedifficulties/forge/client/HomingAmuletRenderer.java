package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.platform.GlStateManager;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.core.x1.HomingAmuletVisualContract;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.HomingAmuletProjectile;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import org.joml.Matrix4f;

/**
 * Recreates the two-pass X1 RenderHomingAmulet state without committing the original PNG.
 */
public final class HomingAmuletRenderer extends EntityRenderer<HomingAmuletProjectile> {
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/homing_amulet.png");

    public HomingAmuletRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.shadowRadius = 0.0F;
    }

    @Override
    public void render(
            HomingAmuletProjectile entity,
            float entityYaw,
            float partialTick,
            PoseStack poseStack,
            MultiBufferSource bufferSource,
            int packedLight
    ) {
        poseStack.pushPose();

        float pitch = Mth.lerp(partialTick, entity.xRotO, entity.getXRot());
        float animation = entity.getLegacyAnimationCount() + partialTick;
        poseStack.mulPose(Axis.XP.rotationDegrees(-pitch));
        poseStack.mulPose(Axis.YP.rotationDegrees(
                HomingAmuletVisualContract.BASE_Y_ROTATION_DEGREES
                        + HomingAmuletVisualContract.Y_ROTATION_PER_ANIMATION_TICK * animation
        ));

        RenderSystem.enableBlend();
        RenderSystem.disableCull();
        RenderSystem.blendFunc(
                GlStateManager.SourceFactor.ONE,
                GlStateManager.DestFactor.ONE_MINUS_SRC_COLOR
        );
        RenderSystem.setShader(GameRenderer::getPositionTexColorShader);
        RenderSystem.setShaderTexture(0, TEXTURE);

        poseStack.scale(
                HomingAmuletVisualContract.RED_FIRST_PASS_SCALE,
                HomingAmuletVisualContract.RED_FIRST_PASS_SCALE,
                HomingAmuletVisualContract.RED_FIRST_PASS_SCALE
        );
        drawQuad(poseStack.last().pose(), 255, 255, 255, 255);

        poseStack.scale(
                HomingAmuletVisualContract.RED_SECOND_PASS_ADDITIONAL_SCALE,
                HomingAmuletVisualContract.RED_SECOND_PASS_ADDITIONAL_SCALE,
                HomingAmuletVisualContract.RED_SECOND_PASS_ADDITIONAL_SCALE
        );
        drawQuad(
                poseStack.last().pose(),
                255,
                25,
                25,
                Math.round(HomingAmuletVisualContract.RED_TINT_A * 255.0F)
        );

        RenderSystem.enableCull();
        RenderSystem.defaultBlendFunc();
        RenderSystem.disableBlend();
        poseStack.popPose();
    }

    private static void drawQuad(Matrix4f matrix, int red, int green, int blue, int alpha) {
        BufferBuilder builder = Tesselator.getInstance().getBuilder();
        builder.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX_COLOR);

        // Exact X1 vertex/UV order from RenderHomingAmulet.
        builder.vertex(matrix, -0.5F, 0.0F, 0.5F)
                .uv(HomingAmuletVisualContract.U_MIN, HomingAmuletVisualContract.V_MIN)
                .color(red, green, blue, alpha).endVertex();
        builder.vertex(matrix, 0.5F, 0.0F, 0.5F)
                .uv(HomingAmuletVisualContract.U_MAX, HomingAmuletVisualContract.V_MIN)
                .color(red, green, blue, alpha).endVertex();
        builder.vertex(matrix, 0.5F, 0.0F, -0.5F)
                .uv(HomingAmuletVisualContract.U_MAX, HomingAmuletVisualContract.V_MAX)
                .color(red, green, blue, alpha).endVertex();
        builder.vertex(matrix, -0.5F, 0.0F, -0.5F)
                .uv(HomingAmuletVisualContract.U_MIN, HomingAmuletVisualContract.V_MAX)
                .color(red, green, blue, alpha).endVertex();

        BufferUploader.drawWithShader(builder.end());
    }

    @Override
    public ResourceLocation getTextureLocation(HomingAmuletProjectile entity) {
        return TEXTURE;
    }
}
