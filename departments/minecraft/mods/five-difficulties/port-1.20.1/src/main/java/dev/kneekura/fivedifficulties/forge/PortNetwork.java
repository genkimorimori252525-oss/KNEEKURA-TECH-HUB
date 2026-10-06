package dev.kneekura.fivedifficulties.forge;

import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;

/**
 * Modern packet boundary. No P0 gameplay packet is registered yet.
 */
public final class PortNetwork {
    private static final String PROTOCOL = "p0";

    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "main"),
            () -> PROTOCOL,
            PROTOCOL::equals,
            PROTOCOL::equals
    );

    private static boolean registered;

    private PortNetwork() {}

    public static synchronized void register() {
        if (registered) return;
        registered = true;
        // P1: register explicit server-authoritative input/time-stop packets here.
    }
}
