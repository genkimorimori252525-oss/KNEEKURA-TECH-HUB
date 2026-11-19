package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.GameRules;

import javax.annotation.Nullable;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * 1 回の {@code runSim} 実行を駆動する。アリーナを並べ、毎 tick 回し、全部終わったら
 * summary を書いてサーバを止める。
 *
 * <p>速度戦略は<b>並列アリーナのみ</b> —— エンジンの tick 間隔には手を入れない。
 * 1 ワールドに N 個のアリーナを {@code spacing} 間隔で並べて同時に走らせることで、
 * 実時間 20 tick/秒 のまま N 倍のスループットを得る。
 */
public final class SimRunner {

    private final MinecraftServer server;
    private final SimScenario scenario;
    private final ServerLevel level;
    private final Path outDir;
    private final String runId;
    private final List<SimArena> arenas = new ArrayList<>();
    private final boolean haltWhenDone;

    private long runTick;
    private boolean finished;

    public SimRunner(MinecraftServer server, SimScenario scenario, Path outRoot, String runId, boolean haltWhenDone) {
        this.server = server;
        this.scenario = scenario;
        this.level = server.overworld();
        this.outDir = outRoot.resolve(scenario.name).resolve(Long.toString(scenario.seed)).resolve(runId);
        this.runId = runId;
        this.haltWhenDone = haltWhenDone;
        // 心拍を始める。**空の水槽でも打つ** —— 中身とは別に「生きている」を示すため。
        // outRoot が手元にあるのはここだけなので、この場所で init する。
        SimHeartbeat.init(outRoot,
                scenario.name,
                scenario.name + "/" + scenario.seed + "/" + runId);
    }

    public SimScenario scenario() {
        return this.scenario;
    }

    public long runTick() {
        return this.runTick;
    }

    public String runId() {
        return this.runId;
    }

    public boolean finished() {
        return this.finished;
    }

    /**
     * 測定を汚す環境要因を止める。<b>これを入れる前は、日光でゾンビが燃えて
     * 30 秒で 33 ダメージ入り、霊夢の与ダメージと区別できなかった</b> ({@code src:"onFire"})。
     *
     * <p>時刻を真夜中に固定するのが要点 —— アンデッド系ダミーの日光焼けを止めつつ、
     * 昼夜サイクルによる run 毎のばらつきも同時に消える (再現性の前提)。
     */
    private void quietTheWorld() {
        try {
            GameRules gr = this.server.getGameRules();
            gr.getRule(GameRules.RULE_DAYLIGHT).set(false, this.server);
            gr.getRule(GameRules.RULE_WEATHER_CYCLE).set(false, this.server);
            gr.getRule(GameRules.RULE_DOFIRETICK).set(false, this.server);
            gr.getRule(GameRules.RULE_DOMOBSPAWNING).set(false, this.server);
            gr.getRule(GameRules.RULE_MOBGRIEFING).set(false, this.server);
            gr.getRule(GameRules.RULE_DO_PATROL_SPAWNING).set(false, this.server);
            gr.getRule(GameRules.RULE_DO_TRADER_SPAWNING).set(false, this.server);
            gr.getRule(GameRules.RULE_DOINSOMNIA).set(false, this.server);
            gr.getRule(GameRules.RULE_ANNOUNCE_ADVANCEMENTS).set(false, this.server);
            // 真夜中に固定: アンデッドが日光で燃えない & 昼夜による run 間のばらつきを消す
            this.level.setDayTime(18000L);
            this.level.setWeatherParameters(999999, 0, false, false);
            TouhouLittleMaid.LOGGER.info("[SIM] world quieted (no daylight cycle, time=midnight, no fire tick, no natural spawns)");
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] failed to quiet the world — measurements may include environmental damage", e);
        }
    }

    /** アリーナを作り、chunk の forceload を要求する。実際の spawn は chunk が乗ってから。 */
    public void start() {
        try {
            Files.createDirectories(this.outDir);
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] cannot create output dir {}", this.outDir, e);
        }
        quietTheWorld();
        for (int i = 0; i < this.scenario.arenas; i++) {
            SimArena a = new SimArena(i, this.scenario, this.level, this.outDir, this.runId);
            a.requestChunks();
            this.arenas.add(a);
        }
        TouhouLittleMaid.LOGGER.info("[SIM] scenario '{}' started: {} arena(s) x {} ticks -> {}",
                this.scenario.name, this.scenario.arenas, this.scenario.duration, this.outDir);
    }

    /** {@code ServerTickEvent(END)} から毎 tick 呼ばれる。 */
    public void tick() {
        if (this.finished) {
            return;
        }
        this.runTick++;
        // **誰も居なくても打つ。** トレースは中の出来事の記録なので、空の水槽では
        // 1 行も出ない —— それだと「誰もいない」と「壊れている」が区別できない。
        SimHeartbeat.beat(this.runTick);

        boolean allDone = true;
        for (SimArena a : this.arenas) {
            a.tick();
            if (!a.done()) {
                allDone = false;
            }
        }
        if (allDone) {
            finish();
        }
    }

    private void finish() {
        this.finished = true;
        // 心拍を止める。**ここで止めるから、Viewer 側は「終わった」と「まだ生きている」を
        // 取り違えない。** 心拍が消える = この水槽はもう観察対象ではない。
        SimHeartbeat.stop();

        JsonObject sum = new JsonObject();
        sum.addProperty("scenario", this.scenario.name);
        sum.addProperty("seed", this.scenario.seed);
        sum.addProperty("duration", this.scenario.duration);
        sum.addProperty("arenas", this.arenas.size());
        sum.addProperty("runTicks", this.runTick);
        JsonArray arr = new JsonArray();
        for (SimArena a : this.arenas) {
            arr.add(a.summary());
        }
        sum.add("results", arr);

        Path f = this.outDir.resolve("summary.json");
        try {
            Files.writeString(f, new GsonBuilder().setPrettyPrinting().create().toJson(sum), StandardCharsets.UTF_8);
            TouhouLittleMaid.LOGGER.info("[SIM] summary written: {}", f);
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] summary write failed: {}", f, e);
        }

        TouhouLittleMaid.LOGGER.info("[SIM] DONE. traces in {}", this.outDir);
        if (this.haltWhenDone) {
            TouhouLittleMaid.LOGGER.info("[SIM] halting server (set -Dtlm.sim.halt=false to keep it running)");
            this.server.halt(false);
        }
    }

    /** すべてのアリーナを畳む (サーバ停止時の保険。書きかけのトレースを閉じる)。 */
    public void abort(String reason) {
        for (SimArena a : this.arenas) {
            a.finish(reason);
        }
        this.finished = true;
    }

    /** ダメージ/音イベントを担当アリーナへ振り分ける。 */
    @Nullable
    public SimArena arenaOf(Entity e) {
        for (SimArena a : this.arenas) {
            if (a.contains(e)) {
                return a;
            }
        }
        return null;
    }

    @Nullable
    public SimArena arenaOfPos(double x, double y, double z) {
        for (SimArena a : this.arenas) {
            if (a.containsPos(x, y, z)) {
                return a;
            }
        }
        return null;
    }
}
