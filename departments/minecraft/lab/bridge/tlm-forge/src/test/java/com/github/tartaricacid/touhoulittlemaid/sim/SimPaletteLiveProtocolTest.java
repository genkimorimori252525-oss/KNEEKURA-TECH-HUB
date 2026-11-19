package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.sim.client.SimPaletteLiveProtocol;
import com.github.tartaricacid.touhoulittlemaid.sim.client.SimPaletteLiveTransport;
import org.junit.Test;

import java.io.DataInputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;

/** Minecraft やファイルを使わず、live palette の wire と loopback transport を検証する。 */
public class SimPaletteLiveProtocolTest {
    private static SimPaletteLiveProtocol.Frame frame(long sequence) {
        String[] names = {"root", "body", "qunzi"};
        float[] palette = new float[names.length * SimPaletteLiveProtocol.PALETTE_STRIDE];
        for (int i = 0; i < palette.length; i++) {
            palette[i] = Float.intBitsToFloat(0x3f000000 + i);
        }
        return new SimPaletteLiveProtocol.Frame(sequence, 12345L, 0.625F, 77,
                UUID.fromString("01234567-89ab-cdef-0123-456789abcdef"),
                "touhou_little_maid:maid", "ysm:reimu", "reimu/texture.png",
                "ysm.Model#root.renderer", names, palette);
    }

    @Test
    public void frameRoundTripsBitExactlyWithIdentity() throws Exception {
        SimPaletteLiveProtocol.Frame expected = frame(9L);
        byte[] wire = SimPaletteLiveProtocol.encode(expected);
        ByteBuffer header = ByteBuffer.wrap(wire).order(ByteOrder.BIG_ENDIAN);
        assertEquals(SimPaletteLiveProtocol.MAGIC, header.getInt());
        assertEquals(SimPaletteLiveProtocol.VERSION, header.getShort() & 0xffff);
        assertEquals(SimPaletteLiveProtocol.PALETTE_STRIDE, header.getShort() & 0xffff);
        // Node live-palette-selftest と共有する cross-language FNV golden。
        assertEquals(0xa0def8774c81cdd2L, expected.layoutHash());
        SimPaletteLiveProtocol.Frame actual = SimPaletteLiveProtocol.decode(wire);

        assertEquals(expected.sequence(), actual.sequence());
        assertEquals(expected.gameTime(), actual.gameTime());
        assertEquals(Float.floatToRawIntBits(expected.partialTick()),
                Float.floatToRawIntBits(actual.partialTick()));
        assertEquals(expected.entityId(), actual.entityId());
        assertEquals(expected.uuid(), actual.uuid());
        assertEquals(expected.entityType(), actual.entityType());
        assertEquals(expected.modelId(), actual.modelId());
        assertEquals(expected.modelTexture(), actual.modelTexture());
        assertEquals(expected.geometryType(), actual.geometryType());
        assertEquals(expected.layoutHash(), actual.layoutHash());
        assertArrayEquals(expected.boneNames(), actual.boneNames());
        assertArrayEquals(expected.palette(), actual.palette(), 0F);
    }

    @Test
    public void layoutHashChangesWithModelOrBoneOrder() {
        SimPaletteLiveProtocol.Frame a = frame(1L);
        SimPaletteLiveProtocol.Frame otherModel = new SimPaletteLiveProtocol.Frame(2L, a.gameTime(),
                a.partialTick(), a.entityId(), a.uuid(), a.entityType(), "ysm:other", a.modelTexture(),
                a.geometryType(), a.boneNames(), a.palette());
        String[] reordered = {"root", "qunzi", "body"};
        SimPaletteLiveProtocol.Frame otherOrder = new SimPaletteLiveProtocol.Frame(3L, a.gameTime(),
                a.partialTick(), a.entityId(), a.uuid(), a.entityType(), a.modelId(), a.modelTexture(),
                a.geometryType(), reordered, a.palette());

        assertNotEquals(a.layoutHash(), otherModel.layoutHash());
        assertNotEquals(a.layoutHash(), otherOrder.layoutHash());
    }

    @Test
    public void transportSendsOneLengthPrefixedFrameOverLoopbackMemory() throws Exception {
        InetAddress loopback = InetAddress.getLoopbackAddress();
        ExecutorService reader = Executors.newSingleThreadExecutor();
        try (ServerSocket server = new ServerSocket()) {
            server.bind(new InetSocketAddress(loopback, 0));
            Future<byte[]> received = reader.submit(() -> {
                try (Socket socket = server.accept();
                     DataInputStream in = new DataInputStream(socket.getInputStream())) {
                    int length = in.readInt();
                    byte[] body = new byte[length];
                    in.readFully(body);
                    return body;
                }
            });

            try (SimPaletteLiveTransport transport = new SimPaletteLiveTransport(server.getLocalPort())) {
                transport.offer(frame(42L));
                SimPaletteLiveProtocol.Frame actual = SimPaletteLiveProtocol.decode(
                        received.get(5, TimeUnit.SECONDS));
                assertEquals(42L, actual.sequence());
                assertEquals("ysm:reimu", actual.modelId());
                assertEquals("qunzi", actual.boneNames()[2]);
            }
        } finally {
            reader.shutdownNow();
        }
    }
}
