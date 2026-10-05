package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.DimensionSpecialEffects;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RegisterDimensionSpecialEffectsEvent;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.event.TickEvent;
import org.joml.Vector3f;

/** Observation-only native rendering. Never changes server lighting or entity effects. */
public final class KneekuraDebugTankView {
    private KneekuraDebugTankView() {}

    @Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Registration {
        @SubscribeEvent
        public static void register(RegisterDimensionSpecialEffectsEvent event) {
            if (!KneekuraDebugEnv.fromSystemEnvironment().enabled()) return;
            event.register(new ResourceLocation("minecraft", "overworld"), new DimensionSpecialEffects.OverworldEffects() {
                @Override
                public void adjustLightmapColors(ClientLevel level, float partialTicks, float skyDarken,
                        float blockLightRedFlicker, float skyLight, int pixelX, int pixelY, Vector3f colors) {
                    var view = KneekuraDebugTankPresentation.viewForRender(Minecraft.getInstance().getSingleplayerServer());
                    if (view != null && view.bright() && level.dimension().location().toString().equals("minecraft:overworld")) {
                        colors.set(1.0F, 1.0F, 1.0F);
                    }
                }
            });
        }
    }

    @Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID, value = Dist.CLIENT)
    public static final class Grid {
        private static final KneekuraDebugTankPresentationRecipe.LightmapTransition LIGHTMAP =
                new KneekuraDebugTankPresentationRecipe.LightmapTransition();

        @SubscribeEvent
        public static void renderTick(TickEvent.RenderTickEvent event) {
            if (event.phase != TickEvent.Phase.START) return;
            var mc = Minecraft.getInstance();
            var view = KneekuraDebugTankPresentation.viewForRender(mc.getSingleplayerServer());
            boolean bright = mc.level != null && view != null && view.bright()
                    && mc.level.dimension().location().toString().equals("minecraft:overworld");
            // LightTexture.tick marks the native lightmap dirty even while server/client game ticks are paused.
            if (LIGHTMAP.update(bright, mc.level != null)) mc.gameRenderer.lightTexture().tick();
            KneekuraDebugClientBootstrap.sampleTankStatus(false);
        }

        @SubscribeEvent
        public static void render(RenderLevelStageEvent event) {
            var mc = Minecraft.getInstance();
            var view = KneekuraDebugTankPresentation.viewForRender(mc.getSingleplayerServer());
            if (view == null || event.getStage() != RenderLevelStageEvent.Stage.AFTER_TRANSLUCENT_BLOCKS) return;
            if (mc.level == null || !mc.level.dimension().location().toString().equals("minecraft:overworld")) return;
            var g = view.geometry();
            PoseStack pose = event.getPoseStack();
            var camera = event.getCamera().getPosition();
            pose.pushPose();
            pose.translate(-camera.x, -camera.y, -camera.z);
            var buffers = mc.renderBuffers().bufferSource();
            VertexConsumer lines = buffers.getBuffer(RenderType.lines());
            double x0 = g.x() + 0.003, x1 = g.x() + g.width() - 0.003;
            double y0 = g.y() + 0.003, y1 = g.y() + g.height() - 0.003;
            double z0 = g.z() + 0.003, z1 = g.z() + g.depth() - 0.003;
            for (int x = g.x(); x <= g.x() + g.width(); x++) {
                for (double y : new double[]{y0, y1}) line(lines, pose, x, y, z0, x, y, z1);
                for (double z : new double[]{z0, z1}) line(lines, pose, x, y0, z, x, y1, z);
            }
            for (int z = g.z(); z <= g.z() + g.depth(); z++) {
                for (double y : new double[]{y0, y1}) line(lines, pose, x0, y, z, x1, y, z);
                for (double x : new double[]{x0, x1}) line(lines, pose, x, y0, z, x, y1, z);
            }
            for (int y = g.y(); y <= g.y() + g.height(); y++) {
                for (double z : new double[]{z0, z1}) line(lines, pose, x0, y, z, x1, y, z);
                for (double x : new double[]{x0, x1}) line(lines, pose, x, y, z0, x, y, z1);
            }
            buffers.endBatch(RenderType.lines());
            pose.popPose();
            KneekuraDebugClientBootstrap.sampleTankStatus(true);
        }
        private static void line(VertexConsumer consumer, PoseStack pose, double x0, double y0, double z0, double x1, double y1, double z1) {
            Vector3f normal = new Vector3f((float)(x1-x0), (float)(y1-y0), (float)(z1-z0)).normalize();
            consumer.vertex(pose.last().pose(), (float)x0, (float)y0, (float)z0).color(90, 102, 118, 255)
                    .normal(pose.last().normal(), normal.x, normal.y, normal.z).endVertex();
            consumer.vertex(pose.last().pose(), (float)x1, (float)y1, (float)z1).color(90, 102, 118, 255)
                    .normal(pose.last().normal(), normal.x, normal.y, normal.z).endVertex();
        }
    }
}
