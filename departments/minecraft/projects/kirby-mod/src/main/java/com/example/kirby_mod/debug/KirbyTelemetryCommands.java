package com.example.kirby_mod.debug;

import net.minecraft.commands.Commands;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.RegisterCommandsEvent;

public final class KirbyTelemetryCommands {

    private KirbyTelemetryCommands() {}

    public static void register(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("tlm")
                .requires(source -> source.getEntity() instanceof ServerPlayer)
                .executes(context -> KirbyTelemetryServer.toggle(context.getSource()))
                .then(Commands.literal("on")
                        .executes(context -> KirbyTelemetryServer.enable(context.getSource())))
                .then(Commands.literal("off")
                        .executes(context -> KirbyTelemetryServer.disable(context.getSource())))
                .then(Commands.literal("once")
                        .executes(context -> KirbyTelemetryServer.once(context.getSource())))
                .then(Commands.literal("kirbydebug")
                        .executes(context -> KirbyTelemetryServer.toggle(context.getSource()))
                        .then(Commands.literal("on")
                                .executes(context -> KirbyTelemetryServer.enable(context.getSource())))
                        .then(Commands.literal("off")
                                .executes(context -> KirbyTelemetryServer.disable(context.getSource())))
                        .then(Commands.literal("once")
                                .executes(context -> KirbyTelemetryServer.once(context.getSource())))));
    }
}
