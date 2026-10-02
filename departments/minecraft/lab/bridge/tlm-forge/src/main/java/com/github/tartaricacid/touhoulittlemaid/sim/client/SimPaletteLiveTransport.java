package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * palette frame を loopback TCP へ送る latest-only transport。
 *
 * <p>描画スレッドは {@link #offer} で UUID ごとの最新 frame を置き換えるだけ。接続、encode、
 * write は daemon thread が担う。受信側が止まっていても履歴や送信待ちを積み上げない。
 */
public final class SimPaletteLiveTransport implements AutoCloseable {
    public static final int DEFAULT_PORT = 8778;
    private static final int CONNECT_TIMEOUT_MS = 200;
    private static final long RETRY_MS = 1000L;

    private final int port;
    private final ConcurrentHashMap<UUID, SimPaletteLiveProtocol.Frame> pending = new ConcurrentHashMap<>();
    private final Object signal = new Object();
    private final AtomicBoolean started = new AtomicBoolean();
    private volatile boolean closed;
    private volatile Socket socket;
    private volatile DataOutputStream out;
    private Thread worker;

    public SimPaletteLiveTransport(int port) {
        if (port < 1 || port > 65535) {
            throw new IllegalArgumentException("invalid live palette port: " + port);
        }
        this.port = port;
    }

    public void offer(SimPaletteLiveProtocol.Frame frame) {
        if (closed || frame == null) {
            return;
        }
        pending.put(frame.uuid(), frame);
        startWorker();
        synchronized (signal) {
            signal.notifyAll();
        }
    }

    private void startWorker() {
        if (!started.compareAndSet(false, true)) {
            return;
        }
        worker = new Thread(this::run, "tlm-live-palette");
        worker.setDaemon(true);
        worker.start();
    }

    private void run() {
        long retryAt = 0L;
        while (!closed) {
            if (pending.isEmpty()) {
                awaitSignal(250L);
                continue;
            }
            long now = System.currentTimeMillis();
            if (out == null && now < retryAt) {
                awaitSignal(Math.min(250L, retryAt - now));
                continue;
            }
            try {
                if (out == null) {
                    connect();
                }
                drainLatest();
            } catch (IOException e) {
                disconnect();
                retryAt = System.currentTimeMillis() + RETRY_MS;
            }
        }
        disconnect();
    }

    private void connect() throws IOException {
        Socket next = new Socket();
        try {
            next.setTcpNoDelay(true);
            next.connect(new InetSocketAddress(InetAddress.getLoopbackAddress(), port), CONNECT_TIMEOUT_MS);
            socket = next;
            out = new DataOutputStream(new BufferedOutputStream(next.getOutputStream(), 64 * 1024));
        } catch (IOException e) {
            try {
                next.close();
            } catch (IOException ignored) {
                // 元の接続失敗を返す。
            }
            throw e;
        }
    }

    private void drainLatest() throws IOException {
        DataOutputStream target = out;
        if (target == null) {
            throw new IOException("live palette socket is not connected");
        }
        boolean wrote = false;
        for (Map.Entry<UUID, SimPaletteLiveProtocol.Frame> entry : pending.entrySet()) {
            SimPaletteLiveProtocol.Frame frame = entry.getValue();
            if (!pending.remove(entry.getKey(), frame)) {
                continue;
            }
            byte[] body = SimPaletteLiveProtocol.encode(frame);
            target.writeInt(body.length);
            target.write(body);
            wrote = true;
        }
        if (wrote) {
            target.flush();
        }
    }

    private void awaitSignal(long millis) {
        synchronized (signal) {
            if (closed) {
                return;
            }
            try {
                signal.wait(Math.max(1L, millis));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                closed = true;
            }
        }
    }

    private void disconnect() {
        DataOutputStream oldOut = out;
        Socket oldSocket = socket;
        out = null;
        socket = null;
        if (oldOut != null) {
            try {
                oldOut.close();
            } catch (IOException ignored) {
                // 接続断の後始末。描画側へ例外を返さない。
            }
        }
        if (oldSocket != null) {
            try {
                oldSocket.close();
            } catch (IOException ignored) {
                // 同上。
            }
        }
    }

    @Override
    public void close() {
        closed = true;
        pending.clear();
        synchronized (signal) {
            signal.notifyAll();
        }
        disconnect();
    }
}
