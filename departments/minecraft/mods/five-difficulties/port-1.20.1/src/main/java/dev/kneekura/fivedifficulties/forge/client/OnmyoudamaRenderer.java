package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.OnmyoudamaEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD;

/**
 * Port of X1 RenderOnmyoudama: a spinning (5° per tick) billboard of the ball, then a 1.4-block light
 * whose size argument X1 never applies. Its unused renderLaser sphere is not ported.
 */
public final class OnmyoudamaRenderer extends EntityRenderer<OnmyoudamaEntity> {
    private static final ResourceLocation BALL = tex("onmyoudama");
    private static final ResourceLocation LIGHT = tex("musou_fuuin");
    private static final float[] R = {224F / 255F, 0F, 0F, 224F / 255F, 224F / 255F, 0F, 1F, 1F};
    private static final float[] G = {0F, 0F, 224F / 255F, 64F / 255F, 0F, 224F / 255F, 128F / 255F, 1F};
    private static final float[] B = {0F, 224F / 255F, 0F, 0F, 224F / 255F, 224F / 255F, 0F, 1F};

    private static ResourceLocation tex(String name) {
        return new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/shot/" + name + ".png");
    }

    public OnmyoudamaRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public void render(OnmyoudamaEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                       int light) {
        pose.pushPose();
        pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
        pose.mulPose(Axis.YP.rotationDegrees(180.0F));
        pose.mulPose(Axis.ZP.rotationDegrees(e.tickCount * 5F));
        float size = e.getShotSize();
        pose.scale(size, size, size);
        X1Tess t = new X1Tess(pose, buffers, getTextureLocation(e));
        float f3 = 0.0F, f4 = 0.5F, f5 = 0.0F, f6 = 1.0F, f7 = 1.0F, f8 = 0.5F, f9 = 0.5F;
        t.begin(INVERT_ADD)
                .v(0.0F - f8, 0.0F - f9, 0.01D, f3, f6).v(f7 - f8, 0.0F - f9, 0.01D, f4, f6)
                .v(f7 - f8, 1.0F - f9, 0.01D, f4, f5).v(0.0F - f8, 1.0F - f9, 0.01D, f3, f5);
        // renderLightEffect(color 0)
        int count = e.getAnimationCount() % 2;
        float u1 = (float) (64 + count * 32) / 128F, u2 = (float) (64 + count * 32 + 32) / 128F;
        float v1 = 0F, v2 = 0.5F, w = 1.4F, h = 0.7F;
        t.begin(INVERT_ADD).color(R[0], G[0], B[0], 0.5F)
                .v(0.0F - h, 0.0F - h, 0.0D, u1, v2).v(w - h, 0.0F - h, 0.0D, u2, v2)
                .v(w - h, w - h, 0.0D, u2, v1).v(0.0F - h, w - h, 0.0D, u1, v1);
        pose.popPose();
    }

    @Override
    public ResourceLocation getTextureLocation(OnmyoudamaEntity e) {
        return e.getAnimationCount() < 0 ? LIGHT : BALL;
    }
}
