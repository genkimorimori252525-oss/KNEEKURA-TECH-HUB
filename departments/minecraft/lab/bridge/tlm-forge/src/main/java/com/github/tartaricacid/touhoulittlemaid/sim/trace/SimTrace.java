package com.github.tartaricacid.touhoulittlemaid.sim.trace;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

import java.io.BufferedWriter;
import java.io.Closeable;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.function.Consumer;

/**
 * JSONL トレース writer。1 アリーナに 1 本。
 *
 * <p>チャンネル定義は {@link SimCh}。書式は「1 行 1 イベント・全行に {@code t}(tick) と {@code ch}」。
 *
 * <p><b>ゲーム本体を巻き込まないこと</b>が最優先。書き込み失敗は 1 度だけログに出して
 * 以降は writer を捨てて黙る (例外をゲームスレッドへ投げ返さない)。
 * これは既存 {@code ReimuAiDebug} / {@code ReimuAirTelemetry} と同じ方針。
 */
public final class SimTrace implements Closeable {
    /**
     * この行数ごとに flush する。クラッシュしても直近だけしか失わない粒度。
     *
     * <p>200 行は戦闘中(実測 300〜380 行/秒)だと 0.5〜0.7 秒ぶん溜め込むことになり、
     * <b>ライブの「動きの粒」の上限をここが決めてしまう</b>。クライアントがどれだけ
     * 細かく取り込んでも、ファイルに現れていないものは送れない。
     * 20 行なら戦闘中(300〜380行/秒)でも 50〜65ms 以内に出る = Minecraft の 1 tick 相当。
     */
    private static final int FLUSH_EVERY = 20;

    /**
     * 行数が溜まらなくても、この間隔で必ず flush する。
     *
     * <p><b>なぜ時間でも刻むのか。</b> 行数だけで刻んでいると、行が減った瞬間に
     * ディスクへ届くまでの時間が延びる。実際、行デルタ化 (2026-08-22) を入れた直後に
     * 「水槽は動いているのに Viewer の時計が止まる」が起きた —— 静止した霊夢が
     * 1 体だけの水槽では 5 秒あたり 3 行 (100tick ごとのキーフレーム) しか出ないので、
     * 200 行が溜まるのに 5 分半かかっていた。実測では 4,600 tick (230 秒) 遅れていた。
     * ライブ配信は「ファイルに現れた分」を送るので、これはそのまま配信の遅れになる。
     *
     * <p><b>値は 50ms = Minecraft の 1 tick。</b> 2000ms → 100ms と詰めてきたが、
     * にーくらの体感はまだ 30fps だった。ライブの経路は jar の flush →
     * serve.mjs の pump → クライアントの取り込み と 3 段あり、
     * <b>一番粗い刻みが全体の「動きの粒」を決める</b>。100ms 刻みだと 2 tick ぶんが
     * まとめて届き、その瞬間だけ動いて残りが止まる —— 補間しても粒は消えない。
     * 3 段すべてを 1 tick(50ms)に揃えると、1 tick ずつ均等に届くので、
     * 実機 Minecraft と同じ「20Hz のデータを partialTick で補間」の形になる。
     *
     * <p>費用は BufferedWriter.flush() が 20 回/秒。書くのは高々 1KB 程度で、
     * ゲームスレッドの tick(50ms)に対して無視できる。これ以上細かくしても
     * 記録は 1 tick に 1 度しか増えないので、50ms が下限。
     */
    private static final long FLUSH_EVERY_MS = 50;

    private static final Gson GSON = new Gson();

    private final Path file;
    private BufferedWriter out;
    private long lines;
    private long lastFlushAt = System.currentTimeMillis();
    private boolean broken;

    private SimTrace(Path file, BufferedWriter out) {
        this.file = file;
        this.out = out;
    }

    /**
     * トレースファイルを開く。親ディレクトリが無ければ作る。
     * 失敗したら null ではなく「壊れた (何も書かない) トレース」を返し、呼び出し側に分岐を強いない。
     */
    public static SimTrace open(Path file) {
        try {
            Files.createDirectories(file.getParent());
            BufferedWriter w = Files.newBufferedWriter(file, StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE);
            return new SimTrace(file, w);
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] trace open failed: {}", file, e);
            return new SimTrace(file, null);
        }
    }

    public Path file() {
        return this.file;
    }

    public long lines() {
        return this.lines;
    }

    /**
     * 1 イベントを書く。{@code t} と {@code ch} は自動で入るので、{@code fill} は残りだけ埋める。
     *
     * <pre>{@code
     * trace.event(tick, SimCh.PHYS, o -> {
     *     o.addProperty("id", reimu.getId());
     *     o.addProperty("onG", reimu.onGround());
     * });
     * }</pre>
     */
    public void event(long tick, String ch, Consumer<JsonObject> fill) {
        if (this.out == null || this.broken) {
            return;
        }
        try {
            JsonObject o = new JsonObject();
            o.addProperty("t", tick);
            o.addProperty("ch", ch);
            if (fill != null) {
                fill.accept(o);
            }
            this.out.write(GSON.toJson(o));
            this.out.write('\n');
            // 行数か経過時間の**早い方**で flush する。行が減っても遅れが伸びない
            // (上の FLUSH_EVERY_MS の説明を参照 —— デルタ化で実際に 230 秒遅れた)。
            long now = System.currentTimeMillis();
            if (++this.lines % FLUSH_EVERY == 0 || now - this.lastFlushAt >= FLUSH_EVERY_MS) {
                this.out.flush();
                this.lastFlushAt = now;
            }
        } catch (Exception e) {
            this.broken = true;
            TouhouLittleMaid.LOGGER.error("[SIM] trace write failed, disabling: {}", this.file, e);
        }
    }

    /** 人間向けの進行メモ ({@code ch:log})。runner の節目でだけ使う。 */
    public void log(long tick, String msg) {
        event(tick, SimCh.LOG, o -> o.addProperty("msg", msg));
    }

    public void flush() {
        if (this.out == null || this.broken) {
            return;
        }
        try {
            this.out.flush();
            this.lastFlushAt = System.currentTimeMillis();   // 時間刻みの起点も進める
        } catch (Exception e) {
            this.broken = true;
            TouhouLittleMaid.LOGGER.error("[SIM] trace flush failed: {}", this.file, e);
        }
    }

    @Override
    public void close() {
        if (this.out == null) {
            return;
        }
        try {
            this.out.flush();
            this.out.close();
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] trace close failed: {}", this.file, e);
        } finally {
            this.out = null;
        }
    }

    /** 座標系の値を小数 3 桁へ丸める。トレースのサイズは丸め方でそのまま倍変わる。 */
    public static double r3(double v) {
        if (!Double.isFinite(v)) {
            return 0.0D;
        }
        return Math.round(v * 1000.0D) / 1000.0D;
    }

    /** 角度・HP など小数 2 桁で足りる値用。 */
    public static double r2(double v) {
        if (!Double.isFinite(v)) {
            return 0.0D;
        }
        return Math.round(v * 100.0D) / 100.0D;
    }
}
