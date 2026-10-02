package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import org.joml.Matrix3f;
import org.joml.Matrix4f;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/**
 * Pass-through tee for one real render invocation.
 *
 * <p>The screen path is untouched. Only the recorder branch receives the inverse outer PoseStack
 * transform so captured final vertices are normalized back to model-local post-deformation space.
 */
public final class SimFinalVertexTeeBuffer implements MultiBufferSource {
    private final MultiBufferSource real;
    private final Matrix4f positionToModel;
    private final Matrix3f normalToModel;
    private final float[] modelToWorld;
    private final float[] modelNormalToWorld;
    private final float[] globalColorMultiplier;
    private final SimGlobalShaderState globalShaderState;
    private final SimAuxiliarySamplerState auxiliarySamplerState;
    private final Map<RenderType, SimFinalVertexRecorder> recorders = new LinkedHashMap<>();
    private final Map<RenderType, VertexConsumer> tees = new LinkedHashMap<>();
    private final java.util.List<RenderType> bufferRequests = new java.util.ArrayList<>();

    public SimFinalVertexTeeBuffer(
            MultiBufferSource real,
            Matrix4f positionToModel,
            Matrix3f normalToModel,
            Matrix4f modelToWorld,
            Matrix3f modelNormalToWorld,
            SimGlobalShaderState globalShaderState,
            SimAuxiliarySamplerState auxiliarySamplerState) {
        this.real = real;
        this.positionToModel = new Matrix4f(positionToModel);
        this.normalToModel = new Matrix3f(normalToModel);
        this.modelToWorld = new float[16];
        new Matrix4f(modelToWorld).get(this.modelToWorld);
        this.modelNormalToWorld = new float[9];
        new Matrix3f(modelNormalToWorld).get(this.modelNormalToWorld);
        if (globalShaderState == null) {
            throw new IllegalArgumentException("globalShaderState is required");
        }
        this.globalShaderState = globalShaderState;
        this.globalColorMultiplier = globalShaderState.shaderColor();
        if (auxiliarySamplerState == null) {
            throw new IllegalArgumentException("auxiliarySamplerState is required");
        }
        this.auxiliarySamplerState = auxiliarySamplerState;
    }

    @Override
    public VertexConsumer getBuffer(RenderType type) {
        this.bufferRequests.add(type);
        VertexConsumer realBuf = this.real.getBuffer(type);
        return this.tees.computeIfAbsent(type, t -> {
            SimFinalVertexRecorder rec = new SimFinalVertexRecorder(
                    this.positionToModel, this.normalToModel, this.auxiliarySamplerState);
            this.recorders.put(t, rec);
            return new Tee(realBuf, rec);
        });
    }

    public Map<RenderType, SimFinalVertexRecorder> recorders() {
        return this.recorders;
    }

    /**
     * RenderPack v1 has one stable group per captured RenderType. If one type is requested, another
     * type is requested, and then the first type is requested again, merging by type would destroy
     * a real draw-call boundary. Such a frame must fail closed instead of silently reordering.
     */
    public boolean hasNonContiguousTypeReentry() {
        Set<RenderType> closed = Collections.newSetFromMap(new IdentityHashMap<>());
        RenderType current = null;
        for (RenderType type : this.bufferRequests) {
            if (type == current) {
                continue;
            }
            if (current != null) {
                closed.add(current);
            }
            if (closed.contains(type)) {
                return true;
            }
            current = type;
        }
        return false;
    }

    public int bufferRequestCount() {
        return this.bufferRequests.size();
    }

    /** JOML column-major float[16], captured before geoRender. */
    public float[] modelToWorld() {
        return this.modelToWorld.clone();
    }

    public float[] modelNormalToWorld() {
        return this.modelNormalToWorld.clone();
    }

    /** RenderSystem shader RGBA observed immediately before this geoRender. */
    public float[] globalColorMultiplier() {
        return this.globalColorMultiplier.clone();
    }

    /** Immutable generic global shader snapshot observed immediately before this geoRender. */
    SimGlobalShaderState globalShaderState() {
        return this.globalShaderState;
    }

    /** Immutable overlay/lightmap texture snapshot observed immediately before this geoRender. */
    SimAuxiliarySamplerState auxiliarySamplerState() {
        return this.auxiliarySamplerState;
    }

    /** False means at least one captured UV could not be resolved; artifact must fail closed. */
    public boolean auxiliaryResolutionValid() {
        for (SimFinalVertexRecorder recorder : this.recorders.values()) {
            if (!recorder.auxiliaryResolutionValid()) return false;
        }
        return true;
    }

    private record Tee(VertexConsumer real, VertexConsumer capture) implements VertexConsumer {
        @Override
        public VertexConsumer vertex(double x, double y, double z) {
            this.real.vertex(x, y, z);
            this.capture.vertex(x, y, z);
            return this;
        }

        @Override
        public VertexConsumer color(int r, int g, int b, int a) {
            this.real.color(r, g, b, a);
            this.capture.color(r, g, b, a);
            return this;
        }

        @Override
        public VertexConsumer uv(float u, float v) {
            this.real.uv(u, v);
            this.capture.uv(u, v);
            return this;
        }

        @Override
        public VertexConsumer overlayCoords(int u, int v) {
            this.real.overlayCoords(u, v);
            this.capture.overlayCoords(u, v);
            return this;
        }

        @Override
        public VertexConsumer uv2(int u, int v) {
            this.real.uv2(u, v);
            this.capture.uv2(u, v);
            return this;
        }

        @Override
        public VertexConsumer normal(float x, float y, float z) {
            this.real.normal(x, y, z);
            this.capture.normal(x, y, z);
            return this;
        }

        @Override
        public void endVertex() {
            this.real.endVertex();
            this.capture.endVertex();
        }

        @Override
        public void defaultColor(int r, int g, int b, int a) {
            this.real.defaultColor(r, g, b, a);
            this.capture.defaultColor(r, g, b, a);
        }

        @Override
        public void unsetDefaultColor() {
            this.real.unsetDefaultColor();
            this.capture.unsetDefaultColor();
        }
    }
}