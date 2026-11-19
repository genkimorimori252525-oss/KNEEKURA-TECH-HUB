package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;

import java.util.function.Function;

/**
 * Minimal emulation of the 1.7.10 {@code Tessellator} as X1 renderers use it:
 * {@code startDrawingQuads} picks the current GL state (a render type), {@code setColorRGBA_F}
 * applies to the following vertices, and a quad without a colour is white. Vertices are
 * transformed by the pose at emission time, like immediate-mode GL.
 *
 * Switching render type in a {@code BufferSource} flushes the previous batch, so X1's draw
 * order across GL state changes is preserved.
 */
final class X1Tess {
    enum State {
        /** no blend, alpha test 0.1, depth write */
        CUTOUT(X1RenderTypes.Blend.NONE, true, false, false),
        /** GL_SRC_ALPHA, GL_ONE, depthMask(false) */
        ADD_ALPHA(X1RenderTypes.Blend.SRC_ALPHA_ONE, false, false, false),
        /** same, GL_CULL_FACE enabled (spiritual strike talisman dark sphere) */
        ADD_ALPHA_CULL(X1RenderTypes.Blend.SRC_ALPHA_ONE, false, true, false),
        /** GL_SRC_ALPHA, GL_ONE with depth writes (laser cores) */
        ADD_ALPHA_DEPTH(X1RenderTypes.Blend.SRC_ALPHA_ONE, true, false, false),
        /** same, GL_CULL_FACE enabled (normal laser core) */
        ADD_ALPHA_DEPTH_CULL(X1RenderTypes.Blend.SRC_ALPHA_ONE, true, true, false),
        /** GL_ONE, GL_ONE_MINUS_SRC_COLOR, depthMask(false) */
        INVERT_ADD(X1RenderTypes.Blend.ONE_ONE_MINUS_SRC_COLOR, false, false, false),
        /** same, GL_CULL_FACE enabled (normal laser glow) */
        INVERT_ADD_CULL(X1RenderTypes.Blend.ONE_ONE_MINUS_SRC_COLOR, false, true, false),
        /** GL_ONE, GL_ONE_MINUS_SRC_COLOR, depth write */
        INVERT_ADD_DEPTH(X1RenderTypes.Blend.ONE_ONE_MINUS_SRC_COLOR, true, false, false),
        /** GL_ONE, GL_ONE, depthMask(false) */
        ADD_ONE(X1RenderTypes.Blend.ONE_ONE, false, false, false),
        /** GL_ONE, GL_ONE_MINUS_SRC_COLOR, depth write, GL_CULL_FACE (nuclear shot core) */
        INVERT_ADD_DEPTH_CULL(X1RenderTypes.Blend.ONE_ONE_MINUS_SRC_COLOR, true, true, false),
        /** GL_ONE, GL_ONE, depthMask(false), GL_CULL_FACE (nuclear shot glow) */
        ADD_ONE_CULL(X1RenderTypes.Blend.ONE_ONE, false, true, false),
        /** GL_ZERO, GL_ONE_MINUS_SRC_COLOR, depthMask(false) (Rumia's darkness) */
        DARKEN(X1RenderTypes.Blend.ZERO_ONE_MINUS_SRC_COLOR, false, false, false),
        /** same with glDepthFunc(GL_ALWAYS) (Rumia's darkness seen from within 6) */
        DARKEN_ALWAYS(X1RenderTypes.Blend.ZERO_ONE_MINUS_SRC_COLOR, false, false, true),
        /** GL_SRC_ALPHA, GL_SRC_ALPHA with depth writes (RenderSukima's dark backs) */
        SHADE(X1RenderTypes.Blend.SRC_ALPHA_SRC_ALPHA, true, false, false),
        /** Master Spark laser core: GL_SRC_ALPHA, GL_ONE, glDepthFunc(GL_ALWAYS) */
        SPARK_CORE(X1RenderTypes.Blend.SRC_ALPHA_ONE, true, false, true),
        /** Master Spark laser rainbow: GL_ONE, GL_ONE_MINUS_SRC_COLOR, glDepthFunc(GL_ALWAYS) */
        SPARK_GLOW(X1RenderTypes.Blend.ONE_ONE_MINUS_SRC_COLOR, true, false, true);

        final Function<ResourceLocation, RenderType> type;

        State(X1RenderTypes.Blend blend, boolean depthWrite, boolean cull, boolean depthAlways) {
            X1RenderTypes.Spec spec = new X1RenderTypes.Spec(blend, depthWrite, cull, depthAlways);
            this.type = texture -> X1RenderTypes.of(texture, spec);
        }
    }

    private final PoseStack pose;
    private final MultiBufferSource buffers;
    private final ResourceLocation texture;
    private VertexConsumer consumer;
    private float r = 1F, g = 1F, b = 1F, a = 1F;

    X1Tess(PoseStack pose, MultiBufferSource buffers, ResourceLocation texture) {
        this.pose = pose;
        this.buffers = buffers;
        this.texture = texture;
    }

    /** startDrawingQuads under the given GL state; colour resets to "unset" (white). */
    X1Tess begin(State state) {
        consumer = buffers.getBuffer(state.type.apply(texture));
        r = g = b = a = 1F;
        return this;
    }

    /** setColorRGBA_F: 1.7.10 clamps each channel to 0..255; 1.20 byte packing would wrap instead. */
    X1Tess color(float red, float green, float blue, float alpha) {
        r = clamp(red);
        g = clamp(green);
        b = clamp(blue);
        a = clamp(alpha);
        return this;
    }

    private static float clamp(float c) {
        return c < 0F ? 0F : Math.min(c, 1F);
    }

    X1Tess v(double x, double y, double z, float u, float v) {
        consumer.vertex(pose.last().pose(), (float) x, (float) y, (float) z)
                .color(r, g, b, a).uv(u, v).uv2(LightTexture.FULL_BRIGHT).endVertex();
        return this;
    }

    /** A VertexConsumer for ModelPart rendering that keeps only position, colour and UV. */
    VertexConsumer modelSink(State state) {
        VertexConsumer inner = buffers.getBuffer(state.type.apply(texture));
        return new VertexConsumer() {
            @Override
            public void vertex(float x, float y, float z, float red, float green, float blue, float alpha,
                               float u, float v, int overlay, int light, float nx, float ny, float nz) {
                inner.vertex(x, y, z).color(red, green, blue, alpha).uv(u, v)
                        .uv2(LightTexture.FULL_BRIGHT).endVertex();
            }

            @Override public VertexConsumer vertex(double x, double y, double z) { return inner.vertex(x, y, z); }
            @Override public VertexConsumer color(int red, int green, int blue, int alpha) { return inner.color(red, green, blue, alpha); }
            @Override public VertexConsumer uv(float u, float v) { return inner.uv(u, v); }
            @Override public VertexConsumer overlayCoords(int u, int v) { return this; }
            @Override public VertexConsumer uv2(int u, int v) { return inner.uv2(u, v); }
            @Override public VertexConsumer normal(float x, float y, float z) { return this; }
            @Override public void endVertex() { inner.endVertex(); }
            @Override public void defaultColor(int red, int green, int blue, int alpha) { inner.defaultColor(red, green, blue, alpha); }
            @Override public void unsetDefaultColor() { inner.unsetDefaultColor(); }
        };
    }
}
