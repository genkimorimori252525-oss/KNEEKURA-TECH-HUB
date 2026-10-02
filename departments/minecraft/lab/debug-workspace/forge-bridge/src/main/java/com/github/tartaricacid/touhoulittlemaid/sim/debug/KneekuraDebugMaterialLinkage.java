package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
/** Original resource/container observations. Never resident transformed-definition proof. */
final class KneekuraDebugMaterialLinkage {
 private KneekuraDebugMaterialLinkage(){}
 static JsonObject verify(Object instantiatedMod,JsonObject descriptor,Path registeredBuild,Map<String,Class<?>> fixedProbeAnchors)throws IOException{
  KneekuraDebugOwnerInputs.validateMaterials(descriptor);if(instantiatedMod==null)throw new IOException("TARGET_MOD_NOT_INSTANTIATED");Class<?> target=instantiatedMod.getClass();
  Map<String,Class<?>> anchors=new HashMap<>(fixedProbeAnchors);anchors.put(target.getName(),target);String mode=KneekuraDebugOwnerInputs.t(descriptor,"linkageMode");
  Path build=registeredBuild.toRealPath();byte[] artifact=KneekuraDebugOwnerFiles.read(build.getParent(),build.getFileName().toString(),KneekuraDebugOwnerInputs.t(descriptor,"buildArtifactHash"),64*1024*1024);
  URL codeSource=codeSource(target);JsonObject container=container(target,codeSource);
  boolean jarMode=mode.equals("PACKAGED_JAR_CODE_SOURCE_AND_CLASS_RESOURCE_LINKAGE");
  if(jarMode){
   if(!codeSource.getProtocol().equals("file"))throw new IOException("PACKAGED_JAR_CODE_SOURCE_REQUIRED");Path nativeJar;try{nativeJar=Path.of(codeSource.toURI()).toAbsolutePath().normalize();}catch(Exception e){throw new IOException("UNSUPPORTED_NATIVE_CODE_SOURCE",e);}
   if(!nativeJar.toString().endsWith(".jar")||!Files.isRegularFile(nativeJar,LinkOption.NOFOLLOW_LINKS))throw new IOException("PACKAGED_JAR_CODE_SOURCE_REQUIRED");
   KneekuraDebugOwnerFiles.read(nativeJar.getParent(),nativeJar.getFileName().toString(),KneekuraDebugOwnerInputs.t(descriptor,"buildArtifactHash"),64*1024*1024);
  }
  JsonArray members=new JsonArray();boolean targetDeclared=false;
  for(JsonElement item:descriptor.getAsJsonArray("classResources")){
   JsonObject expected=item.getAsJsonObject();String name=KneekuraDebugOwnerInputs.t(expected,"className");Class<?> anchor=anchors.get(name);if(anchor==null)throw new IOException("UNSUPPORTED_CLASS_ANCHOR");boolean targetMember=anchor==target;targetDeclared|=targetMember;
   String path="/"+name.replace('.','/')+".class";URL resource=anchor.getResource(path);if(resource==null||!localResource(resource))throw new IOException("LOCAL_CLASS_RESOURCE_UNAVAILABLE");
   String resourceHash;
   if(resource.getProtocol().equals("file")){try{Path file=Path.of(resource.toURI()).toAbsolutePath().normalize();resourceHash=KneekuraDebugOwnerFiles.sha256(KneekuraDebugOwnerFiles.read(file.getParent(),file.getFileName().toString(),null,1024*1024));}catch(URISyntaxException e){throw new IOException("INVALID_CLASS_RESOURCE_URL",e);}}
   else{InputStream stream=anchor.getResourceAsStream(path);if(stream==null)throw new IOException("CLASS_RESOURCE_UNAVAILABLE");resourceHash=KneekuraDebugOwnerFiles.hashStream(stream,1024*1024);}
   if(!resourceHash.equals(KneekuraDebugOwnerInputs.t(expected,"sha256")))throw new IOException("CLASS_RESOURCE_HASH_MISMATCH");
   if(targetMember&&!jarMemberHash(artifact,path.substring(1)).equals(resourceHash))throw new IOException("REGISTERED_BUILD_MEMBER_MISMATCH");
   JsonObject row=new JsonObject();row.addProperty("className",name);row.addProperty("sha256",resourceHash);row.addProperty("resourceUrl",bounded(resource.toExternalForm()));row.addProperty("role",targetMember?"TARGET_MOD":"FIXED_OWNER_PROBE");row.addProperty("containerSource",bounded(codeSource(anchor).toExternalForm()));members.add(row);
  }
  if(!targetDeclared)throw new IOException("TARGET_MOD_MEMBER_NOT_DECLARED");
  JsonObject result=new JsonObject();result.addProperty("mode",mode);result.addProperty("targetModId",KneekuraDebugOwnerInputs.t(descriptor,"targetModId"));result.addProperty("buildArtifactHash",KneekuraDebugOwnerInputs.t(descriptor,"buildArtifactHash"));result.addProperty("buildArtifactCertainty",jarMode?"JAR_CODE_SOURCE_BYTES_MATCHED":"REGISTERED_BUILD_MEMBERS_MATCHED");result.add("containerIdentity",container);result.add("classResources",members);result.addProperty("configCertainty","ON_DISK_NOT_LOADED");result.addProperty("resourceCertainty","ON_DISK_NOT_LOADED");result.addProperty("transformedClassCertainty","NOT_ESTABLISHED");result.addProperty("fullTargetAttestation","NOT_ESTABLISHED");return result;
 }
 static URL codeSource(Class<?> type)throws IOException{try{if(type.getProtectionDomain()==null||type.getProtectionDomain().getCodeSource()==null||type.getProtectionDomain().getCodeSource().getLocation()==null)throw new IOException("NATIVE_CONTAINER_SOURCE_UNAVAILABLE");URL url=type.getProtectionDomain().getCodeSource().getLocation();if(!Set.of("file","jar","union","modjar").contains(url.getProtocol())||url.getProtocol().equals("jar")&&!localResource(url))throw new IOException("NONLOCAL_CONTAINER_SOURCE_UNSUPPORTED");return url;}catch(SecurityException e){throw new IOException("NATIVE_CONTAINER_SOURCE_UNAVAILABLE",e);}}
 static JsonObject container(Class<?> c,URL source)throws IOException{ClassLoader l=c.getClassLoader();if(l==null)throw new IOException("TARGET_CLASSLOADER_UNAVAILABLE");JsonObject r=new JsonObject();r.addProperty("className",c.getName());r.addProperty("codeSource",bounded(source.toExternalForm()));r.addProperty("codeSourceScheme",source.getProtocol());r.addProperty("classLoaderType",l.getClass().getName());r.addProperty("classLoaderName",l.getName()==null?"UNNAMED":bounded(l.getName()));r.addProperty("classLoaderIdentity",Integer.toHexString(System.identityHashCode(l)));r.addProperty("moduleName",c.getModule().getName()==null?"UNNAMED":c.getModule().getName());return r;}
 private static boolean localResource(URL url){String p=url.getProtocol();return p.equals("file")||p.equals("union")||p.equals("modjar")||p.equals("jar")&&(url.getFile().startsWith("file:")||url.getFile().startsWith("union:")||url.getFile().startsWith("modjar:"));}
 /** Inspect only the already hash-verified artifact bytes, with no second filesystem read.
  * The 64MiB aggregate expansion limit includes unrelated entries before the target member. */
 private static String jarMemberHash(byte[] jar,String member)throws IOException {
  final long expandedLimit=64L*1024*1024;
  final int classLimit=1024*1024;
  try(ZipInputStream archive=new ZipInputStream(new ByteArrayInputStream(jar))) {
   int entries=0;
   long expanded=0;
   byte[] buffer=new byte[8192];
   for(ZipEntry entry;(entry=archive.getNextEntry())!=null;) {
    if(++entries>65536)throw new IOException("BUILD_ARCHIVE_ENTRY_LIMIT");
    boolean selected=entry.getName().equals(member);
    if(selected&&entry.isDirectory())throw new IOException("BUILD_CLASS_MEMBER_UNAVAILABLE");
    ByteArrayOutputStream result=selected?new ByteArrayOutputStream():null;
    // Drain every entry ourselves, so getNextEntry never performs unchecked decompression.
    for(int count;(count=archive.read(buffer))!=-1;) {
     if(count==0)continue;
     expanded+=count;
     if(expanded>expandedLimit)throw new IOException("BUILD_ARCHIVE_EXPANSION_LIMIT");
     if(selected) {
      if(result.size()+count>classLimit)throw new IOException("CLASS_MEMBER_SIZE_LIMIT");
      result.write(buffer,0,count);
     }
    }
    if(selected)return KneekuraDebugOwnerFiles.sha256(result.toByteArray());
   }
  }
  throw new IOException("BUILD_CLASS_MEMBER_UNAVAILABLE");
 }
 private static String bounded(String value)throws IOException{if(value==null||value.length()>2048)throw new IOException("NATIVE_IDENTITY_SIZE_LIMIT");return value;}
}
