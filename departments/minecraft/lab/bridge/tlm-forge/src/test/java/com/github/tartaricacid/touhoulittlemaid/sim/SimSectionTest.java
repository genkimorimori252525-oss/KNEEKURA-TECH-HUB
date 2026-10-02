package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimSection;
import org.junit.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * {@link SimSection#parse} の検証。
 *
 * <p>ケースは {@code simlab/fixtures/section-parse.cases.txt} に {@code ---} 区切りで置く
 * （地上の実物 1 件 / 空中形式 1 件 / 空文字 1 件）。ファイルは JS 側
 * （{@code simlab/stats.mjs} の {@code parseSection}）とも共有する意図で置いてあり、
 * Phase 10-02 で golden ファイルによる相互検証を入れる。
 *
 * <p><b>なぜ期待値をベタ書きするか</b>: パーサの出力をそのまま期待値にすると、
 * パーサが壊れても一緒に壊れて検査が素通りする。<b>実機の section を人が読んで書き下した値</b>
 * を置くことで、実装とは独立した基準になる。
 */
public class SimSectionTest {
    /**
     * ケースファイルはリポジトリ相対で読む。Gradle の {@code test} タスクは
     * {@code workingDir} を上書きしていない（build.gradle の上書きは {@code run/*} のみ）ので、
     * プロジェクトルートから解決できる。
     */
    private static List<String> cases() throws IOException {
        Path p = Paths.get("simlab", "fixtures", "section-parse.cases.txt");
        assertTrue("ケースファイルが無い: " + p.toAbsolutePath(), Files.exists(p));
        String text = new String(Files.readAllBytes(p), StandardCharsets.UTF_8);
        List<String> out = new ArrayList<>();
        // **limit=-1 が要る。** Java の String.split は既定で末尾の空要素を捨てるが、
        // JS の String.split は残す。ケースファイルは末尾が区切りで終わるので、
        // -1 を付けないと「空文字ケース」が Java 側だけ消える（実際に一度落ちた）。
        // 同じ落とし穴は Phase 10-02 の golden 相互検証でも踏みうる。
        for (String c : text.split("\n---\n", -1)) {
            out.add(c.trim());
        }
        return out;
    }

    @Test
    public void groundSectionParsesToExpectedKeys() throws IOException {
        Map<String, Object> m = SimSection.parse(cases().get(0));

        // 接頭辞なし
        assertEquals("APPROACH", m.get("phase"));
        assertEquals(Long.valueOf(0L), m.get("ptimer"));
        assertEquals("BACKDASH(<=2m)", m.get("zone"));
        // 数値化できないものは文字列のまま置く（推測で型を作らない）
        assertEquals("1.0m", m.get("dist"));

        // `cd:` 以降は cd を接頭辞に付ける
        assertEquals(Long.valueOf(17L), m.get("cdAtk"));
        assertEquals(Long.valueOf(0L), m.get("cdDash"));
        assertEquals(Long.valueOf(116L), m.get("cdSlide"));
        assertEquals(Boolean.FALSE, m.get("cdPendMelee"));
        assertEquals("NONE", m.get("cdPendAmulet"));

        // `dash:` で接頭辞が行の途中で切り替わる
        assertEquals(Boolean.FALSE, m.get("dashBack"));
        assertEquals(Double.valueOf(0.0d), m.get("dashTgtDist"));
        assertEquals(Double.valueOf(4.6d), m.get("dashTraveled"));

        // 接頭辞が付いた後のキーが、素の名前で入っていないこと
        assertFalse("cd: の後のキーが接頭辞なしで入っている", m.containsKey("atk"));
    }

    @Test
    public void airSectionParsesWhatItCan() throws IOException {
        Map<String, Object> m = SimSection.parse(cases().get(1));
        assertEquals(Double.valueOf(71.0d), m.get("Y"));
        assertEquals(Double.valueOf(0.08d), m.get("vel"));
        assertEquals(Boolean.TRUE, m.get("air"));
        assertEquals(Long.valueOf(0L), m.get("cdAmulet"));
        assertEquals(Long.valueOf(44L), m.get("cdKakusan"));
        assertEquals("AIR_STRAFE", m.get("cdPhase"));
    }

    @Test
    public void emptyInputsYieldEmptyMapWithoutThrowing() throws IOException {
        assertTrue(SimSection.parse(cases().get(2)).isEmpty());
        assertTrue(SimSection.parse("").isEmpty());
        assertTrue(SimSection.parse("   ").isEmpty());
        assertTrue(SimSection.parse(null).isEmpty());
    }

    @Test
    public void insertionOrderIsPreserved() {
        Map<String, Object> m = SimSection.parse("a=1 b=2 c=3");
        assertEquals(Arrays.asList("a", "b", "c"), new ArrayList<>(m.keySet()));
    }

    @Test
    public void prefixResetsAtEachLine() {
        Map<String, Object> m = SimSection.parse("cd: atk=1\nphase=IDLE");
        assertEquals(Long.valueOf(1L), m.get("cdAtk"));
        // 2 行目は接頭辞が空に戻るので phase のまま
        assertEquals("IDLE", m.get("phase"));
        assertFalse(m.containsKey("cdPhase"));
    }

    @Test
    public void garbageTokensAreDroppedSilently() {
        Map<String, Object> m = SimSection.parse("=novalue ---- 42 ok=1 9bad=2");
        assertEquals(Long.valueOf(1L), m.get("ok"));
        assertEquals("拾えないトークンを拾ってしまっている", 1, m.size());
    }
}
