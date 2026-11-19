package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.MiniHakkeroEntity;
import dev.kneekura.fivedifficulties.forge.entity.MusouFuuinEntity;
import dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity;
import dev.kneekura.fivedifficulties.forge.entity.SukimaEntity;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import org.joml.Quaternionf;

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.ADD_ALPHA_DEPTH;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.ADD_ONE_CULL;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.CUTOUT;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD_DEPTH_CULL;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.SHADE;

/** Ports of X1 RenderMusouFuuin, RenderMiniHakkero (+ its two models), RenderSukima and RenderNuclearShot. */
public final class P12Renderers {
    private P12Renderers() {}

    static ResourceLocation tex(String path) {
        return new ResourceLocation(FiveDifficultiesPort.MOD_ID, path);
    }

    /** THKaguyaRenderLib.getGLRotatefByTherdPersonView */
    static void billboard(PoseStack pose, Quaternionf cameraOrientation) {
        pose.mulPose(cameraOrientation);
        pose.mulPose(Axis.YP.rotationDegrees(180.0F));
    }

    // ---- RenderMusouFuuin ----

    public static final class MusouFuuin extends EntityRenderer<MusouFuuinEntity> {
        private static final ResourceLocation TEXTURE = tex("textures/entity/shot/musou_fuuin.png");

        public MusouFuuin(EntityRendererProvider.Context context) {
            super(context);
            this.shadowRadius = 0.0F;
        }

        @Override
        public void render(MusouFuuinEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            pose.pushPose();
            float size = e.getShotSize();
            pose.scale(size, size, size);
            int pattern = e.getAnimationCount() % 2;
            float umin = (float) ((pattern % 32) * 32) / 64F;
            float umax = (float) ((pattern % 32) * 32 + 32) / 64F;
            float vmin = 0.0F, vmax = 1.0F;
            billboard(pose, this.entityRenderDispatcher.cameraOrientation());
            int color = e.getAnimationCount();
            float r = Mth.sin(color), g = Mth.cos(color), b = -Mth.sin(color) * 2F;
            X1Tess t = new X1Tess(pose, buffers, TEXTURE);
            t.begin(INVERT_ADD).color(r, g, b, 0.60F)
                    .v(-0.6F, -0.6F, 0.0D, umin, vmax).v(0.6F, -0.6F, 0.0D, umax, vmax)
                    .v(0.6F, 0.6F, 0.0D, umax, vmin).v(-0.6F, 0.6F, 0.0D, umin, vmin);
            t.begin(INVERT_ADD).color(r, g, b, 0.60F)
                    .v(-0.5F, -0.5F, 0.001D, umin, vmax).v(0.5F, -0.5F, 0.001D, umax, vmax)
                    .v(0.5F, 0.5F, 0.001D, umax, vmin).v(-0.5F, 0.5F, 0.001D, umin, vmin);
            t.begin(INVERT_ADD).color(1.0F, 1.0F, 1.0F, 0.9F)
                    .v(-0.4F, -0.4F, 0.002D, umin, vmax).v(0.4F, -0.4F, 0.002D, umax, vmax)
                    .v(0.4F, 0.4F, 0.002D, umax, vmin).v(-0.4F, 0.4F, 0.002D, umin, vmin);
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(MusouFuuinEntity e) {
            return TEXTURE;
        }
    }

    // ---- ModelMiniHakkero / ModelMiniHakkero2 ----

    public static final ModelLayerLocation HAKKERO_LAYER =
            new ModelLayerLocation(new ResourceLocation(FiveDifficultiesPort.MOD_ID, "mini_hakkero"), "main");
    public static final ModelLayerLocation HAKKERO2_LAYER =
            new ModelLayerLocation(new ResourceLocation(FiveDifficultiesPort.MOD_ID, "mini_hakkero"), "side");

    /** ModelMiniHakkero: two 16×16×1 plates, 5 apart. */
    public static LayerDefinition createHakkeroLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        root.addOrReplaceChild("plate0", CubeListBuilder.create().texOffs(0, 15).addBox(-8, -8, 0, 16, 16, 1), PartPose.ZERO);
        root.addOrReplaceChild("plate1", CubeListBuilder.create().texOffs(0, 15).addBox(-8, -8, 5, 16, 16, 1), PartPose.ZERO);
        return LayerDefinition.create(mesh, 64, 32);
    }

    /** ModelMiniHakkero2: eight 8×2×6 side boards, 45° apart around Z. */
    public static LayerDefinition createHakkero2Layer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        float pi8 = (float) Math.PI / 4.0F;
        float angle = 0.0F;
        for (int i = 0; i < 8; i++) {
            root.addOrReplaceChild("side" + i, CubeListBuilder.create().texOffs(32, 0).addBox(-4, -10, -0.001F, 8, 2, 6),
                    PartPose.rotation(0F, 0F, angle));
            angle += pi8;
        }
        return LayerDefinition.create(mesh, 64, 32);
    }

    // ---- RenderMiniHakkero ----

    public static final class MiniHakkero extends EntityRenderer<MiniHakkeroEntity> {
        private static final ResourceLocation TEXTURE = tex("textures/entity/mini_hakkero.png");
        private static final float[] R = {255F, 255F, 255F, 0F, 0F, 76F, 128F};
        private static final float[] G = {0F, 165F, 255F, 128F, 0F, 0F, 0F};
        private static final float[] B = {0F, 0F, 0F, 0F, 255F, 130F, 128F};
        private final ModelPart model;
        private final ModelPart model2;

        public MiniHakkero(EntityRendererProvider.Context context) {
            super(context);
            this.shadowRadius = 0.5F;
            this.model = context.bakeLayer(HAKKERO_LAYER);
            this.model2 = context.bakeLayer(HAKKERO2_LAYER);
        }

        /** glRotatef(pitch, -sin((yawA - 90)°), 0, cos((yawB - 90)°)): the axis is unit when yawA == yawB. */
        private static void pitchAxis(PoseStack pose, float pitch, float yawA, float yawB) {
            float x = -Mth.sin((yawA - 90F) / 180F * 3.141593F);
            float z = Mth.cos((yawB - 90F) / 180F * 3.141593F);
            float len = Mth.sqrt(x * x + z * z);
            if (len < 1.0E-6F) return;
            pose.mulPose(new Quaternionf().rotateAxis(pitch / 180F * (float) Math.PI, x / len, 0F, z / len));
        }

        @Override
        public void render(MiniHakkeroEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            // renderMiniHakkero
            pose.pushPose();
            pitchAxis(pose, e.getXRot(), yaw, yaw);
            pose.mulPose(Axis.YP.rotationDegrees(180F - yaw));
            pose.scale(0.5F, 0.5F, 0.5F);
            model.render(pose, buffers.getBuffer(RenderType.entityCutoutNoCull(TEXTURE)), LightTexture.FULL_BRIGHT,
                    OverlayTexture.NO_OVERLAY);
            float uMin = 0F, vMin = 0F, uMax = 1F / 2F, vMax = 1F / 4F;
            float angle = e.getCircleAngle();
            float pi18 = (float) Math.PI / 9F;
            int c = e.tickCount;
            pose.mulPose(Axis.ZP.rotationDegrees(Mth.sin(angle) / 3.141593F * 180F));
            X1Tess t = new X1Tess(pose, buffers, TEXTURE);
            for (int i = 0; i < 19; i++) {
                pose.mulPose(Axis.ZP.rotationDegrees(Mth.sin(pi18) / 3.141593F * 180F));
                float r1 = R[c % 7] / 255F * 0.5F, g1 = G[c % 7] / 255F * 0.5F, b1 = B[c % 7] / 255F * 0.5F;
                int c3 = (c + 3) % 7;
                float r2 = R[c3] / 255F * 0.5F, g2 = G[c3] / 255F * 0.5F, b2 = B[c3] / 255F * 0.5F;
                // near ring
                t.begin(ADD_ALPHA_DEPTH).color(r1, g1, b1, 0.6F)
                        .v(0.77F, 4.5F, -6.0D, uMin, vMin).v(-0.77F, 4.5F, -6.0D, uMax, vMin)
                        .v(-0.77F, 4.5F, -4.0D, uMax, vMax).v(0.77F, 4.5F, -4.0D, uMin, vMax);
                t.begin(ADD_ALPHA_DEPTH).color(r1, g1, b1, 0.6F)
                        .v(-0.77F, 4.5F, -6.0D, uMin, vMin).v(0.77F, 4.5F, -6.0D, uMax, vMin)
                        .v(0.77F, 4.5F, -4.0D, uMax, vMax).v(-0.77F, 4.5F, -4.0D, uMin, vMax);
                // far ring
                t.begin(ADD_ALPHA_DEPTH).color(r2, g2, b2, 0.6F)
                        .v(1.11F, 6.5F, -12.0D, uMin, vMin).v(-1.11F, 6.5F, -12.0D, uMax, vMin)
                        .v(-1.11F, 6.5F, -10.0D, uMax, vMax).v(1.11F, 6.5F, -10.0D, uMin, vMax);
                t.begin(ADD_ALPHA_DEPTH).color(r2, g2, b2, 0.6F)
                        .v(-1.11F, 6.5F, -12.0D, uMin, vMin).v(1.11F, 6.5F, -12.0D, uMax, vMin)
                        .v(1.11F, 6.5F, -10.0D, uMax, vMax).v(-1.11F, 6.5F, -10.0D, uMin, vMax);
                angle += pi18;
            }
            pose.popPose();

            // renderMiniHakkero2
            pose.pushPose();
            pitchAxis(pose, e.getXRot(), e.getYRot(), yaw);
            pose.mulPose(Axis.YP.rotationDegrees(180F - yaw));
            pose.scale(0.501F, 0.501F, 0.501F);
            model2.render(pose, buffers.getBuffer(RenderType.entityCutoutNoCull(TEXTURE)), LightTexture.FULL_BRIGHT,
                    OverlayTexture.NO_OVERLAY);
            pose.popPose();
            super.render(e, yaw, partialTick, pose, buffers, light);
        }

        @Override
        public ResourceLocation getTextureLocation(MiniHakkeroEntity e) {
            return TEXTURE;
        }
    }

    // ---- RenderSukima ----

    public static final class Sukima extends EntityRenderer<SukimaEntity> {
        private static final ResourceLocation TEXTURE = tex("textures/entity/sukima.png");
        private static final int[] R = {30, 179, 59, 81, 37, 123, 40, 128, 51, 216, 65, 222, 102, 211, 237, 240, 179};
        private static final int[] G = {27, 49, 81, 48, 49, 47, 118, 128, 51, 129, 203, 207, 133, 84, 136, 240, 49};
        private static final int[] B = {27, 44, 26, 26, 146, 190, 151, 128, 51, 152, 51, 42, 219, 205, 68, 240, 44};

        public Sukima(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(SukimaEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            pose.pushPose();
            pose.translate(0.0F, 1.0F + Mth.sin((float) e.tickCount / 20F) * 0.1F, 0.0F);
            int color = e.getColor();
            float xl = 1.0F, yl = -0.75F, xr = -1.0F, yr = 0.75F;
            int time = e.tickCount;
            float openRate = Mth.sin((float) time * 15F / 360F * 3.141593F);
            if (color == 17) {
                openRate = Mth.sin((float) time * 40F / 360F * 3.141593F);
                color = 16;
            }
            if (color >= 16) {
                xl *= openRate;
                yl *= openRate;
                xr *= openRate;
                yr *= openRate;
            }
            color = color % 32;
            pose.mulPose(Axis.YP.rotationDegrees(180F - yaw));
            X1Tess t = new X1Tess(pose, buffers, TEXTURE);
            // the gap itself
            t.begin(CUTOUT)
                    .v(-1.0F, -0.75F, 0.0D, 0.00F, 1.00F).v(xl, yl, 0.0D, 0.75F, 1.00F)
                    .v(1.0F, 0.75F, 0.0D, 0.75F, 0.00F).v(xr, yr, 0.0D, 0.00F, 0.00F);
            t.begin(SHADE).color(0F, 0F, 0F, 0.7F)
                    .v(xl, yl, -0.0009D, 0.75F, 1.00F).v(-1.0F, -0.75F, -0.0009D, 0.00F, 1.00F)
                    .v(xr, yr, -0.0009D, 0.00F, 0.00F).v(1.0F, 0.75F, -0.0009D, 0.75F, 0.00F);
            // the two ribbons
            pose.mulPose(Axis.ZP.rotationDegrees(30F));
            float r = R[color] / 255F, g = G[color] / 255F, b = B[color] / 255F;
            t.begin(CUTOUT).color(r, g, b, 0.7F)
                    .v(1.00F, -0.2F, 0.001D, 0.75F, 1.00F).v(1.25F, -0.2F, 0.001D, 1.00F, 1.00F)
                    .v(1.25F, 0.3F, 0.001D, 1.00F, 0.00F).v(1.00F, 0.3F, 0.001D, 0.75F, 0.00F);
            t.begin(CUTOUT).color(r, g, b, 0.7F)
                    .v(-1.30F, -0.3F, 0.001D, 0.75F, 1.00F).v(-1.05F, -0.3F, 0.001D, 1.00F, 1.00F)
                    .v(-1.05F, 0.2F, 0.001D, 1.00F, 0.00F).v(-1.30F, 0.2F, 0.001D, 0.75F, 0.00F);
            t.begin(SHADE).color(0F, 0F, 0F, 0.7F)
                    .v(1.00F, 0.3F, -0.001D, 0.75F, 0.00F).v(1.25F, 0.3F, -0.001D, 1.00F, 0.00F)
                    .v(1.25F, -0.2F, -0.001D, 1.00F, 1.00F).v(1.00F, -0.2F, -0.001D, 0.75F, 1.00F);
            t.begin(SHADE).color(0F, 0F, 0F, 0.7F)
                    .v(-1.30F, 0.2F, -0.001D, 0.75F, 0.00F).v(-1.05F, 0.2F, -0.001D, 1.00F, 0.00F)
                    .v(-1.05F, -0.3F, -0.001D, 1.00F, 1.00F).v(-1.30F, -0.3F, -0.001D, 0.75F, 1.00F);
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(SukimaEntity e) {
            return TEXTURE;
        }
    }

    // ---- RenderNuclearShot ----

    public static final class NuclearShot extends EntityRenderer<NuclearShotEntity> {
        private static final ResourceLocation LASER = tex("textures/entity/shot/laser.png");
        private static final ResourceLocation LIGHT = tex("textures/entity/shot/musou_fuuin.png");
        private static final float[] R = {224F / 255F, 0F / 255F, 0F / 255F, 224F / 255F, 224F / 255F, 0F / 255F, 255F / 255F, 255F / 255F};
        private static final float[] G = {0F / 255F, 0F / 255F, 224F / 255F, 64F / 255F, 0F / 255F, 224F / 255F, 128F / 255F, 255F / 255F};
        private static final float[] B = {0F / 255F, 224F / 255F, 0F / 255F, 0F / 255F, 224F / 255F, 224F / 255F, 0F / 255F, 255F / 255F};

        public NuclearShot(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(NuclearShotEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            pose.pushPose();
            int color = e.getShotColor();
            int time = e.tickCount;
            if (e.getAnimationCount() < 0) {
                int delayCount = Math.min(-e.getAnimationCount(), 10);
                float size2 = Math.min(delayCount * e.getShotSize() * 2F, 1.0F);
                billboard(pose, this.entityRenderDispatcher.cameraOrientation());
                renderLightEffect(new X1Tess(pose, buffers, LIGHT), pose, color % 8, size2, e);
            } else {
                pose.mulPose(Axis.YP.rotationDegrees(yaw));
                pose.mulPose(Axis.XP.rotationDegrees(-e.getXRot()));
                double centerZ1 = e.getShotSize() * 1.2D / 2.0D;
                double centerZ2 = e.getShotSize() / 2.0D;
                X1Tess t = new X1Tess(pose, buffers, LASER);
                renderLaser(t, INVERT_ADD_DEPTH_CULL, e.getShotSize(), centerZ1 - centerZ2, 7, 0.8F, 0);
                renderLaser(t, ADD_ONE_CULL, e.getShotSize() * 1.4F, 0.0D, color, 0.8F, time);
            }
            pose.popPose();
        }

        /** renderLaser: a sphere of 9 rings × 18 quads (the length argument is unused in X1). */
        private static void renderLaser(X1Tess t, X1Tess.State state, float width, double zPos, int color, float alpha,
                                        int time) {
            float maxWidth = width / 2.0F;
            int zAngleDivNum = 18;
            double angleSpanZ = Math.PI * 2.0D / (double) zAngleDivNum;
            int zDivNum = 9;
            zPos = Math.sin(-Math.PI / 2.0D) * maxWidth;
            double zPosOld = zPos;
            float xPos, yPos, xPos2, yPos2, xPosOld, yPosOld, xPos2Old, yPos2Old;
            float angle = -(float) Math.PI / 2.0F;
            float angleSpan = (float) Math.PI / (float) zDivNum;
            angle += angleSpan;
            float widthOld = 0.0F;
            for (int j = 0; j < zDivNum; j++) {
                zPos = Math.sin(angle) * maxWidth;
                width = (float) Math.cos(angle) * maxWidth;
                double angleZ = 0F;
                xPosOld = (float) Math.cos(angleZ) * width;
                yPosOld = (float) Math.sin(angleZ) * width;
                xPos2Old = (float) Math.cos(angleZ) * widthOld;
                yPos2Old = (float) Math.sin(angleZ) * widthOld;
                angleZ = angleSpanZ;
                for (int i = 1; i <= zAngleDivNum; i++) {
                    xPos = (float) Math.cos(angleZ) * width;
                    yPos = (float) Math.sin(angleZ) * width;
                    xPos2 = (float) Math.cos(angleZ) * widthOld;
                    yPos2 = (float) Math.sin(angleZ) * widthOld;
                    double colorVar = time != 0 ? (time + j) / 10.0D : 0.0D;
                    t.begin(state).color(R[color] + (float) Math.sin(colorVar) * 0.2F, G[color] + (float) Math.cos(colorVar) * 0.2F,
                                    B[color] - (float) Math.sin(colorVar) * 0.2F, alpha)
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

        /** renderLightEffect: X1 divides the already 0..1 colours by 255 again (nearly black, kept). */
        private static void renderLightEffect(X1Tess t, PoseStack pose, int color, float size, NuclearShotEntity e) {
            color %= 8;
            int count = e.getAnimationCount() % 2;
            float f3 = (float) (count * 32) / 64F, f4 = (float) (count * 32 + 32) / 64F;
            float f5 = 0F, f6 = 1F, f7 = 1.0F, f8 = 0.5F, f9 = 0.25F;
            pose.scale(size, size, size);
            t.begin(INVERT_ADD).color(R[color] / 255F, G[color] / 255F, B[color] / 255F, 0.5F)
                    .v(0.0F - f8, 0.0F - f9, 0.0D, f3, f6).v(f7 - f8, 0.0F - f9, 0.0D, f4, f6)
                    .v(f7 - f8, 1.0F - f9, 0.0D, f4, f5).v(0.0F - f8, 1.0F - f9, 0.0D, f3, f5);
        }

        @Override
        public ResourceLocation getTextureLocation(NuclearShotEntity e) {
            return e.getAnimationCount() < 0 ? LIGHT : LASER;
        }
    }
}
