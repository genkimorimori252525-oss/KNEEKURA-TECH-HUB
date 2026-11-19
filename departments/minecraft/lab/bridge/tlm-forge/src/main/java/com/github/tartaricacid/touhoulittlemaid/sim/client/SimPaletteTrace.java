package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.geckolib3.geo.IGeoEntity;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import javax.annotation.Nullable;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * 霊夢の<b>実描画経路 (geoRender 直後) の palette</b>を毎フレーム記録するクライアント側レコーダ
 * (14-02)。{@link SimPoseTrace} が頂点 (再構成された姿勢) を録るのに対し、こちらは
 * YSM が<b>その瞬間に実際に使ったボーンごとの合成後ローカル TRS</b> をそのまま録る
 * (spike 004 第3段階の意味づけ、コーデックは 14-01 の {@link SimPaletteCodec})。
 *
 * <h3>ライフサイクルは SimPoseTrace に相乗りする</h3>
 * {@code start}/{@code checkpoint}/{@code finish} は {@link SimPoseTrace} の
 * {@code start}/{@code afterStep}/{@code finish} から呼ばれる ——
 * <b>1 つの stamp・1 つの {@code gt0}・1 つの target</b> を共有することで、
 * {@code /api/pose} 側の既存 uuid 突き合わせが palette companion もそのまま解決できる
 * (新しい突き合わせ規則を作らない)。
 *
 * <h3>採る場所は 1 か所だけ</h3>
 * {@code EntityMaidRenderer} の {@code geoRender} 直後、{@code ReimuBoneSampler} /
 * {@code SimBoneProbe} と同じ post-geoRender グループから {@link #afterRender} が呼ばれる。
 * そこが「当フレームのアニメ適用後」の唯一確実な瞬間であることは {@link SimBoneCapture}
 * の javadoc と同じ理由 —— 別の呼び出しで採ると controller が 1 フレーム進む。
 *
 * <h3>フィールドだけを読む</h3>
 * {@link SimBonePalette#find}/{@link SimBonePalette#slotNames} を経由するのみで、
 * このクラス自身は反射によるメソッド呼び出しを一切行わない (14-02 の非交渉の制約)。
 *
 * <h3>対象は 1 体だけ (霊夢のみ)</h3>
 * {@link SimPoseTrace} が既に選んだ target の entity id と一致する場合だけ記録する。
 * 画面上の他の YSM エンティティを録ると容量が倍々になる (14-CONTEXT §6 の仮定)。
 *
 * <h3>容量の自己上限</h3>
 * {@link #PROP_MAX_BYTES} (既定 512MB) に達したら palette 記録<b>だけ</b>を止め、
 * 姿勢トレース本体は継続する。{@link #PROP_ENABLE} を {@code 0} にすれば palette は
 * まったく録らず、既存の pose companion は今日と完全に同じ挙動のままになる。
 */
@OnlyIn(Dist.CLIENT)
public final class SimPaletteTrace {

    /** palette 記録の有効/無効 (既定 on)。{@code 0} で palette を一切録らない (今日と同じ挙動)。 */
    public static final String PROP_ENABLE = "tlm.sim.palette";
    /** palette 記録バイト数の上限 (既定 512MB)。到達したら palette 記録のみ停止する。 */
    public static final String PROP_MAX_BYTES = "tlm.sim.palbytes";
    private static final long DEFAULT_MAX_BYTES = 536_870_912L;

    /** ライブでの想定 tick レート ({@code B/tick} を {@code MB/hour} へ換算するのに使う)。 */
    private static final double TICKS_PER_HOUR = 20.0 * 3600.0;

    private SimPaletteTrace() {}

    // ---- 進行状態 ----
    private static boolean active = false;
    private static boolean disarmedByFailure = false;
    private static int targetEntityId = -1;
    @Nullable
    private static String targetUuid = null;
    @Nullable
    private static String targetType = null;
    private static long gt0 = 0L;
    @Nullable
    private static Path outJson = null;
    @Nullable
    private static Path outBin = null;

    /** slot -> bone 名。最初に採れたフレームで一度だけ解決し、以後使い回す。 */
    @Nullable
    private static String[] names = null;
    private static int boneCount = -1;
    /** デコーダ写しの状態 (9 float/ボーン)。{@link SimPaletteCodec#encode} が書き換える。 */
    @Nullable
    private static float[] state9 = null;

    /** この tick 既に 1 枚採ったか (フレームレート分の重複描画をデデュープする)。 */
    private static long dedupeTick = Long.MIN_VALUE;
    /** 直近に記録に成功した tick 番号 (= gameTime - gt0)。まだ無ければ負値。 */
    private static long lastRecordedTickIdx = -1;

    private static final List<Integer> slots = new ArrayList<>();
    private static final List<Integer> lens = new ArrayList<>();
    private static final List<String> kinds = new ArrayList<>();

    private static long totalBytes = 0L;
    private static long ticksRecorded = 0L;
    private static long framesWritten = 0L;
    private static long findFailures = 0L;

    private static boolean enabled() {
        return !"0".equals(System.getProperty(PROP_ENABLE));
    }

    private static long maxBytes() {
        return Long.getLong(PROP_MAX_BYTES, DEFAULT_MAX_BYTES);
    }

    /**
     * {@link SimPoseTrace#start} が自身の冪等性ゲートを通した<b>後</b>に呼ぶ。
     * {@code tlm.sim.palette=0} なら何もせず (armed のままにしない) —— これが
     * 既存の pose companion を一切変えずに palette だけを無効化する脱出口になる。
     */
    public static void start(Entity target, long gt0In, String stamp, Path outDir) {
        active = false;
        disarmedByFailure = false;
        if (!enabled()) {
            return;
        }
        targetEntityId = target.getId();
        targetUuid = target.getUUID().toString();
        targetType = String.valueOf(BuiltInRegistries.ENTITY_TYPE.getKey(target.getType()));
        gt0 = gt0In;
        outJson = outDir.resolve(stamp + ".pal.json");
        outBin = outDir.resolve(stamp + ".pal.bin");

        names = null;
        boneCount = -1;
        state9 = null;
        dedupeTick = Long.MIN_VALUE;
        lastRecordedTickIdx = -1;
        slots.clear();
        lens.clear();
        kinds.clear();
        totalBytes = 0L;
        ticksRecorded = 0L;
        framesWritten = 0L;
        findFailures = 0L;

        try {
            Files.deleteIfExists(outBin);
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] palette trace bin cleanup failed", e);
        }
        active = true;
    }

    public static boolean isArmed() {
        return active;
    }

    /**
     * {@code EntityMaidRenderer} の post-{@code geoRender} グループから、{@code
     * ReimuBoneSampler.sample} / {@code SimBoneProbe.sampleIfArmed} と並んで呼ばれる。
     * <b>フィールドを読むだけ</b>で {@code geoEntity} には一切触れない (メソッド呼び出しなし)。
     */
    public static void afterRender(EntityMaid maid, IGeoEntity geoEntity) {
        if (!active || maid == null) {
            return;
        }
        if (maid.getId() != targetEntityId) {
            return;
        }
        long gt = maid.level().getGameTime();
        if (gt == dedupeTick) {
            // 同じ tick 内の2枚目以降の render — controller の状態は同じフレームのものなので、
            // 1 枚目 (最初の render) を残し、以降は捨てる。
            return;
        }
        dedupeTick = gt;
        long tickIdx = gt - gt0;
        if (tickIdx < 0) {
            return;
        }

        Object root = geoEntity == null ? null : geoEntity.getGeoModel();
        SimBonePalette.Found found = root == null ? null : SimBonePalette.find(root);
        if (found == null) {
            findFailures++;
            if (framesWritten == 0) {
                disarm("ボーン配列が見つからない (fail closed)");
            }
            return;
        }

        if (names == null) {
            SimBonePalette.SlotResult sr = SimBonePalette.slotNames(found);
            if (!sr.ok()) {
                findFailures++;
                disarm("bone 名 -> slot の解決に失敗: " + sr.reason());
                return;
            }
            names = sr.names();
            boneCount = found.bones().size();
            state9 = new float[boneCount * SimPaletteCodec.COMPS];
        }

        if (found.palette().length != boneCount * SimPaletteCodec.PALETTE_STRIDE) {
            // 途中でモデルが差し替わったなど、想定外の形。この tick は諦めるが、
            // 既に 1 枚以上採れているので disarm はしない (best effort で継続)。
            findFailures++;
            return;
        }

        boolean keyframe = lastRecordedTickIdx < 0
                || tickIdx % SimPaletteCodec.KEYFRAME_TICKS == 0
                || tickIdx != lastRecordedTickIdx + 1;

        byte[] record;
        try {
            record = SimPaletteCodec.encode(state9, found.palette(), boneCount, keyframe);
            SimPaletteCodec.appendRecord(outBin, record);
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] palette trace record write failed", e);
            return;
        }

        // append と同じ分岐で lens/kinds/slots を積む — SimPoseTrace:483-508 が名指しした
        // .pose.bin のフレーム分割不具合 (quick 260818-6cj) と同じ形の罠をここでも踏まない。
        while (slots.size() <= tickIdx) {
            slots.add(-1);
        }
        int frameIdx = lens.size();
        lens.add(record.length);
        kinds.add(keyframe ? "K" : "D");
        slots.set((int) tickIdx, frameIdx);
        totalBytes += record.length;
        framesWritten++;
        ticksRecorded++;
        lastRecordedTickIdx = tickIdx;

        if (active && totalBytes >= maxBytes()) {
            active = false;
            writeIndex();
            double mbPerHour = meanBytesPerTick() * TICKS_PER_HOUR / (1024.0 * 1024.0);
            String msg = String.format(Locale.ROOT,
                    "[SIM] palette: 上限 %d B に到達したため palette 記録のみ停止"
                            + " (tick %d, 到達レート %.2f MB/hour)。姿勢トレースは継続する",
                    maxBytes(), ticksRecorded, mbPerHour);
            TouhouLittleMaid.LOGGER.warn(msg);
            say(ChatFormatting.YELLOW, msg);
        }
    }

    /** {@link SimPoseTrace#afterStep} と同じ cadence で呼ばれる中間保存。 */
    public static void checkpoint() {
        if (!active) {
            return;
        }
        writeIndex();
    }

    /** {@link SimPoseTrace#finish} から呼ばれる。索引を書き、結果をチャットとログへ出す。 */
    public static void finish() {
        boolean everCaptured = framesWritten > 0;
        active = false;
        if (!everCaptured) {
            TouhouLittleMaid.LOGGER.info("[SIM] palette trace: 記録なし (find 失敗 {} 回)", findFailures);
            if (!disarmedByFailure) {
                // armed のまま一度も afterRender を受け取らなかった (tlm.sim.palette=0 か、
                // 対象が一度も描画されなかった)。にせよ、書くべき索引が無い。
                say(ChatFormatting.GRAY, "[SIM] palette: このrunは palette を1枚も採れなかった (記録は無い)");
            }
            return;
        }
        writeIndex();
        double meanBytesPerTick = meanBytesPerTick();
        double mbPerHour = meanBytesPerTick * TICKS_PER_HOUR / (1024.0 * 1024.0);
        String line = String.format(Locale.ROOT,
                "[SIM] palette trace: %d tick / %d frames / %d bytes / mean %.1f B/tick / %.2f MB/hour"
                        + " (find失敗 %d 回) -> %s",
                ticksRecorded, framesWritten, totalBytes, meanBytesPerTick, mbPerHour, findFailures, outJson);
        TouhouLittleMaid.LOGGER.info(line);
        say(ChatFormatting.GREEN, line);
    }

    private static double meanBytesPerTick() {
        return ticksRecorded > 0 ? (double) totalBytes / ticksRecorded : 0.0;
    }

    /**
     * 記録できない事情が起きたときの唯一の入り口。<b>最初に採れたフレームでの失敗だけ</b>が
     * ここに来る想定 (以降のフレームでの find 失敗は単にその tick を諦めるだけで、
     * disarm はしない) —— 姿勢トレース本体は止めず、{@code .pal.json} は書かない。
     */
    private static void disarm(String reason) {
        active = false;
        disarmedByFailure = true;
        TouhouLittleMaid.LOGGER.error("[SIM] palette trace disarmed: {}", reason);
        say(ChatFormatting.RED, "[SIM] palette: " + reason + " — palette 記録を中止 (姿勢トレースは継続)");
    }

    private static void writeIndex() {
        if (outJson == null || outBin == null || framesWritten == 0 || names == null) {
            return;
        }
        int[] slotsArr = new int[slots.size()];
        for (int i = 0; i < slotsArr.length; i++) {
            slotsArr[i] = slots.get(i);
        }
        int[] lensArr = new int[lens.size()];
        for (int i = 0; i < lensArr.length; i++) {
            lensArr[i] = lens.get(i);
        }
        String[] kindsArr = kinds.toArray(new String[0]);

        SimPaletteCodec.Header header = new SimPaletteCodec.Header(
                SimPaletteCodec.V1, SimPaletteCodec.CODEC, gt0, targetEntityId, targetUuid, targetType,
                boneCount, SimPaletteCodec.COMPS, SimPaletteCodec.KEYFRAME_TICKS, names,
                outBin.getFileName().toString(), new String[0]);
        try {
            SimPaletteCodec.writeIndex(outJson, header, slotsArr, lensArr, kindsArr);
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] palette trace index write failed: {}", outJson, e);
            say(ChatFormatting.RED, "[SIM] palette 索引の書き出しに失敗: " + e.getMessage());
        }
    }

    private static void say(ChatFormatting color, String msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.player.displayClientMessage(Component.literal(msg).withStyle(color), false);
        }
    }
}
