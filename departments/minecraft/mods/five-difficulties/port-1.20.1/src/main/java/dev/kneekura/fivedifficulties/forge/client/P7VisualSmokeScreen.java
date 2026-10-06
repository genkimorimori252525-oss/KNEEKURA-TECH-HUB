package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;

/**
 * CI-only visual oracle screen. It intentionally calls the same rendering
 * primitives as the live Homing / Sakuya renderers instead of drawing mock art.
 */
public final class P7VisualSmokeScreen extends Screen {
    private SakuyaTimeControllerModel watchModel;
    private int renderFrames;

    public P7VisualSmokeScreen() {
        super(Component.literal("Five Difficulties P7 Visual Smoke"));
    }

    @Override
    protected void init() {
        this.watchModel = new SakuyaTimeControllerModel(
                Minecraft.getInstance().getEntityModels().bakeLayer(SakuyaTimeControllerModel.LAYER_LOCATION)
        );
    }

    public int renderFrames() {
        return renderFrames;
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        renderFrames++;

        graphics.fill(0, 0, width, height, 0xFF101018);
        graphics.drawCenteredString(
                this.font,
                "Five Difficulties X1 / 1.20.1 P7 visual smoke",
                width / 2,
                18,
                0xFFFFFF
        );
        graphics.drawCenteredString(
                this.font,
                "canonical private X1 assets + live renderer primitives",
                width / 2,
                31,
                0xA0A0A0
        );

        renderItem(graphics, new ItemStack(PortRegistries.HOMING_AMULET.get()), 42, 58, "Homing");
        renderItem(graphics, new ItemStack(PortRegistries.SAKUYA_WATCH.get()), 42, 125, "Watch");
        renderItem(graphics, new ItemStack(PortRegistries.SAKUYA_STOPWATCH.get()), 42, 192, "StopWatch");

        PoseStack pose = graphics.pose();

        // Exact two-pass Homing primitive.
        pose.pushPose();
        pose.translate(width * 0.34D, height * 0.46D, 220.0D);
        pose.scale(120.0F, 120.0F, 120.0F);
        HomingAmuletRenderer.renderLegacyVisual(pose, 0.0F, 12.0F);
        pose.popPose();

        graphics.drawCenteredString(this.font, "red Homing / X1 two-pass", (int)(width * 0.34D), (int)(height * 0.70D), 0xFFB0B0);

        renderWatch(graphics, SakuyaTimeControllerRenderer.WATCH_TEXTURE, width * 0.65D, height * 0.45D, "Sakuya Watch");
        renderWatch(graphics, SakuyaTimeControllerRenderer.STOPWATCH_TEXTURE, width * 0.84D, height * 0.45D, "StopWatch");

        // Same expanding dark-field mesh used by the live controller renderer.
        pose.pushPose();
        pose.translate(width * 0.74D, height * 0.78D, 100.0D);
        pose.scale(5.0F, 5.0F, 5.0F);
        pose.scale(0.3F, 0.3F, 0.3F);
        SakuyaTimeControllerRenderer.renderDarkField(pose, 5.0F);
        pose.popPose();

        graphics.drawCenteredString(this.font, "X1 dark time field", (int)(width * 0.74D), (int)(height * 0.92D), 0xC8C8FF);
    }

    private void renderItem(GuiGraphics graphics, ItemStack stack, int x, int y, String label) {
        PoseStack pose = graphics.pose();
        pose.pushPose();
        pose.translate(x, y, 0.0D);
        pose.scale(3.0F, 3.0F, 1.0F);
        graphics.renderItem(stack, 0, 0);
        pose.popPose();
        graphics.drawString(this.font, label, x - 3, y + 51, 0xFFFFFF);
    }

    private void renderWatch(GuiGraphics graphics, ResourceLocation texture, double x, double y, String label) {
        Minecraft minecraft = Minecraft.getInstance();
        PoseStack pose = graphics.pose();

        pose.pushPose();
        pose.translate(x, y, 180.0D);
        pose.mulPose(Axis.XP.rotationDegrees(18.0F));
        pose.mulPose(Axis.YP.rotationDegrees(205.0F));
        pose.scale(180.0F, -180.0F, 180.0F);
        pose.scale(0.3F, 0.3F, 0.3F);

        MultiBufferSource.BufferSource buffers = minecraft.renderBuffers().bufferSource();
        VertexConsumer consumer = buffers.getBuffer(watchModel.renderType(texture));
        watchModel.renderToBuffer(
                pose,
                consumer,
                LightTexture.FULL_BRIGHT,
                OverlayTexture.NO_OVERLAY,
                1.0F, 1.0F, 1.0F, 1.0F
        );
        buffers.endBatch();
        pose.popPose();

        graphics.drawCenteredString(this.font, label, (int)x, (int)(y + 90.0D), 0xFFFFFF);
    }
}
