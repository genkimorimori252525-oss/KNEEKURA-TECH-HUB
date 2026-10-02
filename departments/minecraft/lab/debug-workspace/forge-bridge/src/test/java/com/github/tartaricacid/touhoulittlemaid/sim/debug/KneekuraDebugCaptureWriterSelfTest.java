package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** Exercises the real existing writer class and actual Gson/logging dependencies; starts no Minecraft. */
public final class KneekuraDebugCaptureWriterSelfTest {
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("capture-writer-test");
        var config = new KneekuraDebugEnv.Config(true,"session","run",1,"snapshot","n".repeat(32),
                root.resolve("ready.json"),root,root,root.resolve("evidence/raw"),root.resolve("target.json"),
                root.resolve("stop.json"),root.resolve("ack.json"),"KNEEKURA_DEBUG_WORLD");
        byte[] bytes = new byte[4*1024*1024];
        byte[] header = {(byte)137,80,78,71,13,10,26,10}; System.arraycopy(header,0,bytes,0,8);
        String hash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        JsonObject payload = new JsonObject(); payload.addProperty("imageHash",hash); payload.addProperty("imageBytes",bytes.length);
        payload.addProperty("imagePath","evidence/raw/visual/"+hash+".png");
        JsonObject identity = new JsonObject(); identity.addProperty("experimentId","experiment"); payload.add("identity",identity);
        Field lockField = KneekuraDebugEvidenceWriter.class.getDeclaredField("LOCK"); lockField.setAccessible(true);
        List<CompletableFuture<String>> accepted = new ArrayList<>();
        synchronized(lockField.get(null)) {
            for(int i=0;i<4;i++) accepted.add(KneekuraDebugEvidenceWriter.recordVisualObservedAsync(config,0,i,1L,bytes,payload));
            var rejected = KneekuraDebugEvidenceWriter.recordVisualObservedAsync(config,0,5,1L,bytes,payload);
            if(!rejected.isCompletedExceptionally()) throw new AssertionError("image queue exceeded16MiB");
        }
        for(var proof:accepted) if(!proof.get(5,TimeUnit.SECONDS).matches("[a-f0-9]{64}")) throw new AssertionError("invalid row proof");
        if(Files.size(root.resolve("evidence/raw/visual/"+hash+".png"))!=bytes.length)throw new AssertionError("ack before artifact");
        Field pending = KneekuraDebugEvidenceWriter.class.getDeclaredField("pendingImageBytes");pending.setAccessible(true);
        if(pending.getInt(null)!=0)throw new AssertionError("image budget not released");
        var flush = KneekuraDebugEvidenceWriter.sealAndFlush(1000);
        if(!flush.clean()||flush.remainingQueue()!=0)throw new AssertionError("unclean capture shutdown");
        if(!KneekuraDebugEvidenceWriter.recordVisualObservedAsync(config,0,7,1L,bytes,payload).isCompletedExceptionally())
            throw new AssertionError("accepted after finalization");
        System.out.println("real writer image checks=6");
    }
}
