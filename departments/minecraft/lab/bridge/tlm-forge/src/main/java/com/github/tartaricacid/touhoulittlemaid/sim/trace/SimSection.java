package com.github.tartaricacid.touhoulittlemaid.sim.trace;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 霊夢の AI デバッグ section 文字列を、機械可読なマップへ構造化する。
 *
 * <p><b>ここが唯一のパース実装。</b> 同じ処理を他所に書かないこと。
 * 実機が書く文字列の実物（1 行）:
 *
 * <pre>
 * phase=APPROACH ptimer=0  zone=BACKDASH(&lt;=2m) dist=1.0m cd: atk=17 dash=0 slide=116
 * amuletShared=0 pendRanged=none pendMelee=false pendAmulet=NONE combo1=NONE
 * dash: back=false tgtDist=0.0 traveled=4.6
 * </pre>
 *
 * <p><b>規則</b>:
 * <ul>
 *   <li>{@code cd:} のように末尾が {@code :} のトークンは、<b>それ以降のキーに付く接頭辞</b>になる。
 *       行の途中で何度でも切り替わり、<b>行が変わると空に戻る</b></li>
 *   <li>{@code k=v} のトークンは <b>接頭辞 + 先頭大文字化した k</b> をキーにする
 *       （接頭辞が空なら k のまま。{@code atk=17} は {@code cd:} の下で {@code cdAtk}）</li>
 *   <li>値は boolean → 整数 → 小数 → 文字列 の順に試す。<b>推測で型を作らない</b>
 *       （{@code dist=1.0m} は数値にならないので文字列のまま）</li>
 *   <li>空文字 / null は空のマップ。<b>例外を投げない</b></li>
 *   <li>未知の形式（空中 section など）でも {@code k=v} だけは拾い、拾えないものは黙って捨てる</li>
 * </ul>
 *
 * <p><b>なぜ Java 側でパースするのか</b>（AGENT-01）: 人間が読む文字列と機械が読むマップが
 * <b>同じ 1 つの文字列から、供給点で 1 回だけ</b>作られるようにするため。解析側で後から
 * パースし直す形にすると、表示と統計が食い違ったときにどちらが正しいか分からなくなる。
 *
 * <p><b>JS 側の {@code simlab/stats.mjs} の {@code parseSection} と一字一句同じ規則</b>で
 * なければならない。片方だけ直すと、新トレース（{@code ai.sec}）と旧トレース
 * （{@code ai.section} を後からパース）で結果が食い違う。
 *
 * <p>Minecraft の import を<b>一切持たない</b>純粋な Java にしてあるので、
 * JUnit から直接呼べる。
 */
public final class SimSection {
    private SimSection() {
    }

    /**
     * section 文字列を構造化する。挿入順を保つ。
     *
     * @param rawSection 生の section（{@code §} の色コードは除いてあること）。null 可
     * @return キー → 値（{@link Boolean} / {@link Long} / {@link Double} / {@link String}）。
     *         入力が空なら空のマップ
     */
    public static Map<String, Object> parse(String rawSection) {
        Map<String, Object> out = new LinkedHashMap<>();
        if (rawSection == null || rawSection.trim().isEmpty()) {
            return out;
        }
        for (String line : rawSection.split("\n")) {
            String prefix = "";                       // 行が変わると接頭辞は空に戻る
            for (String tok : line.split("\\s+")) {
                if (tok.isEmpty()) {
                    continue;
                }
                if (isLabel(tok)) {
                    prefix = tok.substring(0, tok.length() - 1);
                    continue;
                }
                int eq = tok.indexOf('=');
                if (eq <= 0 || !isKeyName(tok.substring(0, eq))) {
                    continue;                          // 拾えないトークンは黙って捨てる
                }
                String key = tok.substring(0, eq);
                String value = tok.substring(eq + 1);
                out.put(prefix.isEmpty() ? key : prefix + capitalize(key), typed(value));
            }
        }
        return out;
    }

    /** {@code ^[a-z][A-Za-z0-9]*:$} —— 以降のキーに付く接頭辞。 */
    private static boolean isLabel(String tok) {
        int n = tok.length();
        if (n < 2 || tok.charAt(n - 1) != ':') {
            return false;
        }
        char c0 = tok.charAt(0);
        if (c0 < 'a' || c0 > 'z') {
            return false;
        }
        for (int i = 1; i < n - 1; i++) {
            if (!isAlnum(tok.charAt(i))) {
                return false;
            }
        }
        return true;
    }

    /** {@code ^[A-Za-z][A-Za-z0-9_]*$} */
    private static boolean isKeyName(String k) {
        if (k.isEmpty() || !isAlpha(k.charAt(0))) {
            return false;
        }
        for (int i = 1; i < k.length(); i++) {
            char c = k.charAt(i);
            if (!isAlnum(c) && c != '_') {
                return false;
            }
        }
        return true;
    }

    private static boolean isAlpha(char c) {
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
    }

    private static boolean isAlnum(char c) {
        return isAlpha(c) || (c >= '0' && c <= '9');
    }

    private static String capitalize(String s) {
        if (s.isEmpty()) {
            return s;
        }
        return Character.toUpperCase(s.charAt(0)) + s.substring(1);
    }

    /** boolean → 整数 → 小数 → 文字列 の順に解釈する。 */
    private static Object typed(String raw) {
        if ("true".equals(raw)) {
            return Boolean.TRUE;
        }
        if ("false".equals(raw)) {
            return Boolean.FALSE;
        }
        if (matchesInteger(raw)) {
            try {
                return Long.valueOf(raw);
            } catch (NumberFormatException ignored) {
                // 桁溢れは文字列のまま置く
            }
        }
        if (matchesDecimal(raw)) {
            try {
                return Double.valueOf(raw);
            } catch (NumberFormatException ignored) {
                // ここへは来ないはずだが、来たら文字列のまま置く
            }
        }
        return raw;
    }

    /** {@code ^-?\d+$} */
    private static boolean matchesInteger(String s) {
        int i = 0;
        if (s.startsWith("-")) {
            i = 1;
        }
        if (i >= s.length()) {
            return false;
        }
        for (; i < s.length(); i++) {
            if (s.charAt(i) < '0' || s.charAt(i) > '9') {
                return false;
            }
        }
        return true;
    }

    /** {@code ^-?\d*\.\d+$} */
    private static boolean matchesDecimal(String s) {
        int i = 0;
        if (s.startsWith("-")) {
            i = 1;
        }
        int dot = s.indexOf('.', i);
        if (dot < 0 || dot == s.length() - 1) {
            return false;
        }
        for (int j = i; j < dot; j++) {
            if (s.charAt(j) < '0' || s.charAt(j) > '9') {
                return false;
            }
        }
        for (int j = dot + 1; j < s.length(); j++) {
            if (s.charAt(j) < '0' || s.charAt(j) > '9') {
                return false;
            }
        }
        return true;
    }
}
