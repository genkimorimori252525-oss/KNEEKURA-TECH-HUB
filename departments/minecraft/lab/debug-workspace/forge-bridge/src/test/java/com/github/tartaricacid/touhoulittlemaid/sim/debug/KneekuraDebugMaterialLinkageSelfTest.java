package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.nio.file.*;
import java.net.*;
import java.util.*;
import java.util.zip.*;
import java.io.*;
public final class KneekuraDebugMaterialLinkageSelfTest {
 static int checks;
 static void check(boolean b,String label){checks++;if(!b)throw new AssertionError(label);}
 public static void main(String[] args)throws Exception{
  var target=new KneekuraDebugMaterialLinkageSelfTest();Class<?> type=target.getClass();String entry=type.getName().replace('.','/')+".class";
  byte[] member;try(InputStream in=type.getResourceAsStream("/"+entry)){member=in.readAllBytes();}
  Path root=Files.createTempDirectory("material-linkage").toRealPath(),build=root.resolve("build.jar");URL source=type.getProtectionDomain().getCodeSource().getLocation();Path nativePath=Path.of(source.toURI());boolean nativeJar=Files.isRegularFile(nativePath);
  if(nativeJar)Files.copy(nativePath,build);else{try(ZipOutputStream out=new ZipOutputStream(Files.newOutputStream(build))){out.putNextEntry(new ZipEntry(entry));out.write(member);out.closeEntry();}}
  JsonObject d=new JsonObject();d.addProperty("schemaVersion",1);d.addProperty("linkageMode","OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE");d.addProperty("targetModId","fixture_mod");d.addProperty("buildArtifactHash",KneekuraDebugOwnerFiles.sha256(Files.readAllBytes(build)));d.addProperty("configArtifactHash","a".repeat(64));d.addProperty("resourceArtifactHash","b".repeat(64));JsonArray rows=new JsonArray();JsonObject row=new JsonObject();row.addProperty("className",type.getName());row.addProperty("sha256",KneekuraDebugOwnerFiles.sha256(member));rows.add(row);d.add("classResources",rows);
  JsonObject observed=KneekuraDebugMaterialLinkage.verify(target,d,build,Map.of());check(observed.get("fullTargetAttestation").getAsString().equals("NOT_ESTABLISHED"),"not full target proof");check(observed.get("transformedClassCertainty").getAsString().equals("NOT_ESTABLISHED"),"no transformed bytes claim");check(observed.get("buildArtifactCertainty").getAsString().equals("REGISTERED_BUILD_MEMBERS_MATCHED"),"separate container tier");
  JsonObject wrong=d.deepCopy();wrong.getAsJsonArray("classResources").get(0).getAsJsonObject().addProperty("sha256","c".repeat(64));try{KneekuraDebugMaterialLinkage.verify(target,wrong,build,Map.of());throw new AssertionError("wrong class hash");}catch(IOException expected){checks++;}
  wrong=d.deepCopy();wrong.getAsJsonArray("classResources").get(0).getAsJsonObject().addProperty("className","foreign.ClassNeverLoad");try{KneekuraDebugMaterialLinkage.verify(target,wrong,build,Map.of());throw new AssertionError("arbitrary class anchor");}catch(IOException expected){checks++;}
  d.addProperty("linkageMode","PACKAGED_JAR_CODE_SOURCE_AND_CLASS_RESOURCE_LINKAGE");
  if(nativeJar){var jarProof=KneekuraDebugMaterialLinkage.verify(target,d,build,Map.of());check(jarProof.get("buildArtifactCertainty").getAsString().equals("JAR_CODE_SOURCE_BYTES_MATCHED"),"actual native JAR mode");}
  else try{KneekuraDebugMaterialLinkage.verify(target,d,build,Map.of());throw new AssertionError("directory is not JAR proof");}catch(IOException expected){check(expected.getMessage().equals("PACKAGED_JAR_CODE_SOURCE_REQUIRED"),"specific blocked layout");}
  // The compressed artifact fits its disk limit, but unrelated expanded bytes must not exhaust a server tick.
  Path excessiveBuild=root.resolve("excessive-unrelated-entry.jar");
  try(ZipOutputStream out=new ZipOutputStream(Files.newOutputStream(excessiveBuild))){
   out.putNextEntry(new ZipEntry("unrelated-resource.bin"));
   byte[] zeros=new byte[8192];
   for(int i=0;i<65*128;i++)out.write(zeros);
   out.closeEntry();
   out.putNextEntry(new ZipEntry(entry));out.write(member);out.closeEntry();
  }
  check(Files.size(excessiveBuild)<1024*1024,"small compressed fixture");
  JsonObject bounded=d.deepCopy();
  bounded.addProperty("linkageMode","OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE");
  bounded.addProperty("buildArtifactHash",KneekuraDebugOwnerFiles.sha256(Files.readAllBytes(excessiveBuild)));
  try{
   KneekuraDebugMaterialLinkage.verify(target,bounded,excessiveBuild,Map.of());
   throw new AssertionError("unrelated archive expansion exceeded its aggregate budget");
  }catch(IOException expected){
   check(expected.getMessage().equals("BUILD_ARCHIVE_EXPANSION_LIMIT"),"explicit aggregate expansion limit");
  }
  System.out.println("native JVM material linkage checks="+checks+" layout="+(nativeJar?"JAR":"DIRECTORY")+"; no Minecraft fixture proof");
 }
}
