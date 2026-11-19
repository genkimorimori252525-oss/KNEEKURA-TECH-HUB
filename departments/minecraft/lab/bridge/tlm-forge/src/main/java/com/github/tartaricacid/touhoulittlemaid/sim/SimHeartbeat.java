package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

/**
 * 水槽の心拍。<b>中に誰も居なくても打つ。</b>
 *
 * <h3>なぜ要るのか</h3>
 * にーくら 2026-08-20:
 * <blockquote>
 * このviewerサイトは、巨大な研究所の、監視カメラで監視されてる大きな水槽のようなものなんだ。
 * 実験水槽に、検証したいモブを放って始めるかんじ。起動して開いたときには誰もいない感じだね。
 * </blockquote>
 * 空の水槽では<b>「誰もいない」と「壊れている」が同じ絵になる</b>。
 * トレース (ch:pos / ch:ai …) は中の出来事の記録なので、誰も居なければ 1 行も出ない。
 * だから中身とは別に、<b>水槽が生きていること自体</b>を示すものが要る。
 *
 * <p>実測 (2026-08-20): 空の水槽を立てたところ、確かにトレースが育たず脈が打たなかった
 * （{@code tick:null, stalledMs:9062}）。逆に最初の試行では、シナリオの読み込みに失敗して
 * サーバが halt した後も Viewer 側は {@code state:"live"} を表示し続けていた。
 * <b>監視カメラの最悪の壊れ方は、映らなくなることではなく、止まった画像を映し続けること。</b>
 *
 * <h3>記録ではなく状態</h3>
 * トレース (JSONL) は<b>追記される記録</b>で、心拍は<b>上書きされる現在値</b>。
 * 性質が違うのでファイルを分ける —— 心拍をトレースに混ぜると、
 * 「何も起きていない」時間帯が心拍行で埋まって記録が読みにくくなる。
 *
 * <h3>固定パスである理由</h3>
 * {@code outRoot} 直下に置く。トレースのディレクトリ ({@code <name>/<seed>/<runId>}) の中ではなく。
 * こうすると <b>Viewer 側のサーバを再起動しても、走っている水槽を見失わない</b> ——
 * 決まった場所を読めば「今どの水槽が生きているか」が判る。
 *
 * <h3>本番の挙動を変えない</h3>
 * {@link #init} が呼ばれない限り {@link #beat} は即座に return する。
 * sim を起動しない通常のゲームではファイルにも触らない。
 */
public final class SimHeartbeat {

    /** 書き出すファイル名。serve.mjs がこの名前で読む。 */
    public static final String FILE_NAME = "heartbeat.json";

    /** 何 tick ごとに打つか。20 tick = 1 秒。 */
    public static final int EVERY_TICKS = 20;

    private static volatile Path file;
    private static volatile String scenario = "";
    private static volatile String trace = "";
    private static volatile long startedAtMs;

    private SimHeartbeat() {}

    /**
     * 心拍を始める。{@code SimRunner} のコンストラクタから呼ぶ。
     *
     * @param outRoot  トレースの出力ルート（心拍はこの直下に置く）
     * @param scenario シナリオ名
     * @param trace    トレースディレクトリの outRoot からの相対パス（{@code <name>/<seed>/<runId>}）
     */
    public static void init(Path outRoot, String scenario, String trace) {
        SimHeartbeat.scenario = scenario;
        SimHeartbeat.trace = trace;
        SimHeartbeat.startedAtMs = System.currentTimeMillis();
        SimHeartbeat.file = outRoot.resolve(FILE_NAME);
        try {
            Files.createDirectories(outRoot);
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.warn("[SIM] heartbeat のディレクトリを作れなかった", e);
            SimHeartbeat.file = null;
        }
    }

    /**
     * 毎 tick 呼ぶ。実際に書くのは {@link #EVERY_TICKS} tick に 1 回。
     *
     * <p>失敗しても水槽は走り続ける —— 心拍は観察の道具であって、水槽の一部ではない。
     */
    public static void beat(long tick) {
        Path f = file;
        if (f == null || tick % EVERY_TICKS != 0) {
            return;
        }
        try {
            String json = "{\"tick\":" + tick
                    + ",\"scenario\":\"" + scenario + "\""
                    + ",\"trace\":\"" + trace.replace('\\', '/') + "\""
                    + ",\"startedAtMs\":" + startedAtMs
                    + ",\"atMs\":" + System.currentTimeMillis()
                    + "}";
            // **原子的に置き換える。** 毎秒上書きするので、読み手が書き込みの途中を
            // 掴むと壊れた JSON を読む。一時ファイルへ書いてから rename する。
            Path tmp = f.resolveSibling(FILE_NAME + ".tmp");
            Files.write(tmp, json.getBytes(StandardCharsets.UTF_8));
            Files.move(tmp, f, StandardCopyOption.REPLACE_EXISTING);
        } catch (Exception e) {
            // 毎秒失敗し続けるとログが溢れるので、1 度きりで諦める。
            TouhouLittleMaid.LOGGER.warn("[SIM] heartbeat を書けなかった。以後の心拍を止める", e);
            file = null;
        }
    }

    /** 心拍を止める。水槽が終わったとき。 */
    public static void stop() {
        Path f = file;
        file = null;
        if (f == null) {
            return;
        }
        try {
            Files.deleteIfExists(f);
        } catch (Exception e) {
            // 消せなくても atMs が古くなるので、読み手は死んだと判る。
            TouhouLittleMaid.LOGGER.debug("[SIM] heartbeat を消せなかった", e);
        }
    }
}
