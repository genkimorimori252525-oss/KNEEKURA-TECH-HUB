package org.kneekura.bedrockwither.gametest;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.BedrockWitherAttackType;
import org.kneekura.bedrockwither.entity.BedrockWitherBlockRules;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;
import org.kneekura.bedrockwither.registry.ModEntities;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import java.util.function.Consumer;

@GameTestHolder(BedrockWitherMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BedrockWitherLifecycleCompletionGameTests {
    private BedrockWitherLifecycleCompletionGameTests() {}

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_deathnativephase")
    public static void acceptedFirstPhaseDeathUsesNativePhaseZero(GameTestHelper helper) {
        withBoss(helper, boss -> {
            helper.assertTrue(boss.runtimeState().nativePhase() == 1, "Fixture starts in native phase 1");
            kill(helper, boss);
            helper.assertTrue(boss.runtimeState().nativePhase() == 0,
                    "Accepted first-phase death must expose documented native phase 0");
            CompoundTag saved = new CompoundTag();
            boss.saveWithoutId(saved);
            // Migrate an earlier product save carrying the previous phase-1 death bug.
            saved.putInt("NativePhase", 1);
            BedrockWitherEntity restored = requireBoss(helper);
            try {
                restored.load(saved);
                helper.assertTrue(restored.runtimeState().nativePhase() == 0,
                        "Reloading an older death save must normalize native phase 0");
                int remaining = restored.getDeathTicksRemaining();
                restored.tick();
                helper.assertTrue(restored.getDeathTicksRemaining() == remaining - 1,
                        "Ordinary entity tick must advance restored semantic death");
            } finally {
                restored.discard();
            }
        });
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_deathstopsmomentum")
    public static void acceptedDeathStopsResidualCombatMomentum(GameTestHelper helper) {
        withBoss(helper, boss -> {
            boss.setDeltaMovement(new Vec3(0.7D, -0.2D, 0.4D));
            kill(helper, boss);
            helper.assertTrue(boss.getDeltaMovement().lengthSqr() == 0.0D,
                    "Accepted death must cancel residual combat momentum");
            Vec3 position = boss.position();
            boss.tick();
            helper.assertTrue(boss.position().distanceToSqr(position) < 1.0E-8D,
                    "Ordinary death ticking must not continue the previous combat movement");
        });
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_deathflickerpersistence")
    public static void historicalDeathFlickerProgressesAcrossRealEntityReload(GameTestHelper helper) {
        withBoss(helper, boss -> {
            kill(helper, boss);
            helper.assertTrue(boss.getDeathShieldFlicker() == 15,
                    "Historical death flicker starts with an explicit 15-tick divisor");
            helper.assertTrue(boss.isPowered(), "Death starts with the powered armor visible");
            for (int i = 0; i < 5; i++) boss.tick();
            helper.assertTrue(boss.getDeathTicksRemaining() == 195
                            && boss.getDeathShieldFlicker() == 14 && !boss.isPowered(),
                    "At remaining 195, historical divisor toggles armor and decreases to 14");
            CompoundTag saved = new CompoundTag();
            boss.saveWithoutId(saved);
            BedrockWitherEntity restored = requireBoss(helper);
            try {
                restored.load(saved);
                helper.assertTrue(restored.getDeathShieldFlicker() == 14 && !restored.isPowered(),
                        "Death reload must preserve the armor flicker phase and divisor");
                for (int i = 0; i < 13; i++) restored.tick();
                helper.assertTrue(restored.getDeathTicksRemaining() == 182
                                && restored.getDeathShieldFlicker() == 13 && restored.isPowered(),
                        "Reloaded death must advance its next historical flicker at remaining 182");
            } finally {
                restored.discard();
            }
        });
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_chargeobsidianexception")
    public static void chargeObsidianRuleDiffersFromDangerousProjectile(GameTestHelper helper) {
        BlockPos pos = helper.absolutePos(BlockPos.ZERO);
        helper.assertTrue(!BedrockWitherBlockRules.canDestroy(helper.getLevel(), pos,
                        Blocks.OBSIDIAN.defaultBlockState(), BedrockWitherAttackType.CHARGE),
                "Documented Bedrock charge cannot destroy obsidian");
        helper.assertTrue(BedrockWitherBlockRules.canDestroy(helper.getLevel(), pos,
                        Blocks.OBSIDIAN.defaultBlockState(), BedrockWitherAttackType.PROJECTILE),
                "Dangerous skull must retain its distinct obsidian destruction eligibility");
        helper.assertTrue(BedrockWitherBlockRules.canDestroy(helper.getLevel(), pos,
                        Blocks.STONE.defaultBlockState(), BedrockWitherAttackType.CHARGE),
                "The charge exception must not disable ordinary terrain destruction");
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_netherstarlifetime")
    public static void actualNetherStarLootDoesNotAgeOutAfterReload(GameTestHelper helper) {
        withBoss(helper, boss -> {
            kill(helper, boss);
            var stars = helper.getLevel().getEntitiesOfClass(ItemEntity.class,
                    boss.getBoundingBox().inflate(4.0D),
                    item -> item.getItem().is(net.minecraft.world.item.Items.NETHER_STAR));
            helper.assertTrue(stars.size() == 1, "Actual death must create exactly one star fixture");
            ItemEntity star = stars.get(0);
            star.setNoGravity(true);
            star.setDeltaMovement(Vec3.ZERO);
            for (int i = 0; i < 6001; i++) star.tick();
            helper.assertTrue(!star.isRemoved(),
                    "Documented Bedrock Nether Star loot must not use ordinary Java timed despawning");
            CompoundTag saved = new CompoundTag();
            star.saveWithoutId(saved);
            ItemEntity restored = new ItemEntity(helper.getLevel(), star.getX(), star.getY(), star.getZ(),
                    star.getItem().copy());
            try {
                restored.load(saved);
                restored.setNoGravity(true);
                restored.setDeltaMovement(Vec3.ZERO);
                for (int i = 0; i < 6001; i++) restored.tick();
                helper.assertTrue(!restored.isRemoved(),
                        "Nether Star unlimited lifetime must survive actual item NBT restoration");
            } finally {
                restored.discard();
            }
        });
    }

    private static BedrockWitherEntity requireBoss(GameTestHelper helper) {
        BedrockWitherEntity boss = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (boss == null) throw new IllegalStateException("Failed to create Wither fixture");
        boss.setNoAi(true);
        BlockPos origin = helper.absolutePos(new BlockPos(0, 64, 0));
        boss.setPos(origin.getX() + 0.5D, origin.getY(), origin.getZ() + 0.5D);
        return boss;
    }

    private static void kill(GameTestHelper helper, BedrockWitherEntity boss) {
        boss.hurt(helper.getLevel().damageSources().genericKill(), Float.MAX_VALUE);
        helper.assertTrue(boss.isDeadOrDying() && boss.deathController().isActive(),
                "Actual damage/death path must establish the death fixture");
    }

    private static void withBoss(GameTestHelper helper, Consumer<BedrockWitherEntity> test) {
        BedrockWitherEntity boss = requireBoss(helper);
        AABB bounds = boss.getBoundingBox().inflate(4.0D);
        Set<UUID> existing = new HashSet<>();
        for (ItemEntity item : helper.getLevel().getEntitiesOfClass(ItemEntity.class, bounds)) {
            existing.add(item.getUUID());
        }
        try {
            test.accept(boss);
            helper.succeed();
        } finally {
            boss.discard();
            for (ItemEntity item : helper.getLevel().getEntitiesOfClass(ItemEntity.class, bounds)) {
                if (!existing.contains(item.getUUID())) item.discard();
            }
        }
    }
}
