package com.github.tartaricacid.touhoulittlemaid.sim.trace;

import com.github.tartaricacid.touhoulittlemaid.entity.ai.reimu.debug.ReimuAiDebug;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.reimu.EntityReimu;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * エンティティ 1 体を 1 tick 分のトレースイベントへ変換する。
 *
 * <p>「何を記録するか」の判断はここに集約し、{@code SimArena} は
 * 「誰を・いつ」だけを持つ。チャンネル定義は {@link SimCh}。
 */
public final class SimProbe {

    private SimProbe() {}

    // =========================================================================
    // 見た目パラメータの収集
    // =========================================================================
    /**
     * entity クラス -> 見た目に効く getter 群。{@code getSyncXxx()} という命名規約で拾う。
     *
     * <p>弾ごとにフィールドは違う ({@code getSyncScale/Alpha/Color/Spin} 等) が、
     * <b>レンダラが読む値はすべてこの規約で公開されている</b>ので、
     * 弾種ごとの配線を書かずに列挙できる。新しい弾を足しても自動で乗る。
     */
    private static final Map<Class<?>, List<Map.Entry<String, Method>>> SYNC_GETTERS = new ConcurrentHashMap<>();

    private static List<Map.Entry<String, Method>> syncGetters(Class<?> cls) {
        return SYNC_GETTERS.computeIfAbsent(cls, k -> {
            List<Map.Entry<String, Method>> out = new ArrayList<>();
            for (Method m : k.getMethods()) {
                if (m.getParameterCount() != 0) {
                    continue;
                }
                String n = m.getName();
                if (!n.startsWith("getSync") || n.length() <= 7) {
                    continue;
                }
                Class<?> r = m.getReturnType();
                if (r != int.class && r != float.class && r != double.class
                        && r != long.class && r != boolean.class) {
                    continue;
                }
                out.add(Map.entry(Character.toLowerCase(n.charAt(7)) + n.substring(8), m));
            }
            return List.copyOf(out);
        });
    }

    /** この entity は見た目パラメータを持っているか (毎 tick の判定を安くするため)。 */
    public static boolean hasVisual(Entity e) {
        return !syncGetters(e.getClass()).isEmpty();
    }

    /**
     * {@code ch:vis} を 1 行。{@code age}({@code tickCount}) はフィルムストリップの
     * コマ送りに使われている ({@code tickCount / 2 % frames}) ので必ず含める。
     */
    public static void visual(SimTrace tr, long t, Entity e) {
        List<Map.Entry<String, Method>> gs = syncGetters(e.getClass());
        if (gs.isEmpty()) {
            return;
        }
        tr.event(t, SimCh.VIS, o -> {
            o.addProperty("id", e.getId());
            o.addProperty("age", e.tickCount);
            for (Map.Entry<String, Method> g : gs) {
                try {
                    Object v = g.getValue().invoke(e);
                    if (v instanceof Boolean b) {
                        o.addProperty(g.getKey(), b);
                    } else if (v instanceof Number n) {
                        o.addProperty(g.getKey(), SimTrace.r3(n.doubleValue()));
                    }
                } catch (Exception ignored) {
                    // 1 個の getter が転んでも他は残す
                }
            }
        });
    }

    /** {@code EntityType} の登録 id ({@code minecraft:zombie} 等)。 */
    public static String typeId(Entity e) {
        return String.valueOf(BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()));
    }

    /**
     * 追跡開始を記録する。<b>hitbox 実サイズを載せるのが要点</b> ——
     * Viewer は見た目のモデルを持たないので、この幅/高さで箱を描くと
     * 「見た目は箱だが当たり判定は本物と 1mm も違わない」表示になる。
     */
    public static void spawn(SimTrace tr, long t, Entity e, String role) {
        tr.event(t, SimCh.SPAWN, o -> {
            o.addProperty("id", e.getId());
            o.addProperty("type", typeId(e));
            o.addProperty("role", role);
            o.addProperty("name", e.getName().getString());
            // **名指しで消せるようにする。** Viewer の「中にいる」から × で片付けるのに要る。
            // バニラの /kill はネットワーク id を取らないので UUID を残す (SimCh に optional で追加)。
            o.addProperty("uuid", e.getUUID().toString());
            o.addProperty("w", SimTrace.r3(e.getBbWidth()));
            o.addProperty("h", SimTrace.r3(e.getBbHeight()));
            if (e instanceof LivingEntity le) {
                o.addProperty("maxHp", SimTrace.r2(le.getMaxHealth()));
            }
        });
    }

    /** 追跡終了を記録する。{@code reason} は {@code dead} / {@code removed} / {@code end}。 */
    public static void gone(SimTrace tr, long t, int entityId, String reason) {
        tr.event(t, SimCh.GONE, o -> {
            o.addProperty("id", entityId);
            o.addProperty("reason", reason);
        });
    }

    /**
     * 位置・向き・速度・HP。追跡中の全 entity (弾を含む)。
     *
     * <p>13-04: {@code delta} が非 null なら行単位デルタ化する ——
     * 行を組んでから正規化した文字列で {@code delta} へ問い合わせ、書くと答えたときだけ
     * {@link SimTrace#event} を呼ぶ。{@code delta} が null なら今までどおり毎 tick 無条件で書く
     * (呼び出し側を壊さない素通し経路)。フィールドの中身・順序・丸めは変えない
     * (形は同じ、頻度だけが変わる)。
     */
    public static void pos(SimTrace tr, long t, Entity e, SimDelta delta) {
        JsonObject body = new JsonObject();
        Vec3 v = e.getDeltaMovement();
        body.addProperty("id", e.getId());
        body.addProperty("x", SimTrace.r3(e.getX()));
        body.addProperty("y", SimTrace.r3(e.getY()));
        body.addProperty("z", SimTrace.r3(e.getZ()));
        body.addProperty("yaw", SimTrace.r2(e.getYRot()));
        body.addProperty("pitch", SimTrace.r2(e.getXRot()));
        body.addProperty("vx", SimTrace.r3(v.x));
        body.addProperty("vy", SimTrace.r3(v.y));
        body.addProperty("vz", SimTrace.r3(v.z));
        if (e instanceof LivingEntity le) {
            body.addProperty("hp", SimTrace.r2(le.getHealth()));
        }
        // 交戦態勢。ゾンビの腕上げなど、姿勢がこれで変わるモブがいるので Viewer が使う。
        if (e instanceof net.minecraft.world.entity.Mob mob && mob.isAggressive()) {
            body.addProperty("agg", true);
        }
        // 頭の向き。実機のレンダラは (yHeadRot - yBodyRot) と xRot で頭を回すので同じ値を残す。
        // これがあると「どこを見ているか」が Viewer で分かる —— AI 検証では見たい情報。
        if (e instanceof LivingEntity le) {
            float hy = net.minecraft.util.Mth.wrapDegrees(le.yHeadRot - le.yBodyRot);
            if (Math.abs(hy) > 0.05F) {
                body.addProperty("hy", SimTrace.r2(hy));
            }
        }
        if (delta == null || delta.shouldWrite(SimCh.POS, e.getId(), t, canonicalBody(body))) {
            tr.event(t, SimCh.POS, o -> copyInto(o, body));
        }
    }

    /**
     * 霊夢の 1 tick を {@code ai} / {@code anim} / {@code phys} の 3 チャンネルへ展開する。
     *
     * <p>供給元は {@link ReimuAiDebug#snapshot} と {@link ReimuAiDebug#section} ——
     * 実機の HUD / {@code [REIMU-AI]} 行と<b>同じ 1 箇所</b>から読むので、
     * 実機で見た値とトレースの値が食い違うことがない。
     *
     * @param prevSection 直前 tick の section。同一なら {@code ai} 行を書かない (差分のみ記録)
     * @param delta       13-04: {@code phys}/{@code anim} の行単位デルタ判定。null なら
     *                    今までどおり毎 tick 無条件で書く。{@code ai} の判定(上の
     *                    {@code prevSection} 比較)は {@code delta} を一切使わない —— 1文字も変えない
     * @return 今 tick の section (次回の {@code prevSection} に渡す)
     */
    public static String reimu(SimTrace tr, long t, EntityReimu r, String prevSection, SimDelta delta) {
        ReimuAiDebug.Snapshot s = ReimuAiDebug.snapshot(r);

        // phys: 見た目バグ (浮き/めり込み) を数値で検出するためのチャンネル。
        // 13-04: delta が非null なら行単位デルタ化する(フィールドの中身・順序・丸めは変えない)。
        JsonObject physBody = new JsonObject();
        physBody.addProperty("id", r.getId());
        physBody.addProperty("y", SimTrace.r3(s.y()));
        physBody.addProperty("onG", s.onGround());
        physBody.addProperty("embed", s.embed());
        physBody.addProperty("noGrav", s.noGravity());
        physBody.addProperty("air", s.air());
        physBody.addProperty("vel", SimTrace.r3(s.vel()));
        // somer: 宙返り中か (DATA_SOMERSAULTING)。**実機レンダラはこれで体を X 軸に
        // 回している** (EntityMaidRenderer.setupRotations: 36 度/tick、360 度で止まる)が、
        // 記録にも Viewer にも無かったので、水槽の霊夢は**水平にだけ回って縦に回らない**
        // (宙返り蹴りは yaw も回すので、そちらだけが見えていた。にーくら 2026-08-23
        // 「実機で起こる立て回転を正確に描写できない」)。角度は Viewer が同じ式で導く
        // ので、記録するのは真偽だけでよい —— phys はデルタなので変化した tick には必ず行が出る。
        physBody.addProperty("somer", r.isSomersaulting());
        if (delta == null || delta.shouldWrite(SimCh.PHYS, r.getId(), t, canonicalBody(physBody))) {
            tr.event(t, SimCh.PHYS, o -> copyInto(o, physBody));
        }

        // anim: 描画は無いが「何を命令したか」は残す。実機の見た目バグと突き合わせる材料。
        // 13-04: phys と同じくdelta化する。
        JsonObject animBody = new JsonObject();
        animBody.addProperty("id", r.getId());
        animBody.addProperty("anim", s.anim());
        animBody.addProperty("pend", s.pend());
        animBody.addProperty("molang", s.molang());
        animBody.addProperty("main", s.mainHand());
        animBody.addProperty("off", s.offHand());
        // face: 表情の molang 式。**molang フィールドとは別。**
        //   molang = server が「送った」もの (getLastSentReimuMolang)
        //   face   = 今の face 状態が「意味する」もの。実際に撃つのは client なので
        //            server の送信履歴には現れないが、何を撃つべきかは server が持っている。
        // これを書かないと Viewer 側で眼サイズ・睫毛・口が未設定のままになり、
        // 顔が実機と違って見える（2026-08-20、にーくら指摘）。
        animBody.addProperty("face", r.faceMolang());
        if (delta == null || delta.shouldWrite(SimCh.ANIM, r.getId(), t, canonicalBody(animBody))) {
            tr.event(t, SimCh.ANIM, o -> copyInto(o, animBody));
        }

        // ai: 判断が変わった tick だけ書く。毎 tick 書くと section が長いのでファイルが膨れる。
        // **この判定は delta(SimDelta) を一切使わない(既存の prevSection 比較のまま、1文字も変えない)。**
        String section = ReimuAiDebug.section(r);
        String flat = section.replace('\n', ' ').replaceAll("§.", "");
        if (!flat.equals(prevSection)) {
            tr.event(t, SimCh.AI, o -> {
                o.addProperty("id", r.getId());
                o.addProperty("mode", s.air() ? "AIR" : "GROUND");
                o.addProperty("hp", SimTrace.r2(s.hp()));
                o.addProperty("maxHp", SimTrace.r2(s.maxHp()));
                o.addProperty("target", s.targetId());
                o.addProperty("targetType", s.targetType());
                o.addProperty("dist", SimTrace.r2(s.targetDist()));
                o.addProperty("form", s.secondForm() ? 2 : 1);
                o.addProperty("formMode", s.secondFormMode());
                o.addProperty("amuletCd", s.amuletCd());
                o.addProperty("houju", s.houju());
                o.addProperty("gensou", s.gensou());
                o.addProperty("musouTp", s.musouTp());
                o.addProperty("section", flat);
                // sec: 上の section と**同じ文字列**を構造化したもの。
                // 供給点で 1 回だけパースするので、表示と統計が食い違えない（AGENT-01）。
                // 解析側（simlab/stats.mjs）は sec があればそれを使い、無い旧トレースでは
                // section を同一アルゴリズムでパースする。
                JsonObject sec = new JsonObject();
                for (Map.Entry<String, Object> en : SimSection.parse(flat).entrySet()) {
                    Object v = en.getValue();
                    if (v instanceof Boolean) {
                        sec.addProperty(en.getKey(), (Boolean) v);
                    } else if (v instanceof Number) {
                        sec.addProperty(en.getKey(), (Number) v);
                    } else {
                        sec.addProperty(en.getKey(), String.valueOf(v));
                    }
                }
                o.add("sec", sec);
            });
        }
        return flat;
    }

    // =========================================================================
    // 13-04: 行単位デルタ化の補助
    // =========================================================================

    /**
     * {@code body} (t を除いた行の中身) を正規化した文字列にする。キーをアルファベット順に
     * 並べ替えてから直列化する —— Gson {@code JsonObject} の内部反復順(実装依存)に
     * 依存しないため。{@link SimDelta} へ渡す「前回と同じか」の比較材料はこれ。
     */
    private static String canonicalBody(JsonObject body) {
        List<String> keys = new ArrayList<>(body.keySet());
        Collections.sort(keys);
        StringBuilder sb = new StringBuilder();
        for (String k : keys) {
            sb.append(k).append('=').append(body.get(k)).append(';');
        }
        return sb.toString();
    }

    /** {@code body} の全プロパティを {@code o} へコピーする ({@link SimTrace#event} の fill 内で使う)。 */
    private static void copyInto(JsonObject o, JsonObject body) {
        for (Map.Entry<String, JsonElement> en : body.entrySet()) {
            o.add(en.getKey(), en.getValue());
        }
    }
}
