package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import org.joml.Matrix4f;

import java.util.HashSet;
import java.util.Set;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.*;

/**
 * Port of X1 {@code RenderTHShot}. P8 covers the delay light and every form drawn by
 * {@code renderNormalShot} (SMALL, TINY, MEDIUM, PEARL, CIRCLE, HEART, BIG); other forms are
 * not drawn yet and are logged once.
 */
public final class THShotRenderer extends EntityRenderer<THShotEntity> {
    private static ResourceLocation tex(String name) {
        return new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/shot/" + name + ".png");
    }

    static final ResourceLocation SMALL = tex("small_shot");
    static final ResourceLocation PEARL = tex("pearl_shot");
    static final ResourceLocation CIRCLE = tex("circle_shot");
    static final ResourceLocation HEART = tex("heart_shot");
    static final ResourceLocation BIG = tex("big_shot");
    /** X1 resourceLocation_Light = MusouFuuin.png. */
    static final ResourceLocation LIGHT = tex("musou_fuuin");

    private static final Set<Integer> WARNED_FORMS = new HashSet<>();

    public THShotRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.shadowRadius = 0.0F; // X1 getShadowSize = 0
    }

    @Override
    public void render(THShotEntity shot, float entityYaw, float partialTick, PoseStack pose,
                       MultiBufferSource buffers, int packedLight) {
        float size = shot.getShotSize();
        int color = shot.getShotColor();
        int form = shot.getShotForm();
        int animation = shot.getAnimationCount();

        pose.pushPose();
        if (animation < 0) {
            // Delay: only the light is visible.
            int delayCount = Math.min(-animation, 10);
            float size2 = Math.min(delayCount * 0.3F * size, 1.0F);
            billboard(pose);
            renderLightEffect(pose, buffers, color, size2, animation);
        } else if (X1ShotTables.isNormalSpriteForm(form)) {
            renderNormalShot(pose, buffers, texture(form), size, color, form == FORM_BIG);
        } else if (WARNED_FORMS.add(form)) {
            FiveDifficultiesPort.LOGGER.warn("X1 shot form {} has no P8 renderer yet", form);
        }
        pose.popPose();
    }

    private void billboard(PoseStack pose) {
        // THKaguyaRenderLib.getGLRotatefByTherdPersonView: always face the camera.
        pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
        pose.mulPose(Axis.YP.rotationDegrees(180.0F));
    }

    private void renderNormalShot(PoseStack pose, MultiBufferSource buffers, ResourceLocation texture, float size,
                                  int color, boolean blend) {
        pose.scale(size, size, size);
        billboard(pose);
        RenderType type = blend ? X1RenderTypes.SHOT_ADDITIVE.apply(texture) : X1RenderTypes.SHOT_CUTOUT.apply(texture);
        float u1 = (float) color / 8F;
        float u2 = (float) (color + 1) / 8F;
        quad(pose, buffers.getBuffer(type), u1, u2, 0F, 1F, 1F, 1F, 1F, 1F);
    }

    /** renderLightEffect: two 32px frames of MusouFuuin.png, frame = count % 2 (Java remainder). */
    private void renderLightEffect(PoseStack pose, MultiBufferSource buffers, int color, float size, int count) {
        count = count % 2;
        float u1 = (float) (count * 32) / 64F;
        float u2 = (float) (count * 32 + 32) / 64F;
        pose.scale(size, size, size);
        quad(pose, buffers.getBuffer(X1RenderTypes.LIGHT_EFFECT.apply(LIGHT)), u1, u2, 0F, 1F,
                RENDER_COLOR_R[color], RENDER_COLOR_G[color], RENDER_COLOR_B[color], 0.5F);
    }

    private static void quad(PoseStack pose, VertexConsumer vc, float u1, float u2, float v1, float v2,
                             float r, float g, float b, float a) {
        Matrix4f m = pose.last().pose();
        int light = LightTexture.FULL_BRIGHT;
        vc.vertex(m, -1F, -1F, 0F).color(r, g, b, a).uv(u1, v2).uv2(light).endVertex();
        vc.vertex(m, 1F, -1F, 0F).color(r, g, b, a).uv(u2, v2).uv2(light).endVertex();
        vc.vertex(m, 1F, 1F, 0F).color(r, g, b, a).uv(u2, v1).uv2(light).endVertex();
        vc.vertex(m, -1F, 1F, 0F).color(r, g, b, a).uv(u1, v1).uv2(light).endVertex();
    }

    static ResourceLocation texture(int form) {
        return switch (form) {
            case FORM_PEARL -> PEARL;
            case FORM_CIRCLE -> CIRCLE;
            case FORM_HEART -> HEART;
            case FORM_BIG -> BIG;
            default -> SMALL; // SMALL, TINY, MEDIUM share SmallShot.png
        };
    }

    @Override
    public ResourceLocation getTextureLocation(THShotEntity shot) {
        return shot.getAnimationCount() < 0 ? LIGHT : texture(shot.getShotForm());
    }
}
