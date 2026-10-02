package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import java.util.zip.DataFormatException;
import java.util.zip.Deflater;
import java.util.zip.Inflater;

/**
 * palette companion 形式 {@code palmask-deflate-v1} の<b>唯一の</b>読み書き場所 (Java 側)。
 *
 * <p><b>Minecraft のクラスを一切 import しない</b> —— {@link SimPoseCodec} と同じ規約
 * (通常の JUnit でそのまま回ることが、MC のクラス初期化を要らないことの保険になる)。
 *
 * <p>palette は 1058 ボーン × 12 float (pal0=回転 rad / pal1=位置 / pal2=scale / pal3=未使用)。
 * ワイヤ形式は <b>pal3 (comps 9..11) を書かない</b> —— 全 golden 標本で厳密に 0
 * (18 x 1058 x 3 = 57,132 値) であることが {@code SimPaletteCodecTest} の
 * {@code unusedComponentsAreZeroInGolden} で裏取りされている。
 *
 * <p>2 種類のレコード:
 * <ul>
 *   <li><b>K (keyframe)</b> —— 全ゼロ状態を基準に差分を取る。デコードは状態を丸ごとゼロに
 *       してから mask 分だけ埋めるので、K レコード単体で完結する。</li>
 *   <li><b>D (delta)</b> —— 直前に<b>デコードした</b>状態を基準に、9 float のいずれかが
 *       厳密 {@code !=} で変わったボーンだけを含む。イプシロンではなく厳密比較
 *       (でないと形式が非可逆になり、誤差ゼロという主張が崩れる)。</li>
 * </ul>
 *
 * <p>1 レコードの生バイト列 (圧縮前) は {@code mask || payload}:
 * mask は {@code ceil(bones/8)} バイト (LSB-first、ビット b = ボーン b が本レコードに含まれる)、
 * payload はマスクが立ったボーンごとに 9 x float32 リトルエンディアン (36 バイト/ボーン)。
 * これを {@link Deflater} レベル 9・既定 (zlib ラップ、RFC 1950) で圧縮したものがレコード。
 */
public final class SimPaletteCodec {

    private SimPaletteCodec() {}

    /** ワイヤ形式の識別子。索引 JSON の {@code codec} フィールドに書く。 */
    public static final String CODEC = "palmask-deflate-v1";

    /** companion 形式のバージョン。 */
    public static final int V1 = 1;

    /** 1 ボーンあたり、ワイヤに乗る float 数 (pal0/pal1/pal2 のみ。pal3 は落とす)。 */
    public static final int COMPS = 9;

    /** 1 ボーンあたり、実機 palette の float 数 (pal0/pal1/pal2/pal3)。 */
    public static final int PALETTE_STRIDE = 12;

    /** 既定のキーフレーム間隔 (tick)。{@code SimDelta.KEYFRAME_TICKS} と同じ値。 */
    public static final int KEYFRAME_TICKS = 100;

    private static final Gson GSON = new GsonBuilder().create();

    /**
     * palette companion 索引のヘッダ。
     *
     * @param v       companion 形式バージョン (現在 {@link #V1})
     * @param codec   ワイヤ形式の識別子 ({@link #CODEC})
     * @param gt0     記録開始時の {@code level.getGameTime()}
     * @param id      記録対象のクライアント側 entity id (未確定なら {@code -1})
     * @param uuid    記録対象の entity UUID (未確定なら {@code null})
     * @param type    エンティティ種別 (例 {@code touhou_little_maid:reimu})
     * @param bones   ボーン本数 (実機 palette なら 1058)
     * @param comps   1 ボーンあたりワイヤに乗る float 数 ({@link #COMPS})
     * @param keyframe キーフレーム間隔 (tick)
     * @param names   {@code names[slot]} = ボーン名。Viewer 側のボーン番号とは食い違うので
     *                (実測 1058/1058 disagreement)、これが両者を繋ぐ唯一の橋になる
     * @param bin     companion バイナリファイル名 (同ディレクトリ内)
     * @param jars    記録時の jar SHA-256 (再現性の裏取り用。無ければ空配列)
     */
    public record Header(
            int v,
            String codec,
            long gt0,
            int id,
            String uuid,
            String type,
            int bones,
            int comps,
            int keyframe,
            String[] names,
            String bin,
            String[] jars) {
    }

    /**
     * 索引を読み戻した結果。{@code slots[t]} = tick t のフレーム番号 (-1 = 記録なし)、
     * {@code lens[i]} = レコード i の圧縮後バイト長、{@code kinds[i]} = {@code "K"} または
     * {@code "D"}。デコーダは kind を位置から推測してはならない —— 記録側はフレーム落ちを
     * 検出すると予定外の K を挟むことがある。
     */
    public record Index(Header header, int[] slots, int[] lens, String[] kinds) {
    }

    // =========================================================================
    // 符号化・復号
    // =========================================================================

    /**
     * {@code baseline} (9 float/ボーン) と {@code palette} (12 float/ボーン、pal3 は無視) を
     * 突き合わせ、9 float のいずれかが厳密に違うボーンの mask を返す。
     *
     * <p>K レコードのマスクは {@code baseline} に全ゼロ配列を渡せば同じ関数で作れる
     * (全ゼロと比べて非ゼロなボーン = 含めるべきボーン、という定義がそのまま成立する)。
     *
     * <p><b>比較はビット単位で行う (2026-08-24 実測で発見、Rule 1 修正)。</b> 素の
     * {@code !=} だと IEEE754 では {@code -0.0f != 0.0f} が {@code false} になり、
     * golden 標本 003番bone (rx/ry が厳密に {@code -0.0}) がキーフレームの「全ゼロ基準」から
     * 見て「変化なし」と誤判定される —— K レコードにこのボーンが含まれず、デコード後は
     * {@code +0.0} のまま (キーフレームの初期化値)。実測: 18 標本中 15 標本 x 2 comp =
     * 30/171,396 のビット不一致 (round-trip 検証 {@code roundTripIsBitIdentical} で検出)。
     * この形式は「誤差ゼロ」がビット一致で証明される設計 (must_haves) なので、符号だけが違う
     * ゼロも「変化」として扱わなければ、その主張が成立しない。</p>
     */
    public static boolean[] changedBones(float[] baseline, float[] palette, int bones) {
        boolean[] mask = new boolean[bones];
        for (int b = 0; b < bones; b++) {
            for (int k = 0; k < COMPS; k++) {
                float a = palette[b * PALETTE_STRIDE + k];
                float c = baseline[b * COMPS + k];
                if (Float.floatToRawIntBits(a) != Float.floatToRawIntBits(c)) {
                    mask[b] = true;
                    break;
                }
            }
        }
        return mask;
    }

    /**
     * {@code state9} (直前にデコードした状態、9 float/ボーン) から {@code palette}
     * (この tick の実機 palette、12 float/ボーン) への 1 レコードを作る。
     *
     * <p>{@code keyframe} なら全ゼロを基準にマスクを作る (直前の {@code state9} の中身は
     * 無視する)。<b>{@code state9} は呼び出し後、この呼び出しが表す状態へ書き換わる</b>
     * ——次の呼び出し (次の tick の D レコード) がそのまま基準にできるようにするため。
     *
     * @return 圧縮済みレコードのバイト列 (zlib ラップの deflate ストリーム)
     */
    public static byte[] encode(float[] state9, float[] palette, int bones, boolean keyframe) throws IOException {
        float[] baseline = keyframe ? new float[bones * COMPS] : state9;
        boolean[] mask = changedBones(baseline, palette, bones);

        int maskBytes = (bones + 7) / 8;
        int popcount = 0;
        byte[] maskArr = new byte[maskBytes];
        for (int b = 0; b < bones; b++) {
            if (mask[b]) {
                maskArr[b / 8] |= (byte) (1 << (b % 8));
                popcount++;
            }
        }

        ByteBuffer raw = ByteBuffer.allocate(maskBytes + 36 * popcount).order(ByteOrder.LITTLE_ENDIAN);
        raw.put(maskArr);
        for (int b = 0; b < bones; b++) {
            if (mask[b]) {
                for (int k = 0; k < COMPS; k++) {
                    raw.putFloat(palette[b * PALETTE_STRIDE + k]);
                }
            }
        }

        // state9 を advance する。keyframe ならまずゼロへ落とす (デコード側の契約と同じ)。
        if (keyframe) {
            Arrays.fill(state9, 0F);
        }
        for (int b = 0; b < bones; b++) {
            if (mask[b]) {
                System.arraycopy(palette, b * PALETTE_STRIDE, state9, b * COMPS, COMPS);
            }
        }

        return deflate(raw.array());
    }

    /**
     * {@code record} (圧縮済みレコード) を {@code state9} へ復号する。
     *
     * <p><b>検証を先に済ませてから state9 へ書く</b> —— 壊れたレコードが
     * 「途中まで書き換わった state9」を残さないため。解凍後サイズが
     * {@code ceil(bones/8) + 36 * popcount(mask)} と厳密に一致しなければ {@link IOException}
     * を投げ、state9 には一切触れない。
     */
    public static void decode(float[] state9, byte[] record, boolean keyframe, int bones) throws IOException {
        byte[] inflated = inflate(record);

        int maskBytes = (bones + 7) / 8;
        if (inflated.length < maskBytes) {
            throw new IOException("破損したレコード: 解凍後サイズ " + inflated.length
                    + " バイトがマスク長 " + maskBytes + " バイトより小さい");
        }
        int extraBits = maskBytes * 8 - bones;
        if (extraBits > 0) {
            int lastByte = inflated[maskBytes - 1] & 0xFF;
            int highMask = ((1 << extraBits) - 1) << (8 - extraBits);
            if ((lastByte & highMask) != 0) {
                throw new IOException("破損したレコード: マスク末尾 (bones=" + bones
                        + " を超えた分) に余分なビットが立っている");
            }
        }
        int popcount = 0;
        for (int i = 0; i < maskBytes; i++) {
            popcount += Integer.bitCount(inflated[i] & 0xFF);
        }
        long expected = (long) maskBytes + 36L * popcount;
        if (inflated.length != expected) {
            throw new IOException("破損したレコード: 解凍後サイズ " + inflated.length + " バイトが期待値 "
                    + expected + " バイト (mask=" + maskBytes + " + 36*popcount(" + popcount
                    + ")) と一致しない");
        }

        // ここまで来て初めて state9 へ触れる。
        if (keyframe) {
            Arrays.fill(state9, 0, bones * COMPS, 0F);
        }
        ByteBuffer buf = ByteBuffer.wrap(inflated).order(ByteOrder.LITTLE_ENDIAN);
        buf.position(maskBytes);
        for (int b = 0; b < bones; b++) {
            boolean set = ((inflated[b / 8] >> (b % 8)) & 1) != 0;
            if (set) {
                for (int k = 0; k < COMPS; k++) {
                    state9[b * COMPS + k] = buf.getFloat();
                }
            }
        }
    }

    private static byte[] deflate(byte[] data) {
        Deflater deflater = new Deflater(Deflater.BEST_COMPRESSION);
        try {
            deflater.setInput(data);
            deflater.finish();
            ByteArrayOutputStream bos = new ByteArrayOutputStream(Math.max(64, data.length));
            byte[] buf = new byte[8192];
            while (!deflater.finished()) {
                int n = deflater.deflate(buf);
                bos.write(buf, 0, n);
            }
            return bos.toByteArray();
        } finally {
            deflater.end();
        }
    }

    private static byte[] inflate(byte[] data) throws IOException {
        Inflater inflater = new Inflater();
        try {
            inflater.setInput(data);
            ByteArrayOutputStream bos = new ByteArrayOutputStream(Math.max(64, data.length * 4));
            byte[] buf = new byte[8192];
            while (!inflater.finished()) {
                int n = inflater.inflate(buf);
                if (n == 0) {
                    if (inflater.needsInput() || inflater.needsDictionary()) {
                        throw new IOException("破損したレコード: 解凍データが不足している"
                                + " (レコードが壊れているか途中で切れている)");
                    }
                }
                bos.write(buf, 0, n);
            }
            return bos.toByteArray();
        } catch (DataFormatException e) {
            throw new IOException("破損したレコード: 解凍に失敗した (" + e.getMessage() + ")", e);
        } finally {
            inflater.end();
        }
    }

    // =========================================================================
    // 入出力
    // =========================================================================

    /** 圧縮済みレコードを bin ファイルへ追記する (無ければ作る)。 */
    public static void appendRecord(Path bin, byte[] record) throws IOException {
        Path parent = bin.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Files.write(bin, record, StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    }

    /** 索引 JSON を書く (存在すれば上書き)。{@code frames}/{@code bytes} は {@code lens} から導出する。 */
    public static void writeIndex(Path json, Header h, int[] slots, int[] lens, String[] kinds) throws IOException {
        if (lens.length != kinds.length) {
            throw new IOException("lens の長さ(" + lens.length + ") と kinds の長さ(" + kinds.length + ") が一致しない");
        }
        long bytes = 0L;
        for (int l : lens) {
            bytes += l;
        }

        JsonObject o = new JsonObject();
        o.addProperty("v", h.v());
        o.addProperty("codec", h.codec());
        o.addProperty("gt0", h.gt0());
        o.addProperty("id", h.id());
        o.addProperty("uuid", h.uuid());
        o.addProperty("type", h.type());
        o.addProperty("bones", h.bones());
        o.addProperty("comps", h.comps());
        o.addProperty("keyframe", h.keyframe());
        JsonArray namesArr = new JsonArray();
        for (String n : h.names()) {
            namesArr.add(n);
        }
        o.add("names", namesArr);
        o.addProperty("frames", lens.length);
        o.addProperty("bin", h.bin());
        JsonArray slotsArr = new JsonArray();
        for (int s : slots) {
            slotsArr.add(s);
        }
        o.add("slots", slotsArr);
        JsonArray lensArr = new JsonArray();
        for (int l : lens) {
            lensArr.add(l);
        }
        o.add("lens", lensArr);
        JsonArray kindsArr = new JsonArray();
        for (String k : kinds) {
            kindsArr.add(k);
        }
        o.add("kinds", kindsArr);
        o.addProperty("bytes", bytes);
        JsonArray jarsArr = new JsonArray();
        for (String j : h.jars()) {
            jarsArr.add(j);
        }
        o.add("jars", jarsArr);

        Path parent = json.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Files.writeString(json, GSON.toJson(o), StandardCharsets.UTF_8);
    }

    /**
     * 索引 JSON を読み戻す。読者が守るべき不変条件をここで全部検査し、
     * 破っていれば実測値を含む {@link IOException} を投げる (壊れた索引で黙って動かない)。
     */
    public static Index readIndex(Path json) throws IOException {
        String text = Files.readString(json, StandardCharsets.UTF_8);
        JsonObject o = JsonParser.parseString(text).getAsJsonObject();

        int bones = o.get("bones").getAsInt();
        JsonArray namesArr = o.getAsJsonArray("names");
        String[] names = new String[namesArr.size()];
        for (int i = 0; i < names.length; i++) {
            names[i] = namesArr.get(i).getAsString();
        }
        if (names.length != bones) {
            throw new IOException("names の長さ(" + names.length + ") が bones(" + bones + ") と一致しない");
        }

        Header h = new Header(
                o.get("v").getAsInt(),
                o.get("codec").getAsString(),
                o.get("gt0").getAsLong(),
                o.get("id").getAsInt(),
                o.has("uuid") && !o.get("uuid").isJsonNull() ? o.get("uuid").getAsString() : null,
                o.get("type").getAsString(),
                bones,
                o.get("comps").getAsInt(),
                o.get("keyframe").getAsInt(),
                names,
                o.get("bin").getAsString(),
                readStringArray(o.getAsJsonArray("jars")));

        JsonArray slotsArr = o.getAsJsonArray("slots");
        int[] slots = new int[slotsArr.size()];
        for (int i = 0; i < slots.length; i++) {
            slots[i] = slotsArr.get(i).getAsInt();
        }

        JsonArray lensArr = o.getAsJsonArray("lens");
        int[] lens = new int[lensArr.size()];
        for (int i = 0; i < lens.length; i++) {
            lens[i] = lensArr.get(i).getAsInt();
        }

        JsonArray kindsArr = o.getAsJsonArray("kinds");
        String[] kinds = new String[kindsArr.size()];
        for (int i = 0; i < kinds.length; i++) {
            kinds[i] = kindsArr.get(i).getAsString();
        }

        int frames = o.get("frames").getAsInt();
        if (lens.length != frames || kinds.length != frames) {
            throw new IOException("frames(" + frames + ") と lens の長さ(" + lens.length
                    + ") / kinds の長さ(" + kinds.length + ") が一致しない");
        }
        if (frames > 0 && !"K".equals(kinds[0])) {
            throw new IOException("kinds[0] が \"K\" ではない (実測 \"" + kinds[0] + "\")");
        }
        for (int t = 0; t < slots.length; t++) {
            int s = slots[t];
            if (s != -1 && (s < 0 || s >= frames)) {
                throw new IOException("slots[" + t + "]=" + s + " が -1 でも [0," + frames + ") の範囲でもない");
            }
        }

        Path bin = json.toAbsolutePath().getParent().resolve(h.bin());
        long expectedBytes = 0L;
        for (int l : lens) {
            expectedBytes += l;
        }
        if (Files.exists(bin)) {
            long actualBytes = Files.size(bin);
            if (actualBytes != expectedBytes) {
                throw new IOException("bin サイズ不一致: sum(lens)=" + expectedBytes
                        + " バイト, 実測 " + actualBytes + " バイト (" + bin + ")");
            }
        }

        return new Index(h, slots, lens, kinds);
    }

    private static String[] readStringArray(JsonArray arr) {
        if (arr == null) {
            return new String[0];
        }
        String[] out = new String[arr.size()];
        for (int i = 0; i < out.length; i++) {
            out[i] = arr.get(i).getAsString();
        }
        return out;
    }
}
