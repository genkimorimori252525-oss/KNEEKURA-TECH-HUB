package org.kneekura.techhub.warfarewings.trace;

import com.mojang.brigadier.context.CommandContext;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.UUID;

/**
 * Experimental, operator-only manual launcher for the same autopilot pathway
 * exercised by GameTests. /wwai patrol controls a single empty nearby real
 * Warfare Wings airplane for up to 900 ticks; /wwai stop removes its owned
 * dummy pilot without deleting the aircraft. No combat or weapon commands.
 */
final class TacticalPilotCommands {
    private static final Map<UUID, UUID> OWNED = new HashMap<>();

    private TacticalPilotCommands() {}

    static void register(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("wwai")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("patrol").executes(TacticalPilotCommands::patrol))
                .then(Commands.literal("stop").executes(TacticalPilotCommands::stop)));
    }

    static void onServerStopping(ServerStoppingEvent event) {
        OWNED.clear();
    }

    private static int patrol(CommandContext<CommandSourceStack> ctx) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        ServerPlayer operator = ctx.getSource().getPlayerOrException();
        UUID old = OWNED.get(operator.getUUID());
        if (old != null && RuntimeTacticalPilot.active(old)) {
            ctx.getSource().sendFailure(Component.literal("You already control an aircraft; /wwai stop first"));
            return 0;
        }
        ServerLevel level = operator.serverLevel();
        List<Entity> planes = level.getEntities(operator,
                operator.getBoundingBox().inflate(20),
                e -> !e.isRemoved()
                        && BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getNamespace()
                        .equals("warfare_wings"));
        if (planes.size() != 1) {
            ctx.getSource().sendFailure(Component.literal(
                    "Exactly one nearby Warfare Wings airplane required (found " + planes.size() + ")"));
            return 0;
        }
        Entity plane = planes.get(0);
        if (!plane.getPassengers().isEmpty()) {
            ctx.getSource().sendFailure(Component.literal("Aircraft is already crewed"));
            return 0;
        }
        // Flight testing against a grounded vehicle can cause unreviewed
        // runway/taxi behavior; only remotely pilot an already airborne one.
        if (plane.onGround()) {
            ctx.getSource().sendFailure(Component.literal("Research autopilot requires an airborne aircraft"));
            return 0;
        }
        ArmorStand pilot = EntityType.ARMOR_STAND.create(level);
        if (pilot == null) throw new IllegalStateException("Cannot create IA pilot");
        pilot.moveTo(plane.getX(), plane.getY(), plane.getZ());
        pilot.setNoGravity(true);
        pilot.setInvisible(true);
        pilot.setInvulnerable(true);
        level.addFreshEntity(pilot);
        if (!pilot.startRiding(plane, true)) {
            pilot.discard();
            throw new IllegalStateException("Could not mount IA test pilot");
        }
        Vec3 look = operator.getLookAngle();
        Vec3 objective = plane.position().add(look.x * 220, Math.max(-30, look.y * 70), look.z * 220);
        String scenario = "op-" + operator.getUUID().toString().replace("-", "")
                + "-" + level.getGameTime();
        try {
            IaRuntimeAccess.setEngineTarget(plane, 1f);
            RuntimeTacticalPilot.start(scenario, level, plane, pilot,
                    TacticalAirAI.Mission.PATROL, objective, plane.position(),
                    null, null, null, 900, true);
        } catch (RuntimeException ex) {
            pilot.stopRiding();
            pilot.discard();
            throw ex;
        }
        OWNED.put(operator.getUUID(), plane.getUUID());
        ctx.getSource().sendSuccess(() -> Component.literal("WW AI patrol bound to "
                + BuiltInRegistries.ENTITY_TYPE.getKey(plane.getType())
                + "; 900 ticks maximum, controls logged; /wwai stop to detach"), false);
        return 1;
    }

    private static int stop(CommandContext<CommandSourceStack> ctx) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        ServerPlayer operator = ctx.getSource().getPlayerOrException();
        UUID aircraft = OWNED.remove(operator.getUUID());
        if (aircraft == null || !RuntimeTacticalPilot.stop(aircraft)) {
            ctx.getSource().sendFailure(Component.literal("No active research aircraft for this operator"));
            return 0;
        }
        ctx.getSource().sendSuccess(() -> Component.literal("WW AI pilot detached; aircraft retained"), false);
        return 1;
    }
}
