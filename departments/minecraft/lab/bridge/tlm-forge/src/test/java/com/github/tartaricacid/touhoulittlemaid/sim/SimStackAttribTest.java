package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimStackAttrib;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

/**
 * {@link SimStackAttrib} —— magic ソース被弾の技帰属（{@code attrib="stack"}）を支える走査。
 *
 * <p><b>この試験が覆う範囲と、覆わない範囲</b>（10-02-PLAN の artifacts に対する正直な差分）:
 * 覆うのは<b>解決部分だけ</b>である。統合（{@code SimArena.onDamage} が実際に
 * {@code attrib="stack"} と {@code projType} を書くこと）は、{@code SimArena} が
 * {@code ServerLevel}/{@code DamageSource} を直接持つため JUnit に載らず、
 * <b>自動テストでは検査されていない</b>。その根拠は 2026-08-20 の実機実測
 * （コミット {@code bfea153b}、帰属不能が 12% まで低下）1回のみ。
 */
public class SimStackAttribTest {

    private static final String CHILD_ID = "touhou_little_maid:reimu_kakusan_ofuda_child";
    private static final String PARENT_ID = "touhou_little_maid:reimu_kakusan_ofuda_parent";

    /**
     * 代役の弾。<b>自分のメソッドの中から</b> {@code resolve()} を呼ぶ ——
     * 実際の弾が {@code hurt()} を呼ぶのと同じ位置にフレームを作るため。
     */
    static class FakeBullet {
        String fire(SimStackAttrib attrib) {
            return attrib.resolve();
        }
    }

    /** 親クラスだけを台帳に載せ、子のフレームから引く（{@code isAssignableFrom} の枝）。 */
    static class FakeParentBullet {
        String fire(SimStackAttrib attrib) {
            return attrib.resolve();
        }
    }

    /**
     * {@code fire} を<b>override する</b>ことが要点 —— そうしないとフレームの宣言クラスが
     * 親になり、完全一致の枝を通ってしまって継承の枝を検査できない。
     */
    static class FakeChildBullet extends FakeParentBullet {
        @Override
        String fire(SimStackAttrib attrib) {
            return attrib.resolve();
        }
    }

    /** 台帳に一度も載らない、スタックにも現れないクラス。 */
    static class FakeUnrelated {
    }

    // =========================================================================
    // 解決できる場合
    // =========================================================================

    @Test
    public void resolveFindsTheRegisteredClassThatIsOnTheStack() {
        SimStackAttrib attrib = new SimStackAttrib();
        attrib.register(FakeBullet.class, CHILD_ID);

        assertEquals("自分のフレームから引けば登録 id が返る", CHILD_ID, new FakeBullet().fire(attrib));
    }

    @Test
    public void resolveFindsARegisteredSuperclassFromASubclassFrame() {
        SimStackAttrib attrib = new SimStackAttrib();
        attrib.register(FakeParentBullet.class, PARENT_ID);   // 子は登録していない

        assertEquals("親だけ登録されていても子のフレームから引ける",
                PARENT_ID, new FakeChildBullet().fire(attrib));
    }

    @Test
    public void lookupPrefersTheExactMatchOverAnAssignableOne() {
        SimStackAttrib attrib = new SimStackAttrib();
        attrib.register(FakeParentBullet.class, PARENT_ID);
        attrib.register(FakeChildBullet.class, CHILD_ID);

        assertEquals("完全一致が継承より先", CHILD_ID, attrib.lookup(FakeChildBullet.class));
        assertEquals(PARENT_ID, attrib.lookup(FakeParentBullet.class));
    }

    // =========================================================================
    // 解決できない場合 —— **例外ではなく null が契約**
    // =========================================================================

    @Test
    public void lookupReturnsNullForAnUnregisteredClass() {
        SimStackAttrib attrib = new SimStackAttrib();
        attrib.register(FakeBullet.class, CHILD_ID);

        // これは正常な不一致経路であり、resolve() の catch (Throwable) は通らない。
        assertNull("未登録クラスは null（例外にしない）", attrib.lookup(FakeUnrelated.class));
    }

    @Test
    public void resolveReturnsNullWhenTheLedgerIsEmpty() {
        SimStackAttrib attrib = new SimStackAttrib();

        assertTrue(attrib.isEmpty());
        assertNull("台帳が空なら走査もしない", new FakeBullet().fire(attrib));
    }

    @Test
    public void resolveReturnsNullWhenNoRegisteredClassIsOnTheStack() {
        SimStackAttrib attrib = new SimStackAttrib();
        attrib.register(FakeUnrelated.class, "touhou_little_maid:never_on_this_stack");

        // **帰属できないときに嘘の id を返さない。** これが壊れると SimArena 側は
        // attrib="none" ではなく誤った技の行へダメージを載せる。
        assertNull(new FakeBullet().fire(attrib));
    }

    // =========================================================================
    // 台帳
    // =========================================================================

    @Test
    public void registerIsIdempotentPerClass() {
        SimStackAttrib attrib = new SimStackAttrib();
        attrib.register(FakeBullet.class, CHILD_ID);
        attrib.register(FakeBullet.class, CHILD_ID);

        assertEquals("同じクラスの再登録で台帳は増えない", 1, attrib.size());
        assertEquals(CHILD_ID, new FakeBullet().fire(attrib));
    }
}
