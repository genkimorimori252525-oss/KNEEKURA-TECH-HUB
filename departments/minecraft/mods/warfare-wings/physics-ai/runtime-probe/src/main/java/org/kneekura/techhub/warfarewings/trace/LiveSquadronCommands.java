package org.kneekura.techhub.warfarewings.trace;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.commands.arguments.coordinates.Vec3Argument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.RegisterCommandsEvent;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

/**
 * Server-operator explicit live air-group enrollment and mission orders.
 * Does not classify friend/foe from the airframe's historical faction.
 * Only enrolled aircraft appear in automatic team-target scanning.
 */
final class LiveSquadronCommands {
    private static final int MAX_SQUADRON = 16;
    private static final int MAX_DURATION = 900;

    private LiveSquadronCommands() {}

    static void register(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("wwai")
                .requires(s -> s.hasPermission(2))
                .then(Commands.literal("enlist")
                        .then(Commands.argument("aircraft", EntityArgument.entity())
                                .then(Commands.argument("team", StringArgumentType.word())
                                        .then(Commands.argument("mission", StringArgumentType.word())
                                                .executes(LiveSquadronCommands::enlist)))))
                .then(Commands.literal("group")
                        .then(Commands.argument("aircrafts", EntityArgument.entities())
                                .then(Commands.argument("team", StringArgumentType.word())
                                        .then(Commands.argument("mission", StringArgumentType.word())
                                                .executes(LiveSquadronCommands::group)))))
                .then(Commands.literal("mission")
                        .then(Commands.argument("aircraft", EntityArgument.entity())
                                .then(Commands.argument("mission", StringArgumentType.word())
                                        .executes(LiveSquadronCommands::mission))))
                .then(Commands.literal("target")
                        .then(Commands.argument("aircraft", EntityArgument.entity())
                                .then(Commands.argument("target", EntityArgument.entity())
                                        .executes(LiveSquadronCommands::target))))
                .then(Commands.literal("enemyteam")
                        .then(Commands.argument("team", StringArgumentType.word())
                                .then(Commands.argument("enemy", StringArgumentType.word())
                                        .executes(LiveSquadronCommands::enemyTeam))))
                .then(Commands.literal("waypoint")
                        .then(Commands.argument("aircraft", EntityArgument.entity())
                                .then(Commands.argument("point", Vec3Argument.vec3())
                                        .executes(LiveSquadronCommands::waypoint))))
                .then(Commands.literal("leader")
                        .then(Commands.argument("aircraft", EntityArgument.entity())
                                .then(Commands.argument("leader", EntityArgument.entity())
                                        .executes(LiveSquadronCommands::leader))))
                .then(Commands.literal("stopcraft")
                        .then(Commands.argument("aircraft", EntityArgument.entity())
                                .executes(LiveSquadronCommands::stopCraft)))
                .then(Commands.literal("stopteam")
                        .then(Commands.argument("team", StringArgumentType.word())
                                .executes(LiveSquadronCommands::stopTeam)))
                .then(Commands.literal("squadstatus").executes(LiveSquadronCommands::status)));
    }

    private static int enlist(CommandContext<CommandSourceStack> ctx) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        Entity plane = EntityArgument.getEntity(ctx, "aircraft");
        try {
            return enroll(ctx.getSource(), List.of(plane), team(ctx, "team"), selectedMission(ctx));
        } catch (IllegalArgumentException ex) {
            ctx.getSource().sendFailure(Component.literal(ex.getMessage()));
            return 0;
        }
    }

    private static int group(CommandContext<CommandSourceStack> ctx) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        Collection<? extends Entity> entities = EntityArgument.getEntities(ctx, "aircrafts");
        try {
            return enroll(ctx.getSource(), new ArrayList<>(entities), team(ctx, "team"), selectedMission(ctx));
        } catch (IllegalArgumentException ex) {
            ctx.getSource().sendFailure(Component.literal(ex.getMessage()));
            return 0;
        }
    }

    private static int enroll(CommandSourceStack source, List<Entity> planes,
                              String team, TacticalAirAI.Mission mission) {
        if (!RuntimeTacticalPilot.validTeam(team) || planes.isEmpty() || planes.size() > MAX_SQUADRON) {
            source.sendFailure(Component.literal("Team: lowercase [a-z][a-z0-9_-]{0,23}; group size 1..16"));
            return 0;
        }
        ServerLevel world = source.getLevel();
        try {
            // Preflight the entire selection before touching entities.
            if (RuntimeTacticalPilot.liveStatus().size() + planes.size() > 64)
                throw new IllegalArgumentException("Maximum 64 managed aircraft");
            for (Entity plane : planes) {
                if (plane.level() != world)
                    throw new IllegalArgumentException("All aircraft must be in command dimension");
                RuntimeTacticalPilot.validateEnrollment(plane, mission);
            }
        } catch (IllegalArgumentException ex) {
            source.sendFailure(Component.literal(ex.getMessage()));
            return 0;
        }
        List<UUID> enrolled = new ArrayList<>();
        try {
            // Explicit selection still needs deterministic enrollment order.
            // In particular it stabilizes future leader/slot assignments.
            // Copy first: /wwai enlist passes List.of(plane), which is immutable.
            List<Entity> sortedPlanes = new ArrayList<>(planes);
            sortedPlanes.sort(java.util.Comparator.comparing(e -> e.getUUID().toString()));
            for (Entity plane : sortedPlanes) {
                ArmorStand pilot = EntityType.ARMOR_STAND.create(world);
                if (pilot == null) throw new IllegalStateException("Could not create controller pilot");
                pilot.moveTo(plane.getX(), plane.getY(), plane.getZ());
                pilot.setInvisible(true);
                pilot.setInvulnerable(true);
                pilot.setNoGravity(true);
                world.addFreshEntity(pilot);
                if (!pilot.startRiding(plane, true)) {
                    pilot.discard();
                    throw new IllegalStateException("Unable to mount selected aircraft");
                }
                try {
                    Vec3 heading = Vec3.directionFromRotation(plane.getXRot(), plane.getYRot());
                    Vec3 waypoint = plane.position().add(heading.scale(220));
                    var order = new RuntimeTacticalPilot.LiveOrder(team, mission,
                            waypoint, plane.position(), null, null, null);
                    String scenario = "live-" + plane.getUUID().toString().replace("-", "")
                            + "-" + world.getGameTime();
                    RuntimeTacticalPilot.startLive(scenario, world, plane, pilot, order, MAX_DURATION);
                    enrolled.add(plane.getUUID());
                } catch (RuntimeException failure) {
                    pilot.stopRiding();
                    pilot.discard();
                    throw failure;
                }
            }
        } catch (RuntimeException error) {
            for (UUID aircraft : enrolled) RuntimeTacticalPilot.stop(aircraft);
            source.sendFailure(Component.literal("Squadron enrollment rolled back: " + error.getMessage()));
            return 0;
        }
        source.sendSuccess(() -> Component.literal("WW AI enrolled " + enrolled.size()
                + " real aircraft into explicit team " + team + " / " + mission
                + "; no hostile target until /wwai target or /wwai enemyteam"), false);
        return enrolled.size();
    }

    private static int mission(CommandContext<CommandSourceStack> ctx) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        Entity plane = EntityArgument.getEntity(ctx, "aircraft");
        try {
            var old = RuntimeTacticalPilot.liveOrder(plane.getUUID());
            return update(ctx.getSource(), plane.getUUID(), new RuntimeTacticalPilot.LiveOrder(
                    old.team(), selectedMission(ctx), old.waypoint(), old.home(),
                    old.designatedTarget(), old.hostileTeam(), old.leader()));
        } catch (IllegalArgumentException ex) {
            ctx.getSource().sendFailure(Component.literal(ex.getMessage()));
            return 0;
        }
    }

    private static int target(CommandContext<CommandSourceStack> ctx) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        Entity plane = EntityArgument.getEntity(ctx, "aircraft");
        Entity target = EntityArgument.getEntity(ctx, "target");
        try {
            var old = RuntimeTacticalPilot.liveOrder(plane.getUUID());
            return update(ctx.getSource(), plane.getUUID(), new RuntimeTacticalPilot.LiveOrder(
                    old.team(), old.mission(), old.waypoint(), old.home(),
                    target.getUUID(), null, old.leader()));
        } catch (IllegalArgumentException ex) {
            ctx.getSource().sendFailure(Component.literal(ex.getMessage()));
            return 0;
        }
    }

    private static int enemyTeam(CommandContext<CommandSourceStack> ctx) {
        String own = team(ctx, "team"), enemy = team(ctx, "enemy");
        if (!RuntimeTacticalPilot.validTeam(own) || !RuntimeTacticalPilot.validTeam(enemy)
                || own.equals(enemy)) {
            ctx.getSource().sendFailure(Component.literal("Use two different valid explicit teams"));
            return 0;
        }
        List<RuntimeTacticalPilot.LiveStatus> affected = RuntimeTacticalPilot.liveStatus().stream()
                .filter(s -> own.equals(s.team())
                        && ctx.getSource().getLevel().getEntity(s.aircraft()) != null)
                .toList();
        if (affected.isEmpty()) {
            ctx.getSource().sendFailure(Component.literal("No enrolled aircraft of own team in this dimension"));
            return 0;
        }
        for (var s : affected) {
            var old = RuntimeTacticalPilot.liveOrder(s.aircraft());
            RuntimeTacticalPilot.setLiveOrders(s.aircraft(), new RuntimeTacticalPilot.LiveOrder(
                    old.team(), old.mission(), old.waypoint(), old.home(),
                    null, enemy, old.leader()));
        }
        ctx.getSource().sendSuccess(() -> Component.literal("Explicit " + own
                + " -> hostile team " + enemy + " assigned to " + affected.size()
                + " aircraft; real FOV/range/LOS still required"), false);
        return affected.size();
    }

    private static int waypoint(CommandContext<CommandSourceStack> ctx) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        Entity plane = EntityArgument.getEntity(ctx, "aircraft");
        try {
            var old = RuntimeTacticalPilot.liveOrder(plane.getUUID());
            return update(ctx.getSource(), plane.getUUID(), new RuntimeTacticalPilot.LiveOrder(
                    old.team(), old.mission(), Vec3Argument.getVec3(ctx, "point"), old.home(),
                    old.designatedTarget(), old.hostileTeam(), old.leader()));
        } catch (IllegalArgumentException ex) {
            ctx.getSource().sendFailure(Component.literal(ex.getMessage()));
            return 0;
        }
    }

    private static int leader(CommandContext<CommandSourceStack> ctx) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        Entity plane = EntityArgument.getEntity(ctx, "aircraft");
        Entity leader = EntityArgument.getEntity(ctx, "leader");
        try {
            var old = RuntimeTacticalPilot.liveOrder(plane.getUUID());
            return update(ctx.getSource(), plane.getUUID(), new RuntimeTacticalPilot.LiveOrder(
                    old.team(), old.mission(), old.waypoint(), old.home(),
                    old.designatedTarget(), old.hostileTeam(), leader.getUUID()));
        } catch (IllegalArgumentException ex) {
            ctx.getSource().sendFailure(Component.literal(ex.getMessage()));
            return 0;
        }
    }

    private static int update(CommandSourceStack source, UUID aircraft,
                              RuntimeTacticalPilot.LiveOrder order) {
        try {
            RuntimeTacticalPilot.setLiveOrders(aircraft, order);
        } catch (IllegalArgumentException ex) {
            source.sendFailure(Component.literal(ex.getMessage()));
            return 0;
        }
        source.sendSuccess(() -> Component.literal("WW AI orders updated for " + aircraft
                + ": " + order.team() + "/" + order.mission()), false);
        return 1;
    }

    private static int stopCraft(CommandContext<CommandSourceStack> ctx) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        Entity plane = EntityArgument.getEntity(ctx, "aircraft");
        if (!RuntimeTacticalPilot.stop(plane.getUUID())) {
            ctx.getSource().sendFailure(Component.literal("Selected aircraft is not AI controlled"));
            return 0;
        }
        ctx.getSource().sendSuccess(() -> Component.literal("AI detached from selected aircraft"), false);
        return 1;
    }

    private static int stopTeam(CommandContext<CommandSourceStack> ctx) {
        String requested = team(ctx, "team");
        int stopped = 0;
        for (var s : RuntimeTacticalPilot.liveStatus()) {
            if (s.team().equals(requested)
                    && ctx.getSource().getLevel().getEntity(s.aircraft()) != null
                    && RuntimeTacticalPilot.stop(s.aircraft())) stopped++;
        }
        final int count = stopped;
        ctx.getSource().sendSuccess(() -> Component.literal("Detached " + count
                + " live aircraft from " + requested), false);
        return count;
    }

    private static int status(CommandContext<CommandSourceStack> ctx) {
        var entries = RuntimeTacticalPilot.liveStatus().stream()
                .filter(s -> ctx.getSource().getLevel().getEntity(s.aircraft()) != null)
                .toList();
        if (entries.isEmpty()) {
            ctx.getSource().sendSuccess(() -> Component.literal("No active live aircraft in this dimension"), false);
            return 0;
        }
        for (var s : entries) {
            ctx.getSource().sendSuccess(() -> Component.literal(s.aircraftType() + " "
                    + s.aircraft() + " team=" + s.team() + " mission=" + s.mission()
                    + " target=" + (s.target() == null ? s.hostileTeam() : s.target())
                    + " station_slot=" + s.stationSlot()
                    + " visible_ticks=" + s.observedTicks() + "/" + s.elapsedTicks()
                    + " candidate_checks=" + s.sensorCandidates()
                    + " rejected=" + s.blockedContacts()), false);
        }
        return entries.size();
    }

    private static String team(CommandContext<CommandSourceStack> ctx, String name) {
        return StringArgumentType.getString(ctx, name);
    }

    private static TacticalAirAI.Mission selectedMission(CommandContext<CommandSourceStack> ctx) {
        try {
            return TacticalAirAI.Mission.valueOf(team(ctx, "mission").toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new IllegalArgumentException("Expected mission: PATROL, INTERCEPT, ESCORT, LEVEL_BOMB, DIVE_BOMB, STRAFE, TORPEDO");
        }
    }
}
