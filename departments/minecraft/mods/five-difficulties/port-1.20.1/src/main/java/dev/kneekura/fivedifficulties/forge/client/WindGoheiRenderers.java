package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.MiracleCircleEntity;
import dev.kneekura.fivedifficulties.forge.entity.SanaeWindEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

import java.util.Random;

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.ADD_ALPHA_DEPTH;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD;

/** Ports of X1 RenderMiracleCircle and RenderSanaeWind. */
public final class WindGoheiRenderers {
    private WindGoheiRenderers() {}

    /** RenderMiracleCircle: a pentagram of 3-long, 0.2-wide strokes, the last one growing in tenths. */
    public static final class MiracleCircle extends EntityRenderer<MiracleCircleEntity> {
        private static final ResourceLocation TEXTURE =
                new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/miracle_circle.png");
        private static final float[] R = {0.7F, 0.7F, 0.9F, 0.3F, 0.2F};
        private static final float[] G = {0.1F, 0.7F, 0.1F, 0.3F, 0.9F};
        private static final float[] B = {0.9F, 0.1F, 0.2F, 0.9F, 0.2F};

        public MiracleCircle(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public boolean shouldRender(MiracleCircleEntity e, Frustum frustum, double x, double y, double z) {
            return true;
        }

        @Override
        public void render(MiracleCircleEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            int j = Math.min(Math.max(e.getColor(), 0), 4);
            pose.pushPose();
            pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
            pose.mulPose(Axis.YP.rotationDegrees(180.0F));
            pose.mulPose(Axis.ZP.rotationDegrees(e.turnAngle));
            X1Tess t = new X1Tess(pose, buffers, TEXTURE);
            float umin = 0.5F, umax = 0.625F, vmin = 0.0F, vmax = 1.0F;
            float angle = -108F, length = 3.0F, width = 0.10F;
            float py = length / (2.0F * Mth.cos(0.3141593F));
            float px = 0F;
            float nextpx = px + Mth.cos(angle / 180F * 3.141593F) * length;
            float nextpy = py + Mth.sin(angle / 180F * 3.141593F) * length;
            int lastLine = e.getNumberOfDrewLine() - 1;
            int i;
            for (i = 0; i < lastLine; i++) {
                stroke(t, px, py, nextpx, nextpy, angle, width, 0.001D * i, j, umin, umax, vmin, vmax);
                angle += 144F;
                px = nextpx;
                py = nextpy;
                nextpx = px + Mth.cos(angle / 180F * 3.141593F) * length;
                nextpy = py + Mth.sin(angle / 180F * 3.141593F) * length;
            }
            float lastLineLength = length * (float) e.getLastLineTime() / 10F;
            nextpx = px + Mth.cos(angle / 180F * 3.141593F) * lastLineLength;
            nextpy = py + Mth.sin(angle / 180F * 3.141593F) * lastLineLength;
            stroke(t, px, py, nextpx, nextpy, angle, width, 0.001D * i, j, umin, umax, vmin, vmax);
            pose.popPose();
        }

        private static void stroke(X1Tess t, float px, float py, float nx, float ny, float angle, float width, double z,
                                   int j, float umin, float umax, float vmin, float vmax) {
            float wx = Mth.cos((angle + 90F) / 180F * 3.141593F) * width;
            float wy = Mth.sin((angle + 90F) / 180F * 3.141593F) * width;
            t.begin(INVERT_ADD).color(R[j], G[j], B[j], 0.5F)
                    .v(px - wx, py - wy, z, umin, vmax).v(px + wx, py + wy, z, umax, vmax)
                    .v(nx + wx, ny + wy, z, umax, vmin).v(nx - wx, ny - wy, z, umin, vmin);
        }

        @Override
        public ResourceLocation getTextureLocation(MiracleCircleEntity e) {
            return TEXTURE;
        }
    }

    /** RenderSanaeWind: eight 45°-apart blades of WindShot, a new random width every frame. */
    public static final class SanaeWind extends EntityRenderer<SanaeWindEntity> {
        private static final ResourceLocation TEXTURE =
                new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/shot/wind_shot.png");

        public SanaeWind(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(SanaeWindEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            pose.pushPose();
            pose.scale(0.5F, 0.5F, 0.5F);
            Random random = new Random();
            float rand1 = (float) random.nextInt(50) / 100F;
            float rand2 = (float) random.nextInt(100) / 100F;
            int pattern = e.tickCount % 4;
            float f3 = (float) ((pattern % 2) * 32) / 64F, f4 = (float) ((pattern % 2) * 32 + 32) / 64F;
            float f5 = (float) ((pattern / 2) * 16) / 32F, f6 = (float) ((pattern / 2) * 16 + 16) / 32F;
            float f7 = rand1, f8 = 4.0F + rand2, f9 = 0.5F;
            X1Tess t = new X1Tess(pose, buffers, TEXTURE);
            for (int i = 0; i < 8; i++) {
                pose.mulPose(Axis.YP.rotationDegrees(45F));
                t.begin(ADD_ALPHA_DEPTH).color(0.1F, 0.9F, 0.6F, 0.7F)
                        .v(0.0F - f7, -1.0F - f9, 0.0D, f3, f6).v(0.0F + f7, -1.0F - f9, 0.0D, f4, f6)
                        .v(0.0F + f8, 2.0F - f9, 2.0D, f4, f5).v(0.0F - f8, 2.0F - f9, 2.0D, f3, f5);
            }
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(SanaeWindEntity e) {
            return TEXTURE;
        }
    }
}
