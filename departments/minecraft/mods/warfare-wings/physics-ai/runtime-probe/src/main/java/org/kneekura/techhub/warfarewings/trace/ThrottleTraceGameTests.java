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
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder(PhysicsTraceProbeMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ThrottleTraceGameTests {
    private ThrottleTraceGameTests() {}

    @GameTest(template = "empty", timeoutTicks = 520, batch = "ww_physics_trace")
    public static void a6mThrottleStep(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();

        ResourceLocation id = new ResourceLocation("warfare_wings", "a6m");
        EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getOptional(id)
                .orElseThrow(() -> new IllegalStateException("Missing " + id));
        Entity aircraft = type.create(level);
        ArmorStand pilot = EntityType.ARMOR_STAND.create(level);
        if (aircraft == null || pilot == null) throw new IllegalStateException("Could not create trace entities");

        BlockPos base = helper.absolutePos(new BlockPos(0, 200, 0));
        Vec3 start = Vec3.atBottomCenterOf(base);
        aircraft.moveTo(start.x, start.y, start.z, 0.0f, 0.0f);
        aircraft.setInvulnerable(true);
        pilot.moveTo(start.x, start.y, start.z, 0.0f, 0.0f);
        pilot.setInvisible(true);
        pilot.setInvulnerable(true);
        pilot.setNoGravity(true);

        level.addFreshEntity(aircraft);
        level.addFreshEntity(pilot);
        if (!pilot.startRiding(aircraft, true)) throw new IllegalStateException("Could not mount trace pilot");

        aircraft.setDeltaMovement(0.0, 0.0, 0.7);
        aircraft.setYRot(0.0f);
        aircraft.setXRot(0.0f);
        IaRuntimeAccess.chill(aircraft);
        IaRuntimeAccess.setEngineTarget(aircraft, 1.0f);

        RuntimeTraceManager.start(level, aircraft, pilot);

        helper.succeedWhen(() -> {
            String failure = RuntimeTraceManager.failure();
            if (failure != null) throw new IllegalStateException("Runtime trace failed: " + failure);
            if (!RuntimeTraceManager.complete()) {
                throw new GameTestAssertException("A6M throttle trace still running");
            }
        });
    }
}