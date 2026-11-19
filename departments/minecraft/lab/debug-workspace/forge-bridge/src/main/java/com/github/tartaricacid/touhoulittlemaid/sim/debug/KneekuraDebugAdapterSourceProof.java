package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Map;
import java.util.jar.JarFile;

/** Exact development-container/resource correspondence, never transformed resident-byte attestation. */
public final class KneekuraDebugAdapterSourceProof {
    public static final int MAX_CLASS_BYTES=512*1024;
    private static final long MAX_ARTIFACT_BYTES=64L*1024*1024;
    @FunctionalInterface public interface ResourceReader {byte[] read(String owner)throws Exception;}
    private KneekuraDebugAdapterSourceProof(){ }
    public static boolean verify(Path artifact,String artifactHash,Map<String,String> classHashes,ResourceReader resources) {
        if(artifact==null||artifactHash==null||!artifactHash.matches("[a-f0-9]{64}")||classHashes==null||
                classHashes.isEmpty()||classHashes.size()>32||resources==null)return false;
        try {
            if(!Files.isRegularFile(artifact)||Files.size(artifact)>MAX_ARTIFACT_BYTES)return false;
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            try(InputStream in=Files.newInputStream(artifact)) {
                byte[] buffer=new byte[64*1024];int count;long total=0;
                while((count=in.read(buffer))!=-1){total+=count;if(total>MAX_ARTIFACT_BYTES)return false;digest.update(buffer,0,count);}
            }
            if(!HexFormat.of().formatHex(digest.digest()).equals(artifactHash))return false;
            try(JarFile jar=new JarFile(artifact.toFile(),false)) {
                for(var entry:classHashes.entrySet()) {
                    String owner=entry.getKey(),expected=entry.getValue();
                    if(owner==null||!owner.matches("[A-Za-z_$][A-Za-z0-9_$.]{1,255}")||expected==null||!expected.matches("[a-f0-9]{64}"))return false;
                    var item=jar.getJarEntry(owner.replace('.','/')+".class");
                    if(item==null||item.getSize()>MAX_CLASS_BYTES)return false;
                    byte[] captured;try(var in=jar.getInputStream(item)){captured=in.readNBytes(MAX_CLASS_BYTES+1);}
                    byte[] loadedResource=resources.read(owner);
                    if(captured.length>MAX_CLASS_BYTES||loadedResource==null||loadedResource.length>MAX_CLASS_BYTES||
                            !hash(captured).equals(expected)||!hash(loadedResource).equals(expected))return false;
                }
            }
            return true;
        }catch(Exception unavailable){return false;}
    }
    private static String hash(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
}
