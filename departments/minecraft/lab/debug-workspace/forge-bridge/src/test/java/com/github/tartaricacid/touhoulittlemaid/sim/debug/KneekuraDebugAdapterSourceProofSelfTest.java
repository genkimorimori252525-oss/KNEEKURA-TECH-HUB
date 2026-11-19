package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.Map;
import java.util.HexFormat;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;

public final class KneekuraDebugAdapterSourceProofSelfTest {
    public static void main(String[] args)throws Exception {
        String owner=KneekuraDebugAdapterSourceProofSelfTest.class.getName();
        byte[] content;
        try(var in=KneekuraDebugAdapterSourceProofSelfTest.class.getResourceAsStream("/"+owner.replace('.','/')+".class")){content=in.readAllBytes();}
        var path=Files.createTempFile("kneekura-sdk-source-",".jar");
        try {
            try(var out=new JarOutputStream(Files.newOutputStream(path))){out.putNextEntry(new JarEntry(owner.replace('.','/')+".class"));out.write(content);out.closeEntry();}
            String jarHash=hash(Files.readAllBytes(path)),classHash=hash(content);
            var hashes=Map.of(owner,classHash);
            if(!KneekuraDebugAdapterSourceProof.verify(path,jarHash,hashes,key->content))throw new AssertionError("genuine class/JAR/resource proof");
            if(KneekuraDebugAdapterSourceProof.verify(path,"a".repeat(64),hashes,key->content))throw new AssertionError("wrong artifact accepted");
            if(KneekuraDebugAdapterSourceProof.verify(path,jarHash,Map.of(owner,"b".repeat(64)),key->content))throw new AssertionError("wrong class accepted");
            if(KneekuraDebugAdapterSourceProof.verify(path,jarHash,hashes,key->new byte[]{1}))throw new AssertionError("shadowed resource accepted");
            if(KneekuraDebugAdapterSourceProof.verify(path,jarHash,Map.of("absent.Owner",classHash),key->content))throw new AssertionError("missing owner accepted");
            System.out.println("Adapter source proof: exact genuine class/JAR/resource correspondence; no resident-transformation attestation");
        }finally{Files.deleteIfExists(path);}
    }
    private static String hash(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
}
