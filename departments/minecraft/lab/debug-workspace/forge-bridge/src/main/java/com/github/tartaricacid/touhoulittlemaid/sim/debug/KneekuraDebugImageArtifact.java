package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Objects;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;

/** Immutable bounded work item for the existing evidence writer, never a worker/store of its own. */
final class KneekuraDebugImageArtifact {
    private static final byte[] PNG = {(byte) 137, 80, 78, 71, 13, 10, 26, 10};
    private final Path runDir;
    private final byte[] bytes;
    private final String hash;
    KneekuraDebugImageArtifact(Path runDir, byte[] source) {
        if (runDir == null || !runDir.isAbsolute() || source == null || source.length < 8 ||
                source.length > KneekuraDebugCaptureSession.MAX_PNG_BYTES ||
                !Arrays.equals(PNG, Arrays.copyOf(source, 8))) throw new IllegalArgumentException("INVALID_CAPTURE_PNG");
        this.runDir = runDir.normalize(); this.bytes = source.clone(); this.hash = sha256(bytes);
    }
    String hash() { return hash; }
    int size() { return bytes.length; }
    void persist() throws IOException { persist(() -> {}); }
    void persist(Runnable afterExistingCheck) throws IOException {
        for (Path part = runDir; part != null; part = part.getParent())
            if (Files.isSymbolicLink(part)) throw new IOException("CAPTURE_ROOT_SYMLINK");
        if (!Files.isDirectory(runDir, LinkOption.NOFOLLOW_LINKS)) throw new IOException("CAPTURE_RUN_UNAVAILABLE");
        Path dir = runDir;
        for (String name : new String[]{"evidence", "raw", "visual"}) {
            dir = dir.resolve(name);
            if (!Files.exists(dir, LinkOption.NOFOLLOW_LINKS)) Files.createDirectory(dir);
            if (!Files.isDirectory(dir, LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(dir))
                throw new IOException("CAPTURE_DIRECTORY_UNSAFE");
        }
        Path target = dir.resolve(hash + ".png");
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) {
            if (!Files.isRegularFile(target, LinkOption.NOFOLLOW_LINKS) || Files.size(target) != bytes.length)
                throw new IOException("IMMUTABLE_CAPTURE_CONFLICT");
            BasicFileAttributes before = Files.readAttributes(target, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            afterExistingCheck.run();
            // O_RDWR avoids the blocking read-only FIFO open race. No existing byte is ever written.
            try (FileChannel channel = FileChannel.open(target, StandardOpenOption.READ,
                    StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS)) {
                BasicFileAttributes opened = Files.readAttributes(target, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                if (channel.size() != bytes.length || !opened.isRegularFile() || opened.size() != bytes.length ||
                        !Objects.equals(before.fileKey(), opened.fileKey()) ||
                        !target.toRealPath().equals(target.toAbsolutePath().normalize()))
                    throw new IOException("CAPTURE_CHANGED_BEFORE_READ");
                ByteBuffer buffer = ByteBuffer.allocate(bytes.length + 1);
                while (buffer.hasRemaining() && channel.read(buffer) >= 0) { }
                if (buffer.position() != bytes.length || !sha256(Arrays.copyOf(buffer.array(), bytes.length)).equals(hash))
                    throw new IOException("IMMUTABLE_CAPTURE_CONFLICT");
                BasicFileAttributes after = Files.readAttributes(target, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                if (channel.size() != bytes.length || !after.isRegularFile() || after.size() != bytes.length ||
                        !Objects.equals(opened.fileKey(), after.fileKey()) ||
                        !opened.lastModifiedTime().equals(after.lastModifiedTime()) ||
                        !target.toRealPath().equals(target.toAbsolutePath().normalize()))
                    throw new IOException("CAPTURE_CHANGED_DURING_READ");
                channel.force(true); // Reuse establishes the same durable checkpoint as newly written bytes.
            }
            return;
        }
        try (FileChannel channel = FileChannel.open(target, StandardOpenOption.CREATE_NEW,
                StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS)) {
            ByteBuffer buffer = ByteBuffer.wrap(bytes);
            while (buffer.hasRemaining()) channel.write(buffer);
            channel.force(true);
        }
    }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (Exception error) { throw new IllegalStateException(error); }
    }
}
