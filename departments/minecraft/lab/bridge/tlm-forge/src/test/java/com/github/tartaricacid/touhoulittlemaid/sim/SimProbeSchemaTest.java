package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimCh;
import org.junit.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * <b>producer が書くキーが {@link SimCh} に宣言されているか</b>を、実トレース無しで見張る。
 *
 * <p><b>なぜ要るのか</b>: {@code SimChSchemaTest} は {@code SimCh} と {@code simlab/schema.json}
 * の<b>一致</b>しか見ないので、<b>両方が同じ間違いで揃っている</b>間は緑のままになる。
 * 実際 {@code pos.agg} は {@code SimProbe} が書いているのに {@code SimCh} に無く、
 * Java のテストは全部通り、実トレースへ {@code schema-check.mjs} を当てて初めて出た
 * (2026-08-24)。{@code simlab/fixtures} の静的トレースも同じ弱点を持つ ——
 * producer が新しいキーを足して fixture の更新を忘れれば通ってしまう。
 *
 * <p>そこで<b>ソースを直接読む</b>。{@code SimProbe} が {@code addProperty("…")} で書く
 * キーを、それが載るチャンネルへ結び付けて、{@code required ∪ optional} に含まれるかを見る。
 * トレースを1本も持たずに、書いた瞬間に落ちる。
 *
 * <p><b>射程外</b>: {@code visual()} は反射で拾った {@code getSync*} 名を動的に書くので、
 * ソースからは名前が判らない。そちらは実トレースに {@code schema-check.mjs} を当てる側が
 * 受け持つ (だから両方要る)。
 */
public class SimProbeSchemaTest {

    private static final Path SIM_PROBE = Paths.get("src", "main", "java", "com", "github",
            "tartaricacid", "touhoulittlemaid", "sim", "trace", "SimProbe.java");

    /**
     * ラムダの外で組み立てられる本体 (デルタ経路) の変数名 → チャンネル定数名。
     *
     * <p>ここに無い受け皿が現れたらテストは<b>落ちる</b> —— 黙って検査対象から外れるより、
     * 「この変数はどのチャンネルか」を書かせるほうが安全。
     */
    private static final Map<String, String> BODY_VAR_CHANNEL = buildBodyVarChannel();

    private static Map<String, String> buildBodyVarChannel() {
        Map<String, String> m = new HashMap<>();
        m.put("body", SimCh.POS);
        m.put("physBody", SimCh.PHYS);
        m.put("animBody", SimCh.ANIM);
        return m;
    }

    /** tr.event(t, SimCh.XXX, o -> { …… のラムダ開始。 */
    private static final Pattern LAMBDA_START = Pattern.compile(
            "\\w+\\.event\\([^,]+,\\s*SimCh\\.(\\w+),\\s*(\\w+)\\s*->\\s*\\{");

    /** 受け皿.addProperty("キー" 。 */
    private static final Pattern ADD_PROPERTY = Pattern.compile(
            "(\\w+)\\.addProperty\\(\"([^\"]+)\"");

    @Test
    public void everyKeySimProbeWritesIsDeclaredInSimCh() throws IOException {
        String src = readSource();
        List<LambdaBlock> lambdas = findLambdaBlocks(src);

        List<String> problems = new ArrayList<>();
        Set<String> checked = new LinkedHashSet<>();

        Matcher m = ADD_PROPERTY.matcher(src);
        while (m.find()) {
            String receiver = m.group(1);
            String key = m.group(2);
            int at = m.start();

            String channel = channelForLambdaAt(lambdas, receiver, at);
            if (channel == null) {
                channel = BODY_VAR_CHANNEL.get(receiver);
            }
            if (channel == null) {
                problems.add("受け皿 '" + receiver + "' がどのチャンネルか判らない (" + key + " @ "
                        + lineOf(src, at) + " 行目)。BODY_VAR_CHANNEL へ対応を書くこと。");
                continue;
            }

            SimCh.ChannelSpec spec = SimCh.SCHEMA.get(channel);
            if (spec == null) {
                problems.add("SimCh.SCHEMA にチャンネル '" + channel + "' が無い ("
                        + lineOf(src, at) + " 行目)。");
                continue;
            }
            checked.add(channel + "." + key);
            if (!spec.required().contains(key) && !spec.optional().contains(key)) {
                problems.add("SimProbe が書く " + channel + "." + key + " が SimCh に宣言されていない ("
                        + lineOf(src, at) + " 行目)。SimCh の " + channel
                        + " へ足し、SimCh.schemaJson() の出力を simlab/schema.json へ保存すること。");
            }
        }

        assertTrue("addProperty が1件も見つからない —— 走査が壊れている (SimProbe の書き方が変わった?)",
                checked.size() >= 10);

        if (!problems.isEmpty()) {
            fail("producer(SimProbe) と SimCh の宣言がズレている:\n  - "
                    + String.join("\n  - ", problems));
        }
    }

    /**
     * {@code pos.agg} の再発そのものを名指しで見張る。上の走査が何かの理由で
     * この行を拾えなくなっても、ここは落ちる。
     */
    @Test
    public void posDeclaresAgg() {
        SimCh.ChannelSpec pos = SimCh.SCHEMA.get(SimCh.POS);
        assertTrue("pos.optional に \"agg\" が無い。SimProbe は Mob.isAggressive() を書いている",
                pos.optional().contains("agg"));
    }

    // =========================================================================

    private static String readSource() throws IOException {
        assertTrue("SimProbe.java が無い: " + SIM_PROBE.toAbsolutePath(), Files.exists(SIM_PROBE));
        return new String(Files.readAllBytes(SIM_PROBE), StandardCharsets.UTF_8)
                .replace("\r\n", "\n");
    }

    /** ラムダの本体範囲 (開き波括弧から、対応する閉じ波括弧まで)。 */
    private static final class LambdaBlock {
        final String channel;
        final String param;
        final int start;
        final int end;

        LambdaBlock(String channel, String param, int start, int end) {
            this.channel = channel;
            this.param = param;
            this.start = start;
            this.end = end;
        }
    }

    private static List<LambdaBlock> findLambdaBlocks(String src) {
        List<LambdaBlock> out = new ArrayList<>();
        Matcher m = LAMBDA_START.matcher(src);
        while (m.find()) {
            String constant = m.group(1);
            String param = m.group(2);
            int open = src.indexOf('{', m.start());
            int close = matchingBrace(src, open);
            String channel = channelConstant(constant);
            if (channel != null && close > open) {
                out.add(new LambdaBlock(channel, param, open, close));
            }
        }
        return out;
    }

    /**
     * {@code SimCh.POS} のような定数名を、その<b>値</b>へ直す。
     * 値を直接書かないのは、定数名と値がズレたときにここで気づけるようにするため。
     */
    private static String channelConstant(String name) {
        try {
            java.lang.reflect.Field f = SimCh.class.getField(name);
            Object v = f.get(null);
            return v instanceof String ? (String) v : null;
        } catch (ReflectiveOperationException e) {
            return null;
        }
    }

    private static int matchingBrace(String src, int open) {
        if (open < 0) {
            return -1;
        }
        int depth = 0;
        for (int i = open; i < src.length(); i++) {
            char c = src.charAt(i);
            if (c == '{') {
                depth++;
            } else if (c == '}') {
                depth--;
                if (depth == 0) {
                    return i;
                }
            }
        }
        return -1;
    }

    private static String channelForLambdaAt(List<LambdaBlock> lambdas, String receiver, int at) {
        String best = null;
        int bestStart = -1;
        for (LambdaBlock b : lambdas) {
            // 入れ子なら内側 (start が大きいほう) を採る
            if (at > b.start && at < b.end && b.param.equals(receiver) && b.start > bestStart) {
                best = b.channel;
                bestStart = b.start;
            }
        }
        return best;
    }

    private static int lineOf(String src, int offset) {
        int line = 1;
        for (int i = 0; i < offset && i < src.length(); i++) {
            if (src.charAt(i) == '\n') {
                line++;
            }
        }
        return line;
    }
}
