package org.kneekura.observer;

import com.google.gson.*;
import java.io.InputStream;
import java.nio.channels.Channels;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.util.*;

/** Startup binding of original dependency archive bytes. Does not attest loaded classes or memory. */
final class DependencyInventory {
    static final String SCOPE="TARGET_CODE_AND_DEPENDENCY_BYTES";
    private static final long MAX_ARCHIVE=512L*1024*1024,MAX_TOTAL=2L*1024*1024*1024;
    private final Map<Path,Stamp> files;
    private final JsonObject inventory;
    private final JsonArray mappings;
    private DependencyInventory(Map<Path,Stamp> files,JsonObject inventory,JsonArray mappings) {
        this.files=Map.copyOf(files);this.inventory=inventory==null?null:inventory.deepCopy();this.mappings=mappings==null?null:mappings.deepCopy();
    }
    private static void require(boolean ok,String message) {DedicatedSession.require(ok,message);}
    private static String string(JsonObject value,String field) {return DedicatedSession.string(value,field);}
    private static String digest(JsonObject value,String field) {
        String result=string(value,field);require(result.matches("[0-9a-f]{64}"),"Invalid dependency digest: "+field);return result;
    }
    static void scope(JsonObject identity) {
        DedicatedSession.runtimeScope(identity);
    }
    private static long size(JsonObject value) {
        JsonElement e=value.get("size_bytes");
        require(e!=null && e.isJsonPrimitive() && e.getAsJsonPrimitive().isNumber() && e.getAsString().matches("[1-9][0-9]*"),"Positive integer archive size required");
        long size=Long.parseLong(e.getAsString());require(size<=MAX_ARCHIVE,"Dependency archive exceeds bound");return size;
    }
    private static void bounded(JsonObject value,String field) {
        String text=string(value,field);require(!text.isEmpty() && text.length()<=2048 && text.chars().noneMatch(c->c<32 || c==127),"Invalid dependency label: "+field);
    }
    private static Path canonical(String name) throws Exception {
        Path path=Path.of(name);require(path.isAbsolute() && path.equals(path.normalize()) && !Files.isSymbolicLink(path)
                && path.equals(path.toRealPath()),"Dependency path must be canonical and not a symlink");return path;
    }
    private record Stamp(Object key,long size,java.nio.file.attribute.FileTime modified,java.nio.file.attribute.FileTime created) {}
    private static Stamp stamp(Path path) throws Exception {
        require(path.equals(canonical(path.toString())),"Dependency path identity changed");
        BasicFileAttributes a=Files.readAttributes(path,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
        require(a.isRegularFile() && !a.isSymbolicLink(),"Dependency must be a regular archive file");
        return new Stamp(a.fileKey(),a.size(),a.lastModifiedTime(),a.creationTime());
    }
    static DependencyInventory verify(JsonObject session,JsonObject identity) throws Exception {
        if(DedicatedSession.role(identity).equals("legacy"))return new DependencyInventory(Map.of(),null,null);
        scope(identity);
        JsonObject inventory=session.getAsJsonObject("dependency_inventory");
        require(inventory!=null && inventory.keySet().equals(Set.of("schema_version","kind","runtime_scope","export_receipt_hash","resolved_inputs_hash","workspace","source_generation","configuration_fingerprint","entries")),"Exact dependency inventory fields required");
        DedicatedSession.integer(inventory,"schema_version",1,1);
        require(string(inventory,"kind").equals("resolved_dependency_bytes") && string(inventory,"runtime_scope").equals(SCOPE),"Unsupported dependency inventory kind/scope");
        for(String field:List.of("export_receipt_hash","resolved_inputs_hash","source_generation","configuration_fingerprint"))digest(inventory,field);
        require(string(inventory,"source_generation").equals(string(identity,"dirty_hash")),"Dependency inventory source generation mismatch");
        String workspace=string(inventory,"workspace");Path workspacePath=Path.of(workspace);
        require(workspacePath.isAbsolute() && workspacePath.equals(workspacePath.normalize()),"Absolute canonical workspace identity required");
        require(DedicatedSession.hash(inventory).equals(string(identity,"dependency_inventory_hash")),"Dependency inventory hash mismatch");
        JsonArray entries=inventory.getAsJsonArray("entries"),mapped=session.getAsJsonArray("dependency_files");
        require(entries!=null && entries.size()>=1 && entries.size()<=4096 && mapped!=null && entries.size()==mapped.size(),"Complete ordered dependency mapping required");
        Map<Path,Stamp> checked=new LinkedHashMap<>();Map<Path,String> hashes=new HashMap<>();Set<String> scopes=new HashSet<>();long total=0;
        for(int index=0;index<entries.size();index++) {
            JsonObject entry=entries.get(index).getAsJsonObject(),file=mapped.get(index).getAsJsonObject();
            require(entry.keySet().equals(Set.of("order","coordinate","scope","namespace","stage","sha256","size_bytes","retention")),"Exact public dependency entry fields required");
            require(file.keySet().equals(Set.of("order","path","sha256","size_bytes")),"Exact private dependency mapping fields required");
            DedicatedSession.integer(entry,"order",index,index);DedicatedSession.integer(file,"order",index,index);
            for(String label:List.of("coordinate","namespace","stage"))bounded(entry,label);
            require(Set.of("compile","runtime").contains(string(entry,"scope")) && string(entry,"retention").equals("original_archive_bytes"),"Invalid dependency archive scope/retention");
            scopes.add(string(entry,"scope"));
            String expected=digest(entry,"sha256");long length=size(entry);
            require(expected.equals(digest(file,"sha256")) && length==size(file),"Private archive mapping differs from public inventory");
            Path path=canonical(string(file,"path"));String filename=path.getFileName().toString().toLowerCase(Locale.ROOT);
            require(filename.endsWith(".jar") || filename.endsWith(".zip"),"Dependency mapping must name an original JAR/ZIP archive");
            Stamp before=stamp(path);require(before.size()==length,"Dependency archive size mismatch");
            if(checked.containsKey(path)) {
                require(expected.equals(hashes.get(path)) && before.equals(checked.get(path)),"Repeated dependency archive identity mismatch");continue;
            }
            total+=length;require(total<=MAX_TOTAL,"Dependency inventory exceeds byte bound");
            MessageDigest sha=MessageDigest.getInstance("SHA-256");
            try(FileChannel channel=FileChannel.open(path,StandardOpenOption.READ,LinkOption.NOFOLLOW_LINKS);InputStream stream=Channels.newInputStream(channel)) {
                byte[] buffer=new byte[65536];long read=0;
                for(int n;(n=stream.read(buffer))!=-1;) {read+=n;require(read<=length,"Dependency archive grew during startup");sha.update(buffer,0,n);}
                require(read==length,"Dependency archive shortened during startup");
            }
            require(HexFormat.of().formatHex(sha.digest()).equals(expected),"Dependency archive SHA256 mismatch");
            require(before.equals(stamp(path)),"Dependency archive identity changed during startup");
            checked.put(path,before);hashes.put(path,expected);
        }
        require(scopes.equals(Set.of("compile","runtime")),"Both resolved compile and runtime scopes required");
        DependencyInventory result=new DependencyInventory(checked,inventory,mapped);result.checkUnchanged();return result;
    }
    Path selectedArchive(String coordinate,String hash) throws Exception {
        require(inventory!=null && mappings!=null,"No verified dependency inventory");checkUnchanged();
        JsonArray entries=inventory.getAsJsonArray("entries");Path selected=null;
        for(int index=0;index<entries.size();index++) {
            JsonObject entry=entries.get(index).getAsJsonObject();
            if(string(entry,"scope").equals("runtime") && string(entry,"coordinate").equals(coordinate) && string(entry,"sha256").equals(hash)) {
                Path path=Path.of(string(mappings.get(index).getAsJsonObject(),"path"));
                require(files.containsKey(path),"Selected archive was not byte verified");
                if(selected==null)selected=path;
            }
        }
        require(selected!=null,"Selected dependency is absent from verified runtime inventory");return selected;
    }
    /** Metadata-only invalidation after startup; deliberately not continuous byte or memory attestation. */
    void checkUnchanged() throws Exception {
        for(var entry:files.entrySet())require(entry.getValue().equals(stamp(entry.getKey())),"Dependency archive identity changed after startup");
    }
}
