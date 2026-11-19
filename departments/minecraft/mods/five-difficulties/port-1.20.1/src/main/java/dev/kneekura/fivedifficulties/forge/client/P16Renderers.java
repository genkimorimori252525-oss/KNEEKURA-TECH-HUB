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

    /** RenderCirnoIceBox: a vanilla-ice cube of (width / 2 + 0.4) by (height + 0.8), inverted-add blended. */
    public static final class CirnoIceBox extends EntityRenderer<dev.kneekura.fivedifficulties.forge.entity.CirnoIceBoxEntity> {
        private static final ResourceLocation ICE = new ResourceLocation("minecraft", "textures/block/ice.png");

        public CirnoIceBox(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.CirnoIceBoxEntity e, float yaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            float width = e.getIceBoxWidth() / 2.0F + 0.4F;
            float height = e.getIceBoxHeight() + 0.8F;
            float[] px = {-width, width, width, -width, -width, width, width, -width};
            float[] py = {height, height, height, height, 0.0F, 0.0F, 0.0F, 0.0F};
            float[] pz = {width, width, -width, -width, -width, -width, width, width};
            int[][] p = {{0, 1, 2, 3}, {3, 2, 5, 4}, {2, 1, 6, 5}, {1, 0, 7, 6}, {0, 3, 4, 7}, {4, 5, 6, 7}};
            X1Tess t = new X1Tess(pose, buffers, ICE).begin(INVERT_ADD_DEPTH);
            for (int[] q : p) {
                t.color(1F, 1F, 1F, 1F)
                        .v(px[q[0]], py[q[0]], pz[q[0]], 0.0F, 1.0F).v(px[q[1]], py[q[1]], pz[q[1]], 1.0F, 1.0F)
                        .v(px[q[2]], py[q[2]], pz[q[2]], 1.0F, 0.0F).v(px[q[3]], py[q[3]], pz[q[3]], 0.0F, 0.0F);
            }
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.CirnoIceBoxEntity e) {
            return ICE;
        }
    }

    /** RenderHakurouReflecter: three rings of 16 fan blades (radius 1.8, 1.5, 1.2) turning with age. */
    public static final class HakurouReflecter extends EntityRenderer<dev.kneekura.fivedifficulties.forge.entity.HakurouReflecterEntity> {
        private static final ResourceLocation REFLECT = tex("hakurou_reflect");

        public HakurouReflecter(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.HakurouReflecterEntity e, float yaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            pose.pushPose();
            pose.mulPose(Axis.YP.rotationDegrees(Mth.lerp(partialTick, e.yRotO, e.getYRot())));
            pose.mulPose(Axis.XP.rotationDegrees(e.getXRot()));
            float minU = 0.0F, maxU = 0.5F, minV = 0.0F, maxV = 1.0F;
            float angle = e.tickCount / 5F;
            float span = (float) Math.PI / 8F;
            double length = 1.8D;
            X1Tess t = new X1Tess(pose, buffers, REFLECT).begin(INVERT_ADD);
            for (int i = 0; i < 3; i++) {
                for (int j = 0; j < 16; j++) {
                    double x1 = Math.cos(angle) * length, x2 = Math.cos(angle + span) * length;
                    double y1 = Math.sin(angle) * length, y2 = Math.sin(angle + span) * length;
                    t.color(1.0F, 1.0F, 1.0F, 0.2F + j * 0.3F)
                            .v(x1, y1, 0.0D, minU, maxV).v(x2, y2, 0.0D, maxU, maxV)
                            .v(0, 0, 0.0D, maxU, minV).v(0, 0, 0.0D, minU, minV);
                    angle += span;
                }
                length -= 0.3D;
            }
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.HakurouReflecterEntity e) {
            return REFLECT;
        }
    }

    /** RenderSilverKnife: ModelSilverKnife at half size, turned by yaw, pitch and the knife's Z angle; full bright. */
    public static final class SilverKnife extends EntityRenderer<dev.kneekura.fivedifficulties.forge.entity.SilverKnifeEntity> {
        private static final ResourceLocation[] TEX = {tex("shot/silver_knife_blue"), tex("shot/silver_knife_red"),
                tex("shot/silver_knife_green"), tex("shot/silver_knife_white")};
        private final net.minecraft.client.model.geom.ModelPart model;

        public SilverKnife(EntityRendererProvider.Context context) {
            super(context);
            this.shadowRadius = 0.3F;
            this.model = context.bakeLayer(SilverKnifeModel.LAYER_LOCATION);
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.SilverKnifeEntity e, float entityYaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            float yaw = Mth.lerp(partialTick, e.yRotO, e.getYRot());
            pose.pushPose();
            pose.mulPose(Axis.YP.rotationDegrees(180F - yaw));
            pose.mulPose(Axis.XP.rotationDegrees(-e.getXRot()));
            pose.mulPose(Axis.ZP.rotationDegrees(e.getKnifeZAngle()));
            pose.scale(0.5F, 0.5F, 0.5F);
            model.render(pose, new X1Tess(pose, buffers, getTextureLocation(e)).modelSink(CUTOUT),
                    net.minecraft.client.renderer.LightTexture.FULL_BRIGHT,
                    net.minecraft.client.renderer.texture.OverlayTexture.NO_OVERLAY, 1F, 1F, 1F, 1F);
            pose.popPose();
            super.render(e, entityYaw, partialTick, pose, buffers, light);
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.SilverKnifeEntity e) {
            int c = e.getKnifeColor();
            return TEX[c >= 0 && c < 3 ? c : 3];
        }
    }

    public static final net.minecraft.client.model.geom.ModelLayerLocation PARASOL_LAYER =
            new net.minecraft.client.model.geom.ModelLayerLocation(
                    new ResourceLocation(FiveDifficultiesPort.MOD_ID, "yuuka_parasol"), "main");

    /** ModelYuukaParasol: four 4×28×4 stick boxes and a three-box crook handle (64×32). */
    public static net.minecraft.client.model.geom.builders.LayerDefinition createParasolLayer() {
        var mesh = new net.minecraft.client.model.geom.builders.MeshDefinition();
        var root = mesh.getRoot();
        for (int i = 0; i < 4; i++) {
            root.addOrReplaceChild("stick" + i, net.minecraft.client.model.geom.builders.CubeListBuilder.create().texOffs(0, 0)
                    .addBox(-2, i * 28, -2, 4, 28, 4), net.minecraft.client.model.geom.PartPose.ZERO);
        }
        root.addOrReplaceChild("handle0", net.minecraft.client.model.geom.builders.CubeListBuilder.create().texOffs(32, 16)
                .addBox(-3, -10, -3, 6, 10, 6), net.minecraft.client.model.geom.PartPose.ZERO);
        root.addOrReplaceChild("handle1", net.minecraft.client.model.geom.builders.CubeListBuilder.create().texOffs(32, 16)
                .addBox(0, 0, -6, 6, 10, 6),
                net.minecraft.client.model.geom.PartPose.offsetAndRotation(-3F, -10F, -3F, (float) Math.PI / 3F * 2F, 0F, 0F));
        root.addOrReplaceChild("handle2", net.minecraft.client.model.geom.builders.CubeListBuilder.create().texOffs(32, 16)
                .addBox(0, 0, -6, 6, 10, 6),
                net.minecraft.client.model.geom.PartPose.offsetAndRotation(-3F, -10F + Mth.cos((float) Math.PI / 3F * 2F) * 10F,
                        -3F + Mth.sin((float) Math.PI / 3F * 2F) * 10F, (float) Math.PI / 3F, 0F, 0F));
        return net.minecraft.client.model.geom.builders.LayerDefinition.create(mesh, 64, 32);
    }

    /** RenderYuukaParasol: an 18-panel canopy and the stick model, 2.4 below the entity, scaled 0.7. */
    public static final class YuukaParasol extends EntityRenderer<dev.kneekura.fivedifficulties.forge.entity.YuukaParasolEntity> {
        private static final ResourceLocation PARASOL = tex("yuuka_parasol");
        private final net.minecraft.client.model.geom.ModelPart model;

        public YuukaParasol(EntityRendererProvider.Context context) {
            super(context);
            this.model = context.bakeLayer(PARASOL_LAYER);
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.YuukaParasolEntity e, float entityYaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            float yaw = Mth.lerp(partialTick, e.yRotO, e.getYRot());
            pose.pushPose();
            pose.translate(0.0F, -2.4F, 0.0F);
            pose.mulPose(Axis.YP.rotationDegrees(180F - yaw));
            pose.mulPose(Axis.XP.rotationDegrees(e.getXRot()));
            double stickHeight = 2.7D;
            float uMin = 0.5F, uMax = 0.75F, vMin = 0.0F, vMax = 0.5F;
            float length = 2.2F, width = 0.5F, span = 360F / 18F;
            pose.scale(0.7F, 0.7F, 0.7F);
            X1Tess t = new X1Tess(pose, buffers, PARASOL).begin(CUTOUT);
            for (int i = 0; i < 18; i++) {
                t.v(0.0F, stickHeight, 0.0D, uMin, vMax).v(0.0F, stickHeight, 0.0D, uMax, vMax)
                        .v(width, length, -1.0D, uMax, vMin).v(-width, length, -1.0D, uMin, vMin);
                t.v(-width, length, -1.0D, uMin, vMax).v(width, length, -1.0D, uMax, vMax)
                        .v(width * 2F, length - 0.5F, -1.7D, uMax, vMin).v(-width * 2F, length - 0.5F, -1.7D, uMin, vMin);
                pose.mulPose(Axis.YP.rotationDegrees(span));
            }
            pose.scale(0.3F, 0.4F, 0.3F);
            model.render(pose, new X1Tess(pose, buffers, PARASOL).modelSink(CUTOUT), light,
                    net.minecraft.client.renderer.texture.OverlayTexture.NO_OVERLAY, 1F, 1F, 1F, 1F);
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.YuukaParasolEntity e) {
            return PARASOL;
        }
    }

    public static final net.minecraft.client.model.geom.ModelLayerLocation HISOU_LAYER =
            new net.minecraft.client.model.geom.ModelLayerLocation(new ResourceLocation(FiveDifficultiesPort.MOD_ID, "hisou"), "main");

    /** ModelHisou: guard, blade and a flat 12×12 flame (64×32). */
    public static net.minecraft.client.model.geom.builders.LayerDefinition createHisouLayer() {
        var mesh = new net.minecraft.client.model.geom.builders.MeshDefinition();
        var root = mesh.getRoot();
        var zero = net.minecraft.client.model.geom.PartPose.ZERO;
        root.addOrReplaceChild("hisou0", net.minecraft.client.model.geom.builders.CubeListBuilder.create().texOffs(32, 0)
                .addBox(-2, -12, -2, 4, 8, 4), zero);
        root.addOrReplaceChild("hisou1", net.minecraft.client.model.geom.builders.CubeListBuilder.create().texOffs(0, 0)
                .addBox(-2, -4, -2, 4, 28, 4), zero);
        root.addOrReplaceChild("hisou2", net.minecraft.client.model.geom.builders.CubeListBuilder.create().texOffs(32, 16)
                .addBox(-2, -20, 0, 12, 12, 0), zero);
        return net.minecraft.client.model.geom.builders.LayerDefinition.create(mesh, 64, 32);
    }

    /** RenderHisou: the sword model turned by yaw, pitch and its spin, additive, alpha num / 8. */
    public static final class Hisou extends EntityRenderer<dev.kneekura.fivedifficulties.forge.entity.HisouEntity> {
        private static final ResourceLocation HISOU = tex("hisou");
        private final net.minecraft.client.model.geom.ModelPart model;

        public Hisou(EntityRendererProvider.Context context) {
            super(context);
            this.shadowRadius = 0.5F;
            this.model = context.bakeLayer(HISOU_LAYER);
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.HisouEntity e, float entityYaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            float yaw = Mth.lerp(partialTick, e.yRotO, e.getYRot());
            pose.pushPose();
            pose.mulPose(Axis.YP.rotationDegrees(-yaw));
            pose.mulPose(Axis.XP.rotationDegrees(e.getXRot()));
            pose.mulPose(Axis.ZP.rotationDegrees(e.getAngle()));
            pose.scale(0.3F, 0.7F, 0.3F);
            model.render(pose, new X1Tess(pose, buffers, HISOU).modelSink(X1Tess.State.ADD_ALPHA_DEPTH),
                    net.minecraft.client.renderer.LightTexture.FULL_BRIGHT,
                    net.minecraft.client.renderer.texture.OverlayTexture.NO_OVERLAY, 1F, 1F, 1F, (float) e.getNum() * 0.125F);
            pose.popPose();
            super.render(e, entityYaw, partialTick, pose, buffers, light);
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.HisouEntity e) {
            return HISOU;
        }
    }

    public static final net.minecraft.client.model.geom.ModelLayerLocation KINKAKUZI_LAYER =
            new net.minecraft.client.model.geom.ModelLayerLocation(new ResourceLocation(FiveDifficultiesPort.MOD_ID, "kinkakuzi"), "main");

    /** ModelKinkakuzi: one 30×30×2 plate laid flat (64×32). */
    public static net.minecraft.client.model.geom.builders.LayerDefinition createKinkakuziLayer() {
        var mesh = new net.minecraft.client.model.geom.builders.MeshDefinition();
        mesh.getRoot().addOrReplaceChild("kinkakuzi", net.minecraft.client.model.geom.builders.CubeListBuilder.create().texOffs(0, 0)
                .addBox(-15, -15, -2, 30, 30, 2), net.minecraft.client.model.geom.PartPose.rotation((float) Math.PI / 2F, 0F, 0F));
        return net.minecraft.client.model.geom.builders.LayerDefinition.create(mesh, 64, 32);
    }

    /** RenderKinkakuzi: the plate scaled 3 × 0.75 × 3, rocking after a hit like a boat. */
    public static final class Kinkakuzi extends EntityRenderer<dev.kneekura.fivedifficulties.forge.entity.KinkakuziEntity> {
        private static final ResourceLocation PLATE = tex("kinkakuzi");
        private final net.minecraft.client.model.geom.ModelPart model;

        public Kinkakuzi(EntityRendererProvider.Context context) {
            super(context);
            this.shadowRadius = 3.0F;
            this.model = context.bakeLayer(KINKAKUZI_LAYER);
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.KinkakuziEntity e, float yaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            pose.pushPose();
            pose.scale(3.0F, 0.75F, 3.0F);
            pose.mulPose(Axis.YP.rotationDegrees(180F - yaw));
            float f = (float) e.getTimeSinceHit() - partialTick;
            float f1 = Math.max(0.0F, e.getDamageTaken() - partialTick);
            if (f > 0.0F) pose.mulPose(Axis.XP.rotationDegrees(Mth.sin(f) * f * f1 / 10.0F * e.getForwardDirection()));
            model.render(pose, buffers.getBuffer(net.minecraft.client.renderer.RenderType.entityCutoutNoCull(PLATE)), light,
                    net.minecraft.client.renderer.texture.OverlayTexture.NO_OVERLAY, 1F, 1F, 1F, 1F);
            pose.popPose();
            super.render(e, yaw, partialTick, pose, buffers, light);
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.KinkakuziEntity e) {
            return PLATE;
        }
    }

    /** RenderMarisaBroom: a 2.8-long square rod with a three-stage brush, drawn with the tessellator (no model). */
    public static final class MarisaBroom extends EntityRenderer<dev.kneekura.fivedifficulties.forge.entity.MarisaBroomEntity> {
        private static final ResourceLocation BROOM = tex("magic_broom");

        public MarisaBroom(EntityRendererProvider.Context context) {
            super(context);
            this.shadowRadius = 0.5F;
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.MarisaBroomEntity e, float yaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            pose.pushPose();
            pose.mulPose(Axis.YP.rotationDegrees(180.0F - yaw));
            float f2 = (float) e.getTimeSinceHit() - partialTick;
            float f3 = Math.max(0.0F, e.getDamageTaken() - partialTick);
            if (f2 > 0.0F) pose.mulPose(Axis.ZP.rotationDegrees(Mth.sin(f2) * f2 * f3 / 10.0F * e.getForwardDirection()));
            pose.scale(-1.0F, -1.0F, 1.0F);
            pose.mulPose(Axis.YP.rotationDegrees(-90F));
            pose.mulPose(Axis.XP.rotationDegrees(-e.getXRot()));
            float w = 0.05F, w2 = 0.3F, w3 = 0.4F, w4 = 0.15F;
            double half = 2.8D / 2.0D;
            X1Tess t = new X1Tess(pose, buffers, BROOM).begin(CUTOUT);
            for (int i = 0; i < 4; i++) {
                t.v(w, -w, half, 0F, 2F / 32F).v(w, -w, -half, 1F, 2F / 32F).v(w, w, -half, 1F, 0F).v(w, w, half, 0F, 0F);
                pose.mulPose(Axis.ZP.rotationDegrees(90F));
            }
            t.v(-w, -w, half, 0F, 2F / 32F).v(w, -w, half, 2F / 64F, 2F / 32F).v(w, w, half, 2F / 64F, 4F / 32F).v(-w, w, half, 0F, 4F / 32F);
            t.v(-w4, -w4, -half + 0.3D, 0.25F, 0.5F).v(w4, -w4, -half + 0.3D, 0.50F, 0.5F)
                    .v(w4, w4, -half + 0.3D, 0.50F, 1.0F).v(-w4, w4, -half + 0.3D, 0.25F, 1.0F);
            t.v(-w3, -w3, -half - 1.3D, 0.25F, 0.5F).v(-w3, w3, -half - 1.3D, 0.25F, 1.0F)
                    .v(w3, w3, -half - 1.3D, 0.50F, 1.0F).v(w3, -w3, -half - 1.3D, 0.50F, 0.5F);
            for (int i = 0; i < 4; i++) {
                t.v(w4, -w4, -half + 0.3D, 0.5F, 0.5F).v(w, -w, -half, 0.5F, 3F / 32F).v(w, w, -half, 1.0F, 3F / 32F).v(w4, w4, -half + 0.3D, 1.0F, 0.5F);
                t.v(w, -w, -half, 0.5F, 0.5F).v(w2, -w2, -half - 0.6D, 0.5F, 3F / 32F).v(w2, w2, -half - 0.6D, 1.0F, 3F / 32F).v(w, w, -half, 1.0F, 0.5F);
                t.v(w2, -w2, -half - 0.6D, 0.5F, 1.0F).v(w3, -w3, -half - 1.3D, 0.5F, 16F / 32F)
                        .v(w3, w3, -half - 1.3D, 1.0F, 16F / 32F).v(w2, w2, -half - 0.6D, 1.0F, 1.0F);
                pose.mulPose(Axis.ZP.rotationDegrees(90F));
            }
            pose.popPose();
            super.render(e, yaw, partialTick, pose, buffers, light);
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.MarisaBroomEntity e) {
            return BROOM;
        }
    }
}
