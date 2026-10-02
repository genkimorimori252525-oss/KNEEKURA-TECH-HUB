package org.kneekura.observer;

import com.google.gson.*;
import java.io.InputStream;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/** Explicit selected-archive resource checks; no namespace or transformed-memory equivalence claim. */
final class TargetDependency {
    private static final int MAX_CLASS=16*1024*1024;
    private static final Set<String> HYDRA=Set.of("twilightforest/entity/boss/Hydra.class","twilightforest/entity/boss/HydraPart.class",
        "twilightforest/entity/boss/HydraHeadContainer.class","twilightforest/client/TFClientSetup.class",
        "twilightforest/client/JappaPackReloadListener.class","twilightforest/client/renderer/entity/HydraRenderer.class",
        "twilightforest/client/model/entity/HydraModel.class");
    private static void require(boolean value,String message) {DedicatedSession.require(value,message);}
    private static String string(JsonObject value,String field) {return DedicatedSession.string(value,field);}
    private static String hash(JsonObject value,String field) {
        String text=string(value,field);require(text.matches("[0-9a-f]{64}"),"Invalid selected dependency digest");return text;
    }
    private static String resource(JsonElement value) {
        require(value!=null && value.isJsonPrimitive() && value.getAsJsonPrimitive().isString(),"Class resource string required");
        String text=value.getAsString();
        require(text.length()<=2048 && text.matches("twilightforest/(?:[A-Za-z0-9_$]+/)*[A-Za-z0-9_$]+\\.class"),"Canonical bounded class resource required");
        return text;
    }
    private static String sha(InputStream in) throws Exception {
        require(in!=null,"Selected class resource missing");
        byte[] bytes=in.readNBytes(MAX_CLASS+1);require(bytes.length>0 && bytes.length<=MAX_CLASS,"Selected class resource exceeds byte bound");
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    static void verify(JsonObject session,JsonObject identity,DependencyInventory dependencies,ClassLoader loader) throws Exception {
        require(DedicatedSession.role(identity).equals("integrated_client"),"Selected U04 dependency requires integrated schema3 role");
        JsonObject selection=session.getAsJsonObject("target_selection");
        require(selection!=null && selection.keySet().equals(Set.of("schema_version","kind","coordinate","sha256","provider_receipt_hash","class_resources")),"Exact target selection fields required");
        DedicatedSession.integer(selection,"schema_version",1,1);
        require(string(selection,"kind").equals("u04_hydra_derived_dependency"),"Wrong fixed target selection kind");
        String coordinate=string(selection,"coordinate");require(coordinate.startsWith("twilightforest-") && coordinate.length()<=2048 && coordinate.chars().noneMatch(c->c<32 || c==127),"Invalid selected coordinate");
        hash(selection,"provider_receipt_hash");String archiveHash=hash(selection,"sha256");
        require(DedicatedSession.hash(selection).equals(hash(identity,"target_selection_hash")),"Target selection hash mismatch");
        JsonArray resources=selection.getAsJsonArray("class_resources"),probes=session.getAsJsonArray("target_dependency_probes");
        require(resources!=null && resources.size()>=1 && resources.size()<=32 && probes!=null && probes.size()==resources.size(),"Complete bounded target probe mapping required");
        Set<String> markerResources=new HashSet<>();
        for(JsonElement marker:session.getAsJsonArray("class_probes"))markerResources.add(string(marker.getAsJsonObject(),"resource"));
        Set<String> seen=new HashSet<>();List<String> names=new ArrayList<>(),expected=new ArrayList<>();
        for(int index=0;index<resources.size();index++) {
            String name=resource(resources.get(index));require(seen.add(name) && !markerResources.contains(name),"Duplicate target resource or marker/target probe overlap");
            JsonObject probe=probes.get(index).getAsJsonObject();
            require(probe.keySet().equals(Set.of("resource","sha256")) && resource(probe.get("resource")).equals(name),"Target probe order/fields differ from selection");
            names.add(name);expected.add(hash(probe,"sha256"));
        }
        require(seen.containsAll(HYDRA),"The fixed Hydra entity/renderer/model/marker resource slice is incomplete");
        Path archive=dependencies.selectedArchive(coordinate,archiveHash);
        try(ZipFile zip=new ZipFile(archive.toFile())) {
            Map<String,Integer> occurrences=new HashMap<>();var entries=zip.entries();int scanned=0;
            while(entries.hasMoreElements()) {
                ZipEntry entry=entries.nextElement();require(++scanned<=50000,"Selected archive entry bound exceeded");
                if(seen.contains(entry.getName()))occurrences.merge(entry.getName(),1,Integer::sum);
            }
            for(int index=0;index<names.size();index++) {
                String name=names.get(index);ZipEntry entry=zip.getEntry(name);
                require(occurrences.getOrDefault(name,0)==1 && entry!=null && !entry.isDirectory()
                    && entry.getSize()>0 && entry.getSize()<=MAX_CLASS,"Missing, ambiguous or oversized selected archive class");
                try(InputStream in=zip.getInputStream(entry)) {require(sha(in).equals(expected.get(index)),"Selected archive class bytes differ from probe");}
                try(InputStream in=loader.getResourceAsStream(name)) {require(sha(in).equals(expected.get(index)),"Runtime selected class resource bytes differ from archive probe");}
            }
        }
        dependencies.checkUnchanged();
    }
}
