package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;

/**
 * 姿勢 companion 形式 v1 の<b>唯一の</b>読み書き場所 (Java 側)。
 *
 * <p><b>Minecraft のクラスを一切 import しない</b> —— 通常の JUnit でそのまま回ることが
 * D-01 の insurance になる (MC のクラス初期化が要るコードが混ざっていればテストが落ちる)。
 * {@link SimPoseTrace} がクライアント tick から呼び出す薄いラッパーとして使う。
 *
 * <p>companion は 2 ファイル 1 組:
 * <ul>
 *   <li>{@code <stamp>.pose.json} — 索引 ({@link Header} + tick 毎の {@code slots[]})</li>
 *   <li>{@code <stamp>.pose.bin} — float32 リトルエンディアン。相異なるフレームだけを
 *       {@code frames × verts × stride} で連結したもの (デデュープ済み)</li>
 * </ul>
 *
 * <p>デデュープの比較規則は {@code SimPoseDump.sameVerts} と同じ誤差 1.0e-4 を使う
 * (新しい規則を発明しない)。
 */
public final class SimPoseCodec {

    private SimPoseCodec() {}

    /** {@link #same(float[], float[])} が許容する要素あたりの誤差。 */
    private static final float SAME_EPS = 1.0e-4F;

    /**
     * {@link #unrotateYaw} が前提とする 1 頂点あたりの float 数。
     * {@code SimVertexRecorder.STRIDE} と同じ値だが、このクラスは「Minecraft のクラスを
     * 一切 import しない」規約のため参照できず、値をここに写している。
     */
    private static final int VERTEX_STRIDE = 11;

    private static final Gson GSON = new GsonBuilder().create();

    /**
     * 姿勢 companion 索引のヘッダ。
     *
     * @param v          companion 形式バージョン (現在 1)
     * @param gt0        記録開始時の {@code level.getGameTime()}。本体 trace の
     *                   {@code meta.gameTime} と突き合わせる唯一の接点
     *                   ({@code t = gameTime - gt0})
     * @param id         記録対象のクライアント側 entity id
     * @param type       エンティティ種別 (例 {@code touhou_little_maid:reimu})
     * @param texture    描画に使ったテクスチャ ID (取得できなければ {@code null})
     * @param stride     1 頂点あたりの float 数 ({@code SimVertexRecorder.STRIDE} と同じ、11)
     * @param verts      1 フレームの頂点数
     * @param quant      量子化桁数 (0 以下 = 量子化なし、既定)
     * @param idempotent 記録開始時の二重 {@code shoot()} 一致結果 (Pitfall 3 の実測値)
     * @param frames     相異なるフレーム数 (bin に書かれているフレーム総数と一致する)
     * @param verts      先頭フレームの頂点数 (後方互換のため残す)。フレームごとの正しい値は
     *                   {@link Index#lens}——頂点数はフレームによって変わりうる
     *                   (quick 260818-6cj)。
     * @param bin        companion バイナリファイル名 (同ディレクトリ内、{@code <stamp>.pose.bin})
     * @param uuid       記録対象の entity UUID (形式 v2 で追加。v1 の索引を読んだときは {@code null})。
     *                   <b>これが run を一意に決める鍵</b> —— {@code gt0} と本体 trace の
     *                   {@code gameTime} だけで突き合わせると、宣言 {@code duration} が大きい
     *                   シナリオ (tank = 24 時間) では過去のあらゆる companion が窓に入ってしまい、
     *                   <b>別 run の姿勢が黙って採用される</b> (2026-08-24 実測: 最新 trace の
     *                   {@code gameTime=1} に対し {@code gt0=104870} の companion が選ばれ、
     *                   {@code base=-104869} で実機頂点が 1 フレームも使われていなかった)。
     *                   新しい run は新しい entity を作るので、UUID だけで run は一意に決まる
     *                   (サーバ側の runId をクライアントへ渡す同期経路は無い)。
     */
    public record Header(
            int v,
            long gt0,
            int id,
            String type,
            String texture,
            int stride,
            int verts,
            int quant,
            boolean idempotent,
            int frames,
            String bin,
            String uuid) {

        /**
         * {@code uuid} を持たない旧来の 11 引数呼び出しをそのまま残すための便宜コンストラクタ。
         * <b>既存の呼び出し側とテストを 1 行も書き換えずに v2 を足せる</b>ことを優先している
         * (書き換えると「読めるはずの旧形式」を検査していたテストまで一緒に動いてしまう)。
         */
        public Header(int v, long gt0, int id, String type, String texture, int stride,
                      int verts, int quant, boolean idempotent, int frames, String bin) {
            this(v, gt0, id, type, texture, stride, verts, quant, idempotent, frames, bin, null);
        }
    }

    /** 姿勢 companion 形式のバージョン。{@code V2} で {@link Header#uuid()} が入った。 */
    public static final int V1 = 1;

    /** @see #V1 */
    public static final int V2 = 2;

    /**
     * 索引を読み戻した結果。{@link Header}、tick 毎の {@code slots} (tick→フレーム番号、
     * -1 = その tick は記録できなかった)、そして {@code lens} (フレーム番号→頂点数、
     * {@code lens[i]} が bin の i 番目のフレームの頂点数、{@code lens.length == header.frames()})。
     *
     * <p>{@code lens} は旧形式の索引 (quick 260818-6cj 以前) には存在しないため {@code null}
     * になりうる —— その場合は {@code header.verts()} による固定幅読み込みへフォールバックする
     * (旧 {@code .pose.json} / {@code .pose.bin} を例外なく読めることが条件)。
     *
     * <p>{@code groups} (quick 260818-oq4) は 1 フレームが複数の RenderType グループから成る
     * ことを表す索引。{@code textures}/{@code glens}/{@code gtex} の<b>3 つすべてが配列として
     * 存在するときだけ</b>組み立てられ、そうでなければ {@code null} になる
     * (旧 {@code .pose.json} / グループ表を持たない索引も例外なく読めることが条件)。
     */
    public record Index(Header header, int[] slots, int[] lens, Groups groups) {
    }

    /**
     * companion 索引のグループ表 (quick 260818-oq4)。1 フレームが複数の RenderType グループから
     * 成ることを表す —— {@code glens[i][k]} はフレーム i のグループ k の頂点数、
     * {@code gtex[i][k]} は {@code textures} への添字。常に
     * {@code sum(glens[i]) == lens[i]} ({@link #validateGroups} が書き込み時・読み戻し時の
     * 両方で検査する)。
     *
     * <p><b>配列成分を持つので生成 {@code equals} は参照比較になる。等値比較には使わず、
     * 要素ごとに突き合わせること</b> (quick 260818-6cj で {@code Header} に配列を足すと
     * 既存アサーションが壊れると分かった判例の再発防止)。
     */
    public record Groups(int[][] glens, int[][] gtex, String[] textures) {
    }

    /**
     * {@code Groups} が {@code lens} と整合しているかを検査する。
     *
     * @return 整合していれば {@code null}、不整合ならそのまま例外文へ入れられる日本語の説明文
     */
    public static String validateGroups(int[] lens, Groups g) {
        if (g.glens().length != lens.length) {
            return "glens の長さ(" + g.glens().length + ") が lens の長さ(" + lens.length + ") と一致しない";
        }
        if (g.gtex().length != lens.length) {
            return "gtex の長さ(" + g.gtex().length + ") が lens の長さ(" + lens.length + ") と一致しない";
        }
        for (int i = 0; i < lens.length; i++) {
            if (g.gtex()[i].length != g.glens()[i].length) {
                return "フレーム " + i + ": gtex[i].length(" + g.gtex()[i].length
                        + ") != glens[i].length(" + g.glens()[i].length + ")";
            }
            long sum = 0L;
            for (int v : g.glens()[i]) {
                sum += v;
            }
            if (sum != lens[i]) {
                return "フレーム " + i + ": sum(glens[i])=" + sum + " != lens[i]=" + lens[i]
                        + " (期待 " + lens[i] + ", 実測 " + sum + ")";
            }
        }
        for (int i = 0; i < g.gtex().length; i++) {
            for (int k = 0; k < g.gtex()[i].length; k++) {
                int t = g.gtex()[i][k];
                if (t < 0 || t >= g.textures().length) {
                    return "フレーム " + i + " グループ " + k + ": gtex 添字 " + t
                            + " が textures の範囲外 (0.." + (g.textures().length - 1) + ")";
                }
            }
        }
        for (int i = 0; i < g.textures().length; i++) {
            if (g.textures()[i] == null) {
                return "textures[" + i + "] が null";
            }
        }
        return null;
    }

    // =========================================================================
    // 量子化・デデュープ
    // =========================================================================

    /**
     * 座標配列を {@code digits} 桁へ丸める。
     *
     * <p><b>{@code digits<=0} なら入力をそのまま (要素が完全一致する新しい配列として) 返す</b>
     * —— 既定では何も変えないことを機械で守る ({@code SimTuningGuardTest} と同じ思想)。
     * RESEARCH の Pitfall 1 (idle アニメの微細ゆらぎでデデュープが効かない) への保険として
     * 用意するが、既定では作動させない。
     */
    public static float[] quantize(float[] v, int digits) {
        float[] out = new float[v.length];
        if (digits <= 0) {
            System.arraycopy(v, 0, out, 0, v.length);
            return out;
        }
        float scale = (float) Math.pow(10, digits);
        for (int i = 0; i < v.length; i++) {
            out[i] = Math.round(v[i] * scale) / scale;
        }
        return out;
    }

    /**
     * 2 つのフレームが「同じ姿勢」とみなせるか。{@code SimPoseDump.sameVerts} /
     * {@code SimModelDump} のデデュープと同じ誤差 1.0e-4 の比較規則。長さが違えば
     * (要素を比較するまでもなく) 必ず {@code false}。
     */
    public static boolean same(float[] a, float[] b) {
        if (a.length != b.length) {
            return false;
        }
        for (int i = 0; i < a.length; i++) {
            if (Math.abs(a[i] - b[i]) > SAME_EPS) {
                return false;
            }
        }
        return true;
    }

    /**
     * {@code shot} を既存 {@code frames} と突き合わせ、slot 番号を返す。
     *
     * <p>一致するフレームが既にあればその index を返す (リストは伸びない)。
     * 無ければ末尾に追加して新しい index を返す。ただし {@code frames.size()} が
     * 既に {@code maxFrames} に達している状態で新規フレームが来たら {@code -1} を返し、
     * {@code frames} には触れない —— 上限超過時に既存フレームを間引いたり近いフレームで
     * 代用したりしない (嘘のデータを作らない)、呼び出し側が警告を出すための合図。
     */
    public static int slotFor(List<float[]> frames, float[] shot, int maxFrames) {
        for (int i = 0; i < frames.size(); i++) {
            if (same(frames.get(i), shot)) {
                return i;
            }
        }
        if (frames.size() >= maxFrames) {
            return -1;
        }
        frames.add(shot);
        return frames.size() - 1;
    }

    /**
     * 末尾の未記録 tick ({@code -1}) を落とし、記録範囲を「最後に本当に録れた tick」で
     * 終わらせる。<b>破壊的</b>。落とした件数を返す。
     *
     * <p><b>なぜ要るか</b>: Viewer の {@code poseTraceParts()} (gl.js:995-1017) は
     * <b>範囲内</b>の {@code -1} を「記録なし」として扱わず、直前の有効フレームまで遡って
     * 貼る ({@code backfilled})。範囲<b>外</b>なら {@code null} を返してアニメライブラリ/
     * 再構成へ落ちる。つまり末尾に {@code -1} を残したまま記録を止めると、
     * <b>上限時の古い 1 枚を貼り続ける</b> —— 2026-08-19 に「夢想封印が実機と違う」の
     * 正体だった不具合と同じ形になる。範囲そのものを縮めるのが正しい止め方。
     *
     * <p>途中の穴 (画面外などで撮れなかった tick) は落とさない。あれは backfill されることを
     * 承知の上での既存挙動で、{@code poseSource} が {@code backfilled} と区別して出る。
     */
    public static int trimTrailingUnrecorded(List<Integer> slots) {
        int removed = 0;
        while (!slots.isEmpty() && slots.get(slots.size() - 1) < 0) {
            slots.remove(slots.size() - 1);
            removed++;
        }
        return removed;
    }

    // =========================================================================
    // 多方向撮影 (quick 260818-x0k)
    // =========================================================================

    /**
     * 撮影時に付けた Y 軸まわりの向き {@code yawDeg} を打ち消し、頂点を
     * 「yaw=0 で撮ったときの座標系」へ戻す (quick 260818-x0k)。
     * 入力 {@code v} は<b>変更せず</b>新しい配列を返す ({@link #quantize} と同じ非破壊契約)。
     *
     * <p><b>{@code stride} は {@code SimVertexRecorder.STRIDE}({@value #VERTEX_STRIDE}) の
     * {@code [x,y,z,u,v,nx,ny,nz,r,g,b]} レイアウト専用。</b> このクラスは
     * 「Minecraft のクラスを一切 import しない」規約のため {@code SimVertexRecorder} を
     * 参照できず、他のレイアウトを安全に扱えない。よって {@code stride != }{@value #VERTEX_STRIDE}
     * は {@link IllegalArgumentException} で拒否する —— 誤ったレイアウト解釈で頂点データを
     * 黙って壊さないため。
     *
     * <p><b>0° と 180° は符号反転のみの厳密パスを通る。</b> 三角関数を使うと
     * {@code cos(180°)} が厳密な {@code -1} にならず丸め誤差が入るので、この 2 角度だけは
     * 避ける (180° を 2 回適用したら入力へ<b>ビット単位</b>で戻ることが acceptance)。
     * 180° の逆回転は位置 {@code (x,y,z)→(-x,y,-z)}、法線 {@code (nx,ny,nz)→(-nx,ny,-nz)}。
     * 90°/270° 等の拡張角度は将来のために一般式 (三角関数) パスへ落ちる ——
     * 今回は使われないが、{@code SimModelDump.SHOT_YAWS_DEG} へ角度を足すだけで
     * 拡張できる形にしてある。
     *
     * @param yawDeg 撮影時に与えた向き (度)。{@code [0,360)} へ正規化してから使うので
     *               {@code -180} や {@code 540} を渡しても {@code 180} と同じ結果になる
     */
    public static float[] unrotateYaw(float[] v, int stride, float yawDeg) {
        if (stride != VERTEX_STRIDE) {
            throw new IllegalArgumentException("unrotateYaw は stride=" + VERTEX_STRIDE
                    + " ([x,y,z,u,v,nx,ny,nz,r,g,b]) 専用だが stride=" + stride + " が渡された");
        }
        float[] out = new float[v.length];
        System.arraycopy(v, 0, out, 0, v.length);

        float norm = ((yawDeg % 360F) + 360F) % 360F;
        if (norm == 0F) {
            return out;
        }
        if (norm == 180F) {
            // 厳密パス: 符号反転のみ。三角関数を使わないので丸め誤差が入らない。
            for (int b = 0; b + stride <= out.length; b += stride) {
                out[b] = -out[b];               // x
                out[b + 2] = -out[b + 2];       // z
                out[b + 5] = -out[b + 5];       // nx
                out[b + 7] = -out[b + 7];       // nz
            }
            return out;
        }
        // 一般式パス (90°/270° への拡張用)。ここは丸め誤差が入る。
        double th = Math.toRadians(norm);
        float c = (float) Math.cos(th);
        float s = (float) Math.sin(th);
        for (int b = 0; b + stride <= out.length; b += stride) {
            float x = out[b], z = out[b + 2];
            out[b] = x * c + z * s;
            out[b + 2] = -x * s + z * c;
            float nx = out[b + 5], nz = out[b + 7];
            out[b + 5] = nx * c + nz * s;
            out[b + 7] = -nx * s + nz * c;
        }
        return out;
    }

    /**
     * 方向B (yaw != 0 で撮ったショット) を方向Aの座標系へ戻す。ただし<b>戻す前に、
     * 回転前の生配列どうしを {@link #same} で突き合わせる</b>
     * (quick 260818-x0k、plan-checker 指摘の BLOCKER 対応)。
     *
     * <p>{@code renderer.render()} を一切呼ばない<b>純粋関数</b> ——
     * {@link #same} と {@link #unrotateYaw} の合成にすぎないので JUnit だけで直接検証できる。
     *
     * <p><b>なぜ独立したガードが要るのか</b>: YSM の実描画は本リポジトリ外の native
     * ({@code geoRender()}) へ委譲されており、同一 tick 内で 2 回 render したときに
     * 1 回目の結果をキャッシュで返す可能性をソースから否定できない。もしそうなら方向Bは
     * 方向Aの複製にすぎず、180° 回して連結すると<b>「鏡像の重複ジオメトリ」が増えるだけで
     * 絵が悪化する</b>。{@code SimPoseTrace} の冪等性ゲートは {@code shoot()} の
     * <b>最終出力どうし</b>を比べるだけなので、決定論的に壊れた結果が毎回一致し続ける
     * このケースを区別できない (壊れていても「一致 = 正常」と読んでしまう)。
     * だから<b>回転前の生配列</b>を直接突き合わせるこのガードが別途必要になる。
     *
     * @return 衝突していれば {@code null} (「このグループは合成に使うな」の合図)、
     *         そうでなければ {@link #unrotateYaw}{@code (rawB, stride, yawDeg)} の結果
     */
    public static float[] mergeDirectionB(float[] rawA, float[] rawB, int stride, float yawDeg) {
        if (same(rawA, rawB)) {
            // 三角関数を使う unrotateYaw を呼ぶ「前」に判定する。
            return null;
        }
        return unrotateYaw(rawB, stride, yawDeg);
    }

    // =========================================================================
    // 入出力
    // =========================================================================

    /** float32 リトルエンディアンで 1 フレーム分の頂点を bin ファイルへ追記する (無ければ作る)。 */
    public static void appendFrame(Path bin, float[] verts) throws IOException {
        ByteBuffer buf = ByteBuffer.allocate(verts.length * Float.BYTES).order(ByteOrder.LITTLE_ENDIAN);
        for (float f : verts) {
            buf.putFloat(f);
        }
        Path parent = bin.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Files.write(bin, buf.array(), StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    }

    /**
     * 索引 JSON を書く (存在すれば上書き)。{@code lens} 無し (旧形式) の薄いラッパー——
     * 既存の呼び出し元・既存テストが無改変で通るよう残す。
     */
    public static void writeIndex(Path json, Header h, int[] slots) throws IOException {
        writeIndex(json, h, slots, null, null);
    }

    /**
     * 索引 JSON を書く (存在すれば上書き)。{@code lens} はフレームごとの頂点数
     * (フレーム番号→頂点数)。{@code null} なら書かない (旧形式のまま)。薄いラッパー——
     * 既存の呼び出し元・既存テストが無改変で通るよう残す。
     */
    public static void writeIndex(Path json, Header h, int[] slots, int[] lens) throws IOException {
        writeIndex(json, h, slots, lens, null);
    }

    /**
     * 索引 JSON を書く (存在すれば上書き)。{@code groups} はグループ表 (quick 260818-oq4)。
     * {@code groups != null} なら<b>書き出す前に</b> {@link #validateGroups} を呼び、
     * {@code null} 以外が返ったら {@link IOException} を投げて<b>ファイルを一切作らない</b>
     * (検証は先頭で行い、ファイル書き込みはその後に限るので、投げた時点でディスクへは
     * 何も触れていない)。通れば既存キーに加えて {@code textures} / {@code glens} /
     * {@code gtex} を書く ({@code glens} / {@code gtex} は JSON の配列の配列)。
     */
    public static void writeIndex(Path json, Header h, int[] slots, int[] lens, Groups groups) throws IOException {
        if (groups != null) {
            if (lens == null) {
                throw new IOException("グループ表(groups)を書くには lens が必須 (groups != null だが lens == null)");
            }
            String err = validateGroups(lens, groups);
            if (err != null) {
                throw new IOException("グループ表が不整合なため索引を書けない: " + err);
            }
        }

        JsonObject o = new JsonObject();
        o.addProperty("v", h.v());
        o.addProperty("gt0", h.gt0());
        o.addProperty("id", h.id());
        o.addProperty("type", h.type());
        o.addProperty("texture", h.texture());
        o.addProperty("stride", h.stride());
        o.addProperty("verts", h.verts());
        o.addProperty("quant", h.quant());
        o.addProperty("idempotent", h.idempotent());
        o.addProperty("frames", h.frames());
        o.addProperty("bin", h.bin());
        // uuid は持っているときだけ書く —— 旧形式 (v1) を書く経路の出力を 1 バイトも変えない。
        // 「読める」だけでなく「書いたものが前と同じ」ことも、既存テストが見張っている。
        if (h.uuid() != null) {
            o.addProperty("uuid", h.uuid());
        }
        JsonArray arr = new JsonArray();
        for (int s : slots) {
            arr.add(s);
        }
        o.add("slots", arr);
        if (lens != null) {
            JsonArray lensArr = new JsonArray();
            for (int l : lens) {
                lensArr.add(l);
            }
            o.add("lens", lensArr);
        }
        if (groups != null) {
            JsonArray texturesArr = new JsonArray();
            for (String t : groups.textures()) {
                texturesArr.add(t);
            }
            o.add("textures", texturesArr);
            JsonArray glensArr = new JsonArray();
            for (int[] g : groups.glens()) {
                JsonArray inner = new JsonArray();
                for (int v : g) {
                    inner.add(v);
                }
                glensArr.add(inner);
            }
            o.add("glens", glensArr);
            JsonArray gtexArr = new JsonArray();
            for (int[] g : groups.gtex()) {
                JsonArray inner = new JsonArray();
                for (int v : g) {
                    inner.add(v);
                }
                gtexArr.add(inner);
            }
            o.add("gtex", gtexArr);
        }

        Path parent = json.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Files.writeString(json, GSON.toJson(o), StandardCharsets.UTF_8);
    }

    /** 索引 JSON を読み戻す。{@code lens} キーが無ければ {@link Index#lens} は {@code null}。 */
    public static Index readIndex(Path json) throws IOException {
        String text = Files.readString(json, StandardCharsets.UTF_8);
        JsonObject o = JsonParser.parseString(text).getAsJsonObject();
        Header h = new Header(
                o.get("v").getAsInt(),
                o.get("gt0").getAsLong(),
                o.get("id").getAsInt(),
                o.get("type").getAsString(),
                o.has("texture") && !o.get("texture").isJsonNull() ? o.get("texture").getAsString() : null,
                o.get("stride").getAsInt(),
                o.get("verts").getAsInt(),
                o.get("quant").getAsInt(),
                o.get("idempotent").getAsBoolean(),
                o.get("frames").getAsInt(),
                o.get("bin").getAsString(),
                // v1 の索引には無い。無ければ null のまま —— 読めることが条件。
                o.has("uuid") && !o.get("uuid").isJsonNull() ? o.get("uuid").getAsString() : null);
        JsonArray arr = o.getAsJsonArray("slots");
        int[] slots = new int[arr.size()];
        for (int i = 0; i < slots.length; i++) {
            slots[i] = arr.get(i).getAsInt();
        }
        int[] lens = null;
        if (o.has("lens") && o.get("lens").isJsonArray()) {
            JsonArray lensArr = o.getAsJsonArray("lens");
            lens = new int[lensArr.size()];
            for (int i = 0; i < lens.length; i++) {
                lens[i] = lensArr.get(i).getAsInt();
            }
        }

        // グループ表 (quick 260818-oq4): textures / glens / gtex の 3 つすべてが配列として
        // 存在するときだけ組み立てる。1 つでも欠けていれば旧形式として null のままにする
        // (旧 .pose.json を例外なく読めることが条件)。
        Groups groups = null;
        if (o.has("textures") && o.get("textures").isJsonArray()
                && o.has("glens") && o.get("glens").isJsonArray()
                && o.has("gtex") && o.get("gtex").isJsonArray()) {
            JsonArray texturesArr = o.getAsJsonArray("textures");
            String[] textures = new String[texturesArr.size()];
            for (int i = 0; i < textures.length; i++) {
                textures[i] = texturesArr.get(i).isJsonNull() ? null : texturesArr.get(i).getAsString();
            }
            JsonArray glensArr = o.getAsJsonArray("glens");
            int[][] glens = new int[glensArr.size()][];
            for (int i = 0; i < glens.length; i++) {
                JsonArray inner = glensArr.get(i).getAsJsonArray();
                glens[i] = new int[inner.size()];
                for (int k = 0; k < glens[i].length; k++) {
                    glens[i][k] = inner.get(k).getAsInt();
                }
            }
            JsonArray gtexArr = o.getAsJsonArray("gtex");
            int[][] gtex = new int[gtexArr.size()][];
            for (int i = 0; i < gtex.length; i++) {
                JsonArray inner = gtexArr.get(i).getAsJsonArray();
                gtex[i] = new int[inner.size()];
                for (int k = 0; k < gtex[i].length; k++) {
                    gtex[i][k] = inner.get(k).getAsInt();
                }
            }
            groups = new Groups(glens, gtex, textures);
            if (lens != null) {
                // 途中まで読んだ「それらしい」結果を返さない (可変長 readFrames と同じ思想)。
                String err = validateGroups(lens, groups);
                if (err != null) {
                    throw new IOException("読み戻した索引のグループ表が不整合: " + err);
                }
            }
        }

        return new Index(h, slots, lens, groups);
    }

    /** bin ファイルから {@code frameCount} 本、1 フレーム {@code floatsPerFrame} 個ずつ読み戻す (固定幅、旧形式用)。 */
    public static List<float[]> readFrames(Path bin, int frameCount, int floatsPerFrame) throws IOException {
        byte[] bytes = Files.readAllBytes(bin);
        ByteBuffer buf = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        List<float[]> out = new ArrayList<>(frameCount);
        for (int f = 0; f < frameCount; f++) {
            float[] v = new float[floatsPerFrame];
            for (int i = 0; i < floatsPerFrame; i++) {
                v[i] = buf.getFloat();
            }
            out.add(v);
        }
        return out;
    }

    /**
     * bin ファイルから可変長のフレームを読み戻す。{@code lens[i]} が i 番目のフレームの頂点数
     * (float 数は {@code lens[i] * stride})。読む前に {@code Files.size(bin)} と
     * {@code sum(lens) * stride * Float.BYTES} を照合し、不一致なら期待値と実測値の両方を
     * 含む {@link IOException} を投げる (途中まで読んだ「それらしい」結果を返さない)。
     */
    public static List<float[]> readFrames(Path bin, int[] lens, int stride) throws IOException {
        long sumVerts = 0L;
        for (int l : lens) {
            sumVerts += l;
        }
        long expectedBytes = sumVerts * stride * Float.BYTES;
        long actualBytes = Files.size(bin);
        if (actualBytes != expectedBytes) {
            throw new IOException("pose bin サイズ不一致: 期待 " + expectedBytes
                    + " バイト (sum(lens)=" + sumVerts + " * stride=" + stride + " * 4), 実測 "
                    + actualBytes + " バイト (" + bin + ")");
        }

        byte[] bytes = Files.readAllBytes(bin);
        ByteBuffer buf = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        List<float[]> out = new ArrayList<>(lens.length);
        for (int len : lens) {
            int floatsPerFrame = len * stride;
            float[] v = new float[floatsPerFrame];
            for (int i = 0; i < floatsPerFrame; i++) {
                v[i] = buf.getFloat();
            }
            out.add(v);
        }
        return out;
    }
}
