package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 描画をそのまま通しつつ、流れた頂点を横で {@link SimVertexRecorder} へ複写する
 * {@link MultiBufferSource}（spike 004 第2段階）。
 *
 * <h3>なぜ「もう一度描く」ではいけないのか</h3>
 * ボーン行列と頂点は<b>同じ 1 回の {@code geoRender} から</b>採らなければならない。
 * {@link SimModelDump#shoot} のように別途もう一度描くと、その間に animation controller が
 * 1 フレーム進み、<b>行列と頂点が違う瞬間のものになる</b>。そうなると誤差を測っても
 * 「実装が違う」のか「フレームがずれている」のか区別できず、判定そのものが成立しない
 * （審査指摘 2026-08-24）。
 *
 * <p>そこで描画を増やさず、<b>行き先を増やす</b>。画面へ出る頂点と記録される頂点は
 * 定義上まったく同じものになる。
 *
 * <h3>RenderType ごとに分ける</h3>
 * 本体・持ち物・発光などは別の {@link RenderType} で流れてくる。比較は<b>本体 geometry に
 * 限る</b>必要がある（YSM の boneIndex は本体基準で、持ち物の頂点は対応表を持たない）ので、
 * 混ぜずに {@code RenderType} ごとの記録器へ分けて溜める。どれが本体かは<b>後で選ぶ</b>
 * —— ここで推測しない。
 */
@OnlyIn(Dist.CLIENT)
public final class SimTeeBuffer implements MultiBufferSource {

    private final MultiBufferSource real;

    /** RenderType → その型で流れた頂点。挿入順（＝描画順）を保つ。 */
    private final Map<RenderType, SimVertexRecorder> recorders = new LinkedHashMap<>();

    /** RenderType → 分岐済み VertexConsumer。同じ型で何度も呼ばれても 1 つに保つ。 */
    private final Map<RenderType, VertexConsumer> tees = new LinkedHashMap<>();

    public SimTeeBuffer(MultiBufferSource real) {
        this.real = real;
    }

    @Override
    public VertexConsumer getBuffer(RenderType type) {
        VertexConsumer realBuf = this.real.getBuffer(type);
        return this.tees.computeIfAbsent(type, t -> {
            SimVertexRecorder rec = new SimVertexRecorder();
            this.recorders.put(t, rec);
            return new Tee(realBuf, rec);
        });
    }

    /** 描画順のまま。{@code RenderType} → 記録器。 */
    public Map<RenderType, SimVertexRecorder> recorders() {
        return this.recorders;
    }

    /**
     * 2 つの {@link VertexConsumer} へ同じ呼び出しを流す。
     *
     * <p><b>戻り値は必ず自分自身を返す。</b> {@code VertexConsumer} は
     * {@code .vertex(…).color(…).uv(…).endVertex()} と繋いで使われるので、
     * 途中で実物や記録器を返すと以降の呼び出しが片側にしか行かない。
     */
    private record Tee(VertexConsumer a, VertexConsumer b) implements VertexConsumer {

        @Override
        public VertexConsumer vertex(double x, double y, double z) {
            this.a.vertex(x, y, z);
            this.b.vertex(x, y, z);
            return this;
        }

        @Override
        public VertexConsumer color(int r, int g, int bl, int al) {
            this.a.color(r, g, bl, al);
            this.b.color(r, g, bl, al);
            return this;
        }

        @Override
        public VertexConsumer uv(float u, float v) {
            this.a.uv(u, v);
            this.b.uv(u, v);
            return this;
        }

        @Override
        public VertexConsumer overlayCoords(int u, int v) {
            this.a.overlayCoords(u, v);
            this.b.overlayCoords(u, v);
            return this;
        }

        @Override
        public VertexConsumer uv2(int u, int v) {
            this.a.uv2(u, v);
            this.b.uv2(u, v);
            return this;
        }

        @Override
        public VertexConsumer normal(float x, float y, float z) {
            this.a.normal(x, y, z);
            this.b.normal(x, y, z);
            return this;
        }

        @Override
        public void endVertex() {
            this.a.endVertex();
            this.b.endVertex();
        }

        @Override
        public void defaultColor(int r, int g, int bl, int al) {
            this.a.defaultColor(r, g, bl, al);
            this.b.defaultColor(r, g, bl, al);
        }

        @Override
        public void unsetDefaultColor() {
            this.a.unsetDefaultColor();
            this.b.unsetDefaultColor();
        }
    }
}
