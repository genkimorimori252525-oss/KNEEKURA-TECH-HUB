package org.kneekura.staff;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.StringReader;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import java.nio.file.Path;
import java.util.UUID;
import net.minecraft.commands.CommandSource;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.commands.arguments.GameModeArgument;
import net.minecraft.commands.arguments.selector.EntitySelector;
import net.minecraft.network.chat.Component;
import net.minecraft.server.commands.GameModeCommand;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec2;
import net.minecraft.world.phys.Vec3;

/** Cached real parsers only: no Bootstrap, game/server/world construction or execution. */
public final class FixtureCommandParserAssertions {
    private static void require(boolean value, String detail) {
        if (!value) throw new AssertionError(detail);
    }

    public static void main(String[] args) throws Exception {
        require(args.length == 5, "Expected exact jar and two UUID/command pairs");
        Path actualJar = Path.of(GameModeCommand.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        require(actualJar.equals(Path.of(args[0]).toRealPath()), "Real cached Minecraft class provenance differs");
        CommandDispatcher<CommandSourceStack> dispatcher = new CommandDispatcher<>();
        GameModeCommand.register(dispatcher); // Actual 1.20.1 command registration, unchanged.
        // The exact as/run parser branches from 1.20.1 ExecuteCommand.register.
        // Its other branches require game registries, which are deliberately not
        // initialized here. The fork is poison-pill guarded: parsing cannot execute.
        var execute = dispatcher.register(Commands.literal("execute").requires(source -> source.hasPermission(2)));
        execute.addChild(Commands.literal("run").redirect(dispatcher.getRoot()).build());
        execute.addChild(Commands.literal("as").then(Commands.argument("targets", EntityArgument.entities())
            .fork(execute, context -> { throw new AssertionError("Offline parser attempted command execution"); })).build());
        CommandSourceStack source = new CommandSourceStack(CommandSource.NULL, Vec3.ZERO, Vec2.ZERO,
            null, 4, "offline-parser", Component.literal("offline-parser"), null, null);
        require(source.getServer() == null && source.getLevel() == null && source.getEntity() == null,
                "Offline parser must have no game server, world or player");
        for (int n = 1; n < args.length; n += 2) {
            UUID expected = UUID.fromString(args[n]);
            String old = "gamemode creative " + expected;
            var rejected = dispatcher.parse(old, source);
            require(rejected.getExceptions().values().stream().anyMatch(e -> e.getType() == EntityArgument.ERROR_ONLY_PLAYERS_ALLOWED),
                    "Original command must reproduce the exact real player-only parse error");
            try {
                EntityArgument.players().parse(new StringReader(expected.toString()));
                throw new AssertionError("Bare UUID unexpectedly accepted as player-only argument");
            } catch (CommandSyntaxException rejection) {
                require(rejection.getType() == EntityArgument.ERROR_ONLY_PLAYERS_ALLOWED, "Wrong rejection type");
            }
            System.out.println("ORIGINAL_UUID_REJECTED " + expected);
            String command = args[n + 1];
            var parsed = dispatcher.parse(command, source);
            require(!parsed.getReader().canRead() && parsed.getExceptions().isEmpty(), "Whole fixed command failed real parsing");
            var outer = parsed.getContext();
            var entity = outer.build(command).getArgument("targets", EntitySelector.class);
            var field = EntitySelector.class.getDeclaredField("entityUUID");
            field.setAccessible(true); // Inspect a parsed value only, never a live object.
            require(expected.equals(field.get(entity)) && entity.getMaxResults() == 1
                    && !entity.usesSelector() && !entity.isSelfSelector(), "Outer selector lost its exact UUID binding");
            var tail = outer;
            while (tail.getChild() != null) tail = tail.getChild();
            var suffix = tail.build(command);
            var target = suffix.getArgument("target", EntitySelector.class);
            require(target.isSelfSelector() && target.getMaxResults() == 1, "Inner gamemode target is not only @s");
            require(GameModeArgument.getGameMode(suffix, "gamemode") == GameType.CREATIVE, "Mode was not creative");
            require(suffix.getCommand() != null, "Missing actual GameModeCommand callback");
            System.out.println("FIXED_UUID_SELF_COMMAND_PARSED " + expected);
        }
        System.out.println("REAL_MINECRAFT_BRIGADIER_PARSE_PASS_NO_COMMAND_EXECUTION");
    }
}
