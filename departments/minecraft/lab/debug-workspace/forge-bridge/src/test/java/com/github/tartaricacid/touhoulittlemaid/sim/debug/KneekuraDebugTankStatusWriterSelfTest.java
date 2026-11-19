package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.io.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

/** Deterministic real writer checks under the actual lock and queue, without a worker race. */
public final class KneekuraDebugTankStatusWriterSelfTest {
    static Field field(String name) throws Exception { var f=KneekuraDebugEvidenceWriter.class.getDeclaredField(name);f.setAccessible(true);return f; }
    static void set(String name,Object value) throws Exception { field(name).set(null,value); }
    static void check(boolean value,String reason) { if(!value)throw new AssertionError(reason); }
    @SuppressWarnings("unchecked")
    public static void main(String[] args) throws Exception {
        var root=Files.createTempDirectory("tank-status-writer-test");
        var config=new KneekuraDebugEnv.Config(true,"s","r",1,"snap","n".repeat(32),root.resolve("ready"),root,root,
                root.resolve("raw"),root.resolve("target"),root.resolve("stop"),root.resolve("ack"),"KNEEKURA_DEBUG_WORLD");
        var queue=(BlockingQueue<Object>)field("QUEUE").get(null);
        var claim=KneekuraDebugEvidenceWriter.class.getDeclaredMethod("claimQueuedRow");claim.setAccessible(true);
        JsonObject payload=new JsonObject();payload.addProperty("schema","kneekura.tank-presentation-status/v1");
        List<List<Long>> timelines=new ArrayList<>();
        for(boolean enabled:new boolean[]{false,true}) {
            queue.clear();set("pendingTankStatus",null);set("tankStatusSuppressedTotal",0L);set("seq",0L);set("droppedTotal",0L);
            set("lastAnyClientTick",Long.MIN_VALUE);set("lastAnyServerTick",Long.MIN_VALUE);set("accepting",true);set("sealed",false);
            set("broken",false);set("writerBusy",false);set("workerStarted",true);set("identityKey",config.identityKey());
            set("out",new BufferedWriter(new StringWriter()));set("file",root.resolve("raw.jsonl"));
            List<Long> ticks=new ArrayList<>();long previous=0;
            for(long tick:new long[]{0,5,10,20,25,40}) {
                if(enabled)KneekuraDebugEvidenceWriter.recordTankStatus(config,0,tick,tick,payload);
                KneekuraDebugEvidenceWriter.maybeClientHeartbeat(config,tick,tick,false);
                for(Object value;(value=claim.invoke(null))!=null;) {
                    var rowMethod=value.getClass().getDeclaredMethod("row");rowMethod.setAccessible(true);Object row=rowMethod.invoke(value);
                    var lineMethod=row.getClass().getDeclaredMethod("line");lineMethod.setAccessible(true);
                    var json=JsonParser.parseString((String)lineMethod.invoke(row)).getAsJsonObject();
                    long seq=json.get("writerSeq").getAsLong();check(seq>previous,"strict source sequence after low-priority drain");previous=seq;
                    if(json.get("lane").getAsString().equals("CLIENT_TICK"))ticks.add(json.getAsJsonObject("payload").get("localClientTick").getAsLong());
                    set("writerBusy",false);
                }
            }
            timelines.add(ticks);check(field("droppedTotal").getLong(null)==0,"status must not add evidence drops");
            // Queue full and one free slot: status never takes a regular row's capacity.
            Class<?> rowClass=Class.forName(KneekuraDebugEvidenceWriter.class.getName()+"$QueuedRow");
            var ctor=rowClass.getDeclaredConstructor(String.class,CompletableFuture.class,KneekuraDebugImageArtifact.class);ctor.setAccessible(true);
            Object dummy=ctor.newInstance("{}",null,null);
            for(int i=0;i<KneekuraDebugEvidenceWriter.QUEUE_CAPACITY;i++)queue.add(dummy);
            KneekuraDebugEvidenceWriter.recordTankStatus(config,0,60,60L,payload);
            check(queue.size()==KneekuraDebugEvidenceWriter.QUEUE_CAPACITY,"full queue preserved");
            check(field("pendingTankStatus").get(null)==null,"full queue suppresses optional status");
            queue.poll();KneekuraDebugEvidenceWriter.recordTankStatus(config,0,61,61L,payload);
            check(queue.remainingCapacity()==1,"status does not consume last regular slot");
            queue.add(dummy);check(field("droppedTotal").getLong(null)==0,"regular evidence remains admissible");
            check(field("lastAnyClientTick").getLong(null)==40,"neither status acceptance nor suppression alters heartbeat clock");
            queue.clear();set("pendingTankStatus",null);set("writerBusy",false);KneekuraDebugEvidenceWriter.sealAndFlush(0);
        }
        check(timelines.get(0).equals(List.of(0L,20L,40L))&&timelines.get(0).equals(timelines.get(1)),"ON/OFF heartbeat ticks identical");
        System.out.println("Actual tank status writer: heartbeat, saturation, recovery and sequence checks passed");
    }
}
