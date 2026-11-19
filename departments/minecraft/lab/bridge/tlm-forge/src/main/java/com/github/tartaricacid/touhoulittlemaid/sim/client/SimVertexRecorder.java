package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import java.util.ArrayList;
import java.util.List;

/**
 * 描画される頂点をそのまま拾う {@link VertexConsumer}。
 *
 * <p><b>これが SimLab のモデル取り込みの中核。</b> Minecraft のモブ描画は、バニラも GeckoLib も
 * YSM も例外なく {@code VertexConsumer} へ頂点を流し込む。そこへこの実装を差し込むと、
 * <b>MC 自身が計算し終えた最終座標・UV・法線</b>がそのまま手に入る。
 *
 * <p>結果として、Bedrock の pivot 規約 / Y 反転 / box UV の展開表 / 面の巻き順を
 * こちら側で再実装する必要が一切なくなる —— これらを自前で書くと、モブが増えるたびに
 * 同じ種類のバグを踏み直すことになる (実際に踏んだ)。
 *
 * <p>MC は四角形 (QUADS) で流してくるので、4 頂点そろうたびに三角形 2 枚へ展開して溜める。
 */
@OnlyIn(Dist.CLIENT)
public final class SimVertexRecorder implements VertexConsumer {

    /** 1 頂点あたりの float 数。[x,y,z, u,v, nx,ny,nz, r,g,b] */
    public static final int STRIDE = 11;

    /** 三角形の頂点を {@link #STRIDE} 個ずつ並べたもの。 */
    private final List<Float> out = new ArrayList<>();

    // 組み立て中の 1 頂点
    private float x, y, z, u, v, nx, ny, nz;
    private float cr = 1, cg = 1, cb = 1;
    private int filled;
    private final float[] quad = new float[4 * STRIDE];

    private int quads;

    public int quadCount() {
        return this.quads;
    }

    public boolean isEmpty() {
        return this.out.isEmpty();
    }

    /** 溜めた三角形を float 配列で取り出す。 */
    public float[] toArray() {
        float[] a = new float[this.out.size()];
        for (int i = 0; i < a.length; i++) {
            a[i] = this.out.get(i);
        }
        return a;
    }

    @Override
    public VertexConsumer vertex(double px, double py, double pz) {
        this.x = (float) px; this.y = (float) py; this.z = (float) pz;
        return this;
    }

    /**
     * 頂点色。草・葉のバイオーム着色はここに乗ってくる
     * ({@code BlockRenderDispatcher.renderSingleBlock} が {@code BlockColors} を掛けるため)。
     * モブは基本 (255,255,255) なので実質何もしない。
     */
    @Override
    public VertexConsumer color(int r, int g, int b, int a) {
        this.cr = r / 255.0F; this.cg = g / 255.0F; this.cb = b / 255.0F;
        return this;
    }

    @Override
    public VertexConsumer uv(float pu, float pv) {
        this.u = pu; this.v = pv;
        return this;
    }

    @Override
    public VertexConsumer overlayCoords(int ou, int ov) {
        return this;
    }

    @Override
    public VertexConsumer uv2(int lu, int lv) {
        return this;
    }

    @Override
    public VertexConsumer normal(float pnx, float pny, float pnz) {
        this.nx = pnx; this.ny = pny; this.nz = pnz;
        return this;
    }

    @Override
    public void endVertex() {
        int base = this.filled * STRIDE;
        this.quad[base] = this.x; this.quad[base + 1] = this.y; this.quad[base + 2] = this.z;
        this.quad[base + 3] = this.u; this.quad[base + 4] = this.v;
        this.quad[base + 5] = this.nx; this.quad[base + 6] = this.ny; this.quad[base + 7] = this.nz;
        this.quad[base + 8] = this.cr; this.quad[base + 9] = this.cg; this.quad[base + 10] = this.cb;
        this.filled++;
        if (this.filled == 4) {
            // 四角形 -> 三角形 2 枚 (0,1,2) (0,2,3)。頂点の並び順は MC が決めたものをそのまま使う。
            emit(0); emit(1); emit(2);
            emit(0); emit(2); emit(3);
            this.filled = 0;
            this.quads++;
        }
    }

    private void emit(int i) {
        int b = i * STRIDE;
        for (int k = 0; k < STRIDE; k++) {
            this.out.add(this.quad[b + k]);
        }
    }

    @Override
    public void defaultColor(int r, int g, int b, int a) {
    }

    @Override
    public void unsetDefaultColor() {
    }
}
