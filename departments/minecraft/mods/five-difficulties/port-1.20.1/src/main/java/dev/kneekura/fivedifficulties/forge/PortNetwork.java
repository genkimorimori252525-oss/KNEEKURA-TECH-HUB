package dev.kneekura.fivedifficulties.forge;

import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;

public final class PortNetwork {
    private static final String PROTOCOL = "p2";

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
        // Time-stop action packets remain deferred until the X1 runtime oracle is captured.
    }
}
