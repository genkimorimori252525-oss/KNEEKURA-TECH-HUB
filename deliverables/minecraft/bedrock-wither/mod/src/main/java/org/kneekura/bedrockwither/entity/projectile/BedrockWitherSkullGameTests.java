package org.kneekura.bedrockwither.entity.projectile;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.Difficulty;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;
import org.kneekura.bedrockwither.registry.ModEntities;

@GameTestHolder(BedrockWitherMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BedrockWitherSkullGameTests {
    private BedrockWitherSkullGameTests() {
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_entityhitmatchesbedrockimpactdamage")
    public static void entityHitMatchesBedrockImpactDamage(GameTestHelper helper) {
        BedrockWitherEntity owner = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        Cow target = EntityType.COW.create(helper.getLevel());
        if (owner == null || target == null) {
            helper.fail("Failed to create Wither/cow test entities");
            return;
        }

        BlockPos pos = helper.absolutePos(new BlockPos(0, 1, 0));
        owner.moveTo(pos.getX() + 0.5D, pos.getY(), pos.getZ() + 0.5D);
        target.moveTo(pos.getX() + 2.5D, pos.getY(), pos.getZ() + 0.5D);
        // The ordinary cow's 10 HP saturates a 12-damage Hard impact. Keep this
        // damage/effect fixture alive on every difficulty; exact assertions stay.
        target.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(40.0D);
        target.setHealth(40.0F);
        helper.getLevel().addFreshEntity(owner);
        helper.getLevel().addFreshEntity(target);

        BedrockWitherSkullEntity skull = BedrockWitherSkullEntity.create(
                helper.getLevel(),
                owner,
                owner.position(),
                new Vec3(1.0D, 0.0D, 0.0D),
                BedrockWitherSkullEntity.Kind.NORMAL
        );

        try {
            float before = target.getHealth();
            skull.onHitEntity(new EntityHitResult(target));

            if (BedrockWitherSkullEntity.impactDamageFor(Difficulty.EASY) != 5.0F
                    || BedrockWitherSkullEntity.impactDamageFor(Difficulty.NORMAL) != 8.0F
                    || BedrockWitherSkullEntity.impactDamageFor(Difficulty.HARD) != 12.0F) {
                helper.fail("Bedrock skull difficulty damage mapping is not 5/8/12");
                return;
            }

            float expectedDamage = BedrockWitherSkullEntity.impactDamageFor(
                    helper.getLevel().getDifficulty()
            );
            float actualDamage = before - target.getHealth();
            if (Math.abs(actualDamage - expectedDamage) > 0.0001F) {
                helper.fail("Bedrock skull impact damage expected "
                        + expectedDamage + " on " + helper.getLevel().getDifficulty()
                        + " but was " + actualDamage);
                return;
            }

            assertWitherEffectMatchesDifficulty(helper, target);
            helper.succeed();
        } finally {
            skull.discard();
            target.discard();
            owner.discard();
        }
    }

    private static void assertWitherEffectMatchesDifficulty(GameTestHelper helper, Cow target) {
        Difficulty difficulty = helper.getLevel().getDifficulty();
        int expectedDuration = switch (difficulty) {
            case PEACEFUL, EASY -> 0;
            case NORMAL -> 200;
            case HARD -> 800;
        };

        MobEffectInstance effect = target.getEffect(MobEffects.WITHER);
        if (expectedDuration == 0) {
            if (effect != null) {
                helper.fail("Bedrock skull added Wither effect on " + difficulty);
            }
            return;
        }

        if (effect == null) {
            helper.fail("Bedrock skull did not add Wither effect on " + difficulty);
            return;
        }
        if (effect.getAmplifier() != 1) {
            helper.fail("Bedrock skull Wither amplifier expected 1 but was " + effect.getAmplifier());
            return;
        }
        if (effect.getDuration() != expectedDuration) {
            helper.fail("Bedrock skull Wither duration expected " + expectedDuration + " but was " + effect.getDuration());
        }
    }
}
