package org.kneekura.observer;

import com.google.gson.*;
import io.netty.channel.*;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.Connection;
import net.minecraft.network.protocol.game.ClientboundCooldownPacket;
import net.minecraft.network.protocol.game.ClientboundUpdateMobEffectPacket;
import net.minecraft.world.effect.MobEffects;
import java.util.ArrayDeque;
import java.util.concurrent.TimeUnit;

/** Opt-in selected vanilla receipt witness. Every message is forwarded unchanged once. */
final class StaffPacketTrace extends ChannelInboundHandlerAdapter implements AutoCloseable {
    private static final String NAME="kneekura_staff_packet_trace";
    private static final int LIMIT=16;
    private final Connection connection;
    private final Channel channel;
    private final String player,channelId;
    private final int entityId;
    private volatile boolean active,closed;
    private long sequence,glowing,cooldown,unknown,dropped;
    private final ArrayDeque<JsonObject> records=new ArrayDeque<>();

    private StaffPacketTrace(Connection connection,String player,int entityId) {
        this.connection=connection;this.channel=connection.channel();this.player=player;this.entityId=entityId;
        if(channel==null || !connection.isConnected() || connection.isMemoryConnection())throw new IllegalArgumentException("Bound TCP connection required");
        channelId=channel.id().asLongText();
    }
    static StaffPacketTrace install(Connection connection,String player,int entityId) throws Exception {
        StaffPacketTrace trace=new StaffPacketTrace(connection,player,entityId);
        Runnable install=()->{
            if(trace.closed)return;
            ChannelPipeline pipeline=trace.channel.pipeline();
            if(pipeline.get(NAME)!=null || pipeline.get("packet_handler")!=connection)throw new IllegalStateException("Exact owned vanilla packet handler required");
            pipeline.addBefore("packet_handler",NAME,trace);
            if(!trace.closed)trace.active=true;
        };
        try {
            if(trace.channel.eventLoop().inEventLoop())install.run();
            else trace.channel.eventLoop().submit(install).get(2,TimeUnit.SECONDS);
            if(!trace.active)throw new IllegalStateException("Packet witness did not activate");
            return trace;
        } catch(Exception error) {trace.close();throw error;}
    }
    @Override public void channelRead(ChannelHandlerContext ctx,Object message) throws Exception {
        try {
            if(active && !closed && ctx.channel()==channel && connection.channel()==channel && connection.isConnected())record(message);
        } catch(Exception unavailable) {synchronized(this){unknown++;}}
        finally {ctx.fireChannelRead(message);}
    }
    private synchronized void record(Object message) {
        JsonObject row=new JsonObject();
        if(message instanceof ClientboundUpdateMobEffectPacket packet) {
            if(packet.getEntityId()!=entityId || packet.getEffect()!=MobEffects.GLOWING)return;
            row.addProperty("kind","glowing");row.addProperty("entity_id",entityId);
            row.addProperty("effect","minecraft:glowing");row.addProperty("amplifier",packet.getEffectAmplifier());row.addProperty("duration_ticks",packet.getEffectDurationTicks());glowing++;
        } else if(message instanceof ClientboundCooldownPacket packet) {
            if(!BuiltInRegistries.ITEM.getKey(packet.getItem()).toString().equals("kneekura:celestial_staff"))return;
            row.addProperty("kind","cooldown");row.addProperty("item","kneekura:celestial_staff");row.addProperty("duration_ticks",packet.getDuration());cooldown++;
        } else return;
        row.addProperty("sequence",++sequence);row.addProperty("player_uuid",player);records.addLast(row);
        if(records.size()>LIMIT){records.removeFirst();dropped++;}
    }
    synchronized JsonObject snapshot() {
        JsonObject out=new JsonObject();out.addProperty("schema_version",1);out.addProperty("supported",true);
        out.addProperty("scope","SELECTED_VANILLA_RECEIPT_NOT_PROCESSING_ATTESTATION");out.addProperty("player_uuid",player);out.addProperty("entity_id",entityId);out.addProperty("channel_id",channelId);
        out.addProperty("active",active && !closed && connection.channel()==channel && connection.isConnected());
        out.addProperty("sequence",sequence);out.addProperty("glowing_count",glowing);out.addProperty("cooldown_count",cooldown);
        out.addProperty("unknown",unknown);out.addProperty("dropped",dropped);out.addProperty("limit",LIMIT);
        JsonArray recent=new JsonArray();for(JsonObject row:records)recent.add(row.deepCopy());out.add("records",recent);return out;
    }
    @Override public void close() {
        closed=true;active=false;
        Runnable remove=()->{if(channel.pipeline().get(NAME)==this)channel.pipeline().remove(this);};
        try {if(channel.eventLoop().inEventLoop())remove.run();else channel.eventLoop().execute(remove);}
        catch(RuntimeException unavailable){synchronized(this){unknown++;}}
    }
}
