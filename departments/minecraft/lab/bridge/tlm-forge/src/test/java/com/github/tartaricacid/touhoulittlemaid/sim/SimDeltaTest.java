package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimDelta;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeMap;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * {@link SimDelta} の検証 (13-04 Task 1)。{@link com.github.tartaricacid.touhoulittlemaid.sim.SimPoseCodecTest}
 * と同じ 3 段構成: 素通し保証 → 本処理 (golden 一致) → 往復一致。
 *
 * <p>{@code SimDelta} は Minecraft のクラスを一切 import しないので、通常の JUnit で
 * そのまま回る —— このテストが green になること自体が「MC を起動せずに使える」の証明になる。
 *
 * <p><b>golden ({@code simlab/fixtures/delta-gate.golden.json}) は Java と JS
 * (delta.mjs) の唯一の共通の物差し。</b> どちらの実装からも生成していない — 期待値は手で書いた。
 * このテストが検出できることを確かめるため、{@code SimDelta} を意図的に壊して
 * (例えば keyframe 判定を外す) golden 一致テストが RED になることを実装中に確認済み。
 */
public class SimDeltaTest {

    private static final Path GOLDEN = Paths.get("simlab", "fixtures", "delta-gate.golden.json");

    // =========================================================================
    // 素通し保証 (D-01 の insurance と同じ思想 — 例外を投げず、安全側に倒すことを機械で守る)
    // =========================================================================

    @Test
    public void nullChannelAlwaysWrites() {
        SimDelta delta = new SimDelta();
        assertTrue("ch が null なら安全側に倒して常に書く", delta.shouldWrite(null, 1, 0, "body"));
        assertTrue("ch が null なら written としてカウントする", delta.written() >= 1);
    }

    @Test
    public void nullCanonicalBodyAlwaysWrites() {
        SimDelta delta = new SimDelta();
        assertTrue("canonicalBody が null なら安全側に倒して常に書く", delta.shouldWrite("pos", 1, 0, null));
    }

    @Test
    public void forgettingAnUnknownIdDoesNotThrow() {
        SimDelta delta = new SimDelta();
        delta.forget(999); // 台帳に無い id を forget しても例外を投げない
        assertTrue("forget後も通常どおり動く", delta.shouldWrite("pos", 999, 0, "x"));
    }

    @Test
    public void keyframeTicksConstantIsOneHundred() {
        // simlab/schema.json の meta.keyframe=100 (13-04 Task 2) と揃える値。ここが真実源。
        assertEquals(100, SimDelta.KEYFRAME_TICKS);
    }

    @Test
    public void deltaModeConstantIsRow() {
        assertEquals("meta.delta に書く値そのもの", "row", SimDelta.DELTA_MODE);
    }

    // =========================================================================
    // 本処理 — golden 一致 (Java と JS の唯一の共通の物差しを、この実装でも満たすこと)
    // =========================================================================

    @Test
    public void goldenCasesMatchAcrossAllEightKinds() throws IOException {
        if (!Files.exists(GOLDEN)) {
            fail("simlab/fixtures/delta-gate.golden.json が無い: " + GOLDEN.toAbsolutePath());
        }
        String text = new String(Files.readAllBytes(GOLDEN), StandardCharsets.UTF_8);
        JsonObject golden = JsonParser.parseString(text).getAsJsonObject();
        int keyframeTicks = golden.has("keyframeTicks") ? golden.get("keyframeTicks").getAsInt() : SimDelta.KEYFRAME_TICKS;
        JsonArray cases = golden.getAsJsonArray("cases");
        assertTrue("golden のケースは12件以上必要 (実際 " + cases.size() + ")", cases.size() >= 12);

        SimDelta delta = new SimDelta(keyframeTicks);
        Set<String> seenKinds = new LinkedHashSet<>();
        for (int i = 0; i < cases.size(); i++) {
            JsonObject c = cases.get(i).getAsJsonObject();
            String kind = c.has("kind") ? c.get("kind").getAsString() : ("case" + i);
            seenKinds.add(kind);
            String ch = c.get("ch").getAsString();
            int id = c.get("id").getAsInt();
            long tick = c.get("tick").getAsLong();
            JsonObject body = c.getAsJsonObject("body");
            boolean expect = c.get("expect").getAsBoolean();
            if (c.has("forget") && c.get("forget").getAsBoolean()) {
                delta.forget(id);
            }
            boolean actual = delta.shouldWrite(ch, id, tick, canonical(body));
            assertEquals("golden[" + i + "] (" + kind + ") ch=" + ch + " id=" + id + " tick=" + tick
                    + " の書く/書かない判定が食い違う", expect, actual);
        }

        // 8種類 (<behavior> が要求する網羅) が実際に golden へ1件以上あることを確かめる。
        // これが欠けていたら golden 自体がこのテストの目的を果たしていない。
        String[] requiredKinds = {
                "初回", "同一", "差分", "keyframe直前", "keyframeちょうど",
                "forget後", "対象外チャンネル", "丸め違い",
        };
        for (String k : requiredKinds) {
            assertTrue("golden に kind=\"" + k + "\" のケースが無い(8種類の網羅漏れ)", seenKinds.contains(k));
        }
    }

    /**
     * {@code body} (t を除いた行の中身) を正規化した文字列にする。golden のケースは
     * 自然な記述順で書かれているので、キーをアルファベット順に並べ替えてから比較する —
     * 記述順に依存せず安定させるため ({@code SimProbe} が実際に書くときは常に同じ
     * 順序でフィールドを追加するので、本番コードは並べ替え無しの単純な直列化で足りる。
     * ここはテストの都合で並べ替えを足しているだけで、SimDelta 自身の要求ではない)。
     */
    private static String canonical(JsonObject body) {
        List<String> keys = new ArrayList<>(body.keySet());
        Collections.sort(keys);
        StringBuilder sb = new StringBuilder();
        for (String k : keys) {
            JsonElement v = body.get(k);
            sb.append(k).append('=').append(v).append(';');
        }
        return sb.toString();
    }

    // =========================================================================
    // 往復一致 — デルタ化した行だけから、前方フィルで密トレースと同じ値を全 tick で復元できること
    // =========================================================================

    @Test
    public void deltaThenForwardFillReproducesTheOriginalPerTickValue() {
        // keyframeTicksを小さくして往復の境界(keyframe再書き込み)も一緒に踏むようにする。
        SimDelta delta = new SimDelta(3);
        // 合成の「密トレース」: 値がA(0-3)->B(4-6)->A(7-9)と変化する10 tick分。
        String[] dense = {"A", "A", "A", "A", "B", "B", "B", "A", "A", "A"};
        TreeMap<Long, String> written = new TreeMap<>();
        for (long t = 0; t < dense.length; t++) {
            String body = dense[(int) t];
            if (delta.shouldWrite("pos", 1, t, body)) {
                written.put(t, body);
            }
        }
        assertTrue("値が変化するのに1行も書かれないのはおかしい", written.size() >= 3);

        // 前方フィル再構成: writtenだけから、密トレースと同じ値を全tickで復元できること
        // (これが「任意のtick tの状態を答えられる」というこのクラスの目的そのもの)。
        String last = null;
        for (long t = 0; t < dense.length; t++) {
            if (written.containsKey(t)) {
                last = written.get(t);
            }
            assertEquals("前方フィル再構成が tick " + t + " で密トレースと食い違う", dense[(int) t], last);
        }
    }

    @Test
    public void statsWrittenSkippedKeyframesAddUpToTheNumberOfCalls() {
        SimDelta delta = new SimDelta(5);
        int calls = 0;
        for (int t = 0; t < 20; t++) {
            // t=0..9は"A"のまま(初回のみ書き、以後は5tickごとのkeyframeだけ書く)、
            // t=10以降は"B"に変わる(差分で書く)。
            String body = t < 10 ? "A" : "B";
            delta.shouldWrite("pos", 1, t, body);
            calls++;
        }
        assertEquals("written+skippedは呼び出し回数に一致する",
                calls, delta.written() + delta.skipped());
        assertTrue("keyframeもwrittenの内数として数えられている", delta.keyframes() >= 1);
        assertTrue("keyframe件数はwritten件数を超えない", delta.keyframes() <= delta.written());
    }

    @Test
    public void resetClearsLedgerAndStats() {
        SimDelta delta = new SimDelta();
        delta.shouldWrite("pos", 1, 0, "x");
        delta.shouldWrite("pos", 1, 1, "x"); // 同一 -> skipped
        assertTrue(delta.written() > 0);
        assertTrue(delta.skipped() > 0);

        delta.reset();
        assertEquals(0L, delta.written());
        assertEquals(0L, delta.skipped());
        assertEquals(0L, delta.keyframes());
        // 台帳も空になっているので、直前と同じ内容でも「初回」として書かれる。
        assertTrue("resetで台帳が空になっているはず", delta.shouldWrite("pos", 1, 0, "x"));
    }

    @Test
    public void forgetIsScopedToASingleIdAndDoesNotAffectOthers() {
        SimDelta delta = new SimDelta();
        assertTrue(delta.shouldWrite("pos", 1, 0, "x"));
        assertTrue(delta.shouldWrite("pos", 2, 0, "y"));
        assertFalse("id=1はまだ同一なのでskipされるはず", delta.shouldWrite("pos", 1, 1, "x"));

        delta.forget(1);

        assertTrue("id=1はforget後なので初回扱いで書かれる", delta.shouldWrite("pos", 1, 2, "x"));
        assertFalse("id=2はforgetしていないのでskipされたままのはず", delta.shouldWrite("pos", 2, 1, "y"));
    }
}
