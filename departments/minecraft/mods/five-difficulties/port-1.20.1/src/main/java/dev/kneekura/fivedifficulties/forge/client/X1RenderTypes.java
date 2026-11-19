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
 * 1.7.10 fixed-function states used by X1 RenderTHShot, as batched 1.20.1 render types.
 *
 * All use the text shader: unlit, vertex colour * texture, and {@code alpha < 0.1} discard,
 * which is the 1.7.10 default alpha test ({@code GL_GREATER 0.1}). Shots are full-bright
 * (X1 getBrightnessForRender = 0xF000F0, lighting disabled).
 */
public final class X1RenderTypes extends RenderType {
    private X1RenderTypes(String name, VertexFormat format, VertexFormat.Mode mode, int bufferSize,
                          boolean affectsCrumbling, boolean sortOnUpload, Runnable setup, Runnable clear) {
        super(name, format, mode, bufferSize, affectsCrumbling, sortOnUpload, setup, clear);
    }

    /** glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR): X1 delay light / homing amulet. */
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

    /** No blending, alpha test, depth write: renderNormalShot(blend = false). */
    public static final Function<ResourceLocation, RenderType> SHOT_CUTOUT = Util.memoize(texture -> create(
            "five_difficulties_shot_cutout", DefaultVertexFormat.POSITION_COLOR_TEX_LIGHTMAP, VertexFormat.Mode.QUADS,
            256, false, false,
            CompositeState.builder()
                    .setShaderState(RENDERTYPE_TEXT_SHADER)
                    .setTextureState(new TextureStateShard(texture, false, false))
                    .setTransparencyState(NO_TRANSPARENCY)
                    .setCullState(NO_CULL)
                    .setLightmapState(LIGHTMAP)
                    .createCompositeState(false)));

    /** glBlendFunc(GL_SRC_ALPHA, GL_ONE), depthMask(false): renderNormalShot(blend = true), i.e. BIG. */
    public static final Function<ResourceLocation, RenderType> SHOT_ADDITIVE = Util.memoize(texture -> create(
            "five_difficulties_shot_additive", DefaultVertexFormat.POSITION_COLOR_TEX_LIGHTMAP, VertexFormat.Mode.QUADS,
            256, false, true,
            CompositeState.builder()
                    .setShaderState(RENDERTYPE_TEXT_SHADER)
                    .setTextureState(new TextureStateShard(texture, false, false))
                    .setTransparencyState(LIGHTNING_TRANSPARENCY)
                    .setCullState(NO_CULL)
                    .setLightmapState(LIGHTMAP)
                    .setWriteMaskState(COLOR_WRITE)
                    .createCompositeState(false)));

    /** glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR) with depth writes: kunai / arrow tips, wind. */
    public static final Function<ResourceLocation, RenderType> INVERT_ADD_DEPTH = Util.memoize(texture -> create(
            "five_difficulties_invert_add_depth", DefaultVertexFormat.POSITION_COLOR_TEX_LIGHTMAP,
            VertexFormat.Mode.QUADS, 256, false, true,
            CompositeState.builder()
                    .setShaderState(RENDERTYPE_TEXT_SHADER)
                    .setTextureState(new TextureStateShard(texture, false, false))
                    .setTransparencyState(ONE_ONE_MINUS_SRC_COLOR)
                    .setCullState(NO_CULL)
                    .setLightmapState(LIGHTMAP)
                    .createCompositeState(false)));

    /** glBlendFunc(GL_ONE, GL_ONE), depthMask(false): phantom. */
    public static final Function<ResourceLocation, RenderType> ADD_ONE = Util.memoize(texture -> create(
            "five_difficulties_add_one", DefaultVertexFormat.POSITION_COLOR_TEX_LIGHTMAP, VertexFormat.Mode.QUADS,
            256, false, true,
            CompositeState.builder()
                    .setShaderState(RENDERTYPE_TEXT_SHADER)
                    .setTextureState(new TextureStateShard(texture, false, false))
                    .setTransparencyState(ADDITIVE_TRANSPARENCY)
                    .setCullState(NO_CULL)
                    .setLightmapState(LIGHTMAP)
                    .setWriteMaskState(COLOR_WRITE)
                    .createCompositeState(false)));

    /** glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR), depthMask(false): delay light effect. */
    public static final Function<ResourceLocation, RenderType> LIGHT_EFFECT = Util.memoize(texture -> create(
            "five_difficulties_light_effect", DefaultVertexFormat.POSITION_COLOR_TEX_LIGHTMAP, VertexFormat.Mode.QUADS,
            256, false, true,
            CompositeState.builder()
                    .setShaderState(RENDERTYPE_TEXT_SHADER)
                    .setTextureState(new TextureStateShard(texture, false, false))
                    .setTransparencyState(ONE_ONE_MINUS_SRC_COLOR)
                    .setCullState(NO_CULL)
                    .setLightmapState(LIGHTMAP)
                    .setWriteMaskState(COLOR_WRITE)
                    .createCompositeState(false)));
}
