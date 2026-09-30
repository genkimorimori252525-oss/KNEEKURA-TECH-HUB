package org.kneekura.observer;

import com.google.gson.JsonObject;
import com.google.gson.JsonArray;
import org.lwjgl.glfw.GLFW;
import org.lwjgl.glfw.GLFWNativeX11;
import org.lwjgl.system.Platform;
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
    private static final AtomicLong TICKS=new AtomicLong();
    static long frames() {return FRAMES.get();}
    static long ticks() {return TICKS.get();}
    private static boolean installed=false;
    public static synchronized void install() {
        if(installed) return; installed=true;
        MinecraftForge.EVENT_BUS.addListener((TickEvent.ClientTickEvent e)->{if(e.phase==TickEvent.Phase.END) TICKS.incrementAndGet();});
        MinecraftForge.EVENT_BUS.addListener((TickEvent.RenderTickEvent e)->{if(e.phase==TickEvent.Phase.END) FRAMES.incrementAndGet();});
    }
    public static void verifyDirectory(Path directory) throws Exception {
        if(!Minecraft.getInstance().gameDirectory.toPath().toRealPath().equals(directory.toRealPath()))
            throw new IllegalStateException("Actual client gameDirectory differs from owned integrated run");
    }
    public static CompletableFuture<JsonObject> capture(Path directory,boolean screenshot) {
        return capture(directory,screenshot,null,null);
    }
    public static CompletableFuture<JsonObject> capture(Path directory,boolean screenshot,JsonObject session,JsonObject query) {
        CompletableFuture<JsonObject> future=new CompletableFuture<>();
        Minecraft.getInstance().execute(()->{
            try {
                Minecraft client=Minecraft.getInstance(); JsonObject out=new JsonObject(); out.addProperty("client_frame_start",FRAMES.get());
                // This scope is covered by the existing response HMAC and run identity.
                // Unsupported platforms retain screenshots but cannot bind native input.
                JsonObject input=new JsonObject(); input.addProperty("platform","unsupported");
                if(Platform.get()==Platform.LINUX) {
                    try {
                        long glfwWindow=client.getWindow().getWindow();
                        long nativeWindow=GLFWNativeX11.glfwGetX11Window(glfwWindow);
                        if(nativeWindow==0) throw new IllegalStateException("No X11 window");
                        int[] width=new int[1],height=new int[1];
                        GLFW.glfwGetWindowSize(glfwWindow,width,height);
                        JsonArray size=new JsonArray(); size.add(width[0]); size.add(height[0]);
                        input.addProperty("process_id",ProcessHandle.current().pid());
                        input.addProperty("process_start",LinuxClientIdentity.processStart());
                        input.addProperty("window_id",Long.toUnsignedString(nativeWindow));
                        input.add("client_size",size);
                        input.addProperty("cursor_mode",GLFW.glfwGetInputMode(glfwWindow,GLFW.GLFW_CURSOR)==GLFW.GLFW_CURSOR_DISABLED?"disabled":"other");
                        input.addProperty("foreground",GLFW.glfwGetWindowAttrib(glfwWindow,GLFW.GLFW_FOCUSED)==GLFW.GLFW_TRUE);
                        input.addProperty("platform","linux-x11");
                    } catch(Exception | LinkageError unavailable) {
                        input=new JsonObject(); input.addProperty("platform","unsupported");
                    }
                }
                out.add("native_input",input);
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
                out.addProperty("client_frame_end",FRAMES.get()); out.addProperty("atomic",false);
                if(session!=null && query!=null && DedicatedSession.role(session.getAsJsonObject("contract")).equals("integrated_client"))
                    out.add("u04_hydra",U04HydraProbe.capture(client,session,query,out));
                future.complete(out);
            } catch(Exception e) {future.completeExceptionally(e);}
        });
        return future;
    }
}
