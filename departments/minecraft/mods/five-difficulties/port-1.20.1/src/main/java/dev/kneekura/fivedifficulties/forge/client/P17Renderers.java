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

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.INVERT_ADD;

/** Renderers for the P17 danmaku mobs. */
public final class P17Renderers {
    private P17Renderers() {}

    public static final ModelLayerLocation FAIRY_LAYER = layer("th_fairy");
    public static final ModelLayerLocation SUNFLOWER_FAIRY_LAYER = layer("sunflower_fairy");

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
}
