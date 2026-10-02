package org.kneekura.bedrockwither.gametest;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.WitherSkeleton;
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
        helper.succeed();
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
