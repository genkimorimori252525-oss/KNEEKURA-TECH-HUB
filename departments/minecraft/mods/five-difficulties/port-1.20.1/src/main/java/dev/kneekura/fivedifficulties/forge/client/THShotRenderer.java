package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

import java.util.Random;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.*;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.*;

/**
 * Literal port of X1 {@code RenderTHShot}: every shot form, the delay light, and
 * {@code getEntityTexture}. GL state changes map to {@link X1Tess.State}; immediate-mode quads
 * go through {@link X1Tess}. Comments name the X1 method each block comes from.
 */
public final class THShotRenderer extends EntityRenderer<THShotEntity> {
    private static ResourceLocation tex(String name) {
        return new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/shot/" + name + ".png");
    }

    static final ResourceLocation SMALL = tex("small_shot");
    static final ResourceLocation PEARL = tex("pearl_shot");
    static final ResourceLocation CIRCLE = tex("circle_shot");
    static final ResourceLocation BIG = tex("big_shot");
    static final ResourceLocation TALISMAN = tex("talisman_shot");
    static final ResourceLocation HEART = tex("heart_shot");
    static final ResourceLocation BUTTERFLY = tex("butterfly_shot");
    static final ResourceLocation STAR = tex("star_shot");
    static final ResourceLocation WIND = tex("wind_shot");
    /** X1 resourceLocation_Light / _Phantom = MusouFuuin.png. */
    static final ResourceLocation LIGHT = tex("musou_fuuin");
    static final ResourceLocation KUNAI = tex("kunai_shot");
    static final ResourceLocation LASER = tex("laser");
    static final ResourceLocation AMULET =
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/homing_amulet.png");
    static final ResourceLocation DIFFUSION = tex("diffusion_amulet");
    static final ResourceLocation FAMILIAR = tex("familiar");
    static final ResourceLocation ARROW = tex("arrow_shot");
    private static final String[] KNIFE_COLOURS = {"red", "blue", "green", "yellow", "purple", "aqua", "orange", "white"};
    static final ResourceLocation[] KNIFE = new ResourceLocation[8];

    static {
        for (int i = 0; i < 8; i++) KNIFE[i] = tex("silver_knife_" + KNIFE_COLOURS[i]);
    }

    private final ModelPart knife;

    public THShotRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.shadowRadius = 0.0F; // X1 getShadowSize = 0
        this.knife = context.bakeLayer(SilverKnifeModel.LAYER_LOCATION);
    }

    @Override
    public void render(THShotEntity shot, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                       int packedLight) {
        float size = shot.getShotSize();
        int color = shot.getShotColor();
        int form = shot.getShotForm();
        int count = shot.getAnimationCount();
        float pitch = shot.getXRot();
        float slope = shot.getAngleZ();
        X1Tess t = new X1Tess(pose, buffers, getTextureLocation(shot));

        pose.pushPose();
        if (count < 0) {
            int delayCount = Math.min(-count, 10);
            float size2 = Math.min(delayCount * 0.3F * size, 1.0F);
            billboard(pose);
            renderLightEffect(t, pose, color, size2, count);
        } else {
            switch (form) {
                case FORM_SMALL, FORM_TINY, FORM_MEDIUM, FORM_PEARL, FORM_CIRCLE, FORM_HEART ->
                        renderNormalShot(t, pose, size, color, false);
                case FORM_BIG -> renderNormalShot(t, pose, size, color, true);
                case FORM_SCALE -> renderScaleShot(t, pose, size, color, yaw, pitch);
                case FORM_BUTTERFLY -> renderButterflyShot(t, pose, size, color, count, yaw, pitch, slope);
                case FORM_SMALLSTAR, FORM_STAR -> renderStarShot(t, pose, size, color, count);
                case FORM_RICE -> renderRiceShot(t, pose, size, yaw, pitch, 4.0F, 1.20F, -2.0D, 7, 5, color, 0.7F);
                case FORM_CRYSTAL -> renderCrystalShot(t, pose, size, color, yaw, pitch);
                case FORM_LIGHT, FORM_BIGLIGHT -> renderLightShot(t, pose, size, color, count % 2);
                case FORM_KUNAI -> renderKunaiShot(t, pose, size, color, yaw, pitch, slope, -2.6F, 0.375F);
                case FORM_ARROW -> renderKunaiShot(t, pose, size, color, yaw, pitch, slope, -5.8F, 0.0F);
                case FORM_TALISMAN -> renderTalismanShot(t, pose, size, color, yaw, pitch, slope);
                case FORM_OVAL -> renderOvalShot(t, pose, size, yaw, pitch, 2.0F, 1.0F, -1.0D, 7, 5, color, 0.7F);
                case FORM_FAMILIAR -> renderFamiliar(t, pose, size, color, count);
                case FORM_PHANTOM -> renderPhantom(t, pose, color, count);
                case FORM_AMULET -> renderAmuletShot(t, pose, size, color, count, yaw, pitch, slope);
                case FORM_KNIFE -> renderKnife(t, pose, size, yaw, pitch, slope);
                case FORM_WIND -> renderWindShot(t, pose, size, color, count);
                case FORM_KISHITU -> renderKishituShot(t, pose, size, color, count);
                default -> {}
            }
        }
        pose.popPose();
    }

    /** THKaguyaRenderLib.getGLRotatefByTherdPersonView: face the camera. */
    private void billboard(PoseStack pose) {
        pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
        pose.mulPose(Axis.YP.rotationDegrees(180.0F));
    }

    private static void rotateYawPitch(PoseStack pose, float yaw, float pitch) {
        pose.mulPose(Axis.YP.rotationDegrees(yaw));
        pose.mulPose(Axis.XP.rotationDegrees(-pitch));
    }

    private static void rotateYawPitchSlope(PoseStack pose, float yaw, float pitch, float slope) {
        rotateYawPitch(pose, yaw, pitch);
        pose.mulPose(Axis.ZP.rotationDegrees(slope));
    }

    private static void billboardQuad(X1Tess t, float w, double z, float u1, float u2, float v1, float v2) {
        t.v(-w, -w, z, u1, v2).v(w, -w, z, u2, v2).v(w, w, z, u2, v1).v(-w, w, z, u1, v1);
    }

    // renderLightEffect
    private void renderLightEffect(X1Tess t, PoseStack pose, int color, float size, int count) {
        count = count % 2;
        float u1 = (float) (count * 32) / 64F, u2 = (float) (count * 32 + 32) / 64F;
        pose.scale(size, size, size);
        t.begin(INVERT_ADD).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.5F);
        billboardQuad(t, 1.0F, 0.0D, u1, u2, 0F, 1F);
    }

    // renderNormalShot
    private void renderNormalShot(X1Tess t, PoseStack pose, float size, int color, boolean blend) {
        pose.scale(size, size, size);
        billboard(pose);
        t.begin(blend ? ADD_ALPHA : CUTOUT);
        billboardQuad(t, 1.0F, 0.0D, (float) color / 8F, (float) (color + 1) / 8F, 0F, 1F);
    }

    // renderLightShot
    private void renderLightShot(X1Tess t, PoseStack pose, float size, int color, int count) {
        pose.scale(size, size, size);
        billboard(pose);
        color %= 8;
        float uMin = (float) (count * 32) / 64F, uMax = (float) (count * 32 + 32) / 64F;
        t.begin(ADD_ALPHA).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.8F);
        billboardQuad(t, 2.0F, 0.0D, uMin, uMax, 0F, 1F);
        t.begin(ADD_ALPHA).color(1F, 1F, 1F, 1F);
        billboardQuad(t, 1.0F, 0.01D, uMin, uMax, 0F, 1F);
    }

    // renderKishituShot
    private void renderKishituShot(X1Tess t, PoseStack pose, float size, int color, int count) {
        pose.scale(size, size, size);
        billboard(pose);
        count = count % 2;
        float uMin = (float) (count * 32) / 64F, uMax = (float) (count * 32 + 32) / 64F;
        t.begin(ADD_ALPHA).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.5F);
        billboardQuad(t, 2.0F, 0.0D, uMin, uMax, 0F, 1F);
        t.begin(ADD_ALPHA).color(1F, 1F, 1F, 0.8F);
        billboardQuad(t, 1.6F, 0.01D, uMin, uMax, 0F, 1F);
    }

    // renderFamiliar
    private void renderFamiliar(X1Tess t, PoseStack pose, float size, int color, int count) {
        pose.scale(size, size, size);
        billboard(pose);
        pose.mulPose(Axis.ZP.rotationDegrees((float) count * 3.7F));
        t.begin(INVERT_ADD).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.5F);
        billboardQuad(t, 1.0F, 0.0D, 0F, 1F, 0F, 1F);
    }

    // renderScaleShot (the live, non-commented branch)
    private void renderScaleShot(X1Tess t, PoseStack pose, float size, int color, float yaw, float pitch) {
        double length = 2.0D;
        float width = 1.0F;
        pose.scale(size, size, size);
        pose.mulPose(Axis.YP.rotationDegrees(yaw + 180F));
        pose.mulPose(Axis.XP.rotationDegrees(pitch));
        t.begin(CUTOUT);
        renderOvalShotPart(t, length * 0.4D, width * 0.5F, -0.85D, 7, 5, 7, 1.0F);
        t.begin(ADD_ALPHA);
        renderHalfOvalShotPart(t, length, width * 1.2F, 7, 8, color, 0.31F);
    }

    // renderButterflyShot
    private void renderButterflyShot(X1Tess t, PoseStack pose, float size, int color, int count, float yaw,
                                     float pitch, float slope) {
        pose.scale(size, size, size);
        float wingAngle = Mth.sin((float) count / 3.0F) * 45F;
        if (pitch > 90F) pitch = 90F - pitch % 90F;
        else if (pitch < -90F) pitch = -90F - pitch % 90F;
        rotateYawPitchSlope(pose, yaw, pitch, slope);
        pose.mulPose(Axis.ZP.rotationDegrees(wingAngle));
        color %= 8;
        float minU = 0F, maxU = 32F / 128F, minV = 0F, maxV = 1F;
        float width = 2.0F, width2 = 1.8F;
        t.begin(ADD_ALPHA).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 1.0F)
                .v(0, 0, width, maxU, minV).v(width, 0, width, minU, minV)
                .v(width, 0, -width, minU, maxV).v(0, 0, -width, maxU, maxV);
        t.begin(ADD_ALPHA).color(1F, 1F, 1F, 0.4F)
                .v(0, 0, width2, maxU, minV).v(width2, 0, width2, minU, minV)
                .v(width2, 0, -width2, minU, maxV).v(0, 0, -width2, maxU, maxV);
        pose.mulPose(Axis.ZP.rotationDegrees(-wingAngle * 2F));
        t.begin(ADD_ALPHA).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 1.0F)
                .v(0, 0, width, maxU, minV).v(-width, 0, width, minU, minV)
                .v(-width, 0, -width, minU, maxV).v(0, 0, -width, maxU, maxV);
        t.begin(ADD_ALPHA).color(1F, 1F, 1F, 0.4F)
                .v(0, 0, width2, maxU, minV).v(-width2, 0, width2, minU, minV)
                .v(-width2, 0, -width2, minU, maxV).v(0, 0, -width2, maxU, maxV);
    }

    // renderStarShot
    private void renderStarShot(X1Tess t, PoseStack pose, float size, int color, int count) {
        pose.scale(size, size, size);
        billboard(pose);
        pose.mulPose(Axis.ZP.rotationDegrees((float) count * 3.7F));
        float[] x = new float[11], y = new float[11];
        float angle = 0F;
        float span = (float) Math.PI * 0.2F;
        for (int i = 0; i < 10; i += 2) {
            x[i] = (float) Math.cos(angle) * 2.0F;
            y[i] = (float) Math.sin(angle) * 2.0F;
            angle += span;
            x[i + 1] = (float) Math.cos(angle) * 1.2F;
            y[i + 1] = (float) Math.sin(angle) * 1.2F;
            angle += span;
        }
        x[10] = x[0];
        y[10] = y[0];
        for (int i = 0; i < 9; i += 2) {
            t.begin(ADD_ALPHA).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.7F)
                    .v(x[i], y[i], 0, 0F, 0F).v(x[i + 1], y[i + 1], 0, 1F, 0F)
                    .v(x[i + 2], y[i + 2], 0, 1F, 1F).v(0, 0, 0, 0F, 1F);
            t.begin(ADD_ALPHA).color(1F, 1F, 1F, 0.7F)
                    .v(x[i] * 0.7F, y[i] * 0.7F, 0.01D, 0F, 0F).v(x[i + 1] * 0.95F, y[i + 1] * 0.95F, 0.01D, 1F, 0F)
                    .v(x[i + 2] * 0.7F, y[i + 2] * 0.7F, 0.01D, 1F, 1F).v(0, 0, 0.01D, 0F, 1F);
        }
    }

    // renderCrystalShot
    private void renderCrystalShot(X1Tess t, PoseStack pose, float size, int color, float yaw, float pitch) {
        pose.scale(size, size, size);
        rotateYawPitch(pose, yaw, pitch);
        float width = 0.96F;
        double length = 4.0D, lengthB = 1.0D;
        float width2 = width * 0.8F;
        double length2 = length * 0.8D, length2B = length * 0.4D;
        for (int i = 0; i < 4; i++) {
            pose.mulPose(Axis.ZP.rotationDegrees(90F));
            t.begin(ADD_ALPHA).color(1F, 1F, 1F, 1F)
                    .v(0, width2, 0, 1F, 0F).v(-width2, 0, 0, 0F, 0F).v(0, 0, length2, 0F, 1F).v(0, 0, length2, 0F, 1F);
            t.begin(ADD_ALPHA).color(1F, 1F, 1F, 1F)
                    .v(0, width2, 0, 1F, 0F).v(width2, 0, 0, 0F, 0F).v(0, 0, -length2B, 0F, 1F).v(0, 0, -length2B, 0F, 1F);
        }
        for (int i = 0; i < 4; i++) {
            pose.mulPose(Axis.ZP.rotationDegrees(90F));
            t.begin(ADD_ALPHA).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.7F)
                    .v(0, width, 0, 1F, 0F).v(-width, 0, 0, 0F, 0F).v(0, 0, length, 0F, 1F).v(0, 0, length, 0F, 1F);
            t.begin(ADD_ALPHA).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.7F)
                    .v(0, width, 0, 1F, 0F).v(width, 0, 0, 0F, 0F).v(0, 0, -lengthB, 0F, 1F).v(0, 0, -lengthB, 0F, 1F);
        }
    }

    /**
     * renderKunaiShot and renderArrowShot (identical except the handle: root -2.6 with V 0.375 for
     * the kunai, root -5.8 with V 0.0 for the arrow).
     */
    private void renderKunaiShot(X1Tess t, PoseStack pose, float size, int color, float yaw, float pitch,
                                 float slope, float root, float handleV) {
        pose.scale(size, size, size);
        rotateYawPitchSlope(pose, yaw, pitch, slope);
        float width2 = 0.6F;
        kunaiHead(t, CUTOUT, false, 0, 0.8F, 1.12F, -0.8F, -1.0F, 0.24F);
        kunaiHead(t, INVERT_ADD_DEPTH, true, color, 1.0F, 1.4F, -0.8F, -1.0F, 0.3F);
        float back2 = -1.0F;
        t.begin(INVERT_ADD_DEPTH).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 1.0F)
                .v(width2, 0, back2, 0.50F, handleV).v(-width2, 0, back2, 0.75F, handleV)
                .v(-width2, 0, root, 0.75F, 1.0F).v(width2, 0, root, 0.50F, 1.0F);
    }

    private static void kunaiHead(X1Tess t, X1Tess.State state, boolean coloured, int color, float width,
                                  float front, float back, float back2, float height) {
        float[][][] quads = {
                {{-width, 0, back, 0.50F, 1.0F}, {0, 0, front, 0.25F, 0.0F}, {width, 0, back, 0.00F, 1.0F}, {0, height, back, 0.25F, 1.0F}},
                {{0, 0, front, 0.25F, 0.0F}, {0, 0, front, 0.25F, 0.0F}, {0, -height, back, 0.25F, 1.0F}, {width, 0, back, 0.00F, 1.0F}},
                {{0, 0, front, 0.25F, 0.0F}, {0, 0, front, 0.25F, 0.0F}, {-width, 0, back, 0.50F, 1.0F}, {0, -height, back, 0.25F, 1.0F}},
                {{0, 0, back2, 0.25F, 0.0F}, {0, 0, back2, 0.25F, 0.0F}, {0, height, back, 0.25F, 1.0F}, {width, 0, back, 0.00F, 1.0F}},
                {{0, 0, back2, 0.25F, 0.0F}, {0, 0, back2, 0.25F, 0.0F}, {width, 0, back, 0.00F, 1.0F}, {0, -height, back, 0.25F, 1.0F}},
                {{0, 0, back2, 0.25F, 0.0F}, {0, 0, back2, 0.25F, 0.0F}, {-width, 0, back, 0.50F, 1.0F}, {0, height, back, 0.25F, 1.0F}},
                {{0, 0, back2, 0.25F, 0.0F}, {0, 0, back2, 0.25F, 0.0F}, {0, -height, back, 0.25F, 1.0F}, {-width, 0, back, 0.50F, 1.0F}}};
        for (float[][] q : quads) {
            t.begin(state);
            if (coloured) t.color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 1.0F);
            for (float[] p : q) t.v(p[0], p[1], p[2], p[3], p[4]);
        }
    }

    // renderTalismanShot
    private void renderTalismanShot(X1Tess t, PoseStack pose, float size, int color, float yaw, float pitch,
                                    float slope) {
        pose.scale(size, size, size);
        rotateYawPitchSlope(pose, yaw, pitch, slope);
        float u1 = (float) color / 8F, u2 = (float) (color + 1) / 8F;
        float width = 1.6F;
        double length = 2.0D;
        t.begin(CUTOUT).v(width, 0, length, u2, 0F).v(-width, 0, length, u1, 0F)
                .v(-width, 0, -length, u1, 1F).v(width, 0, -length, u2, 1F);
    }

    // renderWindShot (X1 draws a new Random every frame, so the flicker is part of the look)
    private void renderWindShot(X1Tess t, PoseStack pose, float size, int color, int count) {
        float size2 = size * 0.5F;
        pose.scale(size2, size2, size2);
        Random random = new Random();
        float rand1 = (float) random.nextInt(50) / 100F;
        float rand2 = (float) random.nextInt(100) / 100F + 4F;
        int pattern = count % 4;
        float u1 = (float) ((pattern % 2) * 32) / 64F, u2 = (float) ((pattern % 2) * 32 + 32) / 64F;
        float v1 = (float) ((pattern / 2) * 16) / 32F, v2 = (float) ((pattern / 2) * 16 + 16) / 32F;
        float f9 = 0.5F;
        for (int i = 0; i < 8; i++) {
            pose.mulPose(Axis.YP.rotationDegrees(45F));
            t.begin(INVERT_ADD_DEPTH).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.7F)
                    .v(-rand1, -1.0F - f9, 0, u1, v2).v(rand1, -1.0F - f9, 0, u2, v2)
                    .v(rand2, 2.0F - f9, 2.0D, u2, v1).v(-rand2, 2.0F - f9, 2.0D, u1, v1);
        }
    }

    // renderRiceShot
    private void renderRiceShot(X1Tess t, PoseStack pose, float size, float yaw, float pitch, double length,
                                float width, double zPos, int zAngleDivNum, int zDivNum, int color, float alpha) {
        rotateYawPitch(pose, yaw, pitch);
        pose.scale(size, size, size);
        t.begin(CUTOUT);
        renderRiceShotPart(t, length * 0.8D, width * 0.8F, zPos + length * 0.1D, zAngleDivNum, zDivNum, 7, 1.0F);
        t.begin(ADD_ALPHA);
        renderRiceShotPart(t, length, width, zPos, zAngleDivNum, zDivNum, color, alpha);
    }

    private static void renderRiceShotPart(X1Tess t, double length, float width, double zPos, int zAngleDivNum,
                                           int zDivNum, int color, float alpha) {
        float maxWidth = width;
        double angleZ = 0F;
        double angleSpanZ = Math.PI * 2.0D / (double) zAngleDivNum;
        double zDivLength = length / (double) (zDivNum - 1);
        double zPosOld = zPos;
        float angle = -(float) Math.PI / 2.0F;
        float angleSpan = (float) Math.PI / (float) zDivNum;
        angle += angleSpan;
        float widthOld = 0.0F;
        t.color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], alpha);
        for (int j = 0; j < zDivNum; j++) {
            zPos += zDivLength;
            width = (float) Math.cos(angle) * maxWidth;
            float xPosOld = (float) Math.cos(angleZ) * width, yPosOld = (float) Math.sin(angleZ) * width;
            float xPos2Old = (float) Math.cos(angleZ) * widthOld, yPos2Old = (float) Math.sin(angleZ) * widthOld;
            angleZ = angleSpanZ;
            for (int i = 0; i <= zAngleDivNum; i++) {
                float xPos = (float) Math.cos(angleZ) * width, yPos = (float) Math.sin(angleZ) * width;
                float xPos2 = (float) Math.cos(angleZ) * widthOld, yPos2 = (float) Math.sin(angleZ) * widthOld;
                t.v(xPosOld, yPosOld, zPos, 0F, 0F).v(xPos2Old, yPos2Old, zPosOld, 0F, 1F)
                        .v(xPos2, yPos2, zPosOld, 1F, 1F).v(xPos, yPos, zPos, 1F, 0F);
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

    // renderOvalShot
    private void renderOvalShot(X1Tess t, PoseStack pose, float size, float yaw, float pitch, double length,
                                float width, double zPos, int zAngleDivNum, int zDivNum, int color, float alpha) {
        pose.scale(size, size, size);
        rotateYawPitch(pose, yaw, pitch);
        t.begin(CUTOUT);
        renderOvalShotPart(t, length * 0.8D, width * 0.8F, zPos + length * 0.1D, zAngleDivNum, zDivNum, 7, 1.0F);
        t.begin(ADD_ALPHA);
        renderOvalShotPart(t, length, width, zPos, zAngleDivNum, zDivNum, color, alpha);
    }

    private static void renderOvalShotPart(X1Tess t, double length, float width, double zOffset, int zAngleDivNum,
                                           int zDivNum, int color, float alpha) {
        float maxWidth = width;
        double angleZ = 0F;
        double angleSpanZ = Math.PI * 2.0D / (double) zAngleDivNum;
        double zPosOld = zOffset - length;
        float angle = -(float) Math.PI / 2.0F;
        float angleSpan = (float) Math.PI / (float) zDivNum;
        angle += angleSpan;
        float widthOld = 0.0F;
        t.color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], alpha);
        for (int j = 0; j < zDivNum; j++) {
            double zPos = zOffset + Math.sin(angle) * length;
            width = (float) Math.cos(angle) * maxWidth;
            float xPosOld = (float) Math.cos(angleZ) * width, yPosOld = (float) Math.sin(angleZ) * width;
            float xPos2Old = (float) Math.cos(angleZ) * widthOld, yPos2Old = (float) Math.sin(angleZ) * widthOld;
            angleZ = angleSpanZ;
            for (int i = 0; i <= zAngleDivNum; i++) {
                float xPos = (float) Math.cos(angleZ) * width, yPos = (float) Math.sin(angleZ) * width;
                float xPos2 = (float) Math.cos(angleZ) * widthOld, yPos2 = (float) Math.sin(angleZ) * widthOld;
                t.v(xPosOld, yPosOld, zPos, 0F, 0F).v(xPos2Old, yPos2Old, zPosOld, 0F, 1F)
                        .v(xPos2, yPos2, zPosOld, 1F, 1F).v(xPos, yPos, zPos, 1F, 0F);
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

    // renderHarfOvalShotPart (alpha fades per ring; the zPos argument is unused by X1)
    private static void renderHalfOvalShotPart(X1Tess t, double length, float width, int zAngleDivNum, int zDivNum,
                                               int color, float alpha) {
        float maxWidth = width;
        double angleZ = 0F;
        double angleSpanZ = Math.PI * 2.0D / (double) zAngleDivNum;
        double zPosOld = -length;
        float angle = -(float) Math.PI / 2.0F;
        float angleSpan = (float) Math.PI / (float) zDivNum;
        angle += angleSpan;
        float widthOld = 0.0F;
        zDivNum = (zDivNum / 2) + 1;
        for (int j = 0; j < zDivNum; j++) {
            double zPos = Math.sin(angle) * length;
            width = (float) Math.cos(angle) * maxWidth;
            float xPosOld = (float) Math.cos(angleZ) * width, yPosOld = (float) Math.sin(angleZ) * width;
            float xPos2Old = (float) Math.cos(angleZ) * widthOld, yPos2Old = (float) Math.sin(angleZ) * widthOld;
            angleZ = angleSpanZ;
            t.color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], alpha);
            for (int i = 0; i <= zAngleDivNum; i++) {
                float xPos = (float) Math.cos(angleZ) * width, yPos = (float) Math.sin(angleZ) * width;
                float xPos2 = (float) Math.cos(angleZ) * widthOld, yPos2 = (float) Math.sin(angleZ) * widthOld;
                t.v(xPosOld, yPosOld, zPos, 0F, 0F).v(xPos2Old, yPos2Old, zPosOld, 0F, 1F)
                        .v(xPos2, yPos2, zPosOld, 1F, 1F).v(xPos, yPos, zPos, 1F, 0F);
                xPosOld = xPos;
                yPosOld = yPos;
                xPos2Old = xPos2;
                yPos2Old = yPos2;
                angleZ += angleSpanZ;
            }
            alpha -= j * 0.05F;
            zPosOld = zPos;
            angle += angleSpan;
            widthOld = width;
        }
    }

    // renderAmuletShot
    private void renderAmuletShot(X1Tess t, PoseStack pose, float size, int color, int count, float yaw, float pitch,
                                  float slope) {
        pose.scale(size, size, size);
        rotateYawPitchSlope(pose, yaw, pitch, slope);
        pose.mulPose(Axis.YP.rotationDegrees(180F - (float) count * 23F));
        t.begin(INVERT_ADD).v(-1F, 0, 1F, 0F, 0F).v(1F, 0, 1F, 0.5F, 0F).v(1F, 0, -1F, 0.5F, 1F).v(-1F, 0, -1F, 0F, 1F);
        t.begin(INVERT_ADD).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.6F)
                .v(-1.2F, 0, 1.2F, 0.5F, 0F).v(1.2F, 0, 1.2F, 1F, 0F).v(1.2F, 0, -1.2F, 1F, 1F).v(-1.2F, 0, -1.2F, 0.5F, 1F);
    }

    // FORM_KNIFE: ModelSilverKnife at 3x shot size
    private void renderKnife(X1Tess t, PoseStack pose, float size, float yaw, float pitch, float slope) {
        float size2 = size * 3.0F;
        pose.scale(size2, size2, size2);
        rotateYawPitchSlope(pose, yaw, pitch, slope);
        knife.render(pose, t.modelSink(CUTOUT), LightTexture.FULL_BRIGHT, OverlayTexture.NO_OVERLAY, 1F, 1F, 1F, 1F);
    }

    // FORM_PHANTOM block in renderTHShot + renderPhantomPart
    private void renderPhantom(X1Tess t, PoseStack pose, int color, int count) {
        double timeR = (double) count / 180.0D * Math.PI;
        billboard(pose);
        float size = 1.0F;
        pose.scale(size, size, size);
        renderPhantomPart(t, color, timeR, 0);
        pose.translate((float) Math.sin(timeR * 5) * 0.2F, 0.1F + (count % 20) * 0.06F, 0F);
        size = 0.9F * ((20F - (float) (count % 20)) / 20F);
        pose.scale(size, size, size);
        renderPhantomPart(t, color, timeR, 0);
        pose.translate((float) Math.cos(timeR * 5) * 0.2F, 0.1F + (count % 20) * 0.07F, 0F);
        size = 0.8F * ((20F - (float) (count % 20)) / 20F);
        pose.scale(size, size, size);
        renderPhantomPart(t, color, timeR, 0);
    }

    private static void renderPhantomPart(X1Tess t, int color, double r, int damage) {
        float umin = 0F, umax = 32F / 64F, vmin = 0F, vmax = 1F;
        float alpha = (40F - (float) damage) / 40F;
        float cr = RENDER_COLOR_R[color] * 0.3F, cg = RENDER_COLOR_G[color] * 0.3F, cb = RENDER_COLOR_B[color] * 0.3F;
        t.begin(ADD_ONE).color(cr, cg, cb, 0.3F * alpha)
                .v(-0.7F + Math.sin(r * 3.0D) * 0.1F, -0.2F - Math.cos(r * 7.0D) * 0.1F, 0, umin, vmax)
                .v(0.7F - Math.cos(r * 4.0D) * 0.1F, -0.2F - Math.sin(r * 5.0D) * 0.1F, 0, umax, vmax)
                .v(0.7F + Math.sin(r * 5.0D) * 0.1F, 1.2F + Math.cos(r * 4.0D) * 0.1F, 0, umax, vmin)
                .v(-0.7F - Math.cos(r * 7.0D) * 0.1F, 1.2F + Math.sin(r * 3.0D) * 0.1F, 0, umin, vmin);
        t.begin(ADD_ONE).color(cr, cg, cb, 0.7F * alpha)
                .v(-0.6F - Math.cos(r * 7.0D) * 0.1F, -0.1F + Math.sin(r * 5.0D) * 0.1F, 0.001D, umin, vmax)
                .v(0.6F + Math.sin(r * 3.0D) * 0.1F, -0.1F + Math.cos(r * 4.0D) * 0.1F, 0.001D, umax, vmax)
                .v(0.6F - Math.cos(r * 4.0D) * 0.1F, 1.1F - Math.sin(r * 3.0D) * 0.1F, 0.001D, umax, vmin)
                .v(-0.6F + Math.sin(r * 5.0D) * 0.1F, 1.1F - Math.cos(r * 7.0D) * 0.1F, 0.001D, umin, vmin);
        for (int i = 0; i < 3; i++) {
            t.begin(ADD_ONE);
            if (damage > 0) t.color(1F, 0F, 0F, alpha);
            t.v(-0.5F, 0, 0.002D, umin, vmax).v(0.5F, 0, 0.002D, umax, vmax)
                    .v(0.5F, 1F, 0.002D, umax, vmin).v(-0.5F, 1F, 0.002D, umin, vmin);
        }
    }

    // getEntityTexture
    @Override
    public ResourceLocation getTextureLocation(THShotEntity shot) {
        if (shot.getAnimationCount() < 0) return LIGHT;
        int color = shot.getShotColor();
        return switch (shot.getShotForm()) {
            case FORM_SMALL, FORM_TINY, FORM_MEDIUM -> SMALL;
            case FORM_PEARL -> PEARL;
            case FORM_CIRCLE -> CIRCLE;
            case FORM_SCALE, FORM_RICE, FORM_OVAL -> LASER;
            case FORM_BUTTERFLY -> BUTTERFLY;
            case FORM_SMALLSTAR, FORM_STAR, FORM_CRYSTAL -> STAR;
            case FORM_HEART -> HEART;
            case FORM_KUNAI -> KUNAI;
            case FORM_TALISMAN -> TALISMAN;
            case FORM_FAMILIAR -> FAMILIAR;
            case FORM_ARROW -> ARROW;
            case FORM_AMULET -> color == 1 ? DIFFUSION : AMULET;
            case FORM_KNIFE -> KNIFE[Math.min(color, 7)];
            case FORM_WIND -> WIND;
            case FORM_BIG -> BIG;
            default -> LIGHT; // LIGHT, BIGLIGHT, PHANTOM, KISHITU and unknown forms
        };
    }
}
