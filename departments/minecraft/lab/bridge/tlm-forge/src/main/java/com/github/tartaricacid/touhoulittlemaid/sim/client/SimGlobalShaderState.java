package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.blaze3d.shaders.FogShape;
import com.mojang.blaze3d.systems.RenderSystem;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Vector3f;

import javax.annotation.Nullable;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.List;

/**
 * Immutable snapshot of generic shader inputs that are global to one real draw invocation.
 *
 * <p>This class only observes RenderSystem's already-resolved state. It never derives fog from
 * biome/weather names and never executes Minecraft/YSM render semantics. Private shader light
 * directions are located structurally as the unique static Vector3f[2] state, not by field name.
 */
final class SimGlobalShaderState {
    static final String MATRIX_CONVENTION = "JOML_COLUMN_MAJOR_COLUMN_VECTOR";

    private final float[] modelViewMatrix;
    private final float[] projectionMatrix;
    private final float[] inverseViewRotationMatrix;
    private final float[] directionalLights;
    private final float[] shaderColor;
    private final float fogStart;
    private final float fogEnd;
    private final float[] fogColor;
    private final String fogShape;

    private SimGlobalShaderState(
            float[] modelViewMatrix,
            float[] projectionMatrix,
            float[] inverseViewRotationMatrix,
            float[] directionalLights,
            float[] shaderColor,
            float fogStart,
            float fogEnd,
            float[] fogColor,
            String fogShape) {
        this.modelViewMatrix = modelViewMatrix.clone();
        this.projectionMatrix = projectionMatrix.clone();
        this.inverseViewRotationMatrix = inverseViewRotationMatrix.clone();
        this.directionalLights = directionalLights.clone();
        this.shaderColor = shaderColor.clone();
        this.fogStart = fogStart;
        this.fogEnd = fogEnd;
        this.fogColor = fogColor.clone();
        this.fogShape = fogShape;
    }

    @Nullable
    static SimGlobalShaderState capture() {
        try {
            float[] modelView = new float[16];
            new Matrix4f(RenderSystem.getModelViewMatrix()).get(modelView);
            float[] projection = new float[16];
            new Matrix4f(RenderSystem.getProjectionMatrix()).get(projection);
            float[] inverseViewRotation = new float[9];
            new Matrix3f(RenderSystem.getInverseViewRotationMatrix()).get(inverseViewRotation);

            float[] shaderColorRaw = RenderSystem.getShaderColor();
            if (shaderColorRaw == null || shaderColorRaw.length < 4) return null;
            float[] shaderColor = new float[]{
                    shaderColorRaw[0], shaderColorRaw[1], shaderColorRaw[2], shaderColorRaw[3]};

            float fogStart = RenderSystem.getShaderFogStart();
            float fogEnd = RenderSystem.getShaderFogEnd();
            float[] fogColorRaw = RenderSystem.getShaderFogColor();
            if (fogColorRaw == null || fogColorRaw.length < 4) return null;
            float[] fogColor = new float[]{
                    fogColorRaw[0], fogColorRaw[1], fogColorRaw[2], fogColorRaw[3]};

            FogShape shape = RenderSystem.getShaderFogShape();
            String shapeId;
            if (shape == FogShape.SPHERE) {
                shapeId = "sphere";
            } else if (shape == FogShape.CYLINDER) {
                shapeId = "cylinder";
            } else {
                return null;
            }

            float[] lights = captureDirectionalLights();
            if (lights == null) return null;

            if (!finite(modelView)
                    || !finite(projection)
                    || !finite(inverseViewRotation)
                    || !finite(lights)
                    || !finite(shaderColor)
                    || !Float.isFinite(fogStart)
                    || !Float.isFinite(fogEnd)
                    || !finite(fogColor)) {
                return null;
            }

            return new SimGlobalShaderState(
                    modelView, projection, inverseViewRotation, lights, shaderColor,
                    fogStart, fogEnd, fogColor, shapeId);
        } catch (Throwable ignored) {
            return null;
        }
    }

    @Nullable
    private static float[] captureDirectionalLights() {
        try {
            List<Vector3f[]> candidates = new ArrayList<>();
            for (Field field : RenderSystem.class.getDeclaredFields()) {
                if (!Modifier.isStatic(field.getModifiers())
                        || !field.getType().isArray()
                        || field.getType().getComponentType() != Vector3f.class) {
                    continue;
                }
                field.setAccessible(true);
                Object raw = field.get(null);
                if (raw instanceof Vector3f[] values && values.length == 2) {
                    candidates.add(values);
                }
            }
            if (candidates.size() != 1) return null;
            Vector3f[] values = candidates.get(0);
            if (values[0] == null || values[1] == null) return null;
            return new float[]{
                    values[0].x(), values[0].y(), values[0].z(),
                    values[1].x(), values[1].y(), values[1].z()};
        } catch (Throwable ignored) {
            return null;
        }
    }

    boolean sameBits(@Nullable SimGlobalShaderState other) {
        return other != null
                && same(this.modelViewMatrix, other.modelViewMatrix)
                && same(this.projectionMatrix, other.projectionMatrix)
                && same(this.inverseViewRotationMatrix, other.inverseViewRotationMatrix)
                && same(this.directionalLights, other.directionalLights)
                && same(this.shaderColor, other.shaderColor)
                && Float.floatToIntBits(this.fogStart) == Float.floatToIntBits(other.fogStart)
                && Float.floatToIntBits(this.fogEnd) == Float.floatToIntBits(other.fogEnd)
                && same(this.fogColor, other.fogColor)
                && this.fogShape.equals(other.fogShape);
    }

    float[] shaderColor() {
        return this.shaderColor.clone();
    }

    JsonObject toJson() {
        JsonObject root = new JsonObject();
        root.addProperty("matrixConvention", MATRIX_CONVENTION);
        root.add("modelViewMatrix", array(this.modelViewMatrix));
        root.add("projectionMatrix", array(this.projectionMatrix));
        root.add("inverseViewRotationMatrix", array(this.inverseViewRotationMatrix));

        JsonArray lights = new JsonArray();
        for (int i = 0; i < 2; i++) {
            JsonArray light = new JsonArray();
            light.add(this.directionalLights[i * 3]);
            light.add(this.directionalLights[i * 3 + 1]);
            light.add(this.directionalLights[i * 3 + 2]);
            lights.add(light);
        }
        root.add("directionalLights", lights);
        root.add("shaderColor", array(this.shaderColor));

        JsonObject fog = new JsonObject();
        fog.addProperty("curve", "smoothstep");
        fog.addProperty("start", this.fogStart);
        fog.addProperty("end", this.fogEnd);
        fog.add("color", array(this.fogColor));
        fog.addProperty("shape", this.fogShape);
        fog.addProperty("distanceSpace", "modelView");
        root.add("fog", fog);
        return root;
    }

    private static JsonArray array(float[] values) {
        JsonArray out = new JsonArray();
        for (float value : values) out.add(value);
        return out;
    }

    private static boolean finite(float[] values) {
        for (float value : values) {
            if (!Float.isFinite(value)) return false;
        }
        return true;
    }

    private static boolean same(float[] a, float[] b) {
        if (a.length != b.length) return false;
        for (int i = 0; i < a.length; i++) {
            if (Float.floatToIntBits(a[i]) != Float.floatToIntBits(b[i])) return false;
        }
        return true;
    }
}
