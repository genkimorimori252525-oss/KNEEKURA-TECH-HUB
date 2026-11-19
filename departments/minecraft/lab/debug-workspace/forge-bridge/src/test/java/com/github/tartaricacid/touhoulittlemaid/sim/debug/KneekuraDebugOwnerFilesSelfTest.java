package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.nio.file.*;
import java.io.IOException;
public final class KneekuraDebugOwnerFilesSelfTest {
 public static void main(String[] args)throws Exception{
  Path root=Files.createTempDirectory("owner-writes").toRealPath(),outside=Files.createTempDirectory("foreign-writes").toRealPath();Files.createSymbolicLink(root.resolve("control"),outside);JsonObject row=new JsonObject();row.addProperty("schemaVersion",1);
  try{KneekuraDebugOwnerFiles.writeNew(root,"control/receipt.json",row);throw new AssertionError("owner receipt followed foreign parent");}catch(IOException expected){}
  if(Files.exists(outside.resolve("receipt.json")))throw new AssertionError("foreign receipt created");
  Files.delete(root.resolve("control"));KneekuraDebugOwnerFiles.writeNew(root,"control/receipt.json",row);if(!KneekuraDebugOwnerFiles.json(root,"control/receipt.json",null,1024).equals(row))throw new AssertionError("durable receipt");
  try{KneekuraDebugOwnerFiles.writeNew(root,"control/receipt.json",row);throw new AssertionError("receipt overwrite");}catch(FileAlreadyExistsException expected){}
  KneekuraDebugOwnerFiles.writeStatus(root,row);row.addProperty("status","OWNER_CLOSED");KneekuraDebugOwnerFiles.writeStatus(root,row);if(!KneekuraDebugOwnerFiles.json(root,"control/owner-status.json",null,1024).equals(row))throw new AssertionError("atomic status replace");
  System.out.println("owner output path and immutable/status checks=5");
 }
}
