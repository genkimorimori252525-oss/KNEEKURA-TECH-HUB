package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.mob.DanmakuMobEntity;
import net.minecraft.client.gui.Font;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.phys.Vec3;

import static dev.kneekura.fivedifficulties.forge.client.X1Tess.State.CUTOUT;

/**
 * Port of X1 {@code RenderTHBoss}: the mob, then (while it has a danmaku pattern and is within 20° of the view
 * centre) a status plate 1.5 above its head, scaled with distance up to 5: a frame, a health bar (blue normally,
 * the spell-card bar while a card is used), its name in green and the card name in white.
 */
public abstract class THBossRenderer<T extends DanmakuMobEntity, M extends EntityModel<T>> extends MobRenderer<T, M> {
    private static final ResourceLocation STATUS = new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/entity/mob/status.png");

    protected THBossRenderer(EntityRendererProvider.Context context, M model, float shadow) {
        super(context, model, shadow);
    }

    @Override
    public void render(T mob, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers, int light) {
        super.render(mob, yaw, partialTick, pose, buffers, light);
        renderStatus(mob, partialTick, pose, buffers);
    }

    private void renderStatus(T mob, float partialTick, PoseStack pose, MultiBufferSource buffers) {
        if (mob.getDanmakuPattern() == DanmakuMobEntity.NOT_ATTACK) return;
        var camera = this.entityRenderDispatcher.camera;
        float viewY = camera.getYRot() % 360F;
        if (viewY > 180F) viewY -= 360F;
        else if (viewY <= -180F) viewY += 360F;
        float viewX = camera.getXRot();
        double rad = Math.PI / 180D;
        Vec3 look = new Vec3(-Math.sin(viewY * rad) * Math.cos(viewX * rad), -Math.sin(viewX * rad), Math.cos(viewY * rad) * Math.cos(viewX * rad));
        Vec3 toEntity = mob.getPosition(partialTick).subtract(camera.getPosition());
        double len = toEntity.length();
        float span = len == 0 ? 0F : (float) (Math.acos(Math.max(-1, Math.min(1, look.dot(toEntity) / len))) / rad);
        if (Math.abs(span) > 20F) return;
        float alpha = 1F - (Math.abs(span) - 20F) / 30F;
        float size = Math.min(5.0F, 1.0F + (float) len / 64F);
        pose.pushPose();
        pose.translate(0.0F, mob.getBbHeight() + 1.5F, 0.0F);
        pose.scale(size, size, size);
        pose.mulPose(this.entityRenderDispatcher.cameraOrientation());
        pose.mulPose(Axis.YP.rotationDegrees(180.0F));
        int cardNo = mob.getUsingSpellCardNo();
        float hp = mob.getHealth() / mob.getMaxHealth();
        float hp2 = hp * 2.0F - 1.0F;
        X1Tess t = new X1Tess(pose, buffers, STATUS).begin(CUTOUT);
        t.v(-1.02F, 0.07F, 0.001D, 0.0F, 3F / 16F).v(1.02F, 0.07F, 0.001D, 1.0F, 3F / 16F)
                .v(1.02F, -0.02F, 0.001D, 1.0F, 4F / 16F).v(-1.02F, -0.02F, 0.001D, 0.0F, 4F / 16F);
        float v0 = cardNo >= 0 ? 8F / 16F : 0F, v1 = cardNo >= 0 ? 11F / 16F : 3F / 16F;
        t.v(-hp2, 0.05F, 0.0D, hp, v0).v(1.0F, 0.05F, 0.0D, 0.0F, v0).v(1.0F, 0.00F, 0.0D, 0.0F, v1).v(-hp2, 0.00F, 0.0D, hp, v1);
        pose.mulPose(Axis.ZP.rotationDegrees(180F));
        pose.scale(0.02F, 0.02F, 0.02F);
        Font font = this.getFont();
        int a = Math.max(4, Math.min(255, (int) (alpha * 255F))) << 24;
        font.drawInBatch(mob.getDanmakuMobName(), -50, 0, a | 0x00FF88, true, pose.last().pose(), buffers,
                Font.DisplayMode.NORMAL, 0, LightTexture.FULL_BRIGHT);
        if (cardNo >= 0) {
            font.drawInBatch(Component.translatable("item.thSpellCard." + cardNo + ".name"), -50, -12, a | 0xFFFFFF, true,
                    pose.last().pose(), buffers, Font.DisplayMode.NORMAL, 0, LightTexture.FULL_BRIGHT);
        }
        pose.popPose();
    }
}
