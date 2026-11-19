package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.nio.file.*;
import java.io.IOException;
import java.util.Comparator;

public final class KneekuraDebugRegisteredWorldSelfTest {
    public static void main(String[] args) throws Exception {
        Path parent = Files.createTempDirectory("registered-world-review").toRealPath();
        Path root = Files.createDirectory(parent.resolve("world"));
        Path foreign = Files.createDirectory(parent.resolve("foreign"));
        int checks = 0;
        try {
            JsonObject world = new JsonObject();
            world.addProperty("canonicalWorldRoot", root.toString());
            world.addProperty("worldName", "KNEEKURA_DEBUG_WORLD");
            world.addProperty("dimensionId", "minecraft:overworld");
            JsonArray permissions = new JsonArray();
            permissions.add("BOUNDED_DIAGNOSTIC_CONTROL");
            world.add("permissions", permissions);
            var observed = KneekuraDebugScopedOwnerGate.verifyWorld(root, "KNEEKURA_DEBUG_WORLD",
                    "minecraft:overworld", world, "a".repeat(64));
            if (!observed.get("canonicalWorldRoot").getAsString().equals(root.toString())) {
                throw new AssertionError("actual canonical root");
            }
            checks++;
            for (int i = 0; i < 3; i++) {
                try {
                    KneekuraDebugScopedOwnerGate.verifyWorld(i == 0 ? foreign : root,
                            i == 1 ? "PRODUCTION" : "KNEEKURA_DEBUG_WORLD",
                            i == 2 ? "minecraft:the_nether" : "minecraft:overworld", world, "a".repeat(64));
                    throw new AssertionError("foreign world accepted");
                } catch (IOException expected) {
                    checks++;
                }
            }
            world.add("permissions", new JsonArray());
            try {
                KneekuraDebugScopedOwnerGate.verifyWorld(root, "KNEEKURA_DEBUG_WORLD",
                        "minecraft:overworld", world, "a".repeat(64));
                throw new AssertionError("world name alone is not authority");
            } catch (IOException expected) {
                checks++;
            }

            // Exercise the same metadata comparison used by requireFast without a fake Minecraft server.
            var stamp = KneekuraDebugScopedOwnerGate.class.getDeclaredMethod("stamp", Path.class);
            stamp.setAccessible(true);
            if (Files.readAttributes(root, java.nio.file.attribute.BasicFileAttributes.class,
                    LinkOption.NOFOLLOW_LINKS).fileKey() == null
                    && !System.getProperty("os.name").startsWith("Windows")) {
                try {
                    stamp.invoke(null, root);
                    throw new AssertionError("directory without stable identity retained owner authority");
                } catch (java.lang.reflect.InvocationTargetException expected) {
                    if (!(expected.getCause() instanceof IOException)
                            || !"OWNER_DIRECTORY_IDENTITY_UNAVAILABLE".equals(expected.getCause().getMessage())) {
                        throw expected;
                    }
                    checks++;
                }
                System.out.println("registered canonical world source checks=" + checks
                        + "; directory identity unavailable: owner authority rejected; no Minecraft world instantiated");
                return;
            }
            Object beforeSave = stamp.invoke(null, root);
            Files.writeString(root.resolve("level.dat_new"), "source-only save fixture");
            Files.move(root.resolve("level.dat_new"), root.resolve("level.dat"));
            if (!beforeSave.equals(stamp.invoke(null, root))) {
                throw new AssertionError("ordinary directory-content changes revoked world identity");
            }
            checks++;
            // Keep the original inode alive so a new directory cannot reuse its identity in this test.
            Files.move(root, parent.resolve("original-world"));
            Files.createDirectory(root);
            if (beforeSave.equals(stamp.invoke(null, root))) {
                throw new AssertionError("replacement directory retained original world authority");
            }
            checks++;
            if (System.getProperty("os.name").startsWith("Windows")) {
                var nativeKey = KneekuraDebugScopedOwnerGate.class.getDeclaredMethod("windowsDirectoryKey", Path.class);
                nativeKey.setAccessible(true);
                Path regular = Files.writeString(parent.resolve("not-a-directory"), "source-only fixture");
                for (Path invalid : new Path[]{regular, parent.resolve("missing-directory")}) {
                    try {
                        nativeKey.invoke(null, invalid);
                        throw new AssertionError("native directory identity accepted a non-directory or missing path");
                    } catch (java.lang.reflect.InvocationTargetException expected) {
                        if (!(expected.getCause() instanceof IOException)
                                || !"OWNER_DIRECTORY_IDENTITY_UNAVAILABLE".equals(expected.getCause().getMessage())) {
                            throw expected;
                        }
                        checks++;
                    }
                }
                // Replaying creationTime must not revive authority for another directory object.
                for (int i = 0; i < 64; i++) {
                    Path replacement = Files.createDirectory(parent.resolve("replace-" + i));
                    Object original = stamp.invoke(null, replacement);
                    var created = Files.readAttributes(replacement, java.nio.file.attribute.BasicFileAttributes.class).creationTime();
                    Files.move(replacement, parent.resolve("kept-" + i));
                    Files.createDirectory(replacement);
                    Files.setAttribute(replacement, "basic:creationTime", created, LinkOption.NOFOLLOW_LINKS);
                    if (original.equals(stamp.invoke(null, replacement))) {
                        throw new AssertionError("creation-time replay revived directory authority");
                    }
                    checks++;
                }
            }
            System.out.println("registered canonical world source checks=" + checks
                    + "; no Minecraft world instantiated");
        } finally {
            try (var files = Files.walk(parent)) {
                for (Path file : files.sorted(Comparator.reverseOrder()).toList()) Files.deleteIfExists(file);
            }
        }
    }
}
