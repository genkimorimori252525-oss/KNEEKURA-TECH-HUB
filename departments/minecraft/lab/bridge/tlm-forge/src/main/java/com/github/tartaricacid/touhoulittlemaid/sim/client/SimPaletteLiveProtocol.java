package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.UUID;

/**
 * 実描画後 palette のメモリ転送用 wire format。
 *
 * <p>各 TCP message は transport 側の {@code int32 bodyLength} に続いて、このクラスが作る
 * body を1個だけ載せる。数値は Java {@link DataOutputStream} の big endian。palette は
 * YSM が持つ生の 3x4 affine matrix（1 bone = 12 float）で、録画用 codec へ変換しない。
 */
public final class SimPaletteLiveProtocol {
    public static final int MAGIC = 0x544C504C; // "TLPL"
    public static final int VERSION = 1;
    public static final int PALETTE_STRIDE = 12;
    public static final int MAX_BONES = 4096;
    public static final int MAX_BODY_BYTES = 16 * 1024 * 1024;
    private static final int MAX_STRING_BYTES = 1024 * 1024;

    private SimPaletteLiveProtocol() {}

    /** 1回の実描画から得た自己完結 frame。配列は構築時に複製する。 */
    public record Frame(long sequence, long gameTime, float partialTick, int entityId, UUID uuid,
                        String entityType, String modelId, String modelTexture, String geometryType,
                        String[] boneNames, float[] palette) {
        public Frame {
            Objects.requireNonNull(uuid, "uuid");
            entityType = Objects.requireNonNullElse(entityType, "");
            modelId = Objects.requireNonNullElse(modelId, "");
            modelTexture = Objects.requireNonNullElse(modelTexture, "");
            geometryType = Objects.requireNonNullElse(geometryType, "");
            boneNames = Objects.requireNonNull(boneNames, "boneNames").clone();
            palette = Objects.requireNonNull(palette, "palette").clone();
            validate(boneNames, palette);
        }

        public long layoutHash() {
            return SimPaletteLiveProtocol.layoutHash(modelId, modelTexture, geometryType, boneNames);
        }
    }

    public static byte[] encode(Frame frame) throws IOException {
        Objects.requireNonNull(frame, "frame");
        ByteArrayOutputStream bytes = new ByteArrayOutputStream(256 + frame.palette().length * Float.BYTES);
        try (DataOutputStream out = new DataOutputStream(bytes)) {
            out.writeInt(MAGIC);
            out.writeShort(VERSION);
            out.writeShort(PALETTE_STRIDE);
            out.writeLong(frame.sequence());
            out.writeLong(frame.gameTime());
            out.writeFloat(frame.partialTick());
            out.writeInt(frame.entityId());
            out.writeLong(frame.uuid().getMostSignificantBits());
            out.writeLong(frame.uuid().getLeastSignificantBits());
            out.writeLong(frame.layoutHash());
            writeString(out, frame.entityType());
            writeString(out, frame.modelId());
            writeString(out, frame.modelTexture());
            writeString(out, frame.geometryType());
            out.writeInt(frame.boneNames().length);
            for (String name : frame.boneNames()) {
                writeString(out, name);
            }
            out.writeInt(frame.palette().length);
            for (float v : frame.palette()) {
                out.writeFloat(v);
            }
        }
        byte[] body = bytes.toByteArray();
        if (body.length > MAX_BODY_BYTES) {
            throw new IOException("live palette body too large: " + body.length);
        }
        return body;
    }

    /** Node 側 decoder と test の基準になる厳格な復号器。余剰 byte も受け入れない。 */
    public static Frame decode(byte[] body) throws IOException {
        if (body == null || body.length == 0 || body.length > MAX_BODY_BYTES) {
            throw new IOException("invalid live palette body length");
        }
        try (DataInputStream in = new DataInputStream(new ByteArrayInputStream(body))) {
            if (in.readInt() != MAGIC) {
                throw new IOException("live palette magic mismatch");
            }
            int version = in.readUnsignedShort();
            int stride = in.readUnsignedShort();
            if (version != VERSION || stride != PALETTE_STRIDE) {
                throw new IOException("unsupported live palette format: version=" + version + ", stride=" + stride);
            }
            long sequence = in.readLong();
            long gameTime = in.readLong();
            float partialTick = in.readFloat();
            int entityId = in.readInt();
            UUID uuid = new UUID(in.readLong(), in.readLong());
            long wireLayoutHash = in.readLong();
            String entityType = readString(in);
            String modelId = readString(in);
            String modelTexture = readString(in);
            String geometryType = readString(in);
            int bones = in.readInt();
            if (bones < 1 || bones > MAX_BONES) {
                throw new IOException("invalid live palette bone count: " + bones);
            }
            String[] names = new String[bones];
            for (int i = 0; i < bones; i++) {
                names[i] = readString(in);
            }
            int floats = in.readInt();
            if (floats != bones * PALETTE_STRIDE) {
                throw new IOException("palette length " + floats + " != bones*stride "
                        + (bones * PALETTE_STRIDE));
            }
            float[] palette = new float[floats];
            for (int i = 0; i < floats; i++) {
                palette[i] = in.readFloat();
            }
            if (in.available() != 0) {
                throw new IOException("trailing bytes in live palette body: " + in.available());
            }
            Frame frame = new Frame(sequence, gameTime, partialTick, entityId, uuid, entityType,
                    modelId, modelTexture, geometryType, names, palette);
            if (frame.layoutHash() != wireLayoutHash) {
                throw new IOException("live palette layout hash mismatch");
            }
            return frame;
        }
    }

    /** model と slot 順 bone 名を同時に識別する FNV-1a 64bit。 */
    public static long layoutHash(String modelId, String modelTexture, String geometryType, String[] names) {
        long h = 0xcbf29ce484222325L;
        h = hashString(h, modelId);
        h = hashString(h, modelTexture);
        h = hashString(h, geometryType);
        for (String name : names) {
            h = hashString(h, name);
        }
        return h;
    }

    private static long hashString(long h, String value) {
        byte[] bytes = Objects.requireNonNullElse(value, "").getBytes(StandardCharsets.UTF_8);
        for (byte b : bytes) {
            h ^= b & 0xffL;
            h *= 0x100000001b3L;
        }
        h ^= 0xffL; // field separator
        return h * 0x100000001b3L;
    }

    private static void validate(String[] names, float[] palette) {
        if (names.length < 1 || names.length > MAX_BONES) {
            throw new IllegalArgumentException("invalid bone count: " + names.length);
        }
        if (palette.length != names.length * PALETTE_STRIDE) {
            throw new IllegalArgumentException("palette length " + palette.length
                    + " != bones*stride " + (names.length * PALETTE_STRIDE));
        }
        for (String name : names) {
            Objects.requireNonNull(name, "bone name");
        }
    }

    private static void writeString(DataOutputStream out, String value) throws IOException {
        byte[] bytes = Objects.requireNonNullElse(value, "").getBytes(StandardCharsets.UTF_8);
        if (bytes.length > MAX_STRING_BYTES) {
            throw new IOException("live palette string too long: " + bytes.length);
        }
        out.writeInt(bytes.length);
        out.write(bytes);
    }

    private static String readString(DataInputStream in) throws IOException {
        int length = in.readInt();
        if (length < 0 || length > MAX_STRING_BYTES) {
            throw new IOException("invalid live palette string length: " + length);
        }
        byte[] bytes = in.readNBytes(length);
        if (bytes.length != length) {
            throw new IOException("truncated live palette string: " + bytes.length + "/" + length);
        }
        return new String(bytes, StandardCharsets.UTF_8);
    }
}
