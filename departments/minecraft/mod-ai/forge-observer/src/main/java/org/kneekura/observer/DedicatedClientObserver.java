package org.kneekura.observer;

import com.google.gson.*;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.Connection;
import net.minecraftforge.client.event.ClientPlayerNetworkEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import java.util.concurrent.CompletableFuture;

/** Physical-client-only lifecycle, loaded reflectively; never connects or writes game state. */
public final class DedicatedClientObserver {
    private final ForgeObserver owner;
    private final DedicatedSession.Lifetime lifetime=new DedicatedSession.Lifetime();
    private final JsonObject policy;
    private final String selectedPlayer;
    private boolean attempted;
    private boolean pendingLogin;
    private LocalPlayer boundPlayer;
    private Object boundChannel;
    private int boundEntityId;
    private StaffPacketTrace packetTrace;

    private DedicatedClientObserver(ForgeObserver owner) throws Exception {
        this.owner=owner; JsonObject session=owner.receiverSession();
        DedicatedSession.session(session,session.getAsJsonObject("contract"));
        policy=session.getAsJsonObject("connection_policy").deepCopy();
        selectedPlayer=DedicatedSession.uuid(DedicatedSession.string(session,"player_uuid"));
    }
    public static void install(ForgeObserver owner) throws Exception {MinecraftForge.EVENT_BUS.register(new DedicatedClientObserver(owner));}

    @SubscribeEvent public void login(ClientPlayerNetworkEvent.LoggingIn event) {
        if(attempted) {invalidate("Receiving client reconnect rejected; epoch is consumed");return;}
        attempted=true;
        try {
            Minecraft client=Minecraft.getInstance();Connection connection=event.getConnection();
            DedicatedSession.require(client.player==event.getPlayer() && client.level!=null && !client.hasSingleplayerServer(),"Receiving client requires its actual remote local player");
            DedicatedSession.require(event.getPlayer().getUUID().toString().equals(selectedPlayer),"Logged-in player differs from fixed selected UUID");
            scope(connection);
            lifetime.bind(connection,connection.channel().id().asLongText(),selectedPlayer);boundPlayer=event.getPlayer();boundChannel=connection.channel();
            // Forge fires LoggingIn before handleLogin assigns the server's entity ID.
            pendingLogin=true;
        } catch(Exception failure) {invalidate("Receiving client startup failed: "+failure.getClass().getSimpleName());}
    }
    @SubscribeEvent public void tick(TickEvent.ClientTickEvent event) {
        if(!pendingLogin || event.phase!=TickEvent.Phase.END)return;
        pendingLogin=false;
        try {
            Minecraft client=Minecraft.getInstance();
            DedicatedSession.require(client.player!=null && client.player==boundPlayer && client.level!=null && !client.hasSingleplayerServer()
                && client.getConnection()!=null,"Original login player is unavailable");
            Connection connection=client.getConnection().getConnection();scope(connection);
            DedicatedSession.require(connection.channel()==boundChannel,"Original login channel changed");
            lifetime.check(connection,connection.channel().id().asLongText(),client.player.getUUID().toString());
            boundEntityId=boundPlayer.getId();
            ClientProbe.install();owner.startReceiver(client.gameDirectory.toPath(),this::capture,()->{
                if(owner.hasVerifiedStaffTrace())packetTrace=StaffPacketTrace.install(connection,selectedPlayer,boundEntityId);
                return null;
            });
        } catch(Exception failure) {invalidate("Receiving client startup failed: "+failure.getClass().getSimpleName());}
    }
    @SubscribeEvent public void logout(ClientPlayerNetworkEvent.LoggingOut event) {
        // Forge can emit a null logout before the first login. It grants no authority.
        if(attempted)invalidate("Receiving client disconnected; epoch is consumed");
    }
    @SubscribeEvent public void clonePlayer(ClientPlayerNetworkEvent.Clone event) {
        if(attempted)invalidate("Receiving player was replaced; fixed no-respawn scenario invalidated");
    }
    private void invalidate(String reason) {pendingLogin=false;lifetime.invalidate();if(packetTrace!=null)packetTrace.close();owner.invalidateReceiver(reason);}
    private JsonObject scope(Connection connection) {
        DedicatedSession.require(connection!=null && connection.channel()!=null && connection.channel().isActive(),"Client channel is not active");
        return DedicatedSession.connection(policy,selectedPlayer,true,connection.isConnected(),connection.isMemoryConnection(),
            connection.channel().id().asLongText(),connection.channel().localAddress(),connection.channel().remoteAddress());
    }
    private JsonObject current(Minecraft client) {
        DedicatedSession.require(client.player!=null && client.player==boundPlayer && client.player.getId()==boundEntityId && client.level!=null && !client.hasSingleplayerServer()
            && client.getConnection()!=null,"Bound dedicated client player is unavailable");
        Connection connection=client.getConnection().getConnection();JsonObject result=scope(connection);
        DedicatedSession.require(connection.channel()==boundChannel,"Bound dedicated client channel changed");
        lifetime.check(connection,connection.channel().id().asLongText(),client.player.getUUID().toString());return result;
    }
    private static JsonArray vector(double x,double y,double z) {JsonArray result=new JsonArray();result.add(x);result.add(y);result.add(z);return result;}

    private CompletableFuture<JsonObject> capture(JsonObject supplied) {
        CompletableFuture<JsonObject> future=new CompletableFuture<>();JsonObject query=supplied.deepCopy();
        Minecraft.getInstance().execute(()->{
            try {
                Minecraft client=Minecraft.getInstance();JsonObject connection=current(client);LocalPlayer player=client.player;
                String dimension=client.level.dimension().location().toString();
                DedicatedSession.query(query,selectedPlayer,dimension);boolean includeStaff=StaffStateQuery.enabled(query);
                long tick=ClientProbe.ticks(),frame=ClientProbe.frames(),log=owner.logSequence();
                JsonObject out=owner.receiverBase();out.addProperty("observation_side","logical_client");
                out.addProperty("client_tick_start",tick);out.addProperty("client_frame_start",frame);out.addProperty("log_sequence_start",log);
                out.add("server_tick_start",JsonNull.INSTANCE);out.add("server_tick_end",JsonNull.INSTANCE);out.addProperty("server_tick_scope","NOT_LOCALLY_OBSERVED");
                out.add("connection",connection.deepCopy());
                JsonObject row=new JsonObject();row.addProperty("uuid",player.getUUID().toString());row.addProperty("dimension",dimension);
                row.add("position",vector(player.getX(),player.getY(),player.getZ()));var velocity=player.getDeltaMovement();
                row.add("velocity",vector(velocity.x,velocity.y,velocity.z));row.addProperty("health",player.getHealth());
                row.add("target_uuid",JsonNull.INSTANCE);row.add("connection",connection.deepCopy());
                if(includeStaff)row.add("staff_state",StaffStateCapture.capture(player,"logical_client"));
                JsonArray entities=new JsonArray();entities.add(row);out.add("entities",entities);out.add("blocks",new JsonArray());
                out.addProperty("entities_truncated",false);out.addProperty("entities_scanned",1);
                boolean screenshot=query.has("screenshot") && query.get("screenshot").getAsBoolean();
                ClientProbe.capture(owner.receiverDirectory(),screenshot).whenComplete((image,failure)->{
                    try {
                        if(failure!=null)throw new IllegalStateException("Client image capture failed",failure);
                        JsonObject after=current(Minecraft.getInstance());
                        DedicatedSession.require(after.equals(connection),"Connection changed during capture");
                        DedicatedSession.require(Minecraft.getInstance().level.dimension().location().toString().equals(dimension),"Client dimension changed during capture");
                        for(var entry:image.entrySet())out.add(entry.getKey(),entry.getValue());
                        out.add("staff_client_trace",owner.staffClientTrace());
                        out.add("staff_packet_trace",packetTrace==null?StaffTrace.unavailable(false,"Fixed staff packet witness is absent from verified build"):packetTrace.snapshot());
                        out.addProperty("client_frame_start",frame);out.addProperty("client_frame_end",ClientProbe.frames());
                        out.addProperty("client_tick_end",ClientProbe.ticks());out.addProperty("log_sequence_end",owner.logSequence());
                        out.addProperty("atomic",false);out.addProperty("config_observation","Explicit registered files, not every in-memory Forge config value");
                        future.complete(out);
                    } catch(Exception e) {future.completeExceptionally(e);}
                });
            } catch(Exception e) {future.completeExceptionally(e);}
        });return future;
    }
}
