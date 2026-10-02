package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * YSM パック ({@code config/yes_steve_model/custom/&lt;id&gt;/}) の
 * <b>アニメーション名の一覧</b>を読む場所と、{@code &lt;stamp&gt;.anims.json} companion の
 * 読み書き場所 (quick 260819-o9l)。
 *
 * <p><b>Minecraft のクラスを一切 import しない</b> —— {@link SimPoseCodec} と同じ規約。
 * 通常の JUnit でそのまま回ることが「MC を起動せずに検証できる」ことの証明になる
 * (MC のクラス初期化が要るコードが混ざっていればテストが落ちる)。
 *
 * <h3>なぜ要るのか</h3>
 * {@link SimPoseTrace} は「今動いている霊夢を毎tick録る」オンライン収集器なので、
 * 夢想封印のように滅多に出ない技の姿勢は<b>記録に入らない</b>。記録に無いものは検証できない。
 * そこで {@link SimAnimSweep} が「パックが持つ全アニメを 1 本ずつ強制再生して録る」を行う
 * —— その入力になる「全アニメ名」をここが作る。
 *
 * <h3>読む対象</h3>
 * {@code ysm.json} の {@code files.player.animation} は
 * {@code {"main":"animations/main.animation.json", ...}} のような「別名→相対パス」表で、
 * 参照先の各ファイルが {@code {"format_version":..., "animations":{"extra43":{...}, ...}}} を持つ。
 * 実測 (霊夢パック {@code 「博丽灵梦」2}) では 6 ファイル・重複除去後 <b>316 本</b>。
 * 名前には {@code hold_mainhand:slashblade} のように {@code :} を含むものが 140 本あるが、
 * 引用符で包む処理は {@code ReimuMaidExtension.fireReimuAnimImmediate} が既に持っているので
 * ここでも {@link SimAnimSweep} でも<b>自前で再実装しない</b>。
 *
 * <h3>沈黙しない</h3>
 * {@code ysm.json} が無い・{@code files.player.animation} が無い/空・参照先ファイルが無い、の
 * いずれでも {@link IOException} を投げる。<b>途中まで読んだ「それらしい」結果を返さない</b>
 * ({@code SimPoseCodec.readFrames} と同じ思想) —— 一部しか読めていない一覧で sweep を回すと、
 * 「録れているはずのアニメが記録に無い」という最も気付きにくい失敗になる。
 */
public final class SimAnimManifest {

    private SimAnimManifest() {}

    private static final Gson GSON = new GsonBuilder().create();

    /** パックの索引ファイル名。 */
    private static final String YSM_JSON = "ysm.json";

    /** 「拡張子つきディレクトリ」形の接尾辞 ({@code ReimuConfig} の javadoc が言う形)。 */
    private static final String YSM_SUFFIX = ".ysm";

    // =========================================================================
    // パック解決
    // =========================================================================

    /**
     * {@code customDir} 配下から、{@code ysmModelId} のパック本体ディレクトリを解決する。
     *
     * <p>候補は 2 つだけ —— 素名の {@code customDir/&lt;id&gt;} と、拡張子つきディレクトリ形の
     * {@code customDir/&lt;id&gt;.ysm} ({@code id} が既に {@code .ysm} で終わるなら、逆に剥がした
     * 素名の方を第 2 候補にする)。<b>zip 化された {@code .ysm} アーカイブの展開は行わない</b>
     * (quick 260819-o9l decisions_fixed §5。実機の対象パックは展開済みディレクトリとして
     * 存在することを確認済み)。
     *
     * <p>「ディレクトリであり、かつ直下に {@code ysm.json} がある」ことまで確かめてから返す
     * —— 名前だけ一致する空ディレクトリを掴むと、失敗が {@code listAnimations} まで遅れて
     * 原因が読みにくくなる。
     *
     * @return 条件を満たす最初の候補。どちらも満たさなければ {@code null}
     */
    public static Path resolvePackRoot(Path customDir, String ysmModelId) {
        if (customDir == null || ysmModelId == null || ysmModelId.isBlank()) {
            return null;
        }
        // id はディレクトリ名 1 個分でしかありえない。区切り文字や .. を含むものは
        // customDir の外を指しうるので、解決する前に断る (探索対象を広げない)。
        if (ysmModelId.contains("/") || ysmModelId.contains("\\") || ysmModelId.contains("..")) {
            return null;
        }
        for (String candidate : candidateNames(ysmModelId)) {
            Path dir = customDir.resolve(candidate);
            if (Files.isDirectory(dir) && Files.isRegularFile(dir.resolve(YSM_JSON))) {
                return dir;
            }
        }
        return null;
    }

    /**
     * {@link #resolvePackRoot} が試すディレクトリ名を、試す順に返す。
     * 理由文字列 (「この 2 つを試したが無かった」) を組み立てるためにも使う。
     */
    public static List<String> candidateNames(String ysmModelId) {
        List<String> out = new ArrayList<>(2);
        out.add(ysmModelId);
        if (ysmModelId.endsWith(YSM_SUFFIX)) {
            out.add(ysmModelId.substring(0, ysmModelId.length() - YSM_SUFFIX.length()));
        } else {
            out.add(ysmModelId + YSM_SUFFIX);
        }
        return out;
    }

    // =========================================================================
    // アニメーション名の列挙
    // =========================================================================

    /**
     * パックが持つアニメーション名を、重複を除いてアルファベット順に並べて返す。
     *
     * @throws IOException {@code ysm.json} が読めない / {@code files.player.animation} が
     *                     無い・空 / 参照先ファイルが 1 つでも無い場合。該当パスを含む説明文つき
     */
    public static List<String> listAnimations(Path packRoot) throws IOException {
        return new ArrayList<>(listAnimationLengths(packRoot).keySet());
    }

    /**
     * パックが持つアニメーション名 → 宣言された長さ (秒、{@code animation_length}) の表を、
     * アルファベット順で返す。{@code animation_length} を持たないアニメは {@code 0.0}。
     *
     * <p>長さは {@code .anims.json} の {@code length} に入れる —— BRIEF の例
     * ({@code {"anim":"extra95","from":0,"to":19,"length":3.75}}) が示すとおり、これは
     * <b>録った時間ではなくアニメ自身の宣言された尺</b>。{@code from..to} が 20 フレーム
     * (1 秒) しか無いのに {@code length} が 3.75 なら「頭 1 秒しか録れていない」と読める
     * —— {@code ticksPerAnim} を上げる判断材料になるので、録り側の値で塗り潰さない。
     *
     * <p>同名のアニメが複数ファイルに現れた場合は<b>先に読んだ方</b>の長さを採る
     * ({@code files.player.animation} の記載順)。
     */
    public static Map<String, Double> listAnimationLengths(Path packRoot) throws IOException {
        if (packRoot == null) {
            throw new IOException("YSM パックのディレクトリが解決できていない (packRoot == null)");
        }
        Path index = packRoot.resolve(YSM_JSON);
        JsonObject root = readJsonObject(index);

        JsonObject animMap = pathToObject(root, "files", "player", "animation");
        if (animMap == null || animMap.size() == 0) {
            throw new IOException(index + " に files.player.animation が無い、または空 "
                    + "(アニメーション一覧を作れない)");
        }

        Map<String, Double> out = new TreeMap<>();
        for (Map.Entry<String, JsonElement> e : animMap.entrySet()) {
            JsonElement v = e.getValue();
            if (v == null || !v.isJsonPrimitive() || !v.getAsJsonPrimitive().isString()) {
                throw new IOException(index + " の files.player.animation." + e.getKey()
                        + " が文字列ではない (相対パスであるべき)");
            }
            String rel = v.getAsString();
            Path animFile = packRoot.resolve(rel);
            if (!Files.isRegularFile(animFile)) {
                throw new IOException("アニメーションファイルが無い: " + animFile
                        + " (" + index + " の files.player.animation." + e.getKey() + " が指す先)");
            }
            JsonObject animRoot = readJsonObject(animFile);
            JsonElement animsEl = animRoot.get("animations");
            if (animsEl == null || !animsEl.isJsonObject()) {
                throw new IOException(animFile + " に animations オブジェクトが無い");
            }
            for (Map.Entry<String, JsonElement> a : animsEl.getAsJsonObject().entrySet()) {
                out.putIfAbsent(a.getKey(), animationLength(a.getValue()));
            }
        }
        if (out.isEmpty()) {
            throw new IOException(index + " が指すファイル群から アニメーション名を 1 つも取れなかった");
        }
        return out;
    }

    /** 1 本のアニメ定義から {@code animation_length} を読む。無ければ {@code 0.0}。 */
    private static double animationLength(JsonElement anim) {
        if (anim == null || !anim.isJsonObject()) {
            return 0.0;
        }
        JsonElement len = anim.getAsJsonObject().get("animation_length");
        if (len == null || !len.isJsonPrimitive() || !len.getAsJsonPrimitive().isNumber()) {
            return 0.0;
        }
        return len.getAsDouble();
    }

    /** {@code root} から {@code keys} を順にたどってオブジェクトを取る。途中で欠けたら {@code null}。 */
    private static JsonObject pathToObject(JsonObject root, String... keys) {
        JsonObject cur = root;
        for (String k : keys) {
            if (cur == null) {
                return null;
            }
            JsonElement next = cur.get(k);
            cur = (next != null && next.isJsonObject()) ? next.getAsJsonObject() : null;
        }
        return cur;
    }

    /** JSON をオブジェクトとして読む。壊れていれば、そのパスを含む {@link IOException} にする。 */
    private static JsonObject readJsonObject(Path file) throws IOException {
        if (!Files.isRegularFile(file)) {
            throw new IOException("ファイルが無い: " + file);
        }
        String text = Files.readString(file, StandardCharsets.UTF_8);
        try {
            JsonElement el = JsonParser.parseString(text);
            if (!el.isJsonObject()) {
                throw new IOException(file + " の中身が JSON オブジェクトではない");
            }
            return el.getAsJsonObject();
        } catch (RuntimeException ex) {
            throw new IOException(file + " を JSON として読めない: " + ex.getMessage(), ex);
        }
    }

    // =========================================================================
    // .anims.json companion
    // =========================================================================

    /**
     * どのフレーム範囲がどのアニメだったか。
     *
     * @param anim   アニメーション名 ({@code ysm play} へ渡したものそのもの)
     * @param from   最初のフレーム番号 ({@code .pose.bin} 内の連番、両端を含む)
     * @param to     最後のフレーム番号 (両端を含む。1 フレームだけなら {@code from == to})
     * @param length そのアニメが宣言している長さ (秒)。パックに無ければ {@code 0.0}
     */
    public record AnimRange(String anim, int from, int to, double length) {
    }

    /**
     * {@code &lt;stamp&gt;.anims.json} を書く (存在すれば上書き)。
     * 形は {@code [{"anim":...,"from":...,"to":...,"length":...}, ...]} (BRIEF の例そのまま)。
     *
     * <p>{@code .pose.json} / {@code .pose.bin} には<b>一切触れない</b> ——
     * 別ファイルとして足すので既存スキーマは無傷で、Viewer と採点器は無改変で読める。
     */
    public static void writeAnimsCompanion(Path path, List<AnimRange> ranges) throws IOException {
        JsonArray arr = new JsonArray();
        for (AnimRange r : ranges) {
            JsonObject o = new JsonObject();
            o.addProperty("anim", r.anim());
            o.addProperty("from", r.from());
            o.addProperty("to", r.to());
            o.addProperty("length", r.length());
            arr.add(o);
        }
        Path parent = path.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Files.writeString(path, GSON.toJson(arr), StandardCharsets.UTF_8);
    }

    /** {@link #writeAnimsCompanion} が書いたものを読み戻す。 */
    public static List<AnimRange> readAnimsCompanion(Path path) throws IOException {
        String text = Files.readString(path, StandardCharsets.UTF_8);
        JsonElement el;
        try {
            el = JsonParser.parseString(text);
        } catch (RuntimeException ex) {
            throw new IOException(path + " を JSON として読めない: " + ex.getMessage(), ex);
        }
        if (!el.isJsonArray()) {
            throw new IOException(path + " の中身が JSON 配列ではない");
        }
        List<AnimRange> out = new ArrayList<>();
        for (JsonElement e : el.getAsJsonArray()) {
            if (!e.isJsonObject()) {
                throw new IOException(path + " に配列要素でないものが混じっている");
            }
            JsonObject o = e.getAsJsonObject();
            out.add(new AnimRange(
                    o.get("anim").getAsString(),
                    o.get("from").getAsInt(),
                    o.get("to").getAsInt(),
                    o.has("length") && !o.get("length").isJsonNull() ? o.get("length").getAsDouble() : 0.0));
        }
        return out;
    }

    /**
     * 名前つきの空の表。{@link SimAnimSweep} が開始前の初期値として使う
     * ({@code null} を配らないため)。
     */
    public static Map<String, Double> emptyLengths() {
        return new LinkedHashMap<>();
    }
}
