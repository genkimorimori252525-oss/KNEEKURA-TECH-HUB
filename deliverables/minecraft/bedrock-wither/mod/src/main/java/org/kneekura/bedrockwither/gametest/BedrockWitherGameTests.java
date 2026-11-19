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

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_officialentitysurface")
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
            if (wither.runtimeState().spawningFrames() <= 0
                    || wither.runtimeState().spawningFrames()
                    > org.kneekura.bedrockwither.entity.BedrockWitherSpawnController.CURRENT_SPAWN_DURATION_TICKS) {
                helper.fail("Modern Bedrock spawn countdown was not active");
                return;
            }
            if (wither.runtimeState().headCount() != 3) {
                helper.fail("Expected three BDS-style head runtime slots");
                return;
            }
            helper.succeed();
        });
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_spawnsequenceusesmodern220tickcontract")
    public static void spawnSequenceUsesModern220TickContract(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);

        if (wither.runtimeState().spawningFrames()
                != org.kneekura.bedrockwither.entity.BedrockWitherSpawnController.CURRENT_SPAWN_DURATION_TICKS) {
            helper.fail("New Bedrock Wither did not initialize a 220-tick spawn countdown");
            return;
        }

        net.minecraft.world.entity.animal.Cow attacker = EntityType.COW.create(helper.getLevel());
        if (attacker == null) {
            helper.fail("Failed to create spawn-sequence attacker");
            return;
        }
        BlockPos attackerPos = helper.absolutePos(new BlockPos(8, 1, 0));
        attacker.moveTo(attackerPos.getX() + 0.5D, attackerPos.getY(), attackerPos.getZ() + 0.5D);
        helper.getLevel().addFreshEntity(attacker);

        float before = wither.getHealth();
        boolean acceptedDuringSpawn = wither.hurt(
                helper.getLevel().damageSources().mobAttack(attacker),
                4.0F
        );
        if (acceptedDuringSpawn || Math.abs(wither.getHealth() - before) > 0.0001F) {
            helper.fail("Spawn sequence did not reject ordinary damage");
            return;
        }

        for (int tick = 0;
             tick < org.kneekura.bedrockwither.entity.BedrockWitherSpawnController.CURRENT_SPAWN_DURATION_TICKS - 1;
             tick++) {
            wither.spawnController().tick();
        }

        if (wither.runtimeState().spawningFrames() != 1
                || wither.getBedrockState() != BedrockWitherState.SPAWN_SEQUENCE) {
            helper.fail("Spawn sequence ended before the 220th controller tick");
            return;
        }

        wither.spawnController().tick();

        if (wither.runtimeState().spawningFrames() != 0
                || wither.getBedrockState() != BedrockWitherState.PHASE1_REPOSITION) {
            helper.fail("Spawn sequence did not complete exactly on the 220th controller tick");
            return;
        }

        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_spawnvisualticksfollowentitydatasnapshots")
    public static void spawnVisualTicksFollowEntityDataSnapshots(GameTestHelper helper) {
        BedrockWitherEntity server = createWither(helper);
        server.setNoAi(true);
        // A fresh replica uses constructor defaults, then receives only normal
        // entity-data snapshots. It never receives the server runtimeState or NBT.
        BedrockWitherEntity replica = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (replica == null) {
            helper.fail("Failed to create entity-data replica");
            return;
        }
        copyInitialEntityData(server, replica);
        if (replica.getVisualInvulnerableTicks() != 220) {
            helper.fail("Initial spawn snapshot lost the visual countdown");
            return;
        }
        for (int tick = 0; tick < 139; tick++) {
            server.spawnController().tick();
        }
        copyInitialEntityData(server, replica);
        if (replica.getVisualInvulnerableTicks() != 81) {
            helper.fail("Mid-spawn entity-data snapshot did not update the visual countdown");
            return;
        }
        net.minecraft.nbt.CompoundTag saved = new net.minecraft.nbt.CompoundTag();
        server.saveWithoutId(saved);
        BedrockWitherEntity restoredServer = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (restoredServer == null) {
            helper.fail("Failed to create mid-spawn saved copy");
            return;
        }
        restoredServer.load(saved);
        BedrockWitherEntity restoredReplica = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (restoredReplica == null) {
            helper.fail("Failed to create restored-spawn replica");
            return;
        }
        copyInitialEntityData(restoredServer, restoredReplica);
        if (restoredReplica.getVisualInvulnerableTicks() != 81) {
            helper.fail("Restored spawn countdown did not reach initial entity data");
            return;
        }
        for (int expected = 80; expected >= 0; expected--) {
            server.spawnController().tick();
            var dirty = server.getEntityData().packDirty();
            if (dirty != null) {
                replica.getEntityData().assignValues(dirty);
            }
            if (replica.getVisualInvulnerableTicks() != expected) {
                helper.fail("Dirty spawn update expected " + expected + " visual ticks");
                return;
            }
        }
        BedrockWitherEntity lateReplica = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (lateReplica == null) {
            helper.fail("Failed to create late-tracking replica");
            return;
        }
        copyInitialEntityData(server, lateReplica);
        if (lateReplica.getVisualInvulnerableTicks() != 0) {
            helper.fail("Late-tracking combat entity retained constructor spawn visuals");
            return;
        }
        helper.succeed();
    }

    private static void copyInitialEntityData(BedrockWitherEntity source, BedrockWitherEntity replica) {
        var initial = source.getEntityData().getNonDefaultValues();
        if (initial != null) {
            replica.getEntityData().assignValues(initial);
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_undeaddamageisrejected")
    public static void undeadDamageIsRejected(GameTestHelper helper) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);
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

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_threealternativeheadtargetsareindependent")
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

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_skullkindsremaindistinct")
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

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_centerheadsequenceisthreenormalthendangerous")
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

    @GameTest(template = "empty", timeoutTicks = 80, batch = "bwr_halfhealthtransitionisoneshotandprojectileimmune")
    public static void halfHealthTransitionIsOneShotAndProjectileImmune(GameTestHelper helper) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);

        helper.runAfterDelay(2, () -> {
            if (!wither.isAerialAttack() || wither.isPowered()) {
                helper.fail("Phase 1 should have AirAttack=1 and powered shield hidden");
                return;
            }

            int threshold = wither.runtimeState().healthThreshold();
            if (threshold <= 0) {
                helper.fail("Difficulty health initialization did not establish half-health threshold");
                return;
            }

            // Current behavior returns to the original firing rate at half health.
            wither.runtimeState().setFireRate(5);
            // Pin this existing controller contract to an already-grounded
            // fixture. The separate ordinary-AI test exercises real descent.
            wither.setNoAi(true);
            wither.setOnGround(true);
            wither.setHealth(threshold);
            wither.phaseController().tick();

            {
                if (wither.runtimeState().nativePhase()
                        != org.kneekura.bedrockwither.entity.BedrockWitherPhaseController.secondPhaseNativeId()) {
                    helper.fail("Half-health transition did not enter native phase 0");
                    return;
                }
                if (wither.isAerialAttack() || !wither.isPowered()) {
                    helper.fail("Phase 2 should have AirAttack=0 and powered shield visible");
                    return;
                }
                if (wither.runtimeState().fireRate()
                        != org.kneekura.bedrockwither.entity.BedrockWitherVolleyController.PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS) {
                    helper.fail("Half-health transition did not reset firing to the original rate");
                    return;
                }
                if (wither.getBedrockState() != BedrockWitherState.PHASE2_BURST) {
                    helper.fail("Half-health transition did not reach PHASE2_BURST");
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
            }
        });
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_destructionrangesmatchobservedcuboids")
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

    @GameTest(template = "empty", timeoutTicks = 60, batch = "bwr_hurtreactiondelaydoesnotresetandfiresdangerousskull")
    public static void hurtReactionDelayDoesNotResetAndFiresDangerousSkull(GameTestHelper helper) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);
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
                    wither.getBoundingBox().inflate(8.0D),
                    skull -> skull.getOwner() == wither
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

    @GameTest(template = "empty", timeoutTicks = 80, batch = "bwr_dashexecutionlastsexactlytwentycontrollerticks")
    public static void dashExecutionLastsExactlyTwentyControllerTicks(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);

        helper.runAfterDelay(2, () -> {
            // This controller fixture explicitly ends spawn before entering
            // phase 2; public dash adapters must not override active spawn/death.
            wither.spawnController().restore(0, BedrockWitherState.PHASE2_DASH_PREP);
            wither.setAerialAttack(false);
            // Put the boss directly into the accepted native second-phase identity.
            wither.runtimeState().setNativePhase(
                    org.kneekura.bedrockwither.entity.BedrockWitherPhaseController.secondPhaseNativeId()
            );
            wither.setBedrockState(BedrockWitherState.PHASE2_DASH_PREP);

            // Zero speed is deliberate in this controller-duration fixture:
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

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_statuseffectsallowonlyinstanthealandharm")
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

    @GameTest(template = "empty", timeoutTicks = 80, batch = "bwr_centervolleyusesfireratethensevensecondcooldown")
    public static void centerVolleyUsesFireRateThenSevenSecondCooldown(GameTestHelper helper) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);
        net.minecraft.world.entity.animal.Cow target = EntityType.COW.create(helper.getLevel());
        if (target == null) {
            helper.fail("Failed to create volley target");
            return;
        }

        BlockPos targetPos = helper.absolutePos(new BlockPos(4, 1, 0));
        target.moveTo(targetPos.getX() + 0.5D, targetPos.getY(), targetPos.getZ() + 0.5D);
        // Other Wither GameTests run in the same GameTest world. Make this
        // controller-test target invulnerable so neighboring bosses/explosions
        // cannot invalidate the target before the synchronous assertion.
        target.setInvulnerable(true);
        helper.getLevel().addFreshEntity(target);

        helper.runAfterDelay(2, () -> {
            // This test drives the volley controller synchronously. Re-establish
            // every precondition here so ambient server AI ticks cannot make the
            // controller-unit assertion nondeterministic.
            wither.specialMovementController().cancelPath();
            wither.runtimeState().setNativePhase(
                    org.kneekura.bedrockwither.entity.BedrockWitherPhaseController.firstPhaseNativeId()
            );
            wither.runtimeState().setSpawningFrames(0);
            wither.spawnController().restore(0, BedrockWitherState.PHASE1_REPOSITION);
            wither.setBedrockState(BedrockWitherState.PHASE1_REPOSITION);
            wither.setTarget(target);

            if (wither.runtimeState().fireRate()
                    != org.kneekura.bedrockwither.entity.BedrockWitherVolleyController.PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS) {
                helper.fail("Volley controller did not initialize provisional native fireRate=20");
                return;
            }

            if (!target.isAlive()) {
                helper.fail("Isolated volley target was not alive before manual controller tick");
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
                    wither.getBoundingBox().inflate(12.0D),
                    skull -> skull.getOwner() == wither
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
            if (wither.getBedrockState() != BedrockWitherState.PHASE1_REPOSITION
                    || !wither.runtimeState().wantsMove()) {
                helper.fail("Volley cooldown did not request the next reposition after 140 ticks");
                return;
            }

            helper.succeed();
        });
    }

    @GameTest(template = "empty", timeoutTicks = 60, batch = "bwr_lasthealthintervaltrackslowesthealthin75pointbuckets")
    public static void lastHealthIntervalTracksLowestHealthIn75PointBuckets(GameTestHelper helper) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);

        helper.runAfterDelay(2, () -> {
            int baseRate = wither.runtimeState().fireRate();
            if (baseRate != org.kneekura.bedrockwither.entity.BedrockWitherVolleyController.PROVISIONAL_NATIVE_BASE_FIRE_RATE_TICKS) {
                helper.fail("Volley controller did not initialize the base fire rate");
                return;
            }

            int maxHealth = Math.round(wither.getMaxHealth());
            int firstLow = Math.max(1, maxHealth - 1);
            wither.setHealth(firstLow);
            wither.volleyController().onAcceptedDamage();

            int expectedFirst = org.kneekura.bedrockwither.entity.BedrockWitherVolleyController
                    .lastHealthIntervalFor(firstLow);
            if (wither.runtimeState().lastHealthValue() != expectedFirst) {
                helper.fail("lastHealthInterval did not track the strict-lower 75-point bucket");
                return;
            }
            if (wither.runtimeState().fireRate() != baseRate) {
                helper.fail("Unmeasured accelerated fire-rate values must not be invented");
                return;
            }

            // Healing must not increase the stored lowest-health interval.
            wither.setHealth(wither.getMaxHealth());
            wither.volleyController().onAcceptedDamage();
            if (wither.runtimeState().lastHealthValue() != expectedFirst) {
                helper.fail("Healing incorrectly increased Bedrock lastHealthInterval");
                return;
            }

            int secondLow = Math.max(1, expectedFirst - 1);
            wither.setHealth(secondLow);
            wither.volleyController().onAcceptedDamage();
            int expectedSecond = org.kneekura.bedrockwither.entity.BedrockWitherVolleyController
                    .lastHealthIntervalFor(secondLow);
            if (wither.runtimeState().lastHealthValue() != expectedSecond) {
                helper.fail("Further damage did not lower lastHealthInterval monotonically");
                return;
            }

            helper.succeed();
        });
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_deathsequencekeepssemanticdeathandextendsremoval")
    public static void deathSequenceKeepsSemanticDeathAndExtendsRemoval(GameTestHelper helper) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);

        boolean accepted = wither.hurt(
                helper.getLevel().damageSources().genericKill(),
                Float.MAX_VALUE
        );

        if (!accepted || !wither.isDeadOrDying()) {
            helper.fail("Killing hit did not enter Java semantic death immediately");
            return;
        }
        if (wither.isRemoved()) {
            helper.fail("Bedrock death sequence removed the boss immediately");
            return;
        }
        if (wither.getBedrockState() != BedrockWitherState.DEATH_SEQUENCE) {
            helper.fail("Killing hit did not enter DEATH_SEQUENCE");
            return;
        }
        if (wither.getDeathTicksRemaining()
                != org.kneekura.bedrockwither.entity.BedrockWitherDeathController.PROVISIONAL_DEATH_DURATION_TICKS) {
            helper.fail("Bedrock death countdown did not initialize to 200 ticks");
            return;
        }

        for (int tick = 0;
             tick < org.kneekura.bedrockwither.entity.BedrockWitherDeathController.PROVISIONAL_DEATH_DURATION_TICKS - 1;
             tick++) {
            wither.deathController().tickServer();
        }

        if (wither.isRemoved()) {
            helper.fail("Bedrock Wither was removed before the final death tick");
            return;
        }
        if (wither.getDeathTicksRemaining() != 1) {
            helper.fail("Death countdown expected one tick remaining");
            return;
        }

        assertClose(
                helper,
                199.0F,
                wither.getDeathSwell(),
                "Historical-corroborated death swell progression"
        );
        assertClose(
                helper,
                0.995F,
                wither.getDeathOverlayAlpha(),
                "Historical-corroborated death overlay progression"
        );

        wither.deathController().tickServer();

        if (!wither.isRemoved()) {
            helper.fail("Bedrock Wither did not remove on the final death tick");
            return;
        }
        if (wither.getDeathTicksRemaining() != 0) {
            helper.fail("Death countdown did not end at zero");
            return;
        }

        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_playerkillpreservesrewardeventsandemitsxponce")
    public static void playerKillPreservesRewardEventsAndEmitsXpOnce(GameTestHelper helper) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);
        wither.setNoAi(true);
        // Own an explicitly high-altitude reward area. A relative +64 placed
        // earlier fixtures near terrain (GameTests originate near world Y=-60)
        // and overlapped ordinary-combat fixtures. Preserve the empty-reward
        // precondition instead of deleting or ignoring another fixture's XP.
        // No world/entity ticks occur inside this synchronous controller fixture.
        wither.setPos(wither.getX(), helper.getLevel().getMaxBuildHeight() - 32.0D, wither.getZ());
        net.minecraft.world.phys.AABB area = wither.getBoundingBox().inflate(16.0D);
        boolean mobLoot = helper.getLevel().getGameRules().getBoolean(net.minecraft.world.level.GameRules.RULE_DOMOBLOOT);
        int existingOrbs = helper.getLevel().getEntitiesOfClass(net.minecraft.world.entity.ExperienceOrb.class, area).size();
        // Ordinary terrain drops are not reward inputs; the final blast can
        // leave them in a reused fixture without affecting either assertion.
        int existingStars = helper.getLevel().getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class, area,
                item -> item.getItem().is(net.minecraft.world.item.Items.NETHER_STAR)).size();
        if (!mobLoot || existingOrbs != 0 || existingStars != 0) {
            wither.discard();
            helper.fail("Reward fixture is not isolated: doMobLoot=" + mobLoot
                    + ", existingOrbs=" + existingOrbs + ", existingStars=" + existingStars);
            return;
        }
        net.minecraft.world.entity.player.Player player = helper.makeMockSurvivalPlayer();
        net.minecraft.world.damagesource.DamageSource source = helper.getLevel().damageSources().playerAttack(player);
        int[] events = {0, 0, 0}; // death, loot, experience
        java.util.function.Consumer<net.minecraftforge.event.entity.living.LivingDeathEvent> death = event -> {
            if (event.getEntity() == wither) {
                events[0]++;
                helper.assertTrue(event.getSource() == source && event.getSource().getEntity() == player
                        && event.getSource().getDirectEntity() == player, "Death event lost player attribution");
            }
        };
        java.util.function.Consumer<net.minecraftforge.event.entity.living.LivingDropsEvent> drops = event -> {
            if (event.getEntity() == wither) {
                events[1]++;
                helper.assertTrue(event.getSource() == source && event.getSource().getEntity() == player
                        && event.isRecentlyHit(), "Loot event lost player attribution");
                int stars = event.getDrops().stream()
                        .filter(item -> item.getItem().is(net.minecraft.world.item.Items.NETHER_STAR))
                        .mapToInt(item -> item.getItem().getCount()).sum();
                helper.assertTrue(stars == 1, "Loot event did not contain exactly one Nether Star");
            }
        };
        java.util.function.Consumer<net.minecraftforge.event.entity.living.LivingExperienceDropEvent> experience = event -> {
            if (event.getEntity() == wither) {
                events[2]++;
                helper.assertTrue(event.getAttackingPlayer() == player, "XP event lost player kill credit");
                helper.assertTrue(event.getOriginalExperience() == 50 && event.getDroppedExperience() == 50,
                        "XP event did not preserve the existing 50-XP contract");
            }
        };
        var bus = net.minecraftforge.common.MinecraftForge.EVENT_BUS;
        bus.addListener(net.minecraftforge.eventbus.api.EventPriority.NORMAL, false,
                net.minecraftforge.event.entity.living.LivingDeathEvent.class, death);
        bus.addListener(net.minecraftforge.eventbus.api.EventPriority.NORMAL, false,
                net.minecraftforge.event.entity.living.LivingDropsEvent.class, drops);
        bus.addListener(net.minecraftforge.eventbus.api.EventPriority.NORMAL, false,
                net.minecraftforge.event.entity.living.LivingExperienceDropEvent.class, experience);
        java.util.Map<UUID, Integer> xpSeen = new java.util.HashMap<>();
        java.util.Map<UUID, Integer> starsSeen = new java.util.HashMap<>();
        int[] emitted = {0, 0};
        long fixtureTick = helper.getLevel().getGameTime();
        try {
            boolean accepted = wither.hurt(source, wither.getMaxHealth() * 10.0F);
            helper.assertTrue(accepted && wither.isDeadOrDying() && wither.getKillCredit() == player,
                    "Player-attributed killing hit lost semantic death or kill credit");
            helper.assertTrue(events[0] == 1 && events[1] == 1 && events[2] == 1,
                    "Initial accepted death did not preserve the three Forge lifecycle events");
            observeRewardEmissions(helper, area, xpSeen, starsSeen, emitted);
            helper.assertTrue(emitted[0] == 50 && emitted[1] == 1,
                    "Actual reward entities did not contain 50 XP and one Nether Star");

            // Forge may repost LivingDeathEvent on repeated die() calls, so its
            // count is not the idempotency invariant. Loot/XP emissions are.
            wither.die(source);
            observeRewardEmissions(helper, area, xpSeen, starsSeen, emitted);
            int duration = org.kneekura.bedrockwither.entity.BedrockWitherDeathController
                    .PROVISIONAL_DEATH_DURATION_TICKS;
            for (int tick = 0; tick < duration; tick++) {
                wither.deathController().tickServer();
                if (tick == 36) {
                    int remaining = wither.getDeathTicksRemaining();
                    wither.die(source);
                    helper.assertTrue(wither.getDeathTicksRemaining() == remaining,
                            "Repeated death restarted the active visual countdown");
                }
                observeRewardEmissions(helper, area, xpSeen, starsSeen, emitted);
            }
            wither.die(source);
            wither.deathController().begin();
            wither.deathController().tickServer();
            observeRewardEmissions(helper, area, xpSeen, starsSeen, emitted);
            helper.assertTrue(wither.isRemoved(), "Reward fixture did not finish visual removal");
            helper.assertTrue(events[1] == 1 && events[2] == 1 && emitted[0] == 50 && emitted[1] == 1,
                    "Repeated death/finalization duplicated loot or experience");
            helper.assertTrue(helper.getLevel().getGameTime() == fixtureTick,
                    "Reward fixture unexpectedly allowed ambient entity ticks");
            helper.succeed();
        } finally {
            bus.unregister(death);
            bus.unregister(drops);
            bus.unregister(experience);
            // XP may already exist when a later loot-listener assertion fails.
            observeRewardEmissions(helper, area, xpSeen, starsSeen, emitted);
            // These identities were observed only in the initially reward-empty
            // area, so cleanup cannot remove another fixture's rewards.
            for (net.minecraft.world.entity.ExperienceOrb orb : helper.getLevel().getEntitiesOfClass(
                    net.minecraft.world.entity.ExperienceOrb.class, area)) {
                if (xpSeen.containsKey(orb.getUUID())) orb.discard();
            }
            for (net.minecraft.world.entity.item.ItemEntity item : helper.getLevel().getEntitiesOfClass(
                    net.minecraft.world.entity.item.ItemEntity.class, area)) {
                if (starsSeen.containsKey(item.getUUID())) item.discard();
            }
            if (!wither.isRemoved()) wither.discard();
        }
    }

    private static void observeRewardEmissions(GameTestHelper helper, net.minecraft.world.phys.AABB area,
                                               java.util.Map<UUID, Integer> xpSeen,
                                               java.util.Map<UUID, Integer> starsSeen, int[] emitted) {
        // Observe positive per-entity changes between synchronous calls rather
        // than counting only survivors of the final explosion. This cannot see
        // an award created and destroyed within one call; ordinary Forge reward
        // duplication is also checked by the event counters. With no ambient
        // ticks, only award() merges XP here; count * value includes its stacks.
        for (net.minecraft.world.entity.ExperienceOrb orb : helper.getLevel().getEntitiesOfClass(
                net.minecraft.world.entity.ExperienceOrb.class, area, entity -> !entity.isRemoved())) {
            net.minecraft.nbt.CompoundTag saved = new net.minecraft.nbt.CompoundTag();
            orb.addAdditionalSaveData(saved);
            int value = orb.getValue() * saved.getInt("Count");
            int previous = xpSeen.getOrDefault(orb.getUUID(), 0);
            emitted[0] += Math.max(0, value - previous);
            xpSeen.put(orb.getUUID(), Math.max(previous, value));
        }
        for (net.minecraft.world.entity.item.ItemEntity item : helper.getLevel().getEntitiesOfClass(
                net.minecraft.world.entity.item.ItemEntity.class, area,
                entity -> !entity.isRemoved() && entity.getItem().is(net.minecraft.world.item.Items.NETHER_STAR))) {
            int value = item.getItem().getCount();
            int previous = starsSeen.getOrDefault(item.getUUID(), 0);
            emitted[1] += Math.max(0, value - previous);
            starsSeen.put(item.getUUID(), Math.max(previous, value));
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_cancelleddeathpreservesaerialstate")
    public static void cancelledDeathPreservesAerialState(GameTestHelper helper) {
        assertCancelledDeathPreservesCombat(helper, false);
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_cancelleddeathpreservesactivedash")
    public static void cancelledDeathPreservesActiveDash(GameTestHelper helper) {
        assertCancelledDeathPreservesCombat(helper, true);
    }

    private static void assertCancelledDeathPreservesCombat(GameTestHelper helper, boolean duringDash) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);
        wither.setNoAi(true);
        if (duringDash) {
            // Own the phase-2 execution fixture; this explicit speed is not a
            // claim about the unresolved current Bedrock dash speed.
            wither.runtimeState().setNativePhase(
                    org.kneekura.bedrockwither.entity.BedrockWitherPhaseController.secondPhaseNativeId());
            wither.setAerialAttack(false);
            wither.dashController().beginMeasuredDash(new Vec3(1.0D, 0.0D, 0.0D), 0.5D);
        }
        BedrockWitherState beforeState = wither.getBedrockState();
        boolean beforeAerial = wither.isAerialAttack();
        boolean beforeCharging = wither.runtimeState().charging();
        int beforeChargeFrames = wither.runtimeState().chargeFrames();
        int[] cancellations = {0};
        java.util.function.Consumer<net.minecraftforge.event.entity.living.LivingDeathEvent> revival = event -> {
            if (event.getEntity() == wither) {
                cancellations[0]++;
                wither.setHealth(32.0F);
                event.setCanceled(true);
            }
        };
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener(
                net.minecraftforge.eventbus.api.EventPriority.NORMAL,
                false,
                net.minecraftforge.event.entity.living.LivingDeathEvent.class,
                revival);
        try {
            wither.hurt(helper.getLevel().damageSources().genericKill(), Float.MAX_VALUE);
        } finally {
            net.minecraftforge.common.MinecraftForge.EVENT_BUS.unregister(revival);
        }
        if (cancellations[0] != 1 || !wither.isAlive() || wither.getHealth() != 32.0F) {
            helper.fail("Scoped Forge revival did not cancel and restore the living entity");
            return;
        }
        if (wither.getDeathTicksRemaining() != 0 || wither.deathController().isActive()
                || wither.getBedrockState() != beforeState
                || wither.isAerialAttack() != beforeAerial
                || wither.runtimeState().charging() != beforeCharging
                || wither.runtimeState().chargeFrames() != beforeChargeFrames) {
            helper.fail("Canceled Forge death committed the custom death state");
            return;
        }

        // After the scoped listener is gone, a genuine later death must still
        // enter and finish the existing sequence. Reset only hit cooldown.
        wither.invulnerableTime = 0;
        wither.hurt(helper.getLevel().damageSources().genericKill(), Float.MAX_VALUE);
        int duration = org.kneekura.bedrockwither.entity.BedrockWitherDeathController
                .PROVISIONAL_DEATH_DURATION_TICKS;
        if (cancellations[0] != 1 || !wither.isDeadOrDying()
                || wither.getBedrockState() != BedrockWitherState.DEATH_SEQUENCE
                || wither.getDeathTicksRemaining() != duration) {
            helper.fail("A later accepted death did not enter the original death sequence");
            return;
        }
        for (int tick = 0; tick < duration - 1; tick++) {
            wither.deathController().tickServer();
        }
        if (wither.isRemoved() || wither.getDeathTicksRemaining() != 1) {
            helper.fail("A later accepted death ended before its final tick");
            return;
        }
        wither.deathController().tickServer();
        if (!wither.isRemoved() || wither.getDeathTicksRemaining() != 0) {
            helper.fail("A later accepted death did not finalize");
            return;
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_livingreloadcanfinishdeathsequence")
    public static void livingReloadCanFinishDeathSequence(GameTestHelper helper) {
        BedrockWitherEntity original = createCombatReadyWither(helper);
        original.setNoAi(true);
        net.minecraft.nbt.CompoundTag saved = new net.minecraft.nbt.CompoundTag();
        original.saveWithoutId(saved);
        original.discard();

        BedrockWitherEntity restored = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (restored == null) {
            helper.fail("Failed to create saved Wither copy");
            return;
        }
        restored.load(saved);
        if (!restored.isAlive() || restored.deathController().isActive()) {
            helper.fail("Loading a living Wither incorrectly entered semantic/visual death");
            return;
        }
        restored.hurt(helper.getLevel().damageSources().genericKill(), Float.MAX_VALUE);
        if (!restored.isDeadOrDying()
                || restored.getBedrockState() != BedrockWitherState.DEATH_SEQUENCE
                || !restored.deathController().isActive()) {
            helper.fail("Loading a living Wither disabled its later death sequence");
            return;
        }
        int duration = org.kneekura.bedrockwither.entity.BedrockWitherDeathController
                .PROVISIONAL_DEATH_DURATION_TICKS;
        for (int tick = 0; tick < duration - 1; tick++) {
            restored.deathController().tickServer();
        }
        if (restored.isRemoved() || restored.getDeathTicksRemaining() != 1) {
            helper.fail("Reloaded Wither did not retain the full provisional death countdown");
            return;
        }
        restored.deathController().tickServer();
        if (!restored.isRemoved() || restored.getDeathTicksRemaining() != 0) {
            helper.fail("Reloaded Wither did not finalize on the last death tick");
            return;
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_activedeathreloadpreservesremainingticks")
    public static void activeDeathReloadPreservesRemainingTicks(GameTestHelper helper) {
        BedrockWitherEntity original = createCombatReadyWither(helper);
        original.setNoAi(true);
        original.hurt(helper.getLevel().damageSources().genericKill(), Float.MAX_VALUE);
        for (int tick = 0; tick < 37; tick++) {
            original.deathController().tickServer();
        }
        int remaining = original.getDeathTicksRemaining();
        float swell = original.getDeathSwell();
        net.minecraft.nbt.CompoundTag saved = new net.minecraft.nbt.CompoundTag();
        original.saveWithoutId(saved);
        original.discard();

        BedrockWitherEntity restored = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (restored == null) {
            helper.fail("Failed to create dying Wither copy");
            return;
        }
        restored.load(saved);
        if (!restored.isDeadOrDying() || !restored.deathController().isActive()
                || restored.getDeathTicksRemaining() != remaining) {
            helper.fail("Loading a dying Wither lost its pending death sequence");
            return;
        }
        assertClose(helper, swell, restored.getDeathSwell(), "Saved death swell");
        for (int tick = 0; tick < remaining - 1; tick++) {
            restored.deathController().tickServer();
        }
        if (restored.isRemoved() || restored.getDeathTicksRemaining() != 1) {
            helper.fail("Saved death sequence restarted or finished early");
            return;
        }
        restored.deathController().tickServer();
        if (!restored.isRemoved()) {
            helper.fail("Saved death sequence did not finish after its remaining ticks");
            return;
        }
        float finalSwell = restored.getDeathSwell();
        restored.deathController().tickServer();
        assertClose(helper, finalSwell, restored.getDeathSwell(), "Finalized death tick is inert");
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_specialmovementgatematchesbedrockstateboundary")
    public static void specialMovementGateMatchesBedrockStateBoundary(GameTestHelper helper) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);
        net.minecraft.world.entity.animal.Cow target = EntityType.COW.create(helper.getLevel());
        if (target == null) {
            helper.fail("Failed to create special-movement target");
            return;
        }

        BlockPos targetPos = helper.absolutePos(new BlockPos(4, 1, 0));
        target.moveTo(targetPos.getX() + 0.5D, targetPos.getY(), targetPos.getZ() + 0.5D);
        target.setInvulnerable(true);
        helper.getLevel().addFreshEntity(target);
        wither.setTarget(target);

        wither.runtimeState().setWantsMove(false);
        wither.runtimeState().setPathing(false);

        if (wither.specialMovementController().canBegin()) {
            helper.fail("Special movement began without wantsMove");
            return;
        }

        wither.specialMovementController().requestMove();
        if (!wither.runtimeState().wantsMove()
                || !wither.specialMovementController().canBegin()) {
            helper.fail("Phase-1 target + wantsMove did not satisfy special-movement gate");
            return;
        }

        wither.setAerialAttack(false);
        if (wither.specialMovementController().canBegin()) {
            helper.fail("Powered/second-phase Wither should not begin phase-1 special movement");
            return;
        }

        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_passivedangeroussidedifficultygate")
    public static void passiveDangerousSideHeadDifficultyGateMatchesBedrock(GameTestHelper helper) {
        if (org.kneekura.bedrockwither.entity.BedrockWitherSideHeadController
                .passiveDangerousEnabled(net.minecraft.world.Difficulty.EASY)) {
            helper.fail("Easy should not enable the historical/current passive dangerous side-head path");
            return;
        }
        if (!org.kneekura.bedrockwither.entity.BedrockWitherSideHeadController
                .passiveDangerousEnabled(net.minecraft.world.Difficulty.NORMAL)
                || !org.kneekura.bedrockwither.entity.BedrockWitherSideHeadController
                .passiveDangerousEnabled(net.minecraft.world.Difficulty.HARD)) {
            helper.fail("Normal/Hard should enable passive dangerous side-head scheduling");
            return;
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_headpitchqueriestracktargets")
    public static void headPitchQueriesTrackTargetsIndependently(GameTestHelper helper) {
        BedrockWitherEntity wither = createCombatReadyWither(helper);

        net.minecraft.world.entity.animal.Cow mainTarget = EntityType.COW.create(helper.getLevel());
        net.minecraft.world.entity.animal.Cow sideTarget = EntityType.COW.create(helper.getLevel());
        if (mainTarget == null || sideTarget == null) {
            helper.fail("Failed to create head-tracking targets");
            return;
        }

        BlockPos mainPos = helper.absolutePos(new BlockPos(4, 5, 0));
        mainTarget.moveTo(mainPos.getX() + 0.5D, mainPos.getY(), mainPos.getZ() + 0.5D);
        mainTarget.setInvulnerable(true);
        helper.getLevel().addFreshEntity(mainTarget);

        BlockPos sidePos = helper.absolutePos(new BlockPos(-4, 1, 0));
        sideTarget.moveTo(sidePos.getX() + 0.5D, sidePos.getY(), sidePos.getZ() + 0.5D);
        sideTarget.setInvulnerable(true);
        helper.getLevel().addFreshEntity(sideTarget);

        wither.setTarget(mainTarget);
        wither.setAlternativeHeadTarget(1, sideTarget.getUUID());
        wither.clearAlternativeHeadTarget(2);

        wither.headTrackingController().tick();

        float centerPitch = wither.getSyncedHeadPitch(0);
        float sidePitch = wither.getSyncedHeadPitch(1);
        float idlePitch = wither.getSyncedHeadPitch(2);

        if (Math.abs(centerPitch) < 0.0001F) {
            helper.fail("Center head did not track elevated main target");
            return;
        }
        if (Math.abs(sidePitch) < 0.0001F) {
            helper.fail("Side head did not track its alternative target");
            return;
        }
        if (Math.abs(idlePitch) > 0.0001F) {
            helper.fail("Untargeted side head should relax toward zero pitch");
            return;
        }
        if (Math.abs(centerPitch - sidePitch) < 0.0001F) {
            helper.fail("Independent head targets produced indistinguishable pitch values");
            return;
        }

        helper.succeed();
    }

    private static BedrockWitherEntity createCombatReadyWither(GameTestHelper helper) {
        BedrockWitherEntity wither = createWither(helper);
        wither.runtimeState().setSpawningFrames(0);
        wither.setBedrockState(BedrockWitherState.PHASE1_REPOSITION);
        wither.spawnController().restore(0, BedrockWitherState.PHASE1_REPOSITION);
        return wither;
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
