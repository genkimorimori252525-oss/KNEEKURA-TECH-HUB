package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.THItemEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.CUTOUT;

/** Port of X1 RenderTHItem: a 0.8-block billboard of the item's own icon. */
public final class THItemRenderer extends EntityRenderer<THItemEntity> {
    private static ResourceLocation tex(String name) {
        return new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/item/" + name + ".png");
    }

    private static final ResourceLocation SMALL_POWER = tex("power_item_small");
    private static final ResourceLocation BIG_POWER = tex("power_item_big");
    private static final ResourceLocation POINT = tex("point_item");
    private static final ResourceLocation BOMB = tex("bomb_item");
    private static final ResourceLocation EXTEND = tex("extend_item");

    public THItemRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public void render(THItemEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers, int light) {
        pose.pushPose();
        pose.scale(2.0F, 2.0F, 2.0F);
        pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
        pose.mulPose(Axis.YP.rotationDegrees(180.0F));
        new X1Tess(pose, buffers, getTextureLocation(e)).begin(CUTOUT)
                .v(0.2F, 0.2F, 0, 1F, 0F).v(-0.2F, 0.2F, 0, 0F, 0F).v(-0.2F, -0.2F, 0, 0F, 1F).v(0.2F, -0.2F, 0, 1F, 1F);
        pose.popPose();
    }

    @Override
    public ResourceLocation getTextureLocation(THItemEntity e) {
        return switch (e.getItemType()) {
            case THItemEntity.ITEM_ID_BIGPOWER -> BIG_POWER;
            case THItemEntity.ITEM_ID_POINT -> POINT;
            case THItemEntity.ITEM_ID_BOMB -> BOMB;
            case THItemEntity.ITEM_ID_EXTEND -> EXTEND;
            default -> SMALL_POWER;
        };
    }
}
