package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimCh;
import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimSection;
import org.junit.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * スキーマ契約の見張り（AGENT-04）。
 *
 * <p><b>守るもの</b>: {@link SimCh} が「トレースの形」の単一の真実源であること。
 * Java 側が形を変えたのに {@code simlab/schema.json} を更新し忘れたら、
 * <b>解析コードは古い形を前提に走り続け、表の数字が静かに 0 になる</b>。
 * それを人が気づく前に落とすのがこのテスト。
 *
 * <p>JS 側の見張りは {@code simlab/schema-check.mjs} が受け持つ（両方向）。
 */
public class SimChSchemaTest {
    private static final Path SCHEMA_JSON = Paths.get("simlab", "schema.json");
    private static final Path CASES = Paths.get("simlab", "fixtures", "section-parse.cases.txt");
    private static final Path GOLDEN = Paths.get("simlab", "fixtures", "section-parse.golden.json");

    @Test
    public void schemaJsonMatchesSimCh() throws IOException {
        String expected = SimCh.schemaJson();
        if (!Files.exists(SCHEMA_JSON)) {
            fail("simlab/schema.json が無い。SimCh.schemaJson() の出力をそのまま保存すること:\n" + expected);
        }
        String actual = new String(Files.readAllBytes(SCHEMA_JSON), StandardCharsets.UTF_8)
                .replace("\r\n", "\n");
        if (!expected.equals(actual)) {
            fail("simlab/schema.json が SimCh と食い違っている。**SimCh が真実源**なので schema.json を"
                    + " 再生成すること（SimCh.schemaJson() の出力を保存）。\n--- 期待 ---\n" + expected
                    + "\n--- 実際 ---\n" + actual);
        }
    }

    @Test
    public void everyChannelConstantIsInTheSchema() {
        // javadoc に書いたが SCHEMA に入れ忘れた、を防ぐ。
        // pose は「本体 trace には書かれない」宣言専用なので対象外。
        for (String ch : new String[]{
                SimCh.META, SimCh.SPAWN, SimCh.GONE, SimCh.POS, SimCh.PHYS,
                SimCh.ANIM, SimCh.AI, SimCh.PROJ, SimCh.DMG, SimCh.VIS,
                SimCh.SOUND, SimCh.LOG, SimCh.END}) {
            assertTrue("SCHEMA に " + ch + " が無い", SimCh.SCHEMA.containsKey(ch));
        }
    }

    @Test
    public void dmgAttribValuesAreExactlyTheFourDocumented() {
        assertEquals(java.util.Arrays.asList("direct", "melee", "stack", "none"),
                SimCh.DMG_ATTRIB_VALUES);
    }

    /**
     * 13-04: {@code meta.optional} に {@code delta}/{@code keyframe} が名指しで在ることを
     * 確かめる。{@link #schemaJsonMatchesSimCh} の文字列一致だけだと、{@code SimCh} と
     * {@code simlab/schema.json} を同じ間違った値で揃えてしまった場合(例えば両方に
     * 誤字入りの同じ文字列を書いてしまった場合)に検出できない —— このテストは
     * 期待値をハードコードしているので、{@code SimCh.SCHEMA} 自体の値が違っていれば
     * {@code schema.json} の中身に関係なく落ちる。同時に {@code required} が動いていない
     * (フィールドを optional へ弱めていない)ことも確かめる。
     */
    @Test
    public void metaOptionalDeclaresDeltaAndKeyframeWithoutWeakeningRequired() {
        SimCh.ChannelSpec meta = SimCh.SCHEMA.get(SimCh.META);
        assertTrue("SCHEMA の meta.optional に \"delta\" が無い", meta.optional().contains("delta"));
        assertTrue("SCHEMA の meta.optional に \"keyframe\" が無い", meta.optional().contains("keyframe"));
        assertEquals("meta.required が13-04で動いてしまっている",
                java.util.Arrays.asList("scenario", "seed", "arena", "duration", "gameTime"),
                meta.required());
        // pos.required も同じくフィールドを弱めていないこと(弱めたのは行そのもの)。
        SimCh.ChannelSpec pos = SimCh.SCHEMA.get(SimCh.POS);
        assertEquals("pos.required が13-04で動いてしまっている",
                java.util.Arrays.asList("id", "x", "y", "z"), pos.required());
    }

    /**
     * Java の {@link SimSection#parse} が golden と一致すること。
     *
     * <p>golden は JS 側（{@code simlab/stats.mjs} の {@code parseSection}）も同じものに
     * 照らされる。**2つの言語の実装が同じ答えを出す**ことを、1つのファイルで担保する。
     */
    @Test
    public void sectionParseMatchesGolden() throws IOException {
        List<String> cases = readCases();
        String expected = goldenJson(cases);
        if (!Files.exists(GOLDEN)) {
            fail("simlab/fixtures/section-parse.golden.json が無い。次の内容で作ること"
                    + "（テストにファイルを書かせない。実行者が1回手で作ってコミットする）:\n" + expected);
        }
        String actual = new String(Files.readAllBytes(GOLDEN), StandardCharsets.UTF_8)
                .replace("\r\n", "\n");
        if (!expected.equals(actual)) {
            fail("SimSection.parse の出力が golden と食い違っている。\n--- 期待 ---\n"
                    + expected + "\n--- 実際 ---\n" + actual);
        }
    }

    private static List<String> readCases() throws IOException {
        assertTrue("ケースファイルが無い: " + CASES.toAbsolutePath(), Files.exists(CASES));
        String text = new String(Files.readAllBytes(CASES), StandardCharsets.UTF_8);
        List<String> out = new ArrayList<>();
        // limit=-1 —— Java は既定で末尾の空要素を捨てるが JS は残す（SimSectionTest 参照）
        for (String c : text.split("\n---\n", -1)) {
            out.add(c.trim());
        }
        return out;
    }

    /** 安定した順序の JSON。キーの挿入順は {@link SimSection#parse} が保つ。 */
    private static String goldenJson(List<String> cases) {
        StringBuilder sb = new StringBuilder("[\n");
        for (int i = 0; i < cases.size(); i++) {
            Map<String, Object> m = SimSection.parse(cases.get(i));
            sb.append("  {");
            int j = 0;
            for (Map.Entry<String, Object> e : m.entrySet()) {
                if (j++ > 0) {
                    sb.append(", ");
                }
                sb.append('"').append(e.getKey()).append("\": ").append(jsonValue(e.getValue()));
            }
            sb.append('}').append(i < cases.size() - 1 ? ",\n" : "\n");
        }
        return sb.append("]\n").toString();
    }

    private static String jsonValue(Object v) {
        if (v instanceof Boolean || v instanceof Long) {
            return String.valueOf(v);
        }
        if (v instanceof Double) {
            double d = (Double) v;
            // 0.0 を "0" と書く —— JS の JSON.stringify(0.0) は "0" なので、
            // 両言語が同じ golden を見られるように揃える
            return d == Math.floor(d) && !Double.isInfinite(d)
                    ? String.valueOf((long) d) : String.valueOf(d);
        }
        return '"' + String.valueOf(v).replace("\\", "\\\\").replace("\"", "\\\"") + '"';
    }
}
