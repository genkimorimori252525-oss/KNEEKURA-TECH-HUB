package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.mojang.blaze3d.vertex.VertexConsumer;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Vector3f;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.List;

/**
 * One actual VertexConsumer draw stream for authoritative final-vertex capture.
 *
 * <p>Unlike {@link SimVertexRecorder}, this recorder does not convert primitives to triangles and
 * does not drop alpha/light/overlay. Vertex order is preserved exactly; RenderType.mode() is stored
 * beside the stream by the caller. V2 also appends the already-resolved overlay/lightmap RGBA
 * sampled from an immutable runtime texture snapshot; the real screen branch is never modified.
 *
 * <p>The optional inverse matrices remove only the outer PoseStack transform from the recorder
 * copy. The real VertexConsumer receives untouched coordinates. This is generic matrix
 * normalization, not YSM TRS reconstruction.
 */
public final class SimFinalVertexRecorder implements VertexConsumer {
    /**
     * x,y,z,u,v,nx,ny,nz,r,g,b,a,overlayU,overlayV,lightU,lightV,
     * overlayR,overlayG,overlayB,overlayA,lightR,lightG,lightB,lightA
     */
    public static final int STRIDE = 24;

    private final List<Float> out = new ArrayList<>();
    @Nullable private final Matrix4f positionToModel;
    @Nullable private final Matrix3f normalToModel;
    @Nullable private final SimAuxiliarySamplerState auxiliarySamplerState;
    private boolean auxiliaryResolutionValid = true;

    private float x, y, z;
    private float u, v;
    private float nx, ny, nz;
    private float r = 1, g = 1, b = 1, a = 1;
    private int overlayU, overlayV;
    private int lightU, lightV;

    private boolean defaultColor;
    private float defaultR = 1, defaultG = 1, defaultB = 1, defaultA = 1;

    public SimFinalVertexRecorder() {
        this(null, null, null);
    }

    public SimFinalVertexRecorder(
            @Nullable Matrix4f positionToModel,
            @Nullable Matrix3f normalToModel,
            @Nullable SimAuxiliarySamplerState auxiliarySamplerState) {
        this.positionToModel = positionToModel == null ? null : new Matrix4f(positionToModel);
        this.normalToModel = normalToModel == null ? null : new Matrix3f(normalToModel);
        this.auxiliarySamplerState = auxiliarySamplerState;
        if (auxiliarySamplerState == null) {
            this.auxiliaryResolutionValid = false;
        }
    }

    public boolean auxiliaryResolutionValid() {
        return this.auxiliaryResolutionValid;
    }

    public int vertexCount() {
        return this.out.size() / STRIDE;
    }

    public boolean isEmpty() {
        return this.out.isEmpty();
    }

    public float[] toArray() {
        float[] a = new float[this.out.size()];
        for (int i = 0; i < a.length; i++) {
            a[i] = this.out.get(i);
        }
        return a;
    }

    @Override
    public VertexConsumer vertex(double px, double py, double pz) {
        float tx = (float) px;
        float ty = (float) py;
        float tz = (float) pz;
        if (this.positionToModel != null) {
            Vector3f p = new Vector3f(tx, ty, tz);
            this.positionToModel.transformPosition(p);
            tx = p.x();
            ty = p.y();
            tz = p.z();
        }
        this.x = tx;
        this.y = ty;
        this.z = tz;
        if (this.defaultColor) {
            this.r = this.defaultR;
            this.g = this.defaultG;
            this.b = this.defaultB;
            this.a = this.defaultA;
        }
        return this;
    }

    @Override
    public VertexConsumer color(int pr, int pg, int pb, int pa) {
        this.r = pr / 255.0F;
        this.g = pg / 255.0F;
        this.b = pb / 255.0F;
        this.a = pa / 255.0F;
        return this;
    }

    @Override
    public VertexConsumer uv(float pu, float pv) {
        this.u = pu;
        this.v = pv;
        return this;
    }

    @Override
    public VertexConsumer overlayCoords(int pu, int pv) {
        this.overlayU = pu;
        this.overlayV = pv;
        return this;
    }

    @Override
    public VertexConsumer uv2(int pu, int pv) {
        this.lightU = pu;
        this.lightV = pv;
        return this;
    }

    @Override
    public VertexConsumer normal(float pnx, float pny, float pnz) {
        float tx = pnx;
        float ty = pny;
        float tz = pnz;
        if (this.normalToModel != null) {
            Vector3f n = new Vector3f(tx, ty, tz);
            this.normalToModel.transform(n);
            float len2 = n.lengthSquared();
            if (Float.isFinite(len2) && len2 > 1.0e-20F) {
                n.mul((float) (1.0 / Math.sqrt(len2)));
            }
            tx = n.x();
            ty = n.y();
            tz = n.z();
        }
        this.nx = tx;
        this.ny = ty;
        this.nz = tz;
        return this;
    }

    @Override
    public void endVertex() {
        float[] overlay = null;
        float[] lightmap = null;
        try {
            if (this.auxiliarySamplerState != null) {
                overlay = this.auxiliarySamplerState.resolveOverlay(this.overlayU, this.overlayV);
                lightmap = this.auxiliarySamplerState.resolveLightmap(this.lightU, this.lightV);
            }
        } catch (Throwable ignored) {
            // Capture evidence is discarded after geoRender; never break the real screen path.
        }
        if (overlay == null || lightmap == null) {
            this.auxiliaryResolutionValid = false;
            overlay = new float[]{0, 0, 0, 0};
            lightmap = new float[]{0, 0, 0, 0};
        }

        add(this.x); add(this.y); add(this.z);
        add(this.u); add(this.v);
        add(this.nx); add(this.ny); add(this.nz);
        add(this.r); add(this.g); add(this.b); add(this.a);
        add(this.overlayU); add(this.overlayV);
        add(this.lightU); add(this.lightV);
        add(overlay[0]); add(overlay[1]); add(overlay[2]); add(overlay[3]);
        add(lightmap[0]); add(lightmap[1]); add(lightmap[2]); add(lightmap[3]);
    }

    private void add(float value) {
        this.out.add(value);
    }

    @Override
    public void defaultColor(int pr, int pg, int pb, int pa) {
        this.defaultColor = true;
        this.defaultR = pr / 255.0F;
        this.defaultG = pg / 255.0F;
        this.defaultB = pb / 255.0F;
        this.defaultA = pa / 255.0F;
    }

    @Override
    public void unsetDefaultColor() {
        this.defaultColor = false;
        this.defaultR = this.defaultG = this.defaultB = this.defaultA = 1.0F;
    }
}