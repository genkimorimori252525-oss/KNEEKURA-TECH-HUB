package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.ai.reimu.ReimuPoseMolangs;
import com.github.tartaricacid.touhoulittlemaid.entity.ai.reimu.net.client.YsmReimuNaianClientRunner;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.reimu.IReimuMaidHost;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import javax.annotation.Nullable;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 霊夢の<b>姿勢</b>を書き出す。
 *
 * <p>霊夢のポーズは、バニラモブのように {@code setupAnim} の入力では決まらない。
 * mod がサーバから molang 式を送り、クライアントが
 * {@code ysmclient debug <位置セレクタ>} → {@code ysmclient molang execute <式>} の 2 段で
 * YSM に流し、YSM 側のコントローラが姿勢を作る。
 * 式の中身は {@code v.lfmx=-69; v.lhdz=-121; ...} のような<b>ボーン回転角の直接代入</b>で、
 * それらは {@link ReimuPoseMolangs} に名前付きで並んでいる。
 *
 * <p>そこでここでは「アニメを再実装する」のではなく、
 * <b>mod が実際に送るのと同じ式を送って、その結果を録る</b>。
 * バニラモブで歩行位相を変えて録ったのと同じ発想 —— 姿勢の計算は YSM に任せたまま。
 *
 * <h3>なぜ tick をまたぐか</h3>
 * YSM へのコマンドはクライアントのコマンドキューで tick 駆動に流れる。
 * 1 回のコマンド実行では完結しないので、
 * 「式を送る → 数 tick 待つ → 録る」を姿勢の数だけ繰り返す駆動役が要る。
 *
 * <h3>なぜ実在の霊夢が要るか</h3>
 * molang の宛先が<b>位置セレクタ</b>
 * ({@code @e[type=#touhou_little_maid:reimu_host,x=..,distance=..1.5]}) で決まるため、
 * ワールドに居ない個体には当てられない。これは YSM 側の仕組みなので回避できない。
 */
@Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID, value = Dist.CLIENT)
public final class SimPoseDump {

    /** 式を送ってから録るまでの待ち。コマンドキューが 1〜2 tick 遅延を挟むので余裕を見る。 */
    private static final int SETTLE_TICKS = 8;
    /** 霊夢を探す半径。molang の位置セレクタが 1.5 なので、それより手前に居ることが前提。 */
    private static final double SEARCH_RADIUS = 16.0;

    private SimPoseDump() {}

    // ---- 進行状態 ----
    private static boolean active = false;
    private static List<Map.Entry<String, String>> poses = List.of();
    private static int index = 0;
    private static int wait = 0;
    private static Entity target = null;
    private static final List<float[]> frames = new ArrayList<>();
    private static final JsonObject poseIndex = new JsonObject();
    private static final JsonObject poseMolang = new JsonObject();
    private static String texture = null;
    private static int quads = 0;

    /**
     * {@link ReimuPoseMolangs} の姿勢式を名前つきで列挙する。
     * public static final String をそのまま拾うので、姿勢を足しても自動で対象になる。
     */
    public static List<Map.Entry<String, String>> collectPoses() {
        Map<String, String> out = new LinkedHashMap<>();
        for (Field f : ReimuPoseMolangs.class.getFields()) {
            if (f.getType() != String.class || !Modifier.isStatic(f.getModifiers())) {
                continue;
            }
            try {
                Object v = f.get(null);
                if (v instanceof String s && !s.isBlank()) {
                    out.put(f.getName(), s);
                }
            } catch (Exception ignored) {
                // 読めないものは飛ばす
            }
        }
        return new ArrayList<>(out.entrySet());
    }

    /** 近くの霊夢 (reimu host) を探す。 */
    @Nullable
    private static Entity findReimu() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return null;
        }
        Entity best = null;
        double bestD = SEARCH_RADIUS * SEARCH_RADIUS;
        for (Entity e : mc.level.entitiesForRendering()) {
            if (!(e instanceof IReimuMaidHost h) || !h.isReimuMaidHost()) {
                continue;
            }
            double d = e.distanceToSqr(mc.player);
            if (d < bestD) {
                bestD = d;
                best = e;
            }
        }
        return best;
    }

    /** @return 開始できたら null、無理なら理由 */
    @Nullable
    public static String start() {
        if (active) {
            return "すでに実行中";
        }
        Entity r = findReimu();
        if (r == null) {
            return "近くに霊夢が居ない (半径 " + (int) SEARCH_RADIUS + "。molang は位置で対象を選ぶので実在の個体が要る)";
        }
        poses = collectPoses();
        if (poses.isEmpty()) {
            return "ReimuPoseMolangs から姿勢式を 1 つも取れなかった";
        }
        target = r;
        index = 0;
        wait = 0;
        frames.clear();
        poseIndex.entrySet().clear();
        poseMolang.entrySet().clear();
        texture = null;
        quads = 0;
        active = true;
        say(ChatFormatting.GRAY, "[SIM] 姿勢を " + poses.size() + " 種 収集する (約 "
                + (poses.size() * SETTLE_TICKS / 20 + 1) + " 秒)。霊夢を動かさないこと");
        return null;
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (!active || event.phase != TickEvent.Phase.END) {
            return;
        }
        try {
            step();
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM] pose dump failed", t);
            say(ChatFormatting.RED, "[SIM] 姿勢収集に失敗: " + t);
            active = false;
        }
    }

    private static void step() {
        if (target == null || !target.isAlive()) {
            say(ChatFormatting.RED, "[SIM] 対象の霊夢が居なくなった");
            active = false;
            return;
        }
        if (wait > 0) {
            wait--;
            return;
        }
        if (index >= poses.size()) {
            finish();
            return;
        }
        Map.Entry<String, String> pose = poses.get(index);

        if (wait == 0 && !poseIndex.has(pose.getKey())) {
            // 式を送った直後は録らない。キューが捌けるまで待つ。
            YsmReimuNaianClientRunner.scheduleSpellCardMolang(
                    target.getX(), target.getY(), target.getZ(), pose.getValue());
            poseMolang.addProperty(pose.getKey(), pose.getValue());
            poseIndex.addProperty(pose.getKey(), -1);   // 予約 (この分岐に戻らないための印)
            wait = SETTLE_TICKS;
            return;
        }

        // 待ち明け → 録る
        SimModelDump.Shot shot = SimModelDump.shoot(target);
        if (shot != null) {
            if (texture == null) {
                texture = shot.texture();
            }
            quads = Math.max(quads, shot.quads());
            int slot = -1;
            for (int i = 0; i < frames.size(); i++) {
                if (sameVerts(frames.get(i), shot.verts())) {
                    slot = i;
                    break;
                }
            }
            if (slot < 0) {
                slot = frames.size();
                frames.add(shot.verts());
            }
            poseIndex.addProperty(pose.getKey(), slot);
        } else {
            poseIndex.remove(pose.getKey());
        }
        index++;
    }

    private static boolean sameVerts(float[] a, float[] b) {
        if (a.length != b.length) {
            return false;
        }
        for (int i = 0; i < a.length; i++) {
            if (Math.abs(a[i] - b[i]) > 1.0e-4F) {
                return false;
            }
        }
        return true;
    }

    private static void finish() {
        active = false;
        // 姿勢を戻しておく (借りた個体を変な格好のままにしない)
        try {
            YsmReimuNaianClientRunner.scheduleSpellCardMolang(
                    target.getX(), target.getY(), target.getZ(), ReimuPoseMolangs.POSE_FULL_RESET);
        } catch (Throwable ignored) {
            // 戻せなくても次の AI 更新で上書きされる
        }

        JsonObject o = new JsonObject();
        o.addProperty("type", "touhou_little_maid:reimu");
        o.addProperty("texture", texture);
        o.addProperty("quads", quads);
        o.add("poses", poseIndex);
        o.add("molang", poseMolang);
        JsonArray arr = new JsonArray();
        for (float[] v : frames) {
            JsonArray f = new JsonArray();
            for (float x : v) {
                f.add(Math.round(x * 10000.0F) / 10000.0F);
            }
            arr.add(f);
        }
        o.add("frames", arr);

        Path f = SimModelDump.outDir().resolve("touhou_little_maid").resolve("reimu.poses.json");
        try {
            Files.createDirectories(f.getParent());
            Files.writeString(f, o.toString(), StandardCharsets.UTF_8);
            int distinct = frames.size();
            say(ChatFormatting.GREEN, "[SIM] 姿勢 " + poseIndex.size() + " 種 -> 形が違うもの "
                    + distinct + " 本（同じ形は畳んだ）");
            say(ChatFormatting.DARK_GRAY, "  -> " + f);
            TouhouLittleMaid.LOGGER.info("[SIM] pose dump: {} poses, {} distinct frames -> {}",
                    poseIndex.size(), distinct, f);
            if (distinct <= 1) {
                say(ChatFormatting.YELLOW, "[SIM] 全部同じ形だった = molang が効いていない可能性が高い");
            }
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] pose dump write failed: {}", f, e);
            say(ChatFormatting.RED, "[SIM] 書き出し失敗: " + e.getMessage());
        }
        target = null;
    }

    private static void say(ChatFormatting color, String msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.player.displayClientMessage(Component.literal(msg).withStyle(color), false);
        }
    }
}
