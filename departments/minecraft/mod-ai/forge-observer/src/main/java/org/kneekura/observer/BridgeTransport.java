package org.kneekura.observer;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/** JDK17-only loopback transport. The handler owns game-thread scheduling. */
public final class BridgeTransport implements AutoCloseable {
    /** Brigadier's callback reports success independently of the integer result.
     * Zero can be a successful query; absent callbacks remain unconfirmed. */
    public static final class CommandResult {
        private boolean observed;
        private boolean failed;
        public void accept(boolean success) { observed=true; failed |= !success; }
        public String outcome() { return !observed ? "UNKNOWN" : failed ? "FAIL" : "PASS"; }
    }

    public interface Handler { String handle(String path, String body, String nonce) throws Exception; }
    private static final Set<String> PATHS = Set.of("/v1/handshake", "/v1/observe", "/v1/logs", "/v1/client", "/v1/command", "/v1/operation");
    private final String token, run, epoch;
    private final Handler handler;
    private HttpServer server;
    private ExecutorService executor;

    public BridgeTransport(String token, String run, String epoch, Handler handler) {
        if (token == null || !token.matches("[a-f0-9]{64}") || run == null || epoch == null) throw new IllegalArgumentException("Invalid session");
        this.token=token; this.run=run; this.epoch=epoch; this.handler=handler;
    }

    public int start() throws IOException {
        server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),8);
        executor=Executors.newFixedThreadPool(2, r -> { Thread t=new Thread(r,"kneekura-observer-http"); t.setDaemon(true); return t; });
        server.setExecutor(executor); server.createContext("/",this::serve); server.start();
        return server.getAddress().getPort();
    }

    private static boolean same(String a, String b) {
        return b != null && MessageDigest.isEqual(a.getBytes(StandardCharsets.UTF_8),b.getBytes(StandardCharsets.UTF_8));
    }

    private void serve(HttpExchange ex) throws IOException {
        String path=ex.getRequestURI().getPath(), method=ex.getRequestMethod();
        String nonce=ex.getRequestHeaders().getFirst("X-Kneekura-Nonce");
        String host=ex.getRequestHeaders().getFirst("Host");
        if (!ex.getRemoteAddress().getAddress().isLoopbackAddress() ||
            !same("127.0.0.1:"+server.getAddress().getPort(),host) ||
            ex.getRequestHeaders().containsKey("Origin") ||
            !same("Bearer "+token,ex.getRequestHeaders().getFirst("Authorization")) ||
            !same(run,ex.getRequestHeaders().getFirst("X-Kneekura-Run")) ||
            !same(epoch,ex.getRequestHeaders().getFirst("X-Kneekura-Epoch")) ||
            nonce==null || !nonce.matches("[a-f0-9]{32}")) {
            ex.sendResponseHeaders(403,-1); ex.close(); return;
        }
        int status=200; String result;
        try {
            if (!PATHS.contains(path) || ex.getRequestURI().getRawQuery()!=null ||
                !method.equals(path.equals("/v1/handshake")?"GET":"POST")) throw new IllegalArgumentException("Unsupported path");
            byte[] input=ex.getRequestBody().readNBytes(16385);
            if (input.length>16384) throw new IllegalArgumentException("Request too large");
            result=handler.handle(path,new String(input,StandardCharsets.UTF_8),nonce);
            if (result.getBytes(StandardCharsets.UTF_8).length>16*1024*1024) throw new IllegalArgumentException("Response too large");
        } catch (Exception failure) {
            status=409; result="{\"status\":\"ERROR\",\"outcome\":\"UNKNOWN\",\"retry_allowed\":false}";
        }
        byte[] payload=result.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type","application/json; charset=utf-8");
        ex.getResponseHeaders().set("Cache-Control","no-store");
        ex.getResponseHeaders().set("X-Kneekura-Signature",sign(token,(method+"\n"+path+"\n"+nonce+"\n").getBytes(StandardCharsets.UTF_8),payload));
        ex.sendResponseHeaders(status,payload.length);
        try (var out=ex.getResponseBody()) { out.write(payload); }
        finally { ex.close(); }
    }

    public static String sign(String token, byte[] prefix, byte[] payload) {
        try {
            Mac mac=Mac.getInstance("HmacSHA256"); mac.init(new SecretKeySpec(token.getBytes(StandardCharsets.UTF_8),"HmacSHA256"));
            mac.update(prefix); return HexFormat.of().formatHex(mac.doFinal(payload));
        } catch (Exception e) { throw new IllegalStateException("HMAC unavailable",e); }
    }
    @Override public void close() {
        if (server!=null) server.stop(0);
        if (executor!=null) executor.shutdownNow();
    }
}
