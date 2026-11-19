package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.ShotMaterialEntity;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardCircleEntity;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardRegistry;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.CUTOUT;
import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD_DEPTH;

/** Ports of X1 RenderSpellCard, RenderSpellCardCircle and RenderShotMaterial. */
public final class SpellCardRenderers {
    private SpellCardRenderers() {}

    static ResourceLocation tex(String path) {
        return new ResourceLocation(FiveDifficultiesPort.MOD_ID, path);
    }

    /** RenderSpellCard: the card spins 21 degrees per tick, tilted 30 degrees, art then level frame. */
    public static final class Card extends EntityRenderer<SpellCardEntity> {
        public Card(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(SpellCardEntity card, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            X1SpellCardRegistry.Entry entry = X1SpellCardRegistry.get(card.getSpellCardNumber());
            if (entry == null) return;
            float rvl = 14F / 128F, rul = 0.0F, rvr = 114F / 128F, rur = 1.00F;
            pose.pushPose();
            pose.mulPose(Axis.YP.rotationDegrees((float) card.tickCount * 21F));
            pose.mulPose(Axis.ZP.rotationDegrees(30F));
            X1Tess art = new X1Tess(pose, buffers, getTextureLocation(card));
            art.begin(CUTOUT).v(0.2F, 0.3F, 0, rvl, rul).v(-0.2F, 0.3F, 0, rvr, rul).v(-0.2F, -0.3F, 0, rvr, rur).v(0.2F, -0.3F, 0, rvl, rur);
            art.begin(CUTOUT).v(-0.2F, 0.3F, 0, rvl, rul).v(0.2F, 0.3F, 0, rvr, rul).v(0.2F, -0.3F, 0, rvr, rur).v(-0.2F, -0.3F, 0, rvl, rur);
            int lv = entry.create().getNeedLevel();
            X1Tess frame = new X1Tess(pose, buffers, tex("textures/item/spellcard/spellcard_lv" + lv + ".png"));
            frame.begin(CUTOUT).v(0.2F, 0.3F, 0.001D, rvl, rul).v(-0.2F, 0.3F, 0.001D, rvr, rul).v(-0.2F, -0.3F, 0.001D, rvr, rur).v(0.2F, -0.3F, 0.001D, rvl, rur);
            frame.begin(CUTOUT).v(-0.2F, 0.3F, -0.001D, rvl, rul).v(0.2F, 0.3F, -0.001D, rvr, rul).v(0.2F, -0.3F, -0.001D, rvr, rur).v(-0.2F, -0.3F, -0.001D, rvl, rur);
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(SpellCardEntity card) {
            X1SpellCardRegistry.Entry entry = X1SpellCardRegistry.get(card.getSpellCardNumber());
            return tex("textures/item/spellcard/" + (entry == null ? "spellcard_frame" : entry.key()) + ".png");
        }
    }

    /** RenderSpellCardCircle (colours are 0..255 values passed to setColorRGBA_F, so they clamp to 0 / 1). */
    public static final class Circle extends EntityRenderer<SpellCardCircleEntity> {
        private static final float[] R = {255F, 255F, 255F, 0F, 0F, 0F, 255F};
        private static final float[] G = {0F, 165F, 255F, 255F, 0F, 255F, 0F};
        private static final float[] B = {0F, 0F, 0F, 0F, 255F, 255F, 255F};
        private static final ResourceLocation TEXTURE = tex("textures/entity/shot/familiar.png");

        public Circle(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public boolean shouldRender(SpellCardCircleEntity e, Frustum frustum, double x, double y, double z) {
            return true;
        }

        @Override
        public void render(SpellCardCircleEntity circle, float yaw, float partialTick, PoseStack pose,
                           MultiBufferSource buffers, int light) {
            pose.pushPose();
            float size = circle.getCircleSize() * 6.0F;
            pose.scale(size, size, size);
            int color = circle.getCircleType();
            if (color >= 16) {
                float angle = Mth.sin(2F * (float) circle.getAnimationCount() / 180F * (float) Math.PI) * 40F;
                var cam = this.entityRenderDispatcher.camera;
                pose.mulPose(Axis.YP.rotationDegrees(180F - cam.getYRot() + angle));
                pose.mulPose(Axis.XP.rotationDegrees(-cam.getXRot() - angle));
                pose.mulPose(Axis.ZP.rotationDegrees(circle.getAnimationCount() * 5F));
                color %= 16;
            } else {
                pose.mulPose(Axis.XP.rotationDegrees(90F));
                pose.mulPose(Axis.ZP.rotationDegrees(circle.getAnimationCount() * 5F));
            }
            X1Tess t = new X1Tess(pose, buffers, TEXTURE).begin(INVERT_ADD_DEPTH);
            if (color == 9) {
                float rainbowTime = circle.tickCount / 3.0F;
                t.color(Mth.sin(rainbowTime), Mth.cos(rainbowTime), -Mth.sin(rainbowTime) * 2F, 1.0F);
            } else {
                color %= 8;
                int c = Math.min(color, 6); // X1 indexes a 7-entry table
                t.color(Math.min(R[c], 1F), Math.min(G[c], 1F), Math.min(B[c], 1F), 1.0F);
            }
            t.v(-0.6F, -0.6F, 0, 0F, 1F).v(0.6F, -0.6F, 0, 1F, 1F).v(0.6F, 0.6F, 0, 1F, 0F).v(-0.6F, 0.6F, 0, 0F, 0F);
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(SpellCardCircleEntity e) {
            return TEXTURE;
        }
    }

    /** RenderShotMaterial: a 0.4 block billboard. */
    public static final class ShotMaterial extends EntityRenderer<ShotMaterialEntity> {
        private static final ResourceLocation TEXTURE = tex("textures/item/material/shot_material.png");

        public ShotMaterial(EntityRendererProvider.Context context) {
            super(context);
        }

        @Override
        public void render(ShotMaterialEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light) {
            pose.pushPose();
            pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
            pose.mulPose(Axis.YP.rotationDegrees(180.0F));
            new X1Tess(pose, buffers, TEXTURE).begin(CUTOUT)
                    .v(-0.2F, 0.2F, 0, 0F, 0F).v(0.2F, 0.2F, 0, 1F, 0F).v(0.2F, -0.2F, 0, 1F, 1F).v(-0.2F, -0.2F, 0, 0F, 1F);
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(ShotMaterialEntity e) {
            return TEXTURE;
        }
    }
}
