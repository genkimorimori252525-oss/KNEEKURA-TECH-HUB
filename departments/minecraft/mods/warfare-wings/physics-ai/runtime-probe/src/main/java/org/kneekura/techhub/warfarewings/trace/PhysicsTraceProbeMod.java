package org.kneekura.techhub.warfarewings.trace;

import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.Mod;

@Mod(PhysicsTraceProbeMod.MOD_ID)
public final class PhysicsTraceProbeMod {
    public static final String MOD_ID = "ww_physics_trace_probe";

    public PhysicsTraceProbeMod() {
        MinecraftForge.EVENT_BUS.addListener(RuntimeTraceManager::onServerTick);
        MinecraftForge.EVENT_BUS.addListener(RuntimeTacticalPilot::onServerTick);
        MinecraftForge.EVENT_BUS.addListener(RuntimeTacticalPilot::onServerStopping);
        MinecraftForge.EVENT_BUS.addListener(TacticalPilotCommands::register);
        MinecraftForge.EVENT_BUS.addListener(TacticalPilotCommands::onServerStopping);
    }
}
