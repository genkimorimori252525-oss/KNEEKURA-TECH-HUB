package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.io.*;
import java.nio.*;
import java.nio.channels.FileChannel;
import java.nio.charset.*;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.*;
import java.util.*;
final class KneekuraDebugOwnerFiles {
 private KneekuraDebugOwnerFiles(){}
 static byte[] read(Path root,String relative,String expected,int maximum)throws IOException{
  if(!root.isAbsolute()||!root.normalize().equals(root.toRealPath())||maximum<1||maximum>64*1024*1024)throw new IOException("UNSAFE_OWNER_ROOT_OR_LIMIT");
  Path rel=Path.of(relative);if(rel.isAbsolute()||rel.getNameCount()>8||relative.contains("\\")||Arrays.stream(relative.split("/",-1)).anyMatch(s->s.isEmpty()||s.equals(".")||s.equals("..")))throw new IOException("UNSAFE_OWNER_PATH");
  Path file=root;for(Path part:rel){file=file.resolve(part);if(Files.isSymbolicLink(file))throw new IOException("OWNER_SYMLINK_REJECTED");}
  BasicFileAttributes before=Files.readAttributes(file,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);if(!before.isRegularFile()||before.size()>maximum)throw new IOException("OWNER_FILE_NOT_REGULAR_OR_TOO_LARGE");
  try(FileChannel channel=FileChannel.open(file,StandardOpenOption.READ,StandardOpenOption.WRITE,LinkOption.NOFOLLOW_LINKS)){
   long size=channel.size();BasicFileAttributes opened=Files.readAttributes(file,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
   if(!opened.isRegularFile()||size!=before.size()||size!=opened.size()||!Objects.equals(before.fileKey(),opened.fileKey()))throw new IOException("OWNER_FILE_DRIFT");
   ByteBuffer bytes=ByteBuffer.allocate((int)size);int zeros=0;while(bytes.hasRemaining()){int n=channel.read(bytes);if(n<0||n==0&&++zeros>2)throw new IOException("OWNER_FILE_DRIFT");}
   BasicFileAttributes after=Files.readAttributes(file,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);if(!after.isRegularFile()||after.size()!=size||channel.size()!=size||!Objects.equals(opened.fileKey(),after.fileKey())||!opened.lastModifiedTime().equals(after.lastModifiedTime()))throw new IOException("OWNER_FILE_DRIFT");
   byte[] data=bytes.array();if(expected!=null&&!sha256(data).equals(KneekuraDebugActionJournal.hash(expected)))throw new IOException("OWNER_FILE_HASH_MISMATCH");return data;
  }
 }
 static JsonObject json(Path root,String name,String hash,int max)throws IOException{byte[] b=read(root,name,hash,max);String text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(b)).toString();return KneekuraDebugActionJournal.object(KneekuraDebugActionJournal.parse(text));}
 static String sha256(byte[] b){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b));}catch(NoSuchAlgorithmException e){throw new AssertionError(e);}}
 static String hashStream(InputStream stream,int max)throws IOException{try(stream){try{MessageDigest digest=MessageDigest.getInstance("SHA-256");byte[] buffer=new byte[8192];long size=0;for(int n;(n=stream.read(buffer))!=-1;){if(n==0)continue;if((size+=n)>max)throw new IOException("OWNER_STREAM_SIZE_LIMIT");digest.update(buffer,0,n);}return HexFormat.of().formatHex(digest.digest());}catch(NoSuchAlgorithmException e){throw new AssertionError(e);}}}
 static void writeNew(Path root,String name,JsonObject body)throws IOException{Path p=writablePath(root,name);write(p,body);}
 /** Checked predecessor and forced temp file, atomic publication only; failed temp files remain for inspection. */
 static String replaceExpected(Path root,String name,String expected,JsonObject body)throws IOException{
  byte[] bytes=(KneekuraDebugActionJournal.canonical(body)+"\n").getBytes(StandardCharsets.UTF_8);
  if(bytes.length>65536)throw new IOException("OWNER_PUBLICATION_SIZE_LIMIT");
  read(root,name,expected,65536);Path target=writablePath(root,name),temp=writablePath(root,name+".tmp-"+UUID.randomUUID());
  write(temp,body);read(root,name,expected,65536);
  Files.move(temp,target,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
  String published=sha256(bytes);read(root,name,published,65536);return published;
 }
 static void writeStatus(Path root,JsonObject body)throws IOException{Path target=writablePath(root,"control/owner-status.json"),temp=writablePath(root,"control/owner-status.tmp-"+UUID.randomUUID());write(temp,body);try{Files.move(temp,target,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}catch(AtomicMoveNotSupportedException e){Files.move(temp,target,StandardCopyOption.REPLACE_EXISTING);}finally{Files.deleteIfExists(temp);}}
 private static Path writablePath(Path root,String relative)throws IOException{
  if(!root.isAbsolute()||!root.normalize().equals(root.toRealPath()))throw new IOException("UNSAFE_OWNER_ROOT");Path rel=Path.of(relative);if(rel.isAbsolute()||rel.getNameCount()>8||relative.contains("\\")||Arrays.stream(relative.split("/",-1)).anyMatch(s->s.isEmpty()||s.equals(".")||s.equals("..")))throw new IOException("UNSAFE_OWNER_PATH");
  Path parent=root;for(int i=0;i<rel.getNameCount()-1;i++){parent=parent.resolve(rel.getName(i));if(!Files.exists(parent,LinkOption.NOFOLLOW_LINKS)){try{Files.createDirectory(parent);}catch(FileAlreadyExistsException raced){}}if(Files.isSymbolicLink(parent)||!Files.isDirectory(parent,LinkOption.NOFOLLOW_LINKS)||!parent.toRealPath().equals(parent))throw new IOException("OWNER_OUTPUT_PARENT_UNSAFE");}
  Path file=parent.resolve(rel.getFileName());if(Files.isSymbolicLink(file))throw new IOException("OWNER_OUTPUT_SYMLINK_REJECTED");return file;
 }
 private static void write(Path p,JsonObject body)throws IOException{try(FileChannel f=FileChannel.open(p,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE,LinkOption.NOFOLLOW_LINKS)){ByteBuffer b=StandardCharsets.UTF_8.encode(KneekuraDebugActionJournal.canonical(body)+"\n");while(b.hasRemaining())f.write(b);f.force(true);}}
}
