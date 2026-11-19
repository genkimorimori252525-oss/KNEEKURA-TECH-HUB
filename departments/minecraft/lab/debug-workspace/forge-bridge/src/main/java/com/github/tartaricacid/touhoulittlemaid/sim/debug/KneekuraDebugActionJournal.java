package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import com.google.gson.stream.*;
import java.io.*;
import java.math.BigDecimal;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.*;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.*;
import java.util.*;

/** Shares the Supervisor's control/actions journal. This is not an ingress or evidence store. */
public final class KneekuraDebugActionJournal {
    private static final Gson JSON = new GsonBuilder().disableHtmlEscaping().create();
    private static final Set<String> TERMINAL = Set.of("VERIFIED", "FAILED", "NOT_RUN", "PARTIAL_APPLY", "OUTCOME_UNKNOWN");
    private static final Map<String, Set<String>> NEXT = Map.of(
            "REQUESTED", Set.of("ACCEPTED", "FAILED", "NOT_RUN"),
            "ACCEPTED", Set.of("APPLIED", "FAILED", "PARTIAL_APPLY", "OUTCOME_UNKNOWN"),
            "APPLIED", Set.of("VERIFIED", "FAILED", "PARTIAL_APPLY", "OUTCOME_UNKNOWN"));
    private final Path runDir;
    public KneekuraDebugActionJournal(Path runDir) throws IOException {
        this.runDir = runDir.toAbsolutePath().normalize();
        if (!runDir.isAbsolute() || !this.runDir.equals(runDir.toRealPath())) throw new IOException("UNSAFE_RUN_DIR");
    }
    public record Acceptance(String status, Handle handle) { }
    private record State(JsonObject request, JsonObject last, int count, String previousHash) { }

    public Acceptance accept(JsonObject expectedAction) throws IOException {
        Path dir = directory(expectedAction);
        Path lock = dir.resolve(".writer-lock");
        try { Files.createDirectory(lock); }
        catch (FileAlreadyExistsException e) { throw new IOException("ACTION_WRITE_IN_PROGRESS", e); }
        boolean removeLock = true;
        try {
            State s = read(dir, expectedAction);
            String status = s.last().get("status").getAsString();
            if (!"REQUESTED".equals(status)) {
                return new Acceptance(TERMINAL.contains(status) ? status : "OUTCOME_UNKNOWN", null);
            }
            Handle h = new Handle(dir, s);
            h.append("ACCEPTED", List.of());
            removeLock = false;
            return new Acceptance("ACCEPTED", h);
        } finally { if (removeLock) Files.delete(lock); }
    }
    public String lookup(JsonObject expectedAction) throws IOException {
        Path dir = directory(expectedAction);
        State s = read(dir, expectedAction);
        String status = s.last().get("status").getAsString();
        return "ACCEPTED".equals(status) || "APPLIED".equals(status) ? "OUTCOME_UNKNOWN" : status;
    }
    /** Internal reset reservation; never accepts caller-selected executable data. */
    void reserveOwnerReset(JsonObject action) throws IOException {
        if (!"reset_arena".equals(action.get("type").getAsString())) throw new IOException("OWNER_RESET_ONLY");
        Path dir = directory(action);
        try { Files.createDirectory(dir); }
        catch (FileAlreadyExistsException e) { read(dir, action); return; }
        String bytes = canonical(action);
        String payloadHash = sha256(bytes);
        writeNew(dir.resolve("canonical-action.json"), bytes);
        JsonObject request = new JsonObject(); request.addProperty("schemaVersion", 1);
        request.addProperty("payloadHash", payloadHash); request.add("action", action.deepCopy());
        writeNew(dir.resolve("request.json"), JSON.toJson(request));
        append(dir, new State(request, null, 0, payloadHash), "REQUESTED", List.of());
    }
    private Path directory(JsonObject action) throws IOException {
        String key = action.get("idempotencyKey").getAsString();
        if (!key.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")) throw new IOException("INVALID_IDENTIFIER");
        Path parent = runDir;
        for (String segment : List.of("control", "actions")) {
            parent = parent.resolve(segment);
            if (Files.isSymbolicLink(parent) || !Files.isDirectory(parent, LinkOption.NOFOLLOW_LINKS)) throw new IOException("UNSAFE_JOURNAL_PARENT");
        }
        Path dir = parent.resolve(sha256(key));
        if (Files.isSymbolicLink(dir)) throw new IOException("SYMLINK_REJECTED");
        return dir;
    }
    private State read(Path dir, JsonObject expectedAction) throws IOException {
        JsonObject request = object(parse(readBounded(dir.resolve("request.json"), 128 * 1024)));
        keys(request, "schemaVersion", "payloadHash", "action");
        if (integer(request.get("schemaVersion")) != 1) throw new IOException("JOURNAL_VERSION");
        String payloadHash = hash(request.get("payloadHash").getAsString());
        String bytes = readBounded(dir.resolve("canonical-action.json"), 128 * 1024);
        JsonObject action = object(parse(bytes));
        if (!sha256(bytes).equals(payloadHash) || !action.equals(request.get("action"))) throw new IOException("ACTION_REQUEST_INTEGRITY");
        if (!action.equals(expectedAction)) throw new IOException("IDEMPOTENCY_CONFLICT");
        List<String> names = new ArrayList<>(); int entries = 0;
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir)) {
            for (Path p : stream) {
                if (++entries > 32) throw new IOException("JOURNAL_ENTRY_LIMIT");
                String name = p.getFileName().toString();
                if (name.startsWith("receipt-")) {
                    if (!name.matches("receipt-[0-9]{6}\\.json")) throw new IOException("JOURNAL_GAP");
                    names.add(name);
                }
            }
        }
        Collections.sort(names);
        if (names.isEmpty() || names.size() > 5) throw new IOException("JOURNAL_INCOMPLETE");
        JsonObject last = null; String previous = payloadHash;
        for (int i = 0; i < names.size(); i++) {
            if (!names.get(i).equals(String.format(Locale.ROOT, "receipt-%06d.json", i))) throw new IOException("JOURNAL_GAP");
            JsonObject row = object(parse(readBounded(dir.resolve(names.get(i)), 64 * 1024)));
            keys(row, "sequence", "payloadHash", "previousHash", "status", "evidenceHashes", "receiptHash");
            String rowHash = hash(row.remove("receiptHash").getAsString());
            if (!sha256(canonical(row)).equals(rowHash) || integer(row.get("sequence")) != i ||
                    !payloadHash.equals(row.get("payloadHash").getAsString()) || !previous.equals(row.get("previousHash").getAsString())) throw new IOException("JOURNAL_INTEGRITY");
            String status = row.get("status").getAsString();
            if (i == 0 ? !"REQUESTED".equals(status) : !NEXT.getOrDefault(last.get("status").getAsString(), Set.of()).contains(status)) throw new IOException("JOURNAL_TRANSITION");
            JsonArray evidence = row.getAsJsonArray("evidenceHashes");
            if (evidence.size() > 32) throw new IOException("INVALID_EVIDENCE");
            for (JsonElement e : evidence) hash(e.getAsString());
            if (Set.of("APPLIED", "VERIFIED", "PARTIAL_APPLY").contains(status) && evidence.isEmpty()) throw new IOException("OUTCOME_EVIDENCE_REQUIRED");
            last = row; previous = rowHash;
        }
        return new State(request, last, names.size(), previous);
    }
    public final class Handle implements AutoCloseable {
        private final Path directory; private State state; private boolean closed;
        private Handle(Path directory, State state) { this.directory = directory; this.state = state; }
        public Path directory() { return directory; }
        public void append(String status, List<String> evidence) throws IOException {
            if (closed || !NEXT.getOrDefault(state.last().get("status").getAsString(), Set.of()).contains(status)) throw new IOException("INVALID_ACTION_TRANSITION");
            state = KneekuraDebugActionJournal.append(directory, state, status, evidence);
        }
        public void close() throws IOException {
            if (closed) return; closed = true;
            // Retain the exclusive fence after interrupted acceptance/applied states.
            if (TERMINAL.contains(state.last().get("status").getAsString())) Files.delete(directory.resolve(".writer-lock"));
        }
    }
    private static State append(Path dir, State state, String status, List<String> evidence) throws IOException {
        if (evidence.size() > 32) throw new IOException("INVALID_EVIDENCE");
        for (String e : evidence) hash(e);
        if (Set.of("APPLIED", "VERIFIED", "PARTIAL_APPLY").contains(status) && evidence.isEmpty()) throw new IOException("OUTCOME_EVIDENCE_REQUIRED");
        JsonObject body = new JsonObject(); body.addProperty("sequence", state.count());
        body.addProperty("payloadHash", state.request().get("payloadHash").getAsString());
        body.addProperty("previousHash", state.previousHash()); body.addProperty("status", status);
        JsonArray hashes = new JsonArray(); evidence.forEach(hashes::add); body.add("evidenceHashes", hashes);
        String digest = sha256(canonical(body)); JsonObject row = body.deepCopy(); row.addProperty("receiptHash", digest);
        writeNew(dir.resolve(String.format(Locale.ROOT, "receipt-%06d.json", state.count())), canonical(row) + "\n");
        return new State(state.request(), body, state.count() + 1, digest);
    }
    private static void writeNew(Path path, String bytes) throws IOException {
        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS)) {
            ByteBuffer b = StandardCharsets.UTF_8.encode(bytes);
            while (b.hasRemaining()) channel.write(b);
            channel.force(true);
        }
    }
    private static String readBounded(Path path, int limit) throws IOException {
        BasicFileAttributes before=Files.readAttributes(path,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
        if(!before.isRegularFile()||before.size()>limit)throw new IOException("NONREGULAR_OR_OVERSIZED_JOURNAL_FILE");
        // O_RDWR avoids a FIFO open wait if a regular path is replaced between stat/open.
        // No write is performed; a zero-size descriptor is never read, and JSON parsing fails closed.
        try(FileChannel channel=FileChannel.open(path,StandardOpenOption.READ,StandardOpenOption.WRITE,LinkOption.NOFOLLOW_LINKS)){
            long size=channel.size();BasicFileAttributes opened=Files.readAttributes(path,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
            if(!opened.isRegularFile()||size!=before.size()||size!=opened.size()||!Objects.equals(before.fileKey(),opened.fileKey()))throw new IOException("JOURNAL_FILE_DRIFT");
            ByteBuffer bytes=ByteBuffer.allocate((int)size);int emptyReads=0;
            while(bytes.hasRemaining()){int n=channel.read(bytes);if(n<0||n==0&&++emptyReads>2)throw new IOException("JOURNAL_FILE_DRIFT");}
            BasicFileAttributes after=Files.readAttributes(path,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
            if(!after.isRegularFile()||after.size()!=size||channel.size()!=size||!Objects.equals(opened.fileKey(),after.fileKey()))throw new IOException("JOURNAL_FILE_DRIFT");
            bytes.flip();return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(bytes).toString();
        }
    }
    static String hash(String s) throws IOException { if (!s.matches("[a-f0-9]{64}")) throw new IOException("INVALID_SHA256"); return s; }
    static long integer(JsonElement e) throws IOException {
        if(e==null||!e.isJsonPrimitive()||!e.getAsJsonPrimitive().isNumber())throw new IOException("NUMERIC_INTEGER_REQUIRED");
        try { return new BigDecimal(e.getAsString()).longValueExact(); }
        catch (RuntimeException ex) { throw new IOException("INVALID_INTEGER", ex); }
    }
    static JsonObject object(JsonElement e) throws IOException {
        if (!e.isJsonObject()) throw new IOException("JSON_OBJECT_REQUIRED"); return e.getAsJsonObject();
    }
    static void keys(JsonObject o, String... names) throws IOException { if (!o.keySet().equals(Set.of(names))) throw new IOException("INVALID_FIELDS"); }
    static String sha256(String bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes.getBytes(StandardCharsets.UTF_8))); }
        catch (NoSuchAlgorithmException e) { throw new AssertionError(e); }
    }
    /** Only receipts and internal reset reservation use this; Node action hashes use exact sidecar bytes. */
    static String canonical(JsonElement value) {
        if (value.isJsonObject()) {
            List<String> keys = new ArrayList<>(value.getAsJsonObject().keySet()); Collections.sort(keys);
            return "{" + String.join(",", keys.stream().map(k -> JSON.toJson(k) + ":" + canonical(value.getAsJsonObject().get(k))).toList()) + "}";
        }
        if (value.isJsonArray()) { List<String> entries = new ArrayList<>(); value.getAsJsonArray().forEach(e -> entries.add(canonical(e))); return "[" + String.join(",", entries) + "]"; }
        return JSON.toJson(value);
    }
    static JsonElement parse(String bytes) throws IOException {
        try (JsonReader reader = new JsonReader(new StringReader(bytes))) {
            reader.setLenient(false); int[] tokens = {0}; JsonElement result = readValue(reader, 0, tokens);
            if (reader.peek() != JsonToken.END_DOCUMENT) throw new IOException("INVALID_JSON_TRAILING"); return result;
        } catch (RuntimeException e) { throw new IOException("INVALID_JSON", e); }
    }
    private static JsonElement readValue(JsonReader r, int depth, int[] tokens) throws IOException {
        if (depth > 32 || ++tokens[0] > 10000) throw new IOException("JSON_COMPLEXITY_LIMIT");
        return switch (r.peek()) {
            case BEGIN_OBJECT -> { JsonObject o = new JsonObject(); r.beginObject(); while (r.hasNext()) { String k = r.nextName(); if (o.has(k)) throw new IOException("DUPLICATE_JSON_KEY"); o.add(k, readValue(r, depth + 1, tokens)); } r.endObject(); yield o; }
            case BEGIN_ARRAY -> { JsonArray a = new JsonArray(); r.beginArray(); while (r.hasNext()) a.add(readValue(r, depth + 1, tokens)); r.endArray(); yield a; }
            case STRING -> new JsonPrimitive(r.nextString());
            case BOOLEAN -> new JsonPrimitive(r.nextBoolean());
            case NULL -> { r.nextNull(); yield JsonNull.INSTANCE; }
            case NUMBER -> { String s = r.nextString(); BigDecimal n = new BigDecimal(s); if (n.abs().compareTo(new BigDecimal("9007199254740991")) > 0 || !Double.isFinite(n.doubleValue())) throw new IOException("UNSAFE_JSON_NUMBER"); yield new JsonPrimitive(n); }
            default -> throw new IOException("INVALID_JSON_TOKEN");
        };
    }
}
