package com.github.tartaricacid.touhoulittlemaid.sim.trace;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 「前 tick と同じ行は書かない」の判定 (jar 側デルタ化、13-04)。
 *
 * <p>Minecraft のクラスを 1 つも import しない純クラス —— {@link SimSection} と同じ方針で、
 * 通常の JUnit でそのまま回る。
 *
 * <p>既に手本がある: {@link SimProbe#reimu} の {@code ai} チャンネルは
 * {@code prevSection} との文字列比較で「判断が変わった tick だけ書く」を実現している。
 * この規則を {@code pos}/{@code phys}/{@code anim} へ広げるのがこのクラスの役目。
 * ただし対象チャンネルを決めるのは<b>呼び出し側</b> ({@code SimProbe}) —— {@code SimDelta}
 * 自身はチャンネル名を特別扱いしない、汎用の (ch,id) → 変化判定台帳。
 *
 * <p><b>目的は「任意の tick t の状態を答えられること」を 1mm も損なわないこと。</b>
 * 欠測 = 前の値（前方フィル、13-03 が {@code simlab/stats.mjs} 側に用意済み）が
 * これを保証する。keyframe 間隔だけは別の理由で存在する ——
 * 配信の途中から入った読み手 (Viewer のライブ視聴) が全エンティティの状態を
 * 得るまでの待ち時間に上限を掛けるため。
 *
 * <p>例外を投げない。判断材料が欠けているとき (ch/canonicalBody が null など) は
 * 「書く」と答える —— 記録を落とすより多く書くほうが安全。
 */
public final class SimDelta {

    /**
     * 最後に書いてから何 tick 経っても無条件で書き直す間隔。値 100 の根拠は2つ:
     * (1) 配信の途中から入った読み手 (Viewer のライブ視聴) が全エンティティの状態を
     * 得るまでの上限を 5 秒 (=100 tick, 20 tick/秒) に抑えるため。
     * (2) 100% 冗長な anim (放置中の水槽で変化 22/94,260 行、実測) でも、
     * 削減率が 99% を割らないようにするため (94,260 / 100 ≈ 943 keyframe 行で足りる)。
     */
    public static final int KEYFRAME_TICKS = 100;

    /** 行単位デルタの方式名。{@code meta.delta} に書く値そのもの (13-04 Task 2)。 */
    public static final String DELTA_MODE = "row";

    private static final class Entry {
        String body;
        long tick;

        Entry(String body, long tick) {
            this.body = body;
            this.tick = tick;
        }
    }

    private final int keyframeTicks;
    /**
     * id → (ch → 直前に書いた内容)。id をキーに一段目を切ると {@link #forget(int)} が
     * O(1) で済む ({@code SimArena} の {@code projPhase}/{@code projType} と同じ
     * 「id で持ち回す」持ち方)。
     */
    private final Map<Integer, Map<String, Entry>> ledger = new LinkedHashMap<>();

    private long written;
    private long skipped;
    private long keyframes;

    public SimDelta() {
        this(KEYFRAME_TICKS);
    }

    public SimDelta(int keyframeTicks) {
        this.keyframeTicks = keyframeTicks;
    }

    /**
     * この行を書くべきか判定する。<b>呼び出し側は「書く」と答えられたときだけ
     * {@link SimTrace#event} を呼ぶこと。</b>
     *
     * @param ch            チャンネル名。null なら安全側に倒して常に書く
     * @param id            エンティティ id
     * @param tick          今の tick
     * @param canonicalBody t を除いて正規化した行の文字列表現 (丸め後の値で比較すること)。
     *                      null なら安全側に倒して常に書く
     * @return true なら書く
     */
    public boolean shouldWrite(String ch, int id, long tick, String canonicalBody) {
        if (ch == null || canonicalBody == null) {
            this.written++;
            return true;
        }
        Map<String, Entry> byCh = this.ledger.computeIfAbsent(id, k -> new LinkedHashMap<>());
        Entry prev = byCh.get(ch);
        if (prev == null) {
            byCh.put(ch, new Entry(canonicalBody, tick));
            this.written++;
            return true;
        }
        if (!prev.body.equals(canonicalBody)) {
            prev.body = canonicalBody;
            prev.tick = tick;
            this.written++;
            return true;
        }
        if (tick - prev.tick >= this.keyframeTicks) {
            // body は同じだが、間隔が空きすぎたので keyframe として書き直す。
            prev.tick = tick;
            this.written++;
            this.keyframes++;
            return true;
        }
        this.skipped++;
        return false;
    }

    /**
     * id が再利用されたときに前のエンティティの値を引き継がないよう、
     * その id に属する全チャンネルの台帳を忘れる。
     *
     * <p>水槽は何度も出し入れするので id 再利用は実際に起きる (T-13-12)。呼び忘れると、
     * 新しい entity の最初の行が「前の entity の値と同じ」と誤って間引かれかねない。
     */
    public void forget(int id) {
        this.ledger.remove(id);
    }

    /** 台帳と統計をすべて空にする。 */
    public void reset() {
        this.ledger.clear();
        this.written = 0L;
        this.skipped = 0L;
        this.keyframes = 0L;
    }

    public long written() {
        return this.written;
    }

    public long skipped() {
        return this.skipped;
    }

    public long keyframes() {
        return this.keyframes;
    }
}
