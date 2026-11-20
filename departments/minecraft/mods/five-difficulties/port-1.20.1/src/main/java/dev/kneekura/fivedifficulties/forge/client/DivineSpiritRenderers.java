package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock;
import dev.kneekura.fivedifficulties.forge.entity.DivineSpiritEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.phys.Vec3;

/** X1 TileEntityDivineSpiritRenderer and RenderDivineSpirit: three stacked MusouFuuin quads, ONE / 1−src colour. */
public final class DivineSpiritRenderers {
    private static final ResourceLocation TEX = P12Renderers.tex("textures/entity/shot/musou_fuuin.png");
    private static final float[] R = {224F / 255F, 0F, 0F, 224F / 255F, 224F / 255F, 0F, 1F, 1F};
    private static final float[] G_BLOCK = {0F, 0F, 224F / 255F, 224F / 255F, 0F, 224F / 255F, 128F / 255F, 1F};
    /** RenderDivineSpirit's yellow green is 64, not the block's 224 (X1). */
    private static final float[] G_ENTITY = {0F, 0F, 224F / 255F, 64F / 255F, 0F, 224F / 255F, 128F / 255F, 1F};
    private static final float[] B = {0F, 224F / 255F, 0F, 0F, 224F / 255F, 224F / 255F, 0F, 1F};

    private DivineSpiritRenderers() {}

    /** The three quads (0.3 / 0.7 / 1.0 alpha) with the wobbling corners. pattern 0: u 0..0.5. */
    static void quads(X1Tess t, int color, float[] g, double timeR) {
        int c = Math.max(0, Math.min(7, color));
        float umin = 0F, umax = 32F / 64F, vmin = 0F, vmax = 1F;
        t.color(R[c], g[c], B[c], 0.3F)
                .v(-0.7F + Math.sin(timeR * 3.0D) * 0.1F, -0.7F - Math.cos(timeR * 7.0D) * 0.1F, 0.0D, umin, vmax)
                .v(0.7F - Math.cos(timeR * 4.0D) * 0.1F, -0.7F - Math.sin(timeR * 5.0D) * 0.1F, 0.0D, umax, vmax)
                .v(0.7F + Math.sin(timeR * 5.0D) * 0.1F, 0.7F + Math.cos(timeR * 4.0D) * 0.1F, 0.0D, umax, vmin)
                .v(-0.7F - Math.cos(timeR * 7.0D) * 0.1F, 0.7F + Math.sin(timeR * 3.0D) * 0.1F, 0.0D, umin, vmin);
        t.color(R[c], g[c], B[c], 0.7F)
                .v(-0.6F - Math.cos(timeR * 7.0D) * 0.1F, -0.6F + Math.sin(timeR * 5.0D) * 0.1F, 0.001D, umin, vmax)
                .v(0.6F + Math.sin(timeR * 3.0D) * 0.1F, -0.6F + Math.cos(timeR * 4.0D) * 0.1F, 0.001D, umax, vmax)
                .v(0.6F - Math.cos(timeR * 4.0D) * 0.1F, 0.6F - Math.sin(timeR * 3.0D) * 0.1F, 0.001D, umax, vmin)
                .v(-0.6F + Math.sin(timeR * 5.0D) * 0.1F, 0.6F - Math.cos(timeR * 7.0D) * 0.1F, 0.001D, umin, vmin);
        t.color(R[c], g[c], B[c], 1.0F)
                .v(-0.4F, -0.4F, 0.002D, umin, vmax).v(0.4F, -0.4F, 0.002D, umax, vmax)
                .v(0.4F, 0.4F, 0.002D, umax, vmin).v(-0.4F, 0.4F, 0.002D, umin, vmin);
    }

    /**
     * TileEntityDivineSpiritRenderer: time = world time + x·y·z; bobs ±0.16 at 5°/tick, faces the camera by yaw
     * and pitch of its offset, pulses its scale (z squashed to 0).
     */
    public static final class Block implements BlockEntityRenderer<DivineSpiritBlock.DivineSpiritBlockEntity> {
        public Block(BlockEntityRendererProvider.Context context) {}

        @Override
        public void render(DivineSpiritBlock.DivineSpiritBlockEntity be, float partialTick, PoseStack pose, MultiBufferSource buffers,
                           int light, int overlay) {
            Minecraft mc = Minecraft.getInstance();
            if (mc.level == null) return;
            var p = be.getBlockPos();
            int time = (int) mc.level.getDayTime() + p.getX() * p.getY() * p.getZ();
            double timeR = time / 180.0D * Math.PI;
            Vec3 cam = mc.gameRenderer.getMainCamera().getPosition();
            double bob = (float) Math.sin(time * 5F / 180F * Math.PI) * 0.16F;
            double posX = p.getX() - cam.x + 0.5D, posY = p.getY() - cam.y + 0.5D + bob, posZ = p.getZ() - cam.z + 0.5D;
            int color = be.getBlockState().getBlock() instanceof DivineSpiritBlock b ? b.color() : 0;
            float viewYaw = (float) Math.atan2(posX, posZ) / (float) Math.PI * 180.0F;
            float viewPitch = (float) Math.atan2(posY, Math.sqrt(posX * posX + posZ * posZ)) / (float) Math.PI * 180.0F;
            pose.pushPose();
            pose.translate(0.5D, 0.5D + bob, 0.5D);
            pose.mulPose(Axis.YP.rotationDegrees(viewYaw - 180F));
            pose.mulPose(Axis.XP.rotationDegrees(viewPitch));
            float s = 0.8F + (float) Math.sin(timeR * 5.0D) * 0.16F;
            pose.scale(s, s, 0.0F);
            quads(new X1Tess(pose, buffers, TEX).begin(X1Tess.State.INVERT_ADD), color, G_BLOCK, timeR);
            pose.popPose();
        }
    }

    /** RenderDivineSpirit: a camera billboard shrinking from 1 to 0 over its 300 ticks. */
    public static final class Spirit extends EntityRenderer<DivineSpiritEntity> {
        public Spirit(EntityRendererProvider.Context context) {
            super(context);
            this.shadowRadius = 0.0F;
        }

        @Override
        public void render(DivineSpiritEntity e, float yaw, float partialTick, PoseStack pose, MultiBufferSource buffers, int light) {
            pose.pushPose();
            double timeR = (double) e.tickCount / 180.0D * Math.PI;
            P12Renderers.billboard(pose, this.entityRenderDispatcher.cameraOrientation());
            float size = (300F - (float) e.getDivineSpiritCount()) / 300F;
            pose.scale(size, size, size);
            quads(new X1Tess(pose, buffers, TEX).begin(X1Tess.State.INVERT_ADD), e.getDivineSpiritColor(), G_ENTITY, timeR);
            pose.popPose();
        }

        @Override
        public ResourceLocation getTextureLocation(DivineSpiritEntity e) {
            return TEX;
        }
    }
}
