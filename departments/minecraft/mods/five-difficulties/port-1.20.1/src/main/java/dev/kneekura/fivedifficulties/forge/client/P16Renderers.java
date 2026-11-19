package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.X1Config;
import dev.kneekura.fivedifficulties.forge.entity.AjaRedStoneEffectEntity;
import dev.kneekura.fivedifficulties.forge.entity.MazinkyoukanEntity;
import dev.kneekura.fivedifficulties.forge.entity.SpiritualStrikeTalismanEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.ADD_ALPHA_CULL;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.CUTOUT;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD_DEPTH_CULL;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD_DEPTH;

/** Renderers for the P16 item-effect entities. */
public final class P16Renderers {
    private P16Renderers() {}

    private static ResourceLocation tex(String path) {
        return new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/" + path + ".png");
    }

    /** RenderSpiritualStrikeTalisman: a spinning two-sided talisman and (time-stop effect on) a blue glow sphere. */
    public static final class SpiritualStrikeTalisman extends EntityRenderer<SpiritualStrikeTalismanEntity> {
        private static final ResourceLocation TALISMAN = tex("spiritual_strike_talisman");

        public SpiritualStrikeTalisman(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(SpiritualStrikeTalismanEntity e, float yaw, float partialTick, PoseStack pose,
                           MultiBufferSource buffers, int light) {
            pose.pushPose();
            pose.mulPose(Axis.YP.rotationDegrees((float) e.tickCount * 21F));
            pose.mulPose(Axis.ZP.rotationDegrees(30F));
            float rvl = 0F, rul = 0F, rvr = 0.5F, rur = 1.0F;
            new X1Tess(pose, buffers, TALISMAN).begin(CUTOUT)
                    .v(0.2F, 0.4F, 0, rvl, rul).v(-0.2F, 0.4F, 0, rvr, rul).v(-0.2F, -0.4F, 0, rvr, rur).v(0.2F, -0.4F, 0, rvl, rur)
                    .v(-0.2F, 0.4F, 0, rvl, rul).v(0.2F, 0.4F, 0, rvr, rul).v(0.2F, -0.4F, 0, rvr, rur).v(-0.2F, -0.4F, 0, rvl, rur);
            pose.popPose();
            double size = Math.min(e.tickCount * 3.0D, 240.0D);
            if (X1Config.useTimeStopEffect()) {
                renderDark(new X1Tess(pose, buffers, SakuyaTimeControllerRenderer.DARK_TEXTURE).begin(ADD_ALPHA_CULL),
                        (float) size, 0.4F);
            }
        }

        /** renderDark: an 18 x 9 sphere of {@code width}, colour (0.2, 0.3, 1.0, alpha). */
        private static void renderDark(X1Tess t, float width, float alpha) {
            float maxWidth = width / 2.0F;
            int zAngleDivNum = 18;
            double angleSpanZ = Math.PI * 2.0D / (double) zAngleDivNum;
            int zDivNum = 9;
            double zPos;
            double zPosOld = Math.sin(-Math.PI / 2.0D) * maxWidth;
            float angle = -(float) Math.PI / 2.0F;
            float angleSpan = (float) Math.PI / (float) zDivNum;
            angle += angleSpan;
            float widthOld = 0.0F;
            for (int j = 0; j < zDivNum; j++) {
                zPos = Math.sin(angle) * maxWidth;
                width = (float) Math.cos(angle) * maxWidth;
                double angleZ = 0D;
                float xPosOld = (float) Math.cos(angleZ) * width, yPosOld = (float) Math.sin(angleZ) * width;
                float xPos2Old = (float) Math.cos(angleZ) * widthOld, yPos2Old = (float) Math.sin(angleZ) * widthOld;
                angleZ = angleSpanZ;
                for (int i = 1; i <= zAngleDivNum; i++) {
                    float xPos = (float) Math.cos(angleZ) * width, yPos = (float) Math.sin(angleZ) * width;
                    float xPos2 = (float) Math.cos(angleZ) * widthOld, yPos2 = (float) Math.sin(angleZ) * widthOld;
                    t.color(0.2F, 0.3F, 1.0F, alpha)
                            .v(xPos, yPos, zPos, 1.0F, 0.0F).v(xPosOld, yPosOld, zPos, 0.0F, 0.0F)
                            .v(xPos2Old, yPos2Old, zPosOld, 0.0F, 1.0F).v(xPos2, yPos2, zPosOld, 1.0F, 1.0F);
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
        }

        @Override
        public ResourceLocation getTextureLocation(SpiritualStrikeTalismanEntity e) {
            return TALISMAN;
        }
    }

    /** RenderMazinkyoukan: the scroll unrolled as {@code count} one-degree strips on a 1.6 ring, with end caps. */
    public static final class Mazinkyoukan extends EntityRenderer<MazinkyoukanEntity> {
        private static final ResourceLocation SCROLL = tex("mazinkyoukan");

        public Mazinkyoukan(EntityRendererProvider.Context context) {
            super(context);
        }

        private static float sin(float deg) {
            return Mth.sin(deg / 180F * 3.141593F);
        }

        private static float cos(float deg) {
            return Mth.cos(deg / 180F * 3.141593F);
        }

        @Override
        public void render(MazinkyoukanEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            int count = e.count;
            float angle = e.getYRot() - 57F;
            float py = -0.3F;
            float px = -sin(angle) * 1.6F;
            double pz = Math.cos(angle / 180F * 3.141593F) * 1.6D;
            float nextpx = -sin(angle + 1F) * 1.6F;
            double nextpz = Math.cos((angle + 1F) / 180F * 3.141593F) * 1.6D;
            float widthY = 0.3F, widthY2 = widthY + 0.1F;
            float px2min = -sin(angle - 2F) * 1.55F, px2max = -sin(angle + 2F) * 1.65F;
            float pz2min = cos(angle - 2F) * 1.55F, pz2max = cos(angle + 2F) * 1.65F;
            X1Tess cap = new X1Tess(pose, buffers, SCROLL);
            cap.begin(CUTOUT).color(1F, 1F, 1F, 1F)
                    .v(px2min, py - widthY2, pz2min, 0.875F, 1.0F).v(px2max, py - widthY2, pz2max, 1.0F, 1.0F)
                    .v(px2max, py + widthY2, pz2max, 1.0F, 0.5F).v(px2min, py + widthY2, pz2min, 0.875F, 0.5F);
            float colorRev = 3.141593F * 3F / 180F;
            float ticks = (float) e.tickCount;
            X1Tess strip = new X1Tess(pose, buffers, SCROLL).begin(INVERT_ADD_DEPTH);
            for (int i = 0; i < count; i++) {
                float color = (angle + ticks) * colorRev;
                float umin = (float) (i % 63) / 64F, umax = ((float) ((i + 1) % 63)) / 64F;
                float vmin = ((float) (i / 63) * 16F) / 32F, vmax = vmin + 0.5F;
                strip.color(Mth.sin(color), Mth.cos(color), -Mth.sin(color), 0.5F)
                        .v(px, py - widthY, pz, umin, vmax).v(nextpx, py - widthY, nextpz, umax, vmax)
                        .v(nextpx, py + widthY, nextpz, umax, vmin).v(px, py + widthY, pz, umin, vmin);
                angle += 1.0F;
                px = nextpx;
                pz = nextpz;
                nextpx = -sin(angle + 1F) * 1.6F;
                nextpz = Math.cos((angle + 1F) / 180F * 3.141593F) * 1.6D;
            }
            px2min = -sin(angle - 2F) * 1.55F;
            px2max = -sin(angle + 2F) * 1.65F;
            pz2min = cos(angle - 2F) * 1.55F;
            pz2max = cos(angle + 2F) * 1.65F;
            cap.begin(CUTOUT).color(1F, 1F, 1F, 1F)
                    .v(px2min, py - widthY2, pz2min, 1.0F, 1.0F).v(px2max, py - widthY2, pz2max, 0.875F, 1.0F)
                    .v(px2max, py + widthY2, pz2max, 0.875F, 0.5F).v(px2min, py + widthY2, pz2min, 1.0F, 0.5F);
        }

        @Override
        public ResourceLocation getTextureLocation(MazinkyoukanEntity e) {
            return SCROLL;
        }
    }

    /**
     * RenderAjaRedStoneEffect: light^2 random red rays (length light^2 / 120) fanned around a camera-facing point,
     * with X1's rotation step sin(360 / n) read as radians.
     */
    public static final class AjaRedStoneEffect extends EntityRenderer<AjaRedStoneEffectEntity> {
        private static final ResourceLocation CIRCLE = tex("miracle_circle");
        private final java.util.Random random = new java.util.Random();

        public AjaRedStoneEffect(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(AjaRedStoneEffectEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            pose.pushPose();
            pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
            pose.mulPose(Axis.YP.rotationDegrees(180.0F));
            int lightNum = e.getLightPower();
            lightNum = lightNum * lightNum;
            float widthX = 0.01F;
            float lengthY = (float) lightNum / 120.0F;
            float iniAngle = (float) random.nextInt(36000) / 100F;
            float angleSpan = 360F / (float) lightNum;
            float umin = 0.5F, umax = 38F / 64F, vmin = 0.0F, vmax = 1.0F;
            pose.mulPose(Axis.ZP.rotationDegrees(Mth.sin(iniAngle / 180F * 3.141593F) / 3.141593F * 180F));
            X1Tess t = new X1Tess(pose, buffers, CIRCLE).begin(INVERT_ADD);
            for (int i = 0; i < lightNum; i++) {
                float lengthY2 = lengthY * (0.2F + (float) random.nextInt(8000) / 8000.0F);
                double zPos = (double) random.nextInt(10000) / 10000.0D;
                pose.mulPose(Axis.ZP.rotationDegrees(Mth.sin(angleSpan) / 3.141593F * 180F));
                t.color(1.0F * (float) random.nextInt(10000) / 10000.0F, 0.0F, 0.0F, 0.7F)
                        .v(-widthX, 0.0F, 0.0D, umin, vmax).v(widthX, 0.0F, 0.0D, umax, vmax)
                        .v(0.0F, lengthY2, zPos, umax, vmin).v(0.0F, lengthY2, zPos, umin, vmin);
            }
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(AjaRedStoneEffectEntity e) {
            return CIRCLE;
        }
    }

    /** RenderPendulum: a 0.3-scale crystal (4 pyramids up and down, 4 crossed tags) swung by the search count. */
    public static final class Pendulum extends EntityRenderer<dev.kneekura.fivedifficulties.forge.entity.PendulumEntity> {
        private static final ResourceLocation PENDULUM = tex("pendulum");

        public Pendulum(EntityRendererProvider.Context context) {
            super(context);
            this.shadowRadius = 0.5F;
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.PendulumEntity e, float entityYaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            float yaw = Mth.lerp(partialTick, e.yRotO, e.getYRot());
            float rotationLength = (float) e.getSearchCount() / 48.0F;
            float xDrawPos = -Mth.sin(e.getSearchAngle() / 180F * 3.141593F) * rotationLength;
            float zDrawPos = Mth.cos(e.getSearchAngle() / 180F * 3.141593F) * rotationLength;
            pose.pushPose();
            pose.translate(xDrawPos, 0.0F, zDrawPos);
            pose.mulPose(Axis.YP.rotationDegrees(180F - yaw));
            float uMin = 16F / 64F, vMin = 20F / 32F, uMax = 28F / 64F, vMax = 32F / 32F;
            float t1u = 12F / 64F, t1v = 4F / 32F, t2u = 1F / 64F, t2v = 19F / 32F, t3u = 22F / 64F, t3v = 19F / 32F;
            float d1u = 33F / 64F, d1v = 0F, d2u = 55F / 64F, d2v = 0F, d3u = 44F / 64F, d3v = 31F / 32F;
            pose.scale(0.3F, 0.3F, 0.3F);
            X1Tess solid = new X1Tess(pose, buffers, PENDULUM).begin(INVERT_ADD_DEPTH_CULL);
            for (int i = 0; i < 4; i++) {
                pose.mulPose(Axis.YP.rotationDegrees(90F));
                solid.v(0.0F, 1.75F, 0.0D, t1u, t1v).v(0.0F, 1.75F, 0.0D, t1u, t1v)
                        .v(0.3F, 1.25F, -0.3D, t3u, t3v).v(-0.3F, 1.25F, -0.3D, t2u, t2v);
                solid.v(-0.3F, 1.25F, -0.3D, d1u, d1v).v(0.3F, 1.25F, -0.3D, d2u, d2v)
                        .v(0.0F, 0.25F, 0.0D, d3u, d3v).v(0.0F, 0.25F, 0.0D, d3u, d3v);
            }
            X1Tess tags = new X1Tess(pose, buffers, PENDULUM).begin(INVERT_ADD_DEPTH);
            for (int i = 0; i < 4; i++) {
                pose.mulPose(Axis.YP.rotationDegrees(45F));
                tags.v(-0.2F, 1.90F, 0.0D, uMin, vMax).v(0.2F, 1.90F, 0.0D, uMax, vMax)
                        .v(0.2F, 1.60F, 0.0D, uMax, vMin).v(-0.2F, 1.60F, 0.0D, uMin, vMin);
            }
            pose.popPose();
            super.render(e, entityYaw, partialTick, pose, buffers, light);
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.PendulumEntity e) {
            return PENDULUM;
        }
    }
}
