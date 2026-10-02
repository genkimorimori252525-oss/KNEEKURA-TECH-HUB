package org.kneekura.bedrockwither.gametest;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.WitherSkeleton;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;
import org.kneekura.bedrockwither.entity.BedrockWitherState;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;
import org.kneekura.bedrockwither.registry.ModEntities;

import java.util.UUID;

@GameTestHolder(BedrockWitherMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BedrockWitherGameTests {
    private BedrockWitherGameTests() {
    }

    @GameTest(template = "empty", timeoutTicks = 40)
    public static void officialEntitySurface(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);

        helper.runAfterDelay(1, () -> {
            assertClose(helper, 1.0F, wither.getBbWidth(), "Bedrock collision width");
            assertClose(helper, 3.0F, wither.getBbHeight(), "Bedrock collision height");
            assertClose(helper, 70.0D, wither.getAttributeValue(Attributes.FOLLOW_RANGE), "Bedrock follow range");
            assertClose(helper, 0.6D, wither.getAttributeValue(Attributes.MOVEMENT_SPEED), "Bedrock native runtime movement speed");
            assertClose(helper, 0.6D, wither.getAttributeValue(Attributes.FLYING_SPEED), "Bedrock native runtime flying speed");

            if (BedrockWitherEntity.maxHealthForDifficulty(net.minecraft.world.Difficulty.EASY) != 300.0D
                    || BedrockWitherEntity.maxHealthForDifficulty(net.minecraft.world.Difficulty.NORMAL) != 450.0D
                    || BedrockWitherEntity.maxHealthForDifficulty(net.minecraft.world.Difficulty.HARD) != 600.0D) {
                helper.fail("Bedrock difficulty health mapping is not 300/450/600");
                return;
            }

            if (wither.getMobType() != net.minecraft.world.entity.MobType.UNDEAD) {
                helper.fail("Bedrock type_family should map Wither to MobType.UNDEAD");
                return;
            }
            if (wither.getBedrockState() != BedrockWitherState.SPAWN_SEQUENCE) {
                helper.fail("Expected initial reconstruction state SPAWN_SEQUENCE");
                return;
            }
            if (wither.runtimeState().headCount() != 3) {
                helper.fail("Expected three BDS-style head runtime slots");
                return;
            }
            helper.succeed();
        });
    }

    @GameTest(template = "empty", timeoutTicks = 40)
    public static void undeadDamageIsRejected(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);
        WitherSkeleton attacker = EntityType.WITHER_SKELETON.create(helper.getLevel());
        if (attacker == null) {
            helper.fail("Failed to create Wither Skeleton attacker");
            return;
        }

        BlockPos attackerPos = helper.absolutePos(new BlockPos(0, 1, 0));
        attacker.moveTo(attackerPos.getX() + 0.5D, attackerPos.getY(), attackerPos.getZ() + 0.5D);
        helper.getLevel().addFreshEntity(attacker);

        float before = wither.getHealth();
        boolean accepted = wither.hurt(helper.getLevel().damageSources().mobAttack(attacker), 10.0F);

        if (accepted) {
            helper.fail("Bedrock damage_sensor contract should reject undead-source damage");
            return;
        }
        if (Math.abs(wither.getHealth() - before) > 0.0001F) {
            helper.fail("Undead-source damage changed Wither health");
            return;
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40)
    public static void threeAlternativeHeadTargetsAreIndependent(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);
        UUID first = UUID.randomUUID();
        UUID second = UUID.randomUUID();
        UUID third = UUID.randomUUID();

        wither.setAlternativeHeadTarget(0, first);
        wither.setAlternativeHeadTarget(1, second);
        wither.setAlternativeHeadTarget(2, third);

        if (!wither.getAlternativeHeadTarget(0).filter(first::equals).isPresent()) {
            helper.fail("Head 0 target did not round-trip");
            return;
        }
        if (!wither.getAlternativeHeadTarget(1).filter(second::equals).isPresent()) {
            helper.fail("Head 1 target did not round-trip");
            return;
        }
        if (!wither.getAlternativeHeadTarget(2).filter(third::equals).isPresent()) {
            helper.fail("Head 2 target did not round-trip");
            return;
        }

        wither.clearAlternativeHeadTarget(1);
        if (wither.getAlternativeHeadTarget(1).isPresent()) {
            helper.fail("Head 1 target clear did not remain independent");
            return;
        }
        if (wither.getAlternativeHeadTarget(0).isEmpty() || wither.getAlternativeHeadTarget(2).isEmpty()) {
            helper.fail("Clearing head 1 changed another head target");
            return;
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40)
    public static void skullKindsRemainDistinct(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);
        Vec3 origin = wither.position().add(0.0D, 2.0D, 0.0D);

        BedrockWitherSkullEntity normal = BedrockWitherSkullEntity.create(
                helper.getLevel(),
                wither,
                origin,
                new Vec3(1.0D, 0.0D, 0.0D),
                BedrockWitherSkullEntity.Kind.NORMAL
        );
        BedrockWitherSkullEntity dangerous = BedrockWitherSkullEntity.create(
                helper.getLevel(),
                wither,
                origin,
                new Vec3(1.0D, 0.0D, 0.0D),
                BedrockWitherSkullEntity.Kind.DANGEROUS
        );

        if (normal.isDangerous()) {
            helper.fail("Normal Bedrock skull was marked dangerous");
            return;
        }
        if (!dangerous.isDangerous()) {
            helper.fail("Dangerous Bedrock skull lost dangerous identity");
            return;
        }
        if (normal.isPickable()) {
            helper.fail("Normal Bedrock skull should not expose reflect_on_hurt");
            return;
        }
        if (!dangerous.isPickable()) {
            helper.fail("Dangerous Bedrock skull should expose reflect_on_hurt");
            return;
        }

        assertClose(helper, 0.15F, normal.getBbWidth(), "Normal skull collision width");
        assertClose(helper, 0.15F, dangerous.getBbWidth(), "Dangerous skull collision width");

        net.minecraft.core.BlockPos resistancePos = helper.absolutePos(new BlockPos(0, 0, 0));
        net.minecraft.world.level.block.state.BlockState obsidian =
                net.minecraft.world.level.block.Blocks.OBSIDIAN.defaultBlockState();
        float sourceResistance = 1200.0F;

        float normalResistance = normal.getBlockExplosionResistance(
                null,
                helper.getLevel(),
                resistancePos,
                obsidian,
                obsidian.getFluidState(),
                sourceResistance
        );
        float dangerousResistance = dangerous.getBlockExplosionResistance(
                null,
                helper.getLevel(),
                resistancePos,
                obsidian,
                obsidian.getFluidState(),
                sourceResistance
        );

        assertClose(helper, sourceResistance, normalResistance, "Normal skull explosion resistance");
        assertClose(helper, 0.8F, dangerousResistance, "Dangerous skull Java-equivalent resistance cap");

        net.minecraft.world.level.block.state.BlockState bedrock =
                net.minecraft.world.level.block.Blocks.BEDROCK.defaultBlockState();
        float dangerousBedrockResistance = dangerous.getBlockExplosionResistance(
                null,
                helper.getLevel(),
                resistancePos,
                bedrock,
                bedrock.getFluidState(),
                sourceResistance
        );
        assertClose(
                helper,
                sourceResistance,
                dangerousBedrockResistance,
                "Dangerous skull must not cap Bedrock resistance"
        );
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40)
    public static void centerHeadSequenceIsThreeNormalThenDangerous(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);

        BedrockWitherSkullEntity.Kind[] expected = {
                BedrockWitherSkullEntity.Kind.NORMAL,
                BedrockWitherSkullEntity.Kind.NORMAL,
                BedrockWitherSkullEntity.Kind.NORMAL,
                BedrockWitherSkullEntity.Kind.DANGEROUS,
                BedrockWitherSkullEntity.Kind.NORMAL
        };

        for (int i = 0; i < expected.length; i++) {
            BedrockWitherSkullEntity.Kind actual = wither.attackController().nextCenterSkullKind();
            if (actual != expected[i]) {
                helper.fail("Center-head projectile " + (i + 1)
                        + " expected " + expected[i] + " but was " + actual);
                return;
            }
        }

        if (wither.runtimeState().projectileCounter() != expected.length) {
            helper.fail("Projectile counter did not retain the Bedrock volley sequence state");
            return;
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 80)
    public static void halfHealthTransitionIsOneShotAndProjectileImmune(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);

        helper.runAfterDelay(2, () -> {
            int threshold = wither.runtimeState().healthThreshold();
            if (threshold <= 0) {
                helper.fail("Difficulty health initialization did not establish half-health threshold");
                return;
            }

            wither.setHealth(threshold);

            helper.runAfterDelay(2, () -> {
                if (wither.runtimeState().nativePhase()
                        != org.kneekura.bedrockwither.entity.BedrockWitherPhaseController.secondPhaseNativeId()) {
                    helper.fail("Half-health transition did not enter native phase 0");
                    return;
                }
                if (wither.getBedrockState() != BedrockWitherState.PHASE2_DASH_PREP) {
                    helper.fail("Half-health transition did not reach PHASE2_DASH_PREP");
                    return;
                }
                if (wither.runtimeState().wantsToExplode()) {
                    helper.fail("Transition explosion latch was not cleared");
                    return;
                }

                int expectedSkeletons = switch (helper.getLevel().getDifficulty()) {
                    case PEACEFUL, EASY -> 0;
                    case NORMAL, HARD -> 3;
                };
                if (wither.runtimeState().maxSkeletons() != expectedSkeletons
                        || wither.runtimeState().numSkeletons() != expectedSkeletons) {
                    helper.fail("Half-health skeleton counters expected "
                            + expectedSkeletons + " but were "
                            + wither.runtimeState().numSkeletons() + "/"
                            + wither.runtimeState().maxSkeletons());
                    return;
                }

                int nearbySkeletons = helper.getLevel().getEntitiesOfClass(
                        WitherSkeleton.class,
                        wither.getBoundingBox().inflate(6.0D)
                ).size();
                if (nearbySkeletons < expectedSkeletons) {
                    helper.fail("Expected at least " + expectedSkeletons
                            + " spawned Wither Skeletons but found " + nearbySkeletons);
                    return;
                }

                Arrow arrow = EntityType.ARROW.create(helper.getLevel());
                if (arrow == null) {
                    helper.fail("Failed to create projectile for phase-2 immunity test");
                    return;
                }

                float beforeProjectile = wither.getHealth();
                boolean accepted = wither.hurt(
                        helper.getLevel().damageSources().arrow(arrow, arrow),
                        10.0F
                );
                if (accepted || Math.abs(wither.getHealth() - beforeProjectile) > 0.0001F) {
                    helper.fail("Phase-2 projectile immunity did not reject arrow damage");
                    return;
                }

                // A second phase-controller tick must not replay the transition.
                int beforeCount = wither.runtimeState().numSkeletons();
                wither.phaseController().tick();
                if (wither.runtimeState().numSkeletons() != beforeCount
                        || wither.runtimeState().wantsToExplode()) {
                    helper.fail("Half-health transition replayed after native phase reached 0");
                    return;
                }

                helper.succeed();
            });
        });
    }

    @GameTest(template = "empty", timeoutTicks = 40)
    public static void destructionRangesMatchObservedCuboids(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);

        int hurtVolume = wither.destructionController().candidateBlockCount(1);
        int chargeVolume = wither.destructionController().candidateBlockCount(2);

        if (hurtVolume != 4 * 6 * 4) {
            helper.fail("Range-1 hurt destruction expected 4x6x4=96 positions but got " + hurtVolume);
            return;
        }
        if (chargeVolume != 6 * 8 * 6) {
            helper.fail("Range-2 charge destruction expected 6x8x6=288 positions but got " + chargeVolume);
            return;
        }

        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 60)
    public static void hurtReactionDelayDoesNotResetAndFiresDangerousSkull(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);
        net.minecraft.world.entity.animal.Cow attacker = EntityType.COW.create(helper.getLevel());
        if (attacker == null) {
            helper.fail("Failed to create hurt-reaction attacker");
            return;
        }

        BlockPos attackerPos = helper.absolutePos(new BlockPos(3, 1, 0));
        attacker.moveTo(attackerPos.getX() + 0.5D, attackerPos.getY(), attackerPos.getZ() + 0.5D);
        helper.getLevel().addFreshEntity(attacker);

        helper.runAfterDelay(2, () -> {
            boolean firstAccepted = wither.hurt(
                    helper.getLevel().damageSources().mobAttack(attacker),
                    1.0F
            );
            if (!firstAccepted || wither.runtimeState().destroyBlocksTick() != 20) {
                helper.fail("First phase-1 hit did not arm a 20-tick destroy timer");
                return;
            }

            for (int i = 0; i < 5; i++) {
                wither.hurtReactionController().tick();
            }
            if (wither.runtimeState().destroyBlocksTick() != 15) {
                helper.fail("Manual hurt reaction countdown expected 15 ticks remaining");
                return;
            }

            // Reset vanilla hurt invulnerability only for this deterministic controller test.
            wither.invulnerableTime = 0;
            boolean secondAccepted = wither.hurt(
                    helper.getLevel().damageSources().mobAttack(attacker),
                    1.0F
            );
            if (!secondAccepted) {
                helper.fail("Second deterministic hurt-reaction hit was unexpectedly rejected");
                return;
            }
            if (wither.runtimeState().destroyBlocksTick() != 15) {
                helper.fail("Repeated damage reset the Bedrock hurt-reaction timer");
                return;
            }

            for (int i = 0; i < 15; i++) {
                wither.hurtReactionController().tick();
            }

            if (wither.runtimeState().destroyBlocksTick() != 0) {
                helper.fail("Hurt reaction did not complete after 20 total controller ticks");
                return;
            }

            java.util.List<BedrockWitherSkullEntity> skulls = helper.getLevel().getEntitiesOfClass(
                    BedrockWitherSkullEntity.class,
                    wither.getBoundingBox().inflate(8.0D)
            );
            long dangerousCount = skulls.stream()
                    .filter(BedrockWitherSkullEntity::isDangerous)
                    .count();
            if (dangerousCount != 1L) {
                helper.fail("Hurt reaction expected exactly one dangerous skull but found " + dangerousCount);
                return;
            }

            helper.succeed();
        });
    }

    @GameTest(template = "empty", timeoutTicks = 80)
    public static void dashExecutionLastsExactlyTwentyControllerTicks(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);

        helper.runAfterDelay(2, () -> {
            // Put the boss directly into the accepted native second-phase identity.
            wither.runtimeState().setNativePhase(
                    org.kneekura.bedrockwither.entity.BedrockWitherPhaseController.secondPhaseNativeId()
            );
            wither.setBedrockState(BedrockWitherState.PHASE2_DASH_PREP);

            // Speed remains a measurement-gated value. Zero is deliberate here:
            // this test validates the Bedrock duration/state/destruction loop only.
            wither.dashController().beginMeasuredDash(new Vec3(1.0D, 0.0D, 0.0D), 0.0D);

            if (!wither.runtimeState().charging()
                    || wither.runtimeState().chargeFrames() != 20
                    || wither.getBedrockState() != BedrockWitherState.PHASE2_DASH) {
                helper.fail("Dash did not initialize the 20-tick Bedrock execution state");
                return;
            }

            for (int i = 0; i < 19; i++) {
                wither.dashController().tick();
            }

            if (!wither.runtimeState().charging()
                    || wither.runtimeState().chargeFrames() != 1) {
                helper.fail("Dash ended before the twentieth controller tick");
                return;
            }

            wither.dashController().tick();

            if (wither.runtimeState().charging()
                    || wither.runtimeState().chargeFrames() != 0
                    || wither.getBedrockState() != BedrockWitherState.PHASE2_RECOVER) {
                helper.fail("Dash did not end exactly after twenty controller ticks");
                return;
            }

            helper.succeed();
        });
    }

    @GameTest(template = "empty", timeoutTicks = 40)
    public static void statusEffectsAllowOnlyInstantHealAndHarm(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);

        if (!wither.canBeAffected(new net.minecraft.world.effect.MobEffectInstance(
                net.minecraft.world.effect.MobEffects.HEAL, 1, 0
        ))) {
            helper.fail("Bedrock Wither should allow Instant Health processing");
            return;
        }
        if (!wither.canBeAffected(new net.minecraft.world.effect.MobEffectInstance(
                net.minecraft.world.effect.MobEffects.HARM, 1, 0
        ))) {
            helper.fail("Bedrock Wither should allow Instant Damage processing");
            return;
        }
        if (wither.canBeAffected(new net.minecraft.world.effect.MobEffectInstance(
                net.minecraft.world.effect.MobEffects.POISON, 200, 0
        ))) {
            helper.fail("Bedrock Wither should reject ordinary status effects");
            return;
        }

        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 80)
    public static void centerVolleyUsesFireRateThenSevenSecondCooldown(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);
        net.minecraft.world.entity.animal.Cow target = EntityType.COW.create(helper.getLevel());
        if (target == null) {
            helper.fail("Failed to create volley target");
            return;
        }

        BlockPos targetPos = helper.absolutePos(new BlockPos(4, 1, 0));
        target.moveTo(targetPos.getX() + 0.5D, targetPos.getY(), targetPos.getZ() + 0.5D);
        helper.getLevel().addFreshEntity(target);

        helper.runAfterDelay(2, () -> {
            wither.setTarget(target);

            if (wither.runtimeState().fireRate()
                    != org.kneekura.bedrockwither.entity.BedrockWitherVolleyController.PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS) {
                helper.fail("Volley controller did not initialize provisional native fireRate=20");
                return;
            }

            // REPOSITION -> BURST without consuming a firing tick.
            wither.volleyController().tick();
            if (wither.getBedrockState() != BedrockWitherState.PHASE1_BURST) {
                helper.fail("Target acquisition did not enter PHASE1_BURST");
                return;
            }

            for (int shot = 0; shot < 4; shot++) {
                int cadence = wither.runtimeState().fireRate();
                for (int tick = 0; tick < cadence; tick++) {
                    wither.volleyController().tick();
                }
            }

            if (wither.runtimeState().projectileCounter() != 4) {
                helper.fail("Expected projectileCounter=4 after one Bedrock center volley");
                return;
            }
            if (wither.getBedrockState() != BedrockWitherState.PHASE1_COOLDOWN) {
                helper.fail("Fourth/dangerous projectile did not enter PHASE1_COOLDOWN");
                return;
            }
            if (wither.runtimeState().mainHeadAttackCountdown()
                    != org.kneekura.bedrockwither.entity.BedrockWitherVolleyController.OBSERVED_INTER_VOLLEY_COOLDOWN_TICKS) {
                helper.fail("Inter-volley cooldown was not armed to 140 ticks");
                return;
            }

            java.util.List<BedrockWitherSkullEntity> skulls = helper.getLevel().getEntitiesOfClass(
                    BedrockWitherSkullEntity.class,
                    wither.getBoundingBox().inflate(12.0D)
            );
            long dangerous = skulls.stream().filter(BedrockWitherSkullEntity::isDangerous).count();
            long normal = skulls.size() - dangerous;
            if (normal != 3L || dangerous != 1L) {
                helper.fail("Expected 3 normal + 1 dangerous center skull, found "
                        + normal + " normal / " + dangerous + " dangerous");
                return;
            }

            for (int tick = 0;
                 tick < org.kneekura.bedrockwither.entity.BedrockWitherVolleyController.OBSERVED_INTER_VOLLEY_COOLDOWN_TICKS - 1;
                 tick++) {
                wither.volleyController().tick();
            }
            if (wither.getBedrockState() != BedrockWitherState.PHASE1_COOLDOWN
                    || wither.runtimeState().mainHeadAttackCountdown() != 1) {
                helper.fail("Volley cooldown ended before 140 controller ticks");
                return;
            }

            wither.volleyController().tick();
            if (wither.getBedrockState() != BedrockWitherState.PHASE1_BURST
                    || wither.runtimeState().mainHeadAttackCountdown() != wither.runtimeState().fireRate()) {
                helper.fail("Volley cooldown did not re-arm the next burst after 140 ticks");
                return;
            }

            helper.succeed();
        });
    }

    @GameTest(template = "empty", timeoutTicks = 60)
    public static void damageIntervalHalvesHistoricalNativeFireRate(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);

        helper.runAfterDelay(2, () -> {
            int initialRate = wither.runtimeState().fireRate();
            int interval = wither.runtimeState().healthIntervals();
            int lastHealth = wither.runtimeState().lastHealthValue();

            if (initialRate != 20 || interval <= 0 || lastHealth <= 0) {
                helper.fail("Volley health-interval state did not initialize");
                return;
            }

            wither.setHealth(Math.max(1.0F, lastHealth - interval - 1.0F));
            wither.volleyController().onAcceptedDamage();

            switch (helper.getLevel().getDifficulty()) {
                case PEACEFUL, EASY -> {
                    if (wither.runtimeState().fireRate() != initialRate) {
                        helper.fail("Easy/Peaceful should not apply the historical fire-rate speedup");
                        return;
                    }
                }
                case NORMAL, HARD -> {
                    if (wither.runtimeState().fireRate() != 10) {
                        helper.fail("Crossing one historical health interval should halve fireRate 20 -> 10");
                        return;
                    }
                    if (wither.runtimeState().lastHealthValue() != lastHealth - interval) {
                        helper.fail("Health interval cursor did not advance by exactly one interval");
                        return;
                    }
                }
            }

            helper.succeed();
        });
    }

    private static BedrockWitherEntity createWither(GameTestHelper helper) {
        BedrockWitherEntity wither = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (wither == null) {
            helper.fail("Failed to create KNEEKURA Bedrock Wither");
            throw new IllegalStateException("GameTest failure already recorded");
        }

        BlockPos pos = helper.absolutePos(new BlockPos(0, 1, 0));
        wither.moveTo(pos.getX() + 0.5D, pos.getY(), pos.getZ() + 0.5D);
        helper.getLevel().addFreshEntity(wither);
        return wither;
    }

    private static void assertClose(GameTestHelper helper, double expected, double actual, String label) {
        if (Math.abs(expected - actual) > 0.0001D) {
            helper.fail(label + " expected " + expected + " but was " + actual);
        }
    }
}
