package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.platform.GlStateManager;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import org.joml.Matrix4f;

public final class SakuyaTimeControllerRenderer extends EntityRenderer<SakuyaTimeControllerEntity> {
    private static final ResourceLocation WATCH_TEXTURE =
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/sakuya_watch.png");
    private static final ResourceLocation STOPWATCH_TEXTURE =
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/sakuya_stopwatch.png");
    private static final ResourceLocation DARK_TEXTURE =
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/sakuya_time_dark.png");

    private final SakuyaTimeControllerModel model;

    public SakuyaTimeControllerRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.model = new SakuyaTimeControllerModel(
                context.bakeLayer(SakuyaTimeControllerModel.LAYER_LOCATION)
        );
        this.shadowRadius = 0.5F;
    }

    @Override
    public void render(
            SakuyaTimeControllerEntity entity,
            float entityYaw,
            float partialTick,
            PoseStack poseStack,
            MultiBufferSource bufferSource,
            int packedLight
    ) {
        poseStack.pushPose();
        poseStack.scale(0.3F, 0.3F, 0.3F);

        float age = entity.tickCount + partialTick;
        renderDarkField(poseStack, age);

        poseStack.mulPose(Axis.YP.rotationDegrees(180.0F - entityYaw + age * 7.0F));

        ResourceLocation texture = getTextureLocation(entity);
        VertexConsumer consumer = bufferSource.getBuffer(model.renderType(texture));
        model.renderToBuffer(
                poseStack,
                consumer,
                packedLight,
                OverlayTexture.NO_OVERLAY,
                1.0F, 1.0F, 1.0F, 1.0F
        );

        poseStack.popPose();
        super.render(entity, entityYaw, partialTick, poseStack, bufferSource, packedLight);
    }

    private static void renderDarkField(PoseStack poseStack, float age) {
        double size = Math.min(age * 12.0D, 240.0D);
        if (size <= 0.0D) return;

        RenderSystem.enableBlend();
        RenderSystem.disableCull();
        RenderSystem.depthMask(false);
        RenderSystem.blendFunc(
                GlStateManager.SourceFactor.ONE_MINUS_DST_COLOR,
                GlStateManager.DestFactor.ZERO
        );
        RenderSystem.setShader(GameRenderer::getPositionTexColorShader);
        RenderSystem.setShaderTexture(0, DARK_TEXTURE);

        Matrix4f matrix = poseStack.last().pose();

        float maxWidth = (float)size / 2.0F;
        int zAngleDivNum = 18;
        double angleSpanZ = Math.PI * 2.0D / zAngleDivNum;
        int zDivNum = 9;

        double zPosOld = -maxWidth;
        float widthOld = 0.0F;
        float angle = -(float)Math.PI / 2.0F;
        float angleSpan = (float)Math.PI / zDivNum;
        angle += angleSpan;

        for (int j = 0; j < zDivNum; j++) {
            double zPos = Math.sin(angle) * maxWidth;
            float width = (float)Math.cos(angle) * maxWidth;

            double angleZ = 0.0D;
            float xPosOld = (float)Math.cos(angleZ) * width;
            float yPosOld = (float)Math.sin(angleZ) * width;
            float xPos2Old = (float)Math.cos(angleZ) * widthOld;
            float yPos2Old = (float)Math.sin(angleZ) * widthOld;

            angleZ = angleSpanZ;
            for (int i = 1; i <= zAngleDivNum; i++) {
                float xPos = (float)Math.cos(angleZ) * width;
                float yPos = (float)Math.sin(angleZ) * width;
                float xPos2 = (float)Math.cos(angleZ) * widthOld;
                float yPos2 = (float)Math.sin(angleZ) * widthOld;

                drawDarkQuad(
                        matrix,
                        xPos, yPos, (float)zPos,
                        xPosOld, yPosOld, (float)zPos,
                        xPos2Old, yPos2Old, (float)zPosOld,
                        xPos2, yPos2, (float)zPosOld
                );

                xPosOld = xPos;
                yPosOld = yPos;
                xPos2Old = xPos2;
                yPos2Old = yPos2;
                angleZ += angleSpanZ;
            }

            zPosOld = zPos;
            angle += angleSpan;
            widthOld = width;
        }

        RenderSystem.depthMask(true);
        RenderSystem.enableCull();
        RenderSystem.defaultBlendFunc();
        RenderSystem.disableBlend();
    }

    private static void drawDarkQuad(
            Matrix4f matrix,
            float x1, float y1, float z1,
            float x2, float y2, float z2,
            float x3, float y3, float z3,
            float x4, float y4, float z4
    ) {
        BufferBuilder builder = Tesselator.getInstance().getBuilder();
        builder.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX_COLOR);

        builder.vertex(matrix, x1, y1, z1).uv(1.0F, 0.0F).color(255,255,255,255).endVertex();
        builder.vertex(matrix, x2, y2, z2).uv(0.0F, 0.0F).color(255,255,255,255).endVertex();
        builder.vertex(matrix, x3, y3, z3).uv(0.0F, 1.0F).color(255,255,255,255).endVertex();
        builder.vertex(matrix, x4, y4, z4).uv(1.0F, 1.0F).color(255,255,255,255).endVertex();

        BufferUploader.drawWithShader(builder.end());
    }

    @Override
    public ResourceLocation getTextureLocation(SakuyaTimeControllerEntity entity) {
        return entity.getControllerKind() == SakuyaControllerKind.STOPWATCH
                ? STOPWATCH_TEXTURE
                : WATCH_TEXTURE;
    }
}
