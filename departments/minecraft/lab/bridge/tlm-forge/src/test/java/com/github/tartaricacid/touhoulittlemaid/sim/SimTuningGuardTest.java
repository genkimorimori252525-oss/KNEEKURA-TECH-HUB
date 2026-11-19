package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.tuning.SimTuning;
import org.junit.After;
import org.junit.Test;

import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * {@link SimTuning} の「本番無改変」保証。world 非依存なので通常の JUnit で回る
 * (既存の {@code AmuletCountSelectorTest} と同じスタイル)。
 *
 * <p>このテストが守るのは 1 点だけ: <b>sim を起動していない通常のゲームでは、
 * ノブを通した定数が既定値と完全に一致する</b>。これが崩れると SimLab は
 * 「検証のために本番を壊す道具」になり、存在価値が消える。
 */
public class SimTuningGuardTest {

    @After
    public void tearDown() {
        SimTuning.clear();
    }

    @Test
    public void inactiveByDefault() {
        SimTuning.clear();
        assertFalse("apply() 前は非活性であること", SimTuning.active());
    }

    @Test
    public void inactiveReturnsDefaultsExactly() {
        SimTuning.clear();
        assertEquals(12.5D, SimTuning.d("reimu.amulet.spread_deg", 12.5D), 0.0D);
        assertEquals(16, SimTuning.i("reimu.amulet.cooldown", 16));
        assertEquals(1.4F, SimTuning.f("reimu.amulet.speed", 1.4F), 0.0F);
    }

    @Test
    public void emptyOverridesStayInactive() {
        SimTuning.apply(new HashMap<>());
        assertFalse("空 Map では活性化しない", SimTuning.active());
        assertEquals(12.5D, SimTuning.d("reimu.amulet.spread_deg", 12.5D), 0.0D);
    }

    @Test
    public void unknownKeyFallsBackToDefaultWhileActive() {
        Map<String, Double> m = new HashMap<>();
        m.put("some.other.knob", 99.0D);
        SimTuning.apply(m);
        assertTrue(SimTuning.active());
        assertEquals("載っていないキーは既定値のまま", 12.5D,
                SimTuning.d("reimu.amulet.spread_deg", 12.5D), 0.0D);
    }

    @Test
    public void appliedOverrideWins() {
        Map<String, Double> m = new HashMap<>();
        m.put("reimu.amulet.spread_deg", 18.0D);
        m.put("reimu.amulet.cooldown", 24.0D);
        SimTuning.apply(m);
        assertEquals(18.0D, SimTuning.d("reimu.amulet.spread_deg", 12.5D), 0.0D);
        assertEquals("JSON の数値は double で来るので int へ丸める", 24,
                SimTuning.i("reimu.amulet.cooldown", 16));
    }

    @Test
    public void clearRestoresDefaults() {
        Map<String, Double> m = new HashMap<>();
        m.put("reimu.amulet.spread_deg", 18.0D);
        SimTuning.apply(m);
        SimTuning.clear();
        assertFalse(SimTuning.active());
        assertEquals(12.5D, SimTuning.d("reimu.amulet.spread_deg", 12.5D), 0.0D);
    }
}
