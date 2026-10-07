package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import com.sun.jna.platform.win32.*;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.ModContainer;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.world.level.storage.LevelResource;
import java.io.IOException;
import java.net.*;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.*;
/** Concrete Supervisor-pinned scoped control gate; full target certainty is intentionally incomplete. */
final class KneekuraDebugScopedOwnerGate implements KneekuraDebugArenaRuntime.OwnerGate {
 private record Stamp(Object key,long size,long modified,boolean directory){}
 private record WindowsDirectoryKey(long volumeSerial,String fileId){}
 private final KneekuraDebugEnv.Config config;private final MinecraftServer server;private final ServerLevel level;private final KneekuraDebugOwnerInputs input;
 private final Class<?> bootstrapAnchor;
 private final Object mod;private final String modId;private final Class<?> modClass;private final ClassLoader loader;private final String source;
 private final Map<Path,Stamp> stamps=new LinkedHashMap<>();private JsonObject linkage;private final JsonObject world;private long materialCostNanos;
 KneekuraDebugScopedOwnerGate(KneekuraDebugEnv.Config cfg,MinecraftServer server,ServerLevel level,KneekuraDebugOwnerInputs input,Class<?> bootstrapAnchor)throws IOException{
  if(bootstrapAnchor==null||!bootstrapAnchor.getName().equals("com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugClientBootstrap")||bootstrapAnchor.getClassLoader()!=KneekuraDebugArenaRuntime.class.getClassLoader())throw new IOException("FIXED_BOOTSTRAP_ANCHOR_REQUIRED");this.bootstrapAnchor=bootstrapAnchor;this.config=cfg;this.server=server;this.level=level;this.input=input;this.modId=KneekuraDebugOwnerInputs.t(input.materials(),"targetModId");
  mod=targetMod(modId);modClass=mod.getClass();loader=modClass.getClassLoader();source=KneekuraDebugMaterialLinkage.codeSource(modClass).toExternalForm();
  world=verifyWorld(server.getWorldPath(LevelResource.ROOT),server.getWorldData().getLevelName(),level.dimension().location().toString(),input.world(),KneekuraDebugOwnerInputs.t(input.envelope(),"worldRegistrationHash"));
  for(String file:List.of("control/owner-envelope.json","control/owner-grant.json","control/owner-material-descriptor.json","control/owner-world-registration.json","control/owner-experiment-request.json","run-snapshot.json","run-snapshot.canonical.json","control/owner-materials/build.jar","control/owner-materials/config.bin","control/owner-materials/resources.bin"))remember(input.runDir().resolve(file));
  if(input.triggerConfig()!=null)remember(input.runDir().resolve("control/owner-trigger-config.json"));
  if(input.envelope().has("tankRotationHash"))for(String file:List.of("control/owner-tank-rotation.json","control/owner-tank-predecessor.json"))remember(input.runDir().resolve(file));
  remember(Path.of(KneekuraDebugOwnerInputs.t(world,"canonicalWorldRoot")));
  rememberLocalCodeFile(KneekuraDebugMaterialLinkage.codeSource(modClass));
  for(JsonElement row:input.materials().getAsJsonArray("classResources")){String name=KneekuraDebugOwnerInputs.t(row.getAsJsonObject(),"className");Class<?> anchor=anchors().get(name);if(anchor==null)throw new IOException("UNSUPPORTED_CLASS_ANCHOR");URL url=anchor.getResource("/"+name.replace('.','/')+".class");if(url!=null)rememberLocalCodeFile(url);}
  revalidateBoundary();requireAuthorized(cfg,server,input.grant());
 }
 private static Object targetMod(String id)throws IOException{ModList list=ModList.get();if(list==null)throw new IOException("FORGE_MOD_LIST_UNAVAILABLE");ModContainer container=list.getModContainerById(id).orElseThrow(()->new IOException("TARGET_MOD_CONTAINER_UNAVAILABLE"));Object mod=container.getMod();if(mod==null)throw new IOException("TARGET_MOD_NOT_INSTANTIATED");return mod;}
 private Map<String,Class<?>> anchors(){Map<String,Class<?>> a=new HashMap<>();a.put(modClass.getName(),modClass);for(Class<?> c:List.of(bootstrapAnchor,KneekuraDebugArenaRuntime.class,KneekuraDebugArenaController.class,KneekuraDebugForgeArenaBackend.class,KneekuraDebugEvidenceWriter.class,KneekuraDebugTankRotationPlan.class,KneekuraDebugTankRotationController.class,KneekuraDebugForgeTankRotationBackend.class,KneekuraDebugMobPovCamera.class,KneekuraDebugMobPovOwner.class,KneekuraDebugMobPovCommands.class,KneekuraDebugCameraOwnership.class,KneekuraDebugMobPovSession.class,KneekuraDebugMotionOverlay.class))a.put(c.getName(),c);return a;}
 void revalidateBoundary()throws IOException{
  long start=System.nanoTime();requireFast();input.verifyDiskMaterials();linkage=KneekuraDebugMaterialLinkage.verify(mod,input.materials(),input.runDir().resolve("control/owner-materials/build.jar"),anchors());requireFast();materialCostNanos=System.nanoTime()-start;
  linkage.addProperty("revalidationScope","INSTALLATION_AND_ACTION_BOUNDARY");linkage.addProperty("verificationCostNanos",materialCostNanos);linkage.addProperty("perCellGuard","EXACT_ANCHOR_CONTAINER_METADATA_WORLD_LEASE");
 }
 private void requireFast()throws IOException{
  if(!server.isSameThread())throw new IOException("SERVER_THREAD_REQUIRED");if(!(server instanceof IntegratedServer integrated)||integrated.isPublished())throw new IOException("PRIVATE_INTEGRATED_SERVER_REQUIRED");
  if(targetMod(modId)!=mod||mod.getClass()!=modClass||modClass.getClassLoader()!=loader||!KneekuraDebugMaterialLinkage.codeSource(modClass).toExternalForm().equals(source))throw new IOException("NATIVE_MOD_CONTAINER_DRIFT");
  for(var e:stamps.entrySet())if(!stamp(e.getKey()).equals(e.getValue()))throw new IOException("OWNER_MATERIAL_OR_INPUT_METADATA_DRIFT");
  JsonObject now=verifyWorld(server.getWorldPath(LevelResource.ROOT),server.getWorldData().getLevelName(),level.dimension().location().toString(),input.world(),KneekuraDebugOwnerInputs.t(input.envelope(),"worldRegistrationHash"));if(!now.equals(world))throw new IOException("NATIVE_WORLD_DRIFT");
 }
 @Override public void requireAuthorized(KneekuraDebugEnv.Config cfg,MinecraftServer current,KneekuraDebugArenaOwnerGrant grant)throws IOException{
  if(current!=server||cfg!=config||!grant.equals(input.grant())||cfg.ownerSetup()==null||!cfg.ownerSetup().sha256().equals(input.envelopeHash()))throw new IOException("SCOPED_OWNER_IDENTITY_MISMATCH");requireFast();
 }
 JsonObject linkage(){return linkage.deepCopy();}JsonObject world(){return world.deepCopy();}
 static JsonObject verifyWorld(Path actualRoot,String actualName,String actualDimension,JsonObject registration,String registrationHash)throws IOException{
  Path expected=Path.of(KneekuraDebugOwnerInputs.t(registration,"canonicalWorldRoot"));Path actual=actualRoot.toRealPath();
  if(!expected.equals(expected.toRealPath())||!actual.equals(expected)||!actualName.equals("KNEEKURA_DEBUG_WORLD")||!actualName.equals(KneekuraDebugOwnerInputs.t(registration,"worldName"))||!actualDimension.equals(KneekuraDebugOwnerInputs.t(registration,"dimensionId")))throw new IOException("OPERATOR_REGISTERED_WORLD_MISMATCH");
  boolean allowed=false;for(JsonElement p:registration.getAsJsonArray("permissions"))allowed|=p.getAsString().equals(KneekuraDebugOwnerInputs.CONTROL);if(!allowed)throw new IOException("WORLD_CONTROL_NOT_REGISTERED");
  JsonObject observed=new JsonObject();observed.addProperty("canonicalWorldRoot",actual.toString());observed.addProperty("worldName",actualName);observed.addProperty("dimensionId",actualDimension);observed.addProperty("registrationHash",KneekuraDebugActionJournal.hash(registrationHash));return observed;
 }
 private void remember(Path file)throws IOException{Path p=file.toAbsolutePath().normalize();if(!p.equals(p.toRealPath())||Files.isSymbolicLink(p))throw new IOException("NATIVE_MATERIAL_PATH_UNSAFE");stamps.put(p,stamp(p));}
 private void rememberLocalCodeFile(URL url)throws IOException{if(!url.getProtocol().equals("file"))return;try{if(url.getHost()!=null&&!url.getHost().isEmpty()&&!url.getHost().equals("localhost"))throw new IOException("NONLOCAL_CODE_SOURCE_UNSUPPORTED");Path p=Path.of(url.toURI());remember(p);}catch(URISyntaxException e){throw new IOException("NATIVE_CODE_SOURCE_URL_INVALID",e);}}
 private static Stamp stamp(Path p)throws IOException{BasicFileAttributes s=Files.readAttributes(p,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);if(!s.isRegularFile()&&!s.isDirectory())throw new IOException("OWNER_METADATA_NOT_REGULAR");Object key=s.fileKey();if(s.isDirectory()&&key==null)key=windowsDirectoryKey(p);return new Stamp(key,s.isDirectory()?-1:s.size(),s.isDirectory()?-1:s.lastModifiedTime().toMillis(),s.isDirectory());}
 /** The existing Forge JNA dependency reads the volume + 128-bit object ID, never creation time. */
 private static WindowsDirectoryKey windowsDirectoryKey(Path p)throws IOException{
  if(!System.getProperty("os.name").startsWith("Windows"))throw new IOException("OWNER_DIRECTORY_IDENTITY_UNAVAILABLE");
  try{
   var api=Kernel32.INSTANCE;
   var handle=api.CreateFile(p.toString(),WinNT.FILE_READ_ATTRIBUTES,WinNT.FILE_SHARE_READ|WinNT.FILE_SHARE_WRITE|WinNT.FILE_SHARE_DELETE,null,WinNT.OPEN_EXISTING,WinNT.FILE_FLAG_BACKUP_SEMANTICS|WinNT.FILE_FLAG_OPEN_REPARSE_POINT,null);
   if(handle==null||WinBase.INVALID_HANDLE_VALUE.equals(handle))throw new IOException("WINDOWS_DIRECTORY_OPEN_FAILED:"+api.GetLastError());
   try{
    var tag=new WinBase.FILE_ATTRIBUTE_TAG_INFO(); // FileAttributeTagInfo = 9.
    if(!api.GetFileInformationByHandleEx(handle,9,tag.getPointer(),new WinDef.DWORD(tag.size())))throw new IOException("WINDOWS_DIRECTORY_ATTRIBUTES_FAILED:"+api.GetLastError());
    tag.read();if((tag.FileAttributes&WinNT.FILE_ATTRIBUTE_DIRECTORY)==0||(tag.FileAttributes&WinNT.FILE_ATTRIBUTE_REPARSE_POINT)!=0)throw new IOException("WINDOWS_DIRECTORY_REPARSE_OR_NON_DIRECTORY");
    var info=new WinBase.FILE_ID_INFO(); // FileIdInfo = 18; supported from Windows 8.
    if(!api.GetFileInformationByHandleEx(handle,18,info.getPointer(),new WinDef.DWORD(info.size())))throw new IOException("WINDOWS_DIRECTORY_ID_FAILED:"+api.GetLastError());
    info.read();byte[] id=new byte[16];boolean nonzero=false;for(int i=0;i<id.length;i++){id[i]=info.FileId.Identifier[i].byteValue();nonzero|=id[i]!=0;}
    if(!nonzero)throw new IOException("WINDOWS_DIRECTORY_ID_UNAVAILABLE");
    return new WindowsDirectoryKey(info.VolumeSerialNumber,HexFormat.of().formatHex(id));
   }finally{if(!api.CloseHandle(handle))throw new IOException("WINDOWS_DIRECTORY_HANDLE_CLOSE_FAILED:"+api.GetLastError());}
  }catch(IOException|RuntimeException|LinkageError e){throw new IOException("OWNER_DIRECTORY_IDENTITY_UNAVAILABLE",e);}
 }
}
