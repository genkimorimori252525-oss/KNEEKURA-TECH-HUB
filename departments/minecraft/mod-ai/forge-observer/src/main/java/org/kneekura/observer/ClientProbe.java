package org.kneekura.observer;

import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HexFormat;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicLong;

/** Loaded reflectively only on physical CLIENT; render work runs on its main thread. */
public final class ClientProbe {
    private static final AtomicLong FRAMES=new AtomicLong();
    private static boolean installed=false;
    public static synchronized void install() {
        if(installed) return; installed=true;
        MinecraftForge.EVENT_BUS.addListener((TickEvent.RenderTickEvent e)->{if(e.phase==TickEvent.Phase.END) FRAMES.incrementAndGet();});
    }
    public static CompletableFuture<JsonObject> capture(Path directory,boolean screenshot) {
        CompletableFuture<JsonObject> future=new CompletableFuture<>();
        Minecraft.getInstance().execute(()->{
            try {
                Minecraft client=Minecraft.getInstance(); JsonObject out=new JsonObject(); out.addProperty("client_frame_start",FRAMES.get());
                out.addProperty("screen",client.screen==null?"none":client.screen.getClass().getName());
                var camera=client.gameRenderer.getMainCamera(); JsonObject pose=new JsonObject();
                pose.addProperty("x",camera.getPosition().x); pose.addProperty("y",camera.getPosition().y); pose.addProperty("z",camera.getPosition().z);
                pose.addProperty("pitch",camera.getXRot()); pose.addProperty("yaw",camera.getYRot()); out.add("camera",pose);
                if(screenshot) {
                    Path imagePath=Files.createTempFile(directory,"capture-", ".png");
                    try(var image=Screenshot.takeScreenshot(client.getMainRenderTarget())) {
                        image.writeToFile(imagePath); if(Files.size(imagePath)>8*1024*1024) throw new IllegalStateException("Screenshot exceeds response budget");
                        byte[] bytes=Files.readAllBytes(imagePath); out.addProperty("png_b64",Base64.getEncoder().encodeToString(bytes));
                        out.addProperty("png_sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
                        out.addProperty("width",image.getWidth()); out.addProperty("height",image.getHeight());
                    } finally {Files.deleteIfExists(imagePath);}
                }
                out.addProperty("client_frame_end",FRAMES.get()); out.addProperty("atomic",false); future.complete(out);
            } catch(Exception e) {future.completeExceptionally(e);}
        });
        return future;
    }
}
