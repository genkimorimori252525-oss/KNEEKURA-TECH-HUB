package org.kneekura.probe;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.level.block.Blocks;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

/** Disposable integration probe, not an example of autonomous entity AI. */
@Mod("kneekura_probe")
@GameTestHolder("kneekura_probe")
@PrefixGameTestTemplate(false)
public final class ProbeMod {
    @GameTest(template="empty", timeoutTicks=1200)
    public static void bridge(GameTestHelper helper) {
        // The external host observes and mutates the real server through the production bridge.
        helper.startSequence().thenWaitUntil(() -> {
            var level=helper.getLevel();
            helper.assertTrue(level.getBlockState(new BlockPos(0,80,1)).is(Blocks.EMERALD_BLOCK),
                              "Waiting for registered observer finish command");
            var objective=level.getScoreboard().getObjective("kneekura");
            helper.assertTrue(objective!=null,"Missing command-created objective");
            helper.assertTrue(level.getScoreboard().getOrCreatePlayerScore("probe",objective).getScore()==1,
                              "Idempotent command executed more than once");
        }).thenIdle(20).thenSucceed();
    }

    @GameTest(template="empty", required=false, timeoutTicks=40)
    public static void knownbad(GameTestHelper helper) {
        helper.assertTrue(false,"Intentional negative control: must remain an optional FAIL");
    }
}
