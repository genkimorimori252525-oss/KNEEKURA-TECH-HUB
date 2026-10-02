package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.ai.reimu.debug.ReimuAiDebug;
import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimNetworkTrace;
import com.github.tartaricacid.touhoulittlemaid.sim.tuning.SimTuning;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraftforge.fml.loading.FMLPaths;

import javax.annotation.Nullable;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.regex.Pattern;

/**
 * SimLab の static facade。既存 {@code ReimuAiDebug} / {@code ReimuAirTelemetry} と同方針
 * (static + {@link #ENABLED} ガード + try/catch) で、<b>OFF のときはゲーム本体に一切触らない</b>。
 *
 * <h3>起動の仕方</h3>
 * <pre>
 * gradlew runSim                          # 組み込みの smoke シナリオ
 * gradlew runSim -Pscenario=amulet-dummy  # simlab/scenarios/amulet-dummy.json
 * </pre>
 *
 * <h3>system property</h3>
 * <ul>
 *   <li>{@code tlm.sim.scenario} — これが無ければ SimLab は完全に眠ったまま
 *       (通常の {@code runServer} / 実機に一切影響しない)</li>
 *   <li>{@code tlm.sim.dir} — シナリオ置き場。既定 {@code <gamedir>/simlab}</li>
 *   <li>{@code tlm.sim.out} — トレース出力先。既定 {@code <gamedir>/simlab-out}</li>
 *   <li>{@code tlm.sim.halt} — {@code false} で終了後もサーバを止めない
 *       (実クライアントを繋いで目で見たいとき)</li>
 *   <li>{@code tlm.sim.run} — run 識別子。出力先の 3 階層目になる。省略時は起動時刻
 *       {@code yyyyMMdd-HHmmss}</li>
 * </ul>
 */
public final class SimLab {

    public static final String PROP_SCENARIO = "tlm.sim.scenario";
    public static final String PROP_DIR = "tlm.sim.dir";
    public static final String PROP_OUT = "tlm.sim.out";
    public static final String PROP_HALT = "tlm.sim.halt";
    public static final String PROP_RUN = "tlm.sim.run";

    private static final Pattern RUN_ID_INVALID_CHARS = Pattern.compile("[^A-Za-z0-9._-]");
    private static final Pattern RUN_ID_DOTS_ONLY = Pattern.compile("\\.+");
    private static final int RUN_ID_MAX_LENGTH = 64;

    /** sim 実行中のみ true。OFF 時は全フックが即 return。 */
    public static volatile boolean ENABLED = false;

    @Nullable
    private static volatile SimRunner runner;

    private SimLab() {}

    public static boolean enabled() {
        return ENABLED;
    }

    @Nullable
    public static SimRunner runner() {
        return runner;
    }

    /** シナリオ名が指定されているか (= この JVM は sim 実行か)。 */
    public static boolean requested() {
        String s = System.getProperty(PROP_SCENARIO);
        return s != null && !s.isBlank();
    }

    private static Path dir(String prop, String fallbackName) {
        String v = System.getProperty(prop);
        if (v != null && !v.isBlank()) {
            return Path.of(v);
        }
        return FMLPaths.GAMEDIR.get().resolve(fallbackName);
    }

    /**
     * {@code tlm.sim.run} を解決する。パス区切り等の危険な文字は {@code _} へ置換し、
     * 空 / ドットのみになった場合は起動時刻へフォールバックする — resolve が
     * outRoot の外へ出ることはない。
     */
    static String runId() {
        String raw = System.getProperty(PROP_RUN);
        String trimmed = raw == null ? "" : raw.trim();
        String sanitized = RUN_ID_INVALID_CHARS.matcher(trimmed).replaceAll("_");
        if (sanitized.length() > RUN_ID_MAX_LENGTH) {
            sanitized = sanitized.substring(0, RUN_ID_MAX_LENGTH);
        }
        String result;
        if (sanitized.isEmpty() || RUN_ID_DOTS_ONLY.matcher(sanitized).matches()) {
            result = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss"));
        } else {
            result = sanitized;
        }
        if (!trimmed.isEmpty() && !result.equals(trimmed)) {
            TouhouLittleMaid.LOGGER.warn("[SIM] tlm.sim.run '{}' を '{}' へ整形して使用", trimmed, result);
        }
        return result;
    }

    /** {@code ServerStartedEvent} から呼ぶ。シナリオ名が無ければ何もしない。 */
    public static void begin(MinecraftServer server) {
        if (!requested()) {
            return;
        }
        try {
            String name = System.getProperty(PROP_SCENARIO).trim();
            Path simDir = dir(PROP_DIR, "simlab");
            Path outRoot = dir(PROP_OUT, "simlab-out");
            boolean halt = !"false".equalsIgnoreCase(System.getProperty(PROP_HALT, "true"));
            String runId = runId();

            SimScenario scenario = SimScenario.load(simDir, name);
            // シナリオ側の keepAlive でも止めない。実クライアントを繋いで
            // 「マイクラのまま住まわせて眺める」使い方のため。
            halt = halt && !scenario.keepAlive;
            SimTuning.apply(scenario.overrides);

            // 水槽へ放てるモブの一覧を書き出す。**jar が真実源、Viewer は読むだけ。**
            // mods/ に mod を足せば選択肢が勝手に増える (サイト側の対応は不要)。
            SimCatalog.write(outRoot);

            // 判断ログ (ch:ai) の供給元は ReimuAiDebug。sim 中は問答無用で ON にする。
            ReimuAiDebug.setEnabled(true);

            SimRunner r = new SimRunner(server, scenario, outRoot, runId, halt);
            SimNetworkTrace.close();
            runner = r;
            ENABLED = true;
            warnAboutRebuilds();
            r.start();
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] begin failed — sim disabled", e);
            ENABLED = false;
            runner = null;
        }
    }

    /**
     * 走っている水槽の傍でビルドしてはいけない、と起動時に一度だけ言う。
     *
     * <p><b>なぜ言う必要があるのか (2026-08-25 実測)</b>: 水槽は jar ではなく
     * <b>dev クラスパス = {@code build/classes/java/main} から直接</b>実行される
     * (build.gradle:80 の注記)。一方 build.gradle:340 の
     * {@code compileJava { outputs.upToDateWhen { false } }} (上流 TLM 由来) により、
     * gradle が走るたびに <b>そのディレクトリは一度空にされてから書き直される</b>。
     * 水槽の JVM は既に読んだクラスは持ち続けるが、<b>まだ読んでいないクラス</b>は
     * その窓に当たると二度と読めない —— {@code NoClassDefFoundError} から
     * 「Ticking entity」でサーバが即死し、心拍が止まって水槽が凍る。
     *
     * <p>2026-08-23 06:12 の crash-report がこれ
     * ({@code MaidBackupsManager}、180 秒タイマーでしか読まれない) で、
     * 2026-08-25 に同一スタックで再現させた。その 1 件は EntityMaid 側で塞いだが、
     * <b>遅延ロードされるクラスは他にもある</b>ので、危険そのものは残っている。
     *
     * <p>ここで消せない理由: {@code upToDateWhen} は上流 TLM が refmap.json の
     * 欠落対策で入れたもので、外すと別の壊れ方を招く。水槽側から見えるのは
     * 「その窓が在る」ことだけなので、<b>黙らずに言う</b>。
     */
    private static void warnAboutRebuilds() {
        TouhouLittleMaid.LOGGER.warn("[SIM] 水槽が走っている間は gradle を回さないこと"
                + " (runSim / test / build / reobfShadowJar のいずれも build/classes を作り直すため、"
                + " まだ読まれていないクラスが消えて NoClassDefFoundError でサーバが即死する)。"
                + " 2026-08-23 と 2026-08-25 に実測・再現済み。");
    }

    /** {@code ServerTickEvent(END)} から毎 tick 呼ぶ。 */
    public static void tick() {
        if (!ENABLED) {
            return;
        }
        SimRunner r = runner;
        if (r == null) {
            return;
        }
        try {
            r.tick();
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] tick failed — aborting run", e);
            shutdown("tick-error");
        }
    }

    /** サーバ停止時。書きかけのトレースを閉じる。 */
    public static void shutdown(String reason) {
        SimRunner r = runner;
        if (r != null) {
            try {
                r.abort(reason);
            } catch (Exception e) {
                TouhouLittleMaid.LOGGER.error("[SIM] shutdown failed", e);
            }
        }
        runner = null;
        ENABLED = false;
        SimNetworkTrace.close();
        SimTuning.clear();
    }

    // =========================================================================
    // フック
    // =========================================================================

    /** {@code LivingDamageEvent} から。 */
    public static void onDamage(LivingEntity victim, DamageSource src, float amount) {
        if (!ENABLED) {
            return;
        }
        try {
            SimRunner r = runner;
            if (r == null || r.finished()) {
                return;
            }
            SimArena a = r.arenaOf(victim);
            if (a != null) {
                a.onDamage(a.currentTick(), victim, src, amount);
            }
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] onDamage failed", e);
        }
    }

    /**
     * Forge の {@code PlayLevelSoundEvent} から。
     *
     * <p>mod 全体で {@code playSound} は 126 箇所/50 ファイルに散っているが、
     * このイベントは {@code Level#playSound} と {@code Level#playSeededSound} の
     * <b>両方</b>から fire される (Forge 自身の javadoc 記載) ので、
     * ここ 1 点で音は漏れなく拾える。Mixin は要らない。
     */
    public static void onSound(net.minecraft.core.Holder<net.minecraft.sounds.SoundEvent> sound,
                               net.minecraft.sounds.SoundSource source,
                               double x, double y, double z, float volume, float pitch) {
        if (!ENABLED) {
            return;
        }
        try {
            if (sound == null) {
                return;
            }
            net.minecraft.sounds.SoundEvent ev = sound.value();
            String id = ev == null ? "?" : String.valueOf(ev.getLocation());
            onSound(id, source == null ? "?" : source.getName(), x, y, z, volume, pitch);
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] onSound(holder) failed", e);
        }
    }

    /** {@link #onSound(net.minecraft.core.Holder, net.minecraft.sounds.SoundSource, double, double, double, float, float)} の実体。 */
    public static void onSound(String soundId, String source, double x, double y, double z,
                               float volume, float pitch) {
        if (!ENABLED) {
            return;
        }
        try {
            SimRunner r = runner;
            if (r == null || r.finished()) {
                return;
            }
            SimArena a = r.arenaOfPos(x, y, z);
            if (a != null) {
                a.onSound(a.currentTick(), soundId, source, x, y, z, volume, pitch);
            }
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] onSound failed", e);
        }
    }
}
