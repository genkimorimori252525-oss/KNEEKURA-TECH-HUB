package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.client.mob.SunFlowerFairyModel;
import dev.kneekura.fivedifficulties.forge.client.mob.THFairyModel;
import dev.kneekura.fivedifficulties.forge.entity.mob.FamiliarEntity;
import dev.kneekura.fivedifficulties.forge.entity.mob.SunFlowerFairyEntity;
import dev.kneekura.fivedifficulties.forge.entity.mob.THFairyEntity;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.ADD_ONE;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD;

/** Renderers for the P17 danmaku mobs. */
public final class P17Renderers {
    private P17Renderers() {}

    public static final ModelLayerLocation FAIRY_LAYER = layer("th_fairy");
    public static final ModelLayerLocation SUNFLOWER_FAIRY_LAYER = layer("sunflower_fairy");
    public static final ModelLayerLocation RUMIA_LAYER = layer("rumia");

    private static ModelLayerLocation layer(String name) {
        return new ModelLayerLocation(new ResourceLocation(FiveDifficultiesPort.MOD_ID, name), "main");
    }

    static ResourceLocation mob(String name) {
        return new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/mob/" + name + ".png");
    }

    /** RenderTHFairy (shadow 0.25): FairyTexture_(pattern % 3), the zombie fairy texture for form < 0. */
    public static final class THFairy extends MobRenderer<THFairyEntity, THFairyModel<THFairyEntity>> {
        private static final ResourceLocation[] FAIRY = {mob("fairy_0"), mob("fairy_1"), mob("fairy_2")};
        private static final ResourceLocation ZOMBIE = mob("zombie_fairy");

        public THFairy(EntityRendererProvider.Context context) {
            super(context, new THFairyModel<>(context.bakeLayer(FAIRY_LAYER)), 0.25F);
        }

        @Override
        public ResourceLocation getTextureLocation(THFairyEntity fairy) {
            if (fairy.getForm() < 0) return ZOMBIE;
            return FAIRY[Math.floorMod(fairy.getDanmakuPattern(), 3)];
        }
    }

    /** RenderSunFlowerFairy (shadow 0.25): FairyTexture_10. */
    public static final class SunFlowerFairy extends MobRenderer<SunFlowerFairyEntity, SunFlowerFairyModel> {
        private static final ResourceLocation TEX = mob("fairy_10");

        public SunFlowerFairy(EntityRendererProvider.Context context) {
            super(context, new SunFlowerFairyModel(context.bakeLayer(SUNFLOWER_FAIRY_LAYER)), 0.25F);
        }

        @Override
        public ResourceLocation getTextureLocation(SunFlowerFairyEntity fairy) {
            return TEX;
        }
    }

    /** RenderFamiliar: a camera-facing, spinning, pulsing (3 ± 0.6) inverted-add disc tinted by its form. */
    public static final class Familiar extends EntityRenderer<FamiliarEntity> {
        private static final ResourceLocation TEX = new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/shot/familiar.png");

        public Familiar(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(FamiliarEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers, int light) {
            if (e.getForm() < 0) return;
            pose.pushPose();
            float size = 3.0F + (float) Math.sin(e.tickCount * 10 / 180.0D * Math.PI) * 0.6F;
            pose.scale(size, size, size);
            pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
            pose.mulPose(Axis.YP.rotationDegrees(180.0F));
            pose.mulPose(Axis.ZP.rotationDegrees(e.tickCount * 5F));
            int color = e.getForm() % 8;
            new X1Tess(pose, buffers, TEX).begin(INVERT_ADD)
                    .color(Mth.sin(color), Mth.cos(color), -Mth.sin(color) * 2F, 0.60F)
                    .v(-0.6F, -0.6F, 0.0D, 0F, 1F).v(0.6F, -0.6F, 0.0D, 1F, 1F).v(0.6F, 0.6F, 0.0D, 1F, 0F).v(-0.6F, 0.6F, 0.0D, 0F, 0F);
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(FamiliarEntity e) {
            return TEX;
        }
    }

    /** RenderTHPhantom: three shrinking, drifting camera-facing wisps (additive), tinted by form, red when hurt. */
    public static final class Phantom extends EntityRenderer<dev.kneekura.fivedifficulties.forge.entity.mob.PhantomEntity> {
        private static final ResourceLocation TEX = new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/shot/musou_fuuin.png");
        private static final float[] R = {224F / 255F, 0F, 0F, 224F / 255F, 224F / 255F, 0F, 1F, 1F};
        private static final float[] G = {0F, 0F, 224F / 255F, 64F / 255F, 0F, 224F / 255F, 128F / 255F, 1F};
        private static final float[] B = {0F, 224F / 255F, 0F, 0F, 224F / 255F, 224F / 255F, 0F, 1F};

        public Phantom(EntityRendererProvider.Context context) {
            super(context);
            this.shadowRadius = 0.25F;
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.mob.PhantomEntity e, float yaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            pose.pushPose();
            int color = Math.floorMod(e.getForm(), 8);
            double t = (double) e.tickCount / 180.0D * Math.PI;
            pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
            pose.mulPose(Axis.YP.rotationDegrees(180.0F));
            X1Tess tess = new X1Tess(pose, buffers, TEX);
            part(tess, color, t, e.hurtTime);
            pose.translate((float) Math.sin(t * 5) * 0.2F, 0.1F + (e.tickCount % 20) * 0.06F, 0F);
            float size = 0.9F * ((20F - (float) (e.tickCount % 20)) / 20F);
            pose.scale(size, size, size);
            part(tess, color, t, e.hurtTime);
            pose.translate((float) Math.cos(t * 5) * 0.2F, 0.1F + (e.tickCount % 20) * 0.07F, 0F);
            size = 0.8F * ((20F - (float) (e.tickCount % 20)) / 20F);
            pose.scale(size, size, size);
            part(tess, color, t, e.hurtTime);
            pose.popPose();
        }

        private static void part(X1Tess t, int c, double r, int damage) {
            float umin = 0F, umax = 32F / 64F, vmin = 0F, vmax = 1F;
            float alpha = (40F - (float) damage) / 40F;
            t.begin(ADD_ONE).color(R[c] * 0.3F, G[c] * 0.3F, B[c] * 0.3F, 0.3F * alpha)
                    .v(-0.7F + Math.sin(r * 3.0D) * 0.1F, -0.2F - Math.cos(r * 7.0D) * 0.1F, 0.0D, umin, vmax)
                    .v(0.7F - Math.cos(r * 4.0D) * 0.1F, -0.2F - Math.sin(r * 5.0D) * 0.1F, 0.0D, umax, vmax)
                    .v(0.7F + Math.sin(r * 5.0D) * 0.1F, 1.2F + Math.cos(r * 4.0D) * 0.1F, 0.0D, umax, vmin)
                    .v(-0.7F - Math.cos(r * 7.0D) * 0.1F, 1.2F + Math.sin(r * 3.0D) * 0.1F, 0.0D, umin, vmin);
            t.color(R[c] * 0.3F, G[c] * 0.3F, B[c] * 0.3F, 0.7F * alpha)
                    .v(-0.6F - Math.cos(r * 7.0D) * 0.1F, -0.1F + Math.sin(r * 5.0D) * 0.1F, 0.001D, umin, vmax)
                    .v(0.6F + Math.sin(r * 3.0D) * 0.1F, -0.1F + Math.cos(r * 4.0D) * 0.1F, 0.001D, umax, vmax)
                    .v(0.6F - Math.cos(r * 4.0D) * 0.1F, 1.1F - Math.sin(r * 3.0D) * 0.1F, 0.001D, umax, vmin)
                    .v(-0.6F + Math.sin(r * 5.0D) * 0.1F, 1.1F - Math.cos(r * 7.0D) * 0.1F, 0.001D, umin, vmin);
            for (int i = 0; i < 3; i++) {
                if (damage > 0) t.color(1.0F, 0.0F, 0.0F, alpha);
                else t.color(1F, 1F, 1F, 1F);
                t.v(-0.5F, 0.0F, 0.002D, umin, vmax).v(0.5F, 0.0F, 0.002D, umax, vmax)
                        .v(0.5F, 1.0F, 0.002D, umax, vmin).v(-0.5F, 1.0F, 0.002D, umin, vmin);
            }
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.mob.PhantomEntity e) {
            return TEX;
        }
    }

    /** X1's renderDark sphere (18 × 9 quads) of {@code width}, white at {@code alpha}. */
    static void darkSphere(X1Tess t, float width, float alpha) {
        float maxWidth = width / 2.0F;
        int zAngleDivNum = 18, zDivNum = 9;
        double angleSpanZ = Math.PI * 2.0D / (double) zAngleDivNum;
        double zPos, zPosOld = Math.sin(-Math.PI / 2.0D) * maxWidth;
        float angle = -(float) Math.PI / 2.0F, angleSpan = (float) Math.PI / (float) zDivNum;
        angle += angleSpan;
        float widthOld = 0.0F;
        for (int j = 0; j < zDivNum; j++) {
            zPos = Math.sin(angle) * maxWidth;
            float w = (float) Math.cos(angle) * maxWidth;
            double angleZ = 0D;
            float xo = (float) Math.cos(angleZ) * w, yo = (float) Math.sin(angleZ) * w;
            float x2o = (float) Math.cos(angleZ) * widthOld, y2o = (float) Math.sin(angleZ) * widthOld;
            angleZ = angleSpanZ;
            for (int i = 1; i <= zAngleDivNum; i++) {
                float x = (float) Math.cos(angleZ) * w, y = (float) Math.sin(angleZ) * w;
                float x2 = (float) Math.cos(angleZ) * widthOld, y2 = (float) Math.sin(angleZ) * widthOld;
                t.color(1.0F, 1.0F, 1.0F, alpha).v(x, y, zPos, 1.0F, 0.0F).v(xo, yo, zPos, 0.0F, 0.0F)
                        .v(x2o, y2o, zPosOld, 0.0F, 1.0F).v(x2, y2, zPosOld, 1.0F, 1.0F);
                xo = x;
                yo = y;
                x2o = x2;
                y2o = y2;
                angleZ += angleSpanZ;
            }
            zPosOld = zPos;
            angle += angleSpan;
            widthOld = w;
        }
    }

    /** RenderRumia: the boss plus a 12-wide darkening sphere 1.3 up (drawn over everything from within 6). */
    public static final class Rumia extends THBossRenderer<dev.kneekura.fivedifficulties.forge.entity.mob.RumiaEntity,
            dev.kneekura.fivedifficulties.forge.client.mob.RumiaModel> {
        private static final ResourceLocation TEX = mob("rumia");

        public Rumia(EntityRendererProvider.Context context) {
            super(context, new dev.kneekura.fivedifficulties.forge.client.mob.RumiaModel(context.bakeLayer(RUMIA_LAYER)), 0.25F);
        }

        @Override
        public void render(dev.kneekura.fivedifficulties.forge.entity.mob.RumiaEntity e, float yaw, float partialTick,
                           PoseStack pose, MultiBufferSource buffers, int light) {
            super.render(e, yaw, partialTick, pose, buffers, light);
            boolean near = this.entityRenderDispatcher.distanceToSqr(e) < 36.0D;
            pose.pushPose();
            pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
            pose.mulPose(Axis.YP.rotationDegrees(180.0F));
            pose.translate(0.0F, 1.3F, 0.0F);
            darkSphere(new X1Tess(pose, buffers, SakuyaTimeControllerRenderer.DARK_TEXTURE)
                    .begin(near ? X1Tess.State.DARKEN_ALWAYS : X1Tess.State.DARKEN), 12.0F, 1.0F);
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(dev.kneekura.fivedifficulties.forge.entity.mob.RumiaEntity e) {
            return TEX;
        }
    }

    /** A RenderTHBoss subclass that only picks the model and texture (X1's RenderCirno, RenderSakuya, ...). */
    public static final class SimpleBoss<T extends dev.kneekura.fivedifficulties.forge.entity.mob.DanmakuMobEntity,
            M extends net.minecraft.client.model.EntityModel<T>> extends THBossRenderer<T, M> {
        private final ResourceLocation texture;

        public SimpleBoss(EntityRendererProvider.Context context, M model, String texture) {
            super(context, model, 0.25F);
            this.texture = mob(texture);
        }

        private boolean fullBright;

        /** X1 getBrightness 1.0 (Wriggle): drawn at full light. */
        public SimpleBoss<T, M> bright() {
            this.fullBright = true;
            return this;
        }

        @Override
        protected int getBlockLightLevel(T e, net.minecraft.core.BlockPos pos) {
            return fullBright ? 15 : super.getBlockLightLevel(e, pos);
        }

        @Override
        protected int getSkyLightLevel(T e, net.minecraft.core.BlockPos pos) {
            return fullBright ? 15 : super.getSkyLightLevel(e, pos);
        }

        @Override
        public ResourceLocation getTextureLocation(T e) {
            return texture;
        }
    }

    /** A plain RenderLiving (no boss plate): X1's RenderRinnosuke. */
    public static final class Plain<T extends net.minecraft.world.entity.Mob, M extends net.minecraft.client.model.EntityModel<T>>
            extends net.minecraft.client.renderer.entity.MobRenderer<T, M> {
        private final ResourceLocation texture;

        public Plain(EntityRendererProvider.Context context, M model, String texture) {
            super(context, model, 0.25F);
            this.texture = mob(texture);
        }

        @Override
        public ResourceLocation getTextureLocation(T e) {
            return texture;
        }
    }

    public static ModelLayerLocation mobLayer(String name) {
        return layer(name);
    }
}
