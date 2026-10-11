package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

/**
 * The first two-real-aircraft server simulation test. Unlike the original
 * synthetic ArmorStand-hostile GameTests, contact here must be identified via
 * explicit opponent team AND actual world-space FOV/range/block ray LOS.
 * Separate batch from the five isolated single-aircraft control scenarios.
 */
@GameTestHolder(PhysicsTraceProbeMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class LiveSquadronGameTests {
    private static final int TICKS = 140;
    private LiveSquadronGameTests() {}

    @GameTest(template = "empty", batch = "ww_live_team_pair", timeoutTicks = 290)
    public static void twoIndependentPilotsAcquireAssignedEnemy(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        Vec3 base = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 190, 0)));
        Entity red = spawn(level, "a6m", base, 0f, .75);
        Entity blue = spawn(level, "p47n", base.add(35, 0, 95), 180f, -.75);
        red.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);
        blue.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);

        String redScenario = "live-pair-a6m-red";
        String blueScenario = "live-pair-p47n-blue";
        RuntimeTacticalPilot.startLive(redScenario, level, red,
                (ArmorStand) red.getFirstPassenger(),
                new RuntimeTacticalPilot.LiveOrder("red", TacticalAirAI.Mission.INTERCEPT,
                        blue.position(), red.position(), null, "blue", null), TICKS);
        RuntimeTacticalPilot.startLive(blueScenario, level, blue,
                (ArmorStand) blue.getFirstPassenger(),
                new RuntimeTacticalPilot.LiveOrder("blue", TacticalAirAI.Mission.INTERCEPT,
                        red.position(), blue.position(), null, "red", null), TICKS);

        helper.succeedWhen(() -> {
            var a = RuntimeTacticalPilot.result(redScenario);
            var b = RuntimeTacticalPilot.result(blueScenario);
            if (a == null || b == null)
                throw new GameTestAssertException("Real two-plane live team flight still active");
            if (!a.complete() || !b.complete())
                throw new IllegalStateException("Live squadron test failed "
                        + a.failure() + " / " + b.failure());
            if (a.samples() != TICKS || b.samples() != TICKS
                    || a.displacementBlocks() < 8 || b.displacementBlocks() < 8)
                throw new IllegalStateException("Two real aircraft failed to move independently");
            if (a.observedContactTicks() < 2 || b.observedContactTicks() < 2)
                throw new IllegalStateException("No FOV/range/LOS-qualified actual enemy observation: "
                        + a.observedContactTicks() + "/" + b.observedContactTicks());
        });
    }

    @GameTest(template = "empty", batch = "ww_live_sight_check", timeoutTicks = 90)
    public static void actualAirplaneFovAndBlockOcclusion(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        Vec3 base = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 185, 0)));
        Entity viewer = createUncrewed(level, "a6m", base, 0f);
        Entity target = createUncrewed(level, "p47n", base.add(0, 0, 45), 180f);
        if (LiveAirSensor.observe(level, viewer, target) == null)
            throw new IllegalStateException("Actual target in clear forward FOV was not observed");
        viewer.setYRot(180f);
        if (LiveAirSensor.observe(level, viewer, target) != null)
            throw new IllegalStateException("Rear target observed outside explicit FOV");
        viewer.setYRot(0f);
        Vec3 midpoint = viewer.getBoundingBox().getCenter().add(
                target.getBoundingBox().getCenter()).scale(.5);
        BlockPos barrier = BlockPos.containing(midpoint);
        level.setBlock(barrier, Blocks.STONE.defaultBlockState(), 3);
        if (LiveAirSensor.observe(level, viewer, target) != null)
            throw new IllegalStateException("Target visible through obstructing solid block");
        level.setBlock(barrier, Blocks.AIR.defaultBlockState(), 3);
        if (LiveAirSensor.observe(level, viewer, target) == null)
            throw new IllegalStateException("Removing obstruction failed to restore target detection");
        helper.succeed();
    }

    @GameTest(template = "empty", batch = "ww_live_same_team", timeoutTicks = 210)
    public static void twoFriendlyAircraftNotImplicitlyHostile(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        Vec3 base = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 190, 0)));
        Entity first = spawn(level, "a6m", base, 0f, .7);
        Entity second = spawn(level, "p47n", base.add(25, 0, 80), 180f, -.7);
        first.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);
        second.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);
        String s1 = "live-no-hostility-a6m";
        String s2 = "live-no-hostility-p47n";
        RuntimeTacticalPilot.startLive(s1, level, first, (ArmorStand) first.getFirstPassenger(),
                new RuntimeTacticalPilot.LiveOrder("allied", TacticalAirAI.Mission.INTERCEPT,
                        second.position(), first.position(), null, null, null), 70);
        RuntimeTacticalPilot.startLive(s2, level, second, (ArmorStand) second.getFirstPassenger(),
                new RuntimeTacticalPilot.LiveOrder("allied", TacticalAirAI.Mission.INTERCEPT,
                        first.position(), second.position(), null, null, null), 70);
        helper.succeedWhen(() -> {
            var a = RuntimeTacticalPilot.result(s1);
            var b = RuntimeTacticalPilot.result(s2);
            if (a == null || b == null)
                throw new GameTestAssertException("Two same-team pilot runs still active");
            if (!a.complete() || !b.complete() || a.samples() != 70 || b.samples() != 70)
                throw new IllegalStateException("Same-team flight failed");
            if (a.observedContactTicks() != 0 || b.observedContactTicks() != 0
                    || a.predictedContactTicks() != 0 || b.predictedContactTicks() != 0)
                throw new IllegalStateException("Implicit hostile discovered from aircraft/faction/team without order");
        });
    }

    private static Entity createUncrewed(ServerLevel level, String name, Vec3 position, float yaw) {
        EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getOptional(
                new ResourceLocation("warfare_wings", name)).orElseThrow();
        Entity entity = type.create(level);
        if (entity == null) throw new IllegalStateException("Could not create sight test aircraft");
        entity.moveTo(position.x, position.y, position.z, yaw, 0);
        entity.setInvulnerable(true);
        level.addFreshEntity(entity);
        return entity;
    }

    private static Entity spawn(ServerLevel level, String name, Vec3 position,
                                float yaw, double initialZVelocity) {
        ResourceLocation id = new ResourceLocation("warfare_wings", name);
        EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getOptional(id)
                .orElseThrow(() -> new IllegalStateException("Missing live test plane " + id));
        Entity plane = type.create(level);
        ArmorStand pilot = EntityType.ARMOR_STAND.create(level);
        if (plane == null || pilot == null)
            throw new IllegalStateException("Missing live GameTest aircraft/pilot");
        plane.moveTo(position.x, position.y, position.z, yaw, 0f);
        plane.setInvulnerable(true);
        pilot.moveTo(position.x, position.y, position.z);
        pilot.setInvisible(true);
        pilot.setInvulnerable(true);
        pilot.setNoGravity(true);
        level.addFreshEntity(plane);
        level.addFreshEntity(pilot);
        if (!pilot.startRiding(plane, true))
            throw new IllegalStateException("Could not mount independent live pilot");
        plane.setDeltaMovement(0, 0, initialZVelocity);
        IaRuntimeAccess.chill(plane);
        IaRuntimeAccess.setEngineTarget(plane, 1f);
        return plane;
    }
}
