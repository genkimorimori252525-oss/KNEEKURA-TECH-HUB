package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.DragonNeckJewelEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;

import java.util.Random;

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.CUTOUT;

/** Port of X1 RenderRyuuLightningBolt: a one-block billboard from thKaguyaTerrain, flickering between cells 16..20. */
public final class DragonNeckJewelRenderer extends EntityRenderer<DragonNeckJewelEntity> {
    private static final ResourceLocation TEXTURE =
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/th_kaguya_terrain.png");
    private final Random random = new Random();

    public DragonNeckJewelRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public void render(DragonNeckJewelEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers,
                       int light) {
        int color = 1 + 16;
        if (random.nextInt(3) == 0) color = random.nextInt(5) + 16;
        float f3 = (float) ((color % 16) * 16) / 256F, f4 = (float) ((color % 16) * 16 + 16) / 256F;
        float f5 = (float) ((color / 16) * 16) / 256F, f6 = (float) ((color / 16) * 16 + 16) / 256F;
        float f7 = 1.0F, f8 = 0.5F, f9 = 0.25F;
        pose.pushPose();
        pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
        pose.mulPose(Axis.YP.rotationDegrees(180.0F));
        new X1Tess(pose, buffers, TEXTURE).begin(CUTOUT)
                .v(0.0F - f8, 0.0F - f9, 0.0D, f3, f6).v(f7 - f8, 0.0F - f9, 0.0D, f4, f6)
                .v(f7 - f8, 1.0F - f9, 0.0D, f4, f5).v(0.0F - f8, 1.0F - f9, 0.0D, f3, f5);
        pose.popPose();
    }

    @Override
    public ResourceLocation getTextureLocation(DragonNeckJewelEntity e) {
        return TEXTURE;
    }
}
