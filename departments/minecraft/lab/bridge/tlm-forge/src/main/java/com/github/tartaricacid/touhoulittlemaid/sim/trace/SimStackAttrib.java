package com.github.tartaricacid.touhoulittlemaid.sim.trace;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

/**
 * 呼び出しスタックから「この被弾を起こした弾クラス」を探す台帳と走査器 (10-02)。
 *
 * <p><b>なぜスタックを読むのか</b>: magic ソースの {@code DamageSource} は attacker も
 * direct も持たない。呼び出し元を辿る以外に、どの弾が当てたのかを知る手が無い。
 * {@code entity/ai/reimu/projectile/} の9ファイルに引数を足して回る案もあるが、
 * <b>挙動のファイルを触らない</b>という制約を守るためこちらを採った。
 *
 * <p><b>壊れ方を見える形にしてある</b>: これが届かなくなっても {@code attrib="none"} が
 * 増えるだけで、<b>誤った数字にはならない</b>。未帰属は表に出るので気づける。
 *
 * <h3>なぜ {@code SimArena} から切り出してあるのか</h3>
 * {@code SimArena} は {@code ServerLevel} / {@code DamageSource} / {@code EntityType} を
 * 直接持つ深く Minecraft 依存したクラスで、JUnit に載らない。10-02-PLAN は
 * 「{@code SimArena.onDamage()} を代役クラスから呼ぶ試験」を求めていたが、その形は
 * 成立しなかった。<b>このクラスは Minecraft の import を持たない</b> ——
 * {@link SimSection} と同じ位置づけで、走査そのものを試験できるようにするため。
 *
 * <p><b>ただしこれで覆えるのは解決部分だけである。</b> 統合 (
 * {@code onDamage} が {@code attrib="stack"} と {@code projType} を書くこと) は
 * 自動テストでは検査されていない。根拠は 2026-08-20 の実機実測 (コミット
 * {@code bfea153b}、帰属不能が 12% まで低下) 1回のみ。
 *
 * <p>スレッド安全ではない。{@code SimArena} と同じくサーバスレッドからのみ触ること。
 */
public final class SimStackAttrib {

    /**
     * 弾の台帳 —— <b>クラス</b> → EntityType の登録 id。
     *
     * <p>id 台帳と違い<b>寿命を切らない</b>。弾が discard された後に
     * {@code LivingDamageEvent} が届く順序があり得るので、消えたからといって落とすと
     * 帰属できるはずのものを取りこぼす。クラスの数は高々数十なので溜めても害が無い。
     */
    private final Map<Class<?>, String> projClassType = new LinkedHashMap<>();

    /**
     * スタック走査器。<b>毎ダメージで作らない</b>ので生成コストを持ち回す。
     * {@code RETAIN_CLASS_REFERENCE} はフレームの宣言クラスを取るために要る。
     */
    private final StackWalker stackWalker =
            StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE);

    /** 弾が湧いたときに呼ぶ。同じクラスが再登録されても害は無い (上書き)。 */
    public void register(Class<?> projectileClass, String typeId) {
        this.projClassType.put(projectileClass, typeId);
    }

    /** 台帳が空か。空なら {@link #resolve()} は走査せず {@code null} を返す。 */
    public boolean isEmpty() {
        return this.projClassType.isEmpty();
    }

    /** 台帳の件数 (試験と診断のため)。 */
    public int size() {
        return this.projClassType.size();
    }

    /**
     * 呼び出しスタックを遡り、最初に見つかった登録済み弾クラスの id を返す。
     *
     * @return 見つかった弾クラスの登録 id。見つからない/例外なら {@code null}
     */
    public String resolve() {
        if (this.projClassType.isEmpty()) {
            return null;
        }
        try {
            // walk の中で findFirst する。**全フレームを配列に落とさない**
            return this.stackWalker.walk(frames -> frames
                    .map(StackWalker.StackFrame::getDeclaringClass)
                    .map(this::lookup)
                    .filter(Objects::nonNull)
                    .findFirst()
                    .orElse(null));
        } catch (Throwable ignored) {
            return null;   // 記録がゲーム本体を巻き込まない
        }
    }

    /**
     * そのクラス（またはその親）が台帳に居れば登録 id を返す。
     *
     * <p><b>未登録は例外ではなく正常な不一致経路</b> —— {@code null} を返すのが契約であり、
     * {@link #resolve()} の {@code catch (Throwable)} はここを通らない。
     */
    public String lookup(Class<?> c) {
        String exact = this.projClassType.get(c);
        if (exact != null) {
            return exact;
        }
        for (Map.Entry<Class<?>, String> en : this.projClassType.entrySet()) {
            if (en.getKey().isAssignableFrom(c)) {
                return en.getValue();
            }
        }
        return null;
    }
}
