package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THSetLaserEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RENDER_COLOR_B;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RENDER_COLOR_G;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RENDER_COLOR_R;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.*;

/** Literal port of X1 {@code RenderTHLaser}. The shot ID range picks the geometry. */
public final class THLaserRenderer<T extends THLaserEntity> extends EntityRenderer<T> {
    static final ResourceLocation LASER = new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/shot/laser.png");
    static final ResourceLocation LIGHT = new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/shot/musou_fuuin.png");

    public THLaserRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.shadowRadius = 0.0F;
    }

    @Override
    public boolean shouldRender(T laser, Frustum frustum, double x, double y, double z) {
        return laser.shouldRenderAtSqrDistance(laser.distanceToSqr(x, y, z)); // ignoreFrustumCheck
    }

    @Override
    public void render(T laser, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers, int light) {
        X1Tess t = new X1Tess(pose, buffers, getTextureLocation(laser));
        int color = laser.getShotId();
        boolean setLaser = laser instanceof THSetLaserEntity;
        float width = 1.0F;
        if (laser.getAnimationCount() < 0 && setLaser) width = 0.1F;
        double length = laser.getLaserLength();
        float size = laser.getShotSize();
        int ticks = laser.tickCount;

        pose.pushPose();
        if (laser.getAnimationCount() < 0 && !setLaser) {
            int delayCount = Math.min(-laser.getAnimationCount(), 10);
            float size2 = Math.min(delayCount * size * 2F, 1.0F);
            pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
            pose.mulPose(Axis.YP.rotationDegrees(180.0F));
            renderLightEffect(t, pose, color % 8, size2, laser.getAnimationCount());
        } else {
            pose.mulPose(Axis.YP.rotationDegrees(yaw));
            pose.mulPose(Axis.XP.rotationDegrees(-laser.getXRot()));
            double centerZ1 = length * 1.2D / 2.0D;
            double centerZ2 = length / 2.0D;
            if (color >= 24) { // Master Spark laser
                pose.scale(width, width, 1.0F);
                float sparkTicks = Math.abs((float) laser.getAnimationCount() * 10.0F);
                renderMasterSparkLaser(t, SPARK_CORE, length, size, 1.0F, false, sparkTicks);
                renderMasterSparkLaser(t, SPARK_GLOW, length, size * 1.2F, 0.6F, true, sparkTicks);
            } else if (color >= 16) { // Laevateinn
                pose.mulPose(Axis.ZP.rotationDegrees(laser.getAngleZ()));
                pose.scale(1.0F, 1.0F, 1.0F * (float) length / 20.8F);
                X1LaserModels.renderLaevateinn(t, ADD_ALPHA_DEPTH, 1.6D, 7, 1.0F, ticks);
                pose.scale(1.2F, 1.2F, 1.2F);
                X1LaserModels.renderLaevateinn(t, INVERT_ADD, 1.0D, color, 0.6F, ticks);
            } else if (color >= 8) { // Spear the Gungnir
                pose.mulPose(Axis.ZP.rotationDegrees((float) ticks * 30F));
                pose.scale(0.3F, 0.3F, 0.5F * (float) length / 10F);
                X1LaserModels.renderSpearTheGungnir(t, ADD_ALPHA_DEPTH, centerZ1 - centerZ2, 7, 1.0F);
                pose.scale(1.2F, 1.2F, 1.2F);
                X1LaserModels.renderSpearTheGungnir(t, INVERT_ADD, -1.0D, color, 0.6F);
            } else {
                pose.scale(width, width, 1.0F);
                renderLaser(t, ADD_ALPHA_DEPTH_CULL, length, size, centerZ1 - centerZ2, 7, 1.0F);
                renderLaser(t, INVERT_ADD_CULL, length * 1.2D, size * 1.2F, 0.0D, color, 0.6F);
            }
        }
        pose.popPose();
    }

    // renderLaser: a 13-segment, 8-sided tube whose radius follows a half sine.
    private static void renderLaser(X1Tess t, X1Tess.State state, double length, float width, double zPos, int color,
                                    float alpha) {
        float maxWidth = width;
        int zAngleDivNum = 8;
        double angleZ = 0F;
        double angleSpanZ = Math.PI * 2.0D / (double) zAngleDivNum;
        int zDivNum = 13;
        double zDivLength = length / (double) (zDivNum - 1);
        double zPosOld = zPos;
        float angle = -(float) Math.PI / 2.0F;
        float angleSpan = (float) Math.PI / (float) zDivNum;
        angle += angleSpan;
        float widthOld = 0.0F;
        t.begin(state).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], alpha);
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

    // renderMasterSparkLaser: a widening tube; the second pass is the rainbow ring colours.
    static void renderMasterSparkLaser(X1Tess t, X1Tess.State state, double length, float width, float alpha,
                                       boolean rainbow, float ticks) {
        float maxWidth = width * 1.6F;
        int zAngleDivNum = rainbow ? 64 : 16;
        double angleSpanZ = Math.PI * 2.0D / (double) zAngleDivNum;
        int zDivNum = 13;
        double zDivLength = length / (double) (zDivNum - 1);
        double zPos = 0.0D;
        double zPosOld = zPos;
        float xPosOld = 0F, yPosOld = 0F, xPos2Old = 0F, yPos2Old = 0F;
        float angle = 0F;
        float angleSpan = (float) Math.PI / (float) (zDivNum - 1);
        width = (float) Math.sin(angle) * maxWidth;
        float colorAngle = 0F;
        float colorRev = 3.141593F * 5.6125F / 180F;
        float width2 = width;
        float widthOld2;
        t.begin(state);
        while (zPos < length) {
            zPos += zDivLength;
            float widthOld = width;
            angle += angleSpan;
            width = width < maxWidth ? (float) Math.sin(angle) * maxWidth : maxWidth;
            widthOld2 = width2;
            width2 = width * ((float) Math.sin(angle + ticks / 40F) * 0.1F + 1.0F);
            double angleZ = angleSpanZ;
            for (int i = 0; i <= zAngleDivNum; i++) {
                float xPos = (float) Math.cos(angleZ) * width2, yPos = (float) Math.sin(angleZ) * width2;
                float xPos2 = (float) Math.cos(angleZ) * widthOld2, yPos2 = (float) Math.sin(angleZ) * widthOld2;
                if (rainbow) {
                    float c = (colorAngle + ticks) * colorRev;
                    colorAngle++;
                    t.color(Mth.sin(c), Mth.cos(c), -Mth.sin(c) * 2F, 0.60F);
                } else {
                    t.color(1.0F, 1.0F, 1.0F, alpha);
                }
                t.v(xPosOld, yPosOld, zPos, 0F, 0F).v(xPos, yPos, zPos, 1F, 0F)
                        .v(xPos2, yPos2, zPosOld, 1F, 1F).v(xPos2Old, yPos2Old, zPosOld, 0F, 1F);
                xPosOld = xPos;
                yPosOld = yPos;
                xPos2Old = xPos2;
                yPos2Old = yPos2;
                angleZ += angleSpanZ;
            }
            ticks += 1.0F;
            zPosOld = zPos;
        }
    }

    // RenderTHLaser.renderLightEffect (blend GL_SRC_ALPHA, GL_ONE; depthMask false)
    private static void renderLightEffect(X1Tess t, PoseStack pose, int color, float size, int animation) {
        color %= 8;
        int count = animation % 2;
        float f3 = (float) (count * 32) / 64F, f4 = (float) (count * 32 + 32) / 64F;
        float f8 = 0.5F, f9 = 0.25F;
        pose.scale(size, size, size);
        t.begin(ADD_ALPHA).color(RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.5F)
                .v(-f8, -f9, 0, f3, 1F).v(1F - f8, -f9, 0, f4, 1F).v(1F - f8, 1F - f9, 0, f4, 0F).v(-f8, 1F - f9, 0, f3, 0F);
    }

    @Override
    public ResourceLocation getTextureLocation(T laser) {
        return laser.getAnimationCount() < 0 && !(laser instanceof THSetLaserEntity) ? LIGHT : LASER;
    }
}
