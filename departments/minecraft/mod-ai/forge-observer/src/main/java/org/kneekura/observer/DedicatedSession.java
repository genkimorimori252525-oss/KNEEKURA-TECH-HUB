package org.kneekura.observer;

import com.google.gson.*;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** Strict, game-independent scope checks shared by the two opt-in dedicated roles. */
final class DedicatedSession {
    private static final Gson JSON=new GsonBuilder().disableHtmlEscaping().serializeNulls().create();
    private DedicatedSession() {}
    static void require(boolean ok,String message) { if(!ok) throw new IllegalArgumentException(message); }
    static String string(JsonObject value,String field) {
        JsonElement e=value.get(field);
        require(e!=null && e.isJsonPrimitive() && e.getAsJsonPrimitive().isString(),"Expected string: "+field);
        return e.getAsString();
    }
    static int integer(JsonObject value,String field,int low,int high) {
        JsonElement e=value.get(field);
        require(e!=null && e.isJsonPrimitive() && e.getAsJsonPrimitive().isNumber()
                && e.getAsString().matches("0|[1-9][0-9]*"),"Expected integer: "+field);
        int result=Integer.parseInt(e.getAsString()); require(result>=low && result<=high,"Integer out of bounds: "+field); return result;
    }
    static String uuid(String value) {
        require(UUID.fromString(value).toString().equals(value),"Canonical UUID required"); return value;
    }
    static String role(JsonObject identity) {
        int schema=integer(identity,"schema_version",1,3);
        if(schema==1) {
            for(String field:List.of("session_role","runtime_scope","dependency_inventory_hash","target_selection_hash"))
                require(!identity.has(field),"Legacy contract cannot select dedicated scope");
            return "legacy";
        }
        String role=string(identity,"session_role");
        if(schema==3) {
            require(role.equals("integrated_client") && string(identity,"physical_side").equals("client")
                && string(identity,"logical_side").equals("server"),"Integrated client side/role mismatch");
            for(String key:List.of("connection_policy","connection_policy_hash","server_contract","server_contract_hash","player_uuid","run_directory_id","run_directory_template_hash"))
                require(!identity.has(key),"Integrated world cannot claim dedicated socket/directory identity");
            return role;
        }
        require(!identity.has("target_selection_hash"),"Selected target dependency requires schema3");
        require(Set.of("dedicated_server","dedicated_client").contains(role),"Unknown dedicated role");
        String side=role.equals("dedicated_client")?"client":"server";
        require(string(identity,"physical_side").equals(side) && string(identity,"logical_side").equals(side),"Dedicated role side mismatch");
        if(side.equals("client")) {
            for(String key:List.of("world_id","world_template_hash","world_seed"))require(!identity.has(key),"Receiving client cannot claim local server-world identity");
        } else {
            for(String key:List.of("run_directory_id","run_directory_template_hash","server_contract_hash","player_uuid"))require(!identity.has(key),"Server cannot claim receiving-client directory identity");
        }
        return role;
    }
    static void policy(JsonObject p) {
        require(p.keySet().equals(Set.of("host","port","player_uuids")),"Exact connection policy fields required");
        require(string(p,"host").equals("127.0.0.1"),"Only explicit IPv4 loopback is allowed");
        integer(p,"port",1,65535);
        JsonElement ids=p.get("player_uuids");
        require(ids!=null && ids.isJsonArray() && ids.getAsJsonArray().size()>=1 && ids.getAsJsonArray().size()<=2,"One or two selected players required");
        Set<String> seen=new HashSet<>();
        for(JsonElement e:ids.getAsJsonArray()) {
            require(e.isJsonPrimitive() && e.getAsJsonPrimitive().isString(),"Player UUID must be a string");
            require(seen.add(uuid(e.getAsString())),"Duplicate selected player");
        }
    }
    static void selected(JsonObject policy,String player) {
        uuid(player); boolean found=false;
        for(JsonElement e:policy.getAsJsonArray("player_uuids")) found|=e.getAsString().equals(player);
        require(found,"Player not in fixed connection policy");
    }
    static void query(JsonObject query,String player,String dimension) {
        require(Set.of("entity_uuids","dimension","limit","staff_state","screenshot").containsAll(query.keySet()),"Unsupported dedicated query field");
        if(query.has("entity_uuids")) {
            JsonElement ids=query.get("entity_uuids");
            require(ids.isJsonArray() && ids.getAsJsonArray().size()==1,"Exactly one selected player required");
            JsonElement e=ids.getAsJsonArray().get(0);
            require(e.isJsonPrimitive() && e.getAsJsonPrimitive().isString() && e.getAsString().equals(player),"Query player differs from selected player");
        }
        if(query.has("dimension")) require(string(query,"dimension").equals(dimension),"Query dimension differs from selected player");
        if(query.has("limit")) integer(query,"limit",1,1);
        for(String field:List.of("staff_state","screenshot")) if(query.has(field))
            require(query.get(field).isJsonPrimitive() && query.get(field).getAsJsonPrimitive().isBoolean(),"Boolean required: "+field);
    }
    static JsonObject endpoint(SocketAddress address) {
        require(address instanceof InetSocketAddress,"Numeric TCP socket endpoint required");
        InetSocketAddress socket=(InetSocketAddress)address;
        require(!socket.isUnresolved() && socket.getAddress()!=null && socket.getAddress().getHostAddress().equals("127.0.0.1"),"Socket is not exact IPv4 loopback");
        require(socket.getPort()>0 && socket.getPort()<=65535,"Invalid socket port");
        JsonObject out=new JsonObject(); out.addProperty("host","127.0.0.1"); out.addProperty("port",socket.getPort()); return out;
    }
    static JsonObject connection(JsonObject p,String player,boolean receiver,boolean connected,boolean memory,String channel,SocketAddress local,SocketAddress remote) {
        policy(p); selected(p,player);
        require(connected && !memory,"A live dedicated TCP connection is required");
        require(channel!=null && !channel.isEmpty() && channel.length()<=256,"Bounded channel identity required");
        JsonObject l=endpoint(local),r=endpoint(remote);
        require((receiver?r:l).get("port").getAsInt()==integer(p,"port",1,65535),"Connection does not use registered server port");
        JsonObject out=new JsonObject(); out.addProperty("player_uuid",player); out.addProperty("connected",true); out.addProperty("memory",false);
        out.addProperty("channel_id",channel); out.add("local",l); out.add("remote",r); return out;
    }
    static JsonElement sorted(JsonElement value) {
        if(value.isJsonObject()) {JsonObject out=new JsonObject(); for(String k:new TreeSet<>(value.getAsJsonObject().keySet()))out.add(k,sorted(value.getAsJsonObject().get(k)));return out;}
        if(value.isJsonArray()) {JsonArray out=new JsonArray();for(JsonElement e:value.getAsJsonArray())out.add(sorted(e));return out;}
        return value;
    }
    static String hash(JsonElement value) {
        try {return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(JSON.toJson(sorted(value)).getBytes(StandardCharsets.UTF_8)));}
        catch(Exception e) {throw new IllegalStateException(e);}
    }
    static void runtimeScope(JsonObject identity) {
        require(string(identity,"runtime_scope").equals("TARGET_CODE_AND_DEPENDENCY_BYTES"),"Unsupported runtime verification scope");
        require(string(identity,"dependency_inventory_hash").matches("[0-9a-f]{64}"),"Invalid dependency inventory digest");
    }
    static void session(JsonObject session,JsonObject identity) {
        String role=role(identity); if(role.equals("legacy")) return;
        runtimeScope(identity);
        if(role.equals("integrated_client")) {
            require(string(identity,"target_selection_hash").matches("[0-9a-f]{64}"),"Invalid target selection digest");
            require(string(session,"world_layout").equals("client") && !string(session,"world").isEmpty(),"Integrated client requires its owned client-layout world");
            for(String key:List.of("connection_policy","connection_policy_hash","server_contract","server_contract_hash","player_uuid","run_directory_id","run_directory_template_hash"))
                require(!session.has(key),"Integrated session cannot contain dedicated socket/directory authority");
            return;
        }
        JsonObject policy=session.getAsJsonObject("connection_policy"); policy(policy);
        require(hash(policy).equals(string(identity,"connection_policy_hash")),"Session connection policy hash mismatch");
        require(identity.has("connection_policy") && hash(identity.get("connection_policy")).equals(hash(policy)),"Contract policy mismatch");
        if(role.equals("dedicated_client")) {
            require(!session.has("world") && !session.has("world_layout"),"Receiver session cannot contain a local world");
            String player=uuid(string(identity,"player_uuid")); selected(policy,player);
            require(player.equals(string(session,"player_uuid")),"Session player mismatch");
            JsonObject server=session.getAsJsonObject("server_contract");
            require(role(server).equals("dedicated_server"),"Referenced server must have dedicated role");
            runtimeScope(server);
            JsonObject serverPolicy=server.getAsJsonObject("connection_policy");policy(serverPolicy);
            require(hash(serverPolicy).equals(string(server,"connection_policy_hash")),"Referenced server policy body mismatch");
            String hash=hash(server);
            require(hash.equals(string(identity,"server_contract_hash")) && hash.equals(string(session,"server_contract_hash")),"Server contract hash mismatch");
            require(string(server,"connection_policy_hash").equals(string(identity,"connection_policy_hash")),"Server policy mismatch");
            for(String key:List.of("build_artifact_hash","source_revision")) require(string(server,key).equals(string(identity,key)),"Server target identity mismatch: "+key);
        }
    }
    static void marker(JsonObject marker,JsonObject identity,String directory) {
        require(string(marker,"directory").equals(directory),"Owned directory marker mismatch");
        JsonElement fresh=marker.get("fresh");
        require(fresh!=null && fresh.isJsonPrimitive() && fresh.getAsJsonPrimitive().isBoolean() && !fresh.getAsBoolean(),"Launch must consume the prepared marker");
        if(role(identity).equals("dedicated_client")) {
            require(string(marker,"kind").equals("client_run_directory"),"Dedicated client directory required");
            for(String key:List.of("world","world_id","world_seed","world_template_hash","world_layout"))require(!marker.has(key),"Client marker cannot stand in for a server world");
            for(String key:List.of("run_directory_id","run_directory_template_hash"))require(string(marker,key).equals(string(identity,key)),"Client directory identity mismatch: "+key);
        } else {
            require(!marker.has("kind") || !string(marker,"kind").equals("client_run_directory"),"Client directory is not a server world");
            if(role(identity).equals("integrated_client")) {
                require(string(marker,"world_layout").equals("client"),"Integrated client requires client save layout");
                java.nio.file.Path world=java.nio.file.Path.of(string(marker,"world"));
                require(world.isAbsolute() && world.equals(world.normalize()) && world.getParent().equals(java.nio.file.Path.of(directory).resolve("saves"))
                    && world.getFileName().toString().codePoints().allMatch(c->Character.isLetterOrDigit(c) || c=='_' || c=='-'),"Integrated world must be one owned client save");
            } else require(!marker.has("world_layout") || string(marker,"world_layout").equals("server"),"Dedicated server requires server world layout");
            for(String key:List.of("world_id","world_template_hash"))require(string(marker,key).equals(string(identity,key)),"Server marker identity mismatch: "+key);
        }
    }
    /** Exactly one live connection per process epoch; an invalidation is terminal. */
    static final class Lifetime {
        private Object connection;
        private String channel,player;
        private boolean consumed,valid;
        synchronized void bind(Object c,String channel,String player) {
            require(!consumed && c!=null && channel!=null && !channel.isEmpty(),"Connection epoch already consumed");
            uuid(player); consumed=true; valid=true; connection=c; this.channel=channel; this.player=player;
        }
        synchronized void check(Object c,String channel,String player) {
            require(valid && connection==c && this.channel.equals(channel) && this.player.equals(player),"Bound client connection changed");
        }
        synchronized void invalidate() {valid=false;consumed=true;}
    }
}
