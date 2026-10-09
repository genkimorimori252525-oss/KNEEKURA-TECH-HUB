package com.example.kirby_mod.client;

import com.example.kirby_mod.entity.KirbyEntity;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.util.Mth;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

public class KirbyRenderer extends GeoEntityRenderer<KirbyEntity> {
    public KirbyRenderer(EntityRendererProvider.Context context) {
        super(context, new KirbyModel());
        this.shadowRadius = 0.6F;
        this.scaleWidth = 1.5F;
        this.scaleHeight = 1.5F;
    }

    @Override
    public void render(KirbyEntity entity, float entityYaw, float partialTick, PoseStack poseStack,
                       MultiBufferSource bufferSource, int packedLight) {
        float scale = entity.getMouthRenderScale(partialTick);
        this.shadowRadius = 0.6F * scale;
        poseStack.pushPose();
        poseStack.scale(scale, scale, scale);
        super.render(entity, entityYaw, partialTick, poseStack, bufferSource, packedLight);
        poseStack.popPose();
    }

    @Override
    protected void applyRotations(KirbyEntity entity, PoseStack poseStack, float ageInTicks,
                                  float rotationYaw, float partialTick) {
        super.applyRotations(entity, poseStack, ageInTicks, rotationYaw, partialTick);
        if (!entity.isKirbySwimming()) return;
        float pitch = Mth.lerp(partialTick, entity.xRotO, entity.getXRot());
        float pivotY = entity.getBbHeight() * 0.5F;
        poseStack.translate(0.0D, pivotY, 0.0D);
        poseStack.mulPose(Axis.XP.rotationDegrees(pitch));
        poseStack.translate(0.0D, -pivotY, 0.0D);
    }
}
