package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.platform.GlStateManager;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.VertexFormat;
import net.minecraft.Util;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;

import java.util.function.Function;

/**
 * 1.7.10 fixed-function states used by X1 renderers, as batched 1.20.1 render types.
 *
 * All use the text shader: unlit, vertex colour * texture, and {@code alpha < 0.1} discard,
 * which is the 1.7.10 default alpha test ({@code GL_GREATER 0.1}). X1 shots and lasers are
 * full-bright (getBrightnessForRender = 0xF000F0, lighting disabled).
 */
public final class X1RenderTypes extends RenderType {
    private X1RenderTypes(String name, VertexFormat format, VertexFormat.Mode mode, int bufferSize,
                          boolean affectsCrumbling, boolean sortOnUpload, Runnable setup, Runnable clear) {
        super(name, format, mode, bufferSize, affectsCrumbling, sortOnUpload, setup, clear);
    }

    /** glBlendFunc settings X1 uses. */
    public enum Blend { NONE, SRC_ALPHA_ONE, ONE_ONE_MINUS_SRC_COLOR, ONE_ONE, SRC_ALPHA_SRC_ALPHA, ZERO_ONE_MINUS_SRC_COLOR }

    private static final TransparencyStateShard SRC_ALPHA_SRC_ALPHA = new TransparencyStateShard(
            "five_difficulties_src_alpha_src_alpha",
            () -> {
                RenderSystem.enableBlend();
                RenderSystem.blendFunc(GlStateManager.SourceFactor.SRC_ALPHA, GlStateManager.DestFactor.SRC_ALPHA);
            },
            () -> {
                RenderSystem.disableBlend();
                RenderSystem.defaultBlendFunc();
            });

    /** One GL state combination: blend, glDepthMask, GL_CULL_FACE, glDepthFunc(GL_ALWAYS). */
    public record Spec(Blend blend, boolean depthWrite, boolean cull, boolean depthAlways) {}

    private static final TransparencyStateShard ONE_ONE_MINUS_SRC_COLOR = new TransparencyStateShard(
            "five_difficulties_one_one_minus_src_color",
            () -> {
                RenderSystem.enableBlend();
                RenderSystem.blendFunc(GlStateManager.SourceFactor.ONE, GlStateManager.DestFactor.ONE_MINUS_SRC_COLOR);
            },
            () -> {
                RenderSystem.disableBlend();
                RenderSystem.defaultBlendFunc();
            });

    private static final TransparencyStateShard ZERO_ONE_MINUS_SRC_COLOR = new TransparencyStateShard(
            "five_difficulties_zero_one_minus_src_color",
            () -> {
                RenderSystem.enableBlend();
                RenderSystem.blendFunc(GlStateManager.SourceFactor.ZERO, GlStateManager.DestFactor.ONE_MINUS_SRC_COLOR);
            },
            () -> {
                RenderSystem.disableBlend();
                RenderSystem.defaultBlendFunc();
            });

    private record Key(ResourceLocation texture, Spec spec) {}

    private static final Function<Key, RenderType> CACHE = Util.memoize(key -> {
        Spec s = key.spec();
        TransparencyStateShard transparency = switch (s.blend()) {
            case NONE -> NO_TRANSPARENCY;
            case SRC_ALPHA_ONE -> LIGHTNING_TRANSPARENCY;
            case ONE_ONE_MINUS_SRC_COLOR -> ONE_ONE_MINUS_SRC_COLOR;
            case ONE_ONE -> ADDITIVE_TRANSPARENCY;
            case SRC_ALPHA_SRC_ALPHA -> SRC_ALPHA_SRC_ALPHA;
            case ZERO_ONE_MINUS_SRC_COLOR -> ZERO_ONE_MINUS_SRC_COLOR;
        };
        String name = "five_difficulties_" + s.blend().name().toLowerCase() + (s.depthWrite() ? "_depth" : "")
                + (s.cull() ? "_cull" : "") + (s.depthAlways() ? "_always" : "");
        return create(name, DefaultVertexFormat.POSITION_COLOR_TEX_LIGHTMAP, VertexFormat.Mode.QUADS, 256, false,
                s.blend() != Blend.NONE,
                CompositeState.builder()
                        .setShaderState(RENDERTYPE_TEXT_SHADER)
                        .setTextureState(new TextureStateShard(key.texture(), false, false))
                        .setTransparencyState(transparency)
                        .setCullState(s.cull() ? CULL : NO_CULL)
                        .setDepthTestState(s.depthAlways() ? NO_DEPTH_TEST : LEQUAL_DEPTH_TEST)
                        .setLightmapState(LIGHTMAP)
                        .setWriteMaskState(s.depthWrite() ? COLOR_DEPTH_WRITE : COLOR_WRITE)
                        .createCompositeState(false));
    });

    public static RenderType of(ResourceLocation texture, Spec spec) {
        return CACHE.apply(new Key(texture, spec));
    }

    /** No blending, alpha test, depth write: renderNormalShot(blend = false). */
    public static final Function<ResourceLocation, RenderType> SHOT_CUTOUT =
            t -> of(t, new Spec(Blend.NONE, true, false, false));
    /** glBlendFunc(GL_SRC_ALPHA, GL_ONE), depthMask(false). */
    public static final Function<ResourceLocation, RenderType> SHOT_ADDITIVE =
            t -> of(t, new Spec(Blend.SRC_ALPHA_ONE, false, false, false));
    /** glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR), depthMask(false). */
    public static final Function<ResourceLocation, RenderType> LIGHT_EFFECT =
            t -> of(t, new Spec(Blend.ONE_ONE_MINUS_SRC_COLOR, false, false, false));
    /** glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR) with depth writes. */
    public static final Function<ResourceLocation, RenderType> INVERT_ADD_DEPTH =
            t -> of(t, new Spec(Blend.ONE_ONE_MINUS_SRC_COLOR, true, false, false));
    /** glBlendFunc(GL_ONE, GL_ONE), depthMask(false). */
    public static final Function<ResourceLocation, RenderType> ADD_ONE =
            t -> of(t, new Spec(Blend.ONE_ONE, false, false, false));
}
