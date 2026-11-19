package org.kneekura.bedrockwither.entity;

import java.lang.reflect.Field;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.ai.BedrockFlyingMoveControl;
import org.kneekura.bedrockwither.entity.ai.BedrockLookGoal;
import org.kneekura.bedrockwither.registry.ModEntities;

@GameTestHolder(BedrockWitherMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BedrockWitherParityPolishGameTests {
    private BedrockWitherParityPolishGameTests() {}

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_officialsupplementalgoals")
    public static void officialSupplementalGoalsAreRegistered(GameTestHelper helper) {
        BedrockWitherEntity boss = requireBoss(helper);
        try {
            GoalSelector selector = goalSelector(boss);
            boolean hasFloat = selector.getAvailableGoals().stream()
                    .anyMatch(goal -> goal.getPriority() == 1 && goal.getGoal() instanceof FloatGoal);
            boolean hasTargetLook = selector.getAvailableGoals().stream()
                    .anyMatch(goal -> goal.getPriority() == 5
                            && goal.getGoal() instanceof BedrockLookGoal look
                            && look.source() == BedrockLookGoal.Source.CURRENT_TARGET);
            boolean hasPlayerLook = selector.getAvailableGoals().stream()
                    .anyMatch(goal -> goal.getPriority() == 6
                            && goal.getGoal() instanceof BedrockLookGoal look
                            && look.source() == BedrockLookGoal.Source.NEAREST_PLAYER);

            helper.assertTrue(hasFloat, "Pinned Bedrock Wither behavior.float priority 1 must be registered");
            helper.assertTrue(hasTargetLook, "Pinned look_at_target priority 5 must be registered");
            helper.assertTrue(hasPlayerLook, "Pinned look_at_player priority 6 must be registered");
            helper.assertTrue(BedrockLookGoal.LOOK_DISTANCE == 8.0D
                            && BedrockLookGoal.START_PROBABILITY == 0.02F
                            && BedrockLookGoal.MIN_LOOK_TICKS == 20
                            && BedrockLookGoal.MAX_LOOK_TICKS == 40,
                    "Look goals must retain the current public defaults and explicit 1..2 second Wither range");
            helper.succeed();
        } finally {
            boss.discard();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_withersoundprofile")
    public static void witherSoundProfileUsesVanillaWitherAdapters(GameTestHelper helper) {
        BedrockWitherEntity boss = requireBoss(helper);
        try {
            helper.assertTrue(boss.getAmbientSound() == SoundEvents.WITHER_AMBIENT,
                    "Standalone boss must expose the Wither ambient sound");
            helper.assertTrue(boss.getHurtSound(helper.getLevel().damageSources().generic()) == SoundEvents.WITHER_HURT,
                    "Standalone boss must expose the Wither hurt sound");
            helper.assertTrue(boss.getDeathSound() == SoundEvents.WITHER_DEATH,
                    "Standalone boss must expose the Wither death sound");
            helper.assertTrue(BedrockWitherAttackController.JAVA_WITHER_SHOOT_LEVEL_EVENT == 1024,
                    "Shoot bridge must use Java's Wither shoot level event");
            helper.assertTrue(BedrockWitherDestructionController.JAVA_WITHER_BREAK_BLOCK_LEVEL_EVENT == 1022,
                    "Block destruction bridge must use Java's Wither break level event");
            helper.assertTrue(BedrockWitherSpawnController.JAVA_WITHER_SPAWN_LEVEL_EVENT == 1023,
                    "Spawn bridge must use Java's global Wither spawn level event");
            helper.succeed();
        } finally {
            boss.discard();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_witherroseplace")
    public static void customWitherKillPlacesWitherRose(GameTestHelper helper) {
        var level = helper.getLevel();
        boolean oldMobGriefing = level.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING);
        BlockPos anchor = helper.absolutePos(BlockPos.ZERO);
        BlockPos floor = new BlockPos(anchor.getX(), level.getMaxBuildHeight() - 40, anchor.getZ());
        BlockPos victimPos = floor.above();
        BedrockWitherEntity boss = requireBoss(helper);
        Cow cow = EntityType.COW.create(level);
        if (cow == null) throw new IllegalStateException("Failed to create cow fixture");

        try {
            level.getGameRules().getRule(GameRules.RULE_MOBGRIEFING).set(true, level.getServer());
            level.setBlock(floor, Blocks.NETHERRACK.defaultBlockState(), 3);
            level.setBlock(victimPos, Blocks.AIR.defaultBlockState(), 3);
            boss.setPos(victimPos.getX() + 4.5D, victimPos.getY(), victimPos.getZ() + 0.5D);
            cow.setPos(victimPos.getX() + 0.5D, victimPos.getY(), victimPos.getZ() + 0.5D);
            level.addFreshEntity(boss);
            level.addFreshEntity(cow);

            cow.hurt(level.damageSources().mobAttack(boss), Float.MAX_VALUE);
            helper.assertTrue(level.getBlockState(victimPos).is(Blocks.WITHER_ROSE),
                    "A kill credited to the standalone Wither must place a Wither Rose when mobGriefing permits it");
            helper.succeed();
        } finally {
            level.getGameRules().getRule(GameRules.RULE_MOBGRIEFING).set(oldMobGriefing, level.getServer());
            level.setBlock(victimPos, Blocks.AIR.defaultBlockState(), 3);
            level.setBlock(floor, Blocks.AIR.defaultBlockState(), 3);
            boss.discard();
            cow.discard();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_witherrosedrop")
    public static void customWitherKillDropsRoseWhenPlacementIsDisabled(GameTestHelper helper) {
        var level = helper.getLevel();
        boolean oldMobGriefing = level.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING);
        BlockPos anchor = helper.absolutePos(BlockPos.ZERO);
        BlockPos victimPos = new BlockPos(anchor.getX(), level.getMaxBuildHeight() - 40, anchor.getZ());
        BedrockWitherEntity boss = requireBoss(helper);
        Cow cow = EntityType.COW.create(level);
        if (cow == null) throw new IllegalStateException("Failed to create cow fixture");
        AABB roseArea = new AABB(victimPos).inflate(3.0D);
        Set<UUID> existing = new HashSet<>();
        for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, roseArea,
                entity -> entity.getItem().is(net.minecraft.world.item.Items.WITHER_ROSE))) {
            existing.add(item.getUUID());
        }

        try {
            level.getGameRules().getRule(GameRules.RULE_MOBGRIEFING).set(false, level.getServer());
            level.setBlock(victimPos, Blocks.AIR.defaultBlockState(), 3);
            boss.setPos(victimPos.getX() + 4.5D, victimPos.getY(), victimPos.getZ() + 0.5D);
            cow.setPos(victimPos.getX() + 0.5D, victimPos.getY(), victimPos.getZ() + 0.5D);
            level.addFreshEntity(boss);
            level.addFreshEntity(cow);

            cow.hurt(level.damageSources().mobAttack(boss), Float.MAX_VALUE);
            long newRoses = level.getEntitiesOfClass(ItemEntity.class, roseArea,
                            entity -> entity.getItem().is(net.minecraft.world.item.Items.WITHER_ROSE)
                                    && !existing.contains(entity.getUUID()))
                    .size();
            helper.assertTrue(newRoses == 1,
                    "Wither Rose must fall back to one item when mobGriefing prevents block placement");
            helper.succeed();
        } finally {
            level.getGameRules().getRule(GameRules.RULE_MOBGRIEFING).set(oldMobGriefing, level.getServer());
            boss.discard();
            cow.discard();
            for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, roseArea,
                    entity -> entity.getItem().is(net.minecraft.world.item.Items.WITHER_ROSE)
                            && !existing.contains(entity.getUUID()))) {
                item.discard();
            }
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_publicmaxturn")
    public static void publicMovementMaxTurnAppliesToYaw(GameTestHelper helper) {
        BedrockWitherEntity boss = requireBoss(helper);
        try {
            boss.setPos(0.5D, helper.getLevel().getMaxBuildHeight() - 40.0D, 0.5D);
            boss.setYRot(0.0F);
            boss.setXRot(0.0F);

            helper.assertTrue(boss.getMoveControl() instanceof BedrockFlyingMoveControl,
                    "Standalone boss must use the Bedrock max-turn flying controller");
            helper.assertTrue(BedrockFlyingMoveControl.PUBLIC_MAX_TURN_DEGREES == 180.0F,
                    "Pinned movement.basic max_turn must remain 180 degrees per tick");

            boss.getMoveControl().setWantedPosition(
                    boss.getX(),
                    boss.getY(),
                    boss.getZ() - 10.0D,
                    1.0D
            );
            boss.getMoveControl().tick();

            float yawError = Math.abs(Mth.wrapDegrees(boss.getYRot() - 180.0F));
            helper.assertTrue(yawError < 1.0E-4F,
                    "A 180-degree yaw request must be reachable in one control tick under max_turn=180");
            helper.succeed();
        } finally {
            boss.discard();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_publicpushability")
    public static void publicPushabilityRemainsEnabledWhileClimbing(GameTestHelper helper) {
        var level = helper.getLevel();
        BlockPos anchor = helper.absolutePos(BlockPos.ZERO);
        BlockPos floor = new BlockPos(anchor.getX(), level.getMaxBuildHeight() - 40, anchor.getZ());
        BlockPos climb = floor.above();
        BedrockWitherEntity boss = requireBoss(helper);

        try {
            level.setBlock(floor, Blocks.STONE.defaultBlockState(), 3);
            level.setBlock(climb, Blocks.SCAFFOLDING.defaultBlockState(), 3);
            boss.setPos(climb.getX() + 0.5D, climb.getY(), climb.getZ() + 0.5D);
            level.addFreshEntity(boss);

            helper.assertTrue(boss.onClimbable(),
                    "Inherited LivingEntity ladder/scaffolding handling must satisfy minecraft:can_climb");
            helper.assertTrue(boss.isPushable(),
                    "minecraft:pushable_by_entity must remain true independently of can_climb");
            helper.assertTrue(boss.getPistonPushReaction() == PushReaction.NORMAL,
                    "minecraft:pushable_by_block must retain the normal Java piston push reaction");
            helper.succeed();
        } finally {
            boss.discard();
            level.setBlock(climb, Blocks.AIR.defaultBlockState(), 3);
            level.setBlock(floor, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static GoalSelector goalSelector(BedrockWitherEntity boss) {
        try {
            Field field = Mob.class.getDeclaredField("goalSelector");
            field.setAccessible(true);
            return (GoalSelector) field.get(boss);
        } catch (ReflectiveOperationException exception) {
            throw new IllegalStateException("Unable to inspect goal selector", exception);
        }
    }

    private static BedrockWitherEntity requireBoss(GameTestHelper helper) {
        BedrockWitherEntity boss = ModEntities.BEDROCK_WITHER.get().create(helper.getLevel());
        if (boss == null) throw new IllegalStateException("Failed to create Wither fixture");
        boss.setNoAi(true);
        return boss;
    }
}
