package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.nio.file.FileSystemException;
import java.util.*;

/** One failure supplement only. No messages, paths, authority changes or retry. */
final class KneekuraDebugOwnerFailure {
 @FunctionalInterface interface Persistence {void write(String diagnostic)throws Exception;}
 static boolean capture(String stage,Throwable error,Persistence persistence){
  try{persistence.write(describe(stage,error));return true;}catch(Exception unavailable){return false;}
 }
 static String describe(String stage,Throwable error){
  StringBuilder out=new StringBuilder("stage="+safe(stage,32));
  Set<Throwable> seen=Collections.newSetFromMap(new IdentityHashMap<>());int causes=0,frames=0;
  for(Throwable current=error;current!=null&&causes<4&&seen.add(current);current=current.getCause(),causes++){
   out.append("\ncause=").append(safe(current.getClass().getName(),96));
   if(current instanceof FileSystemException fs)out.append(" file=").append(basename(fs.getFile())).append(" other=").append(basename(fs.getOtherFile()));
   for(var frame:current.getStackTrace()){
    if(frames++>=8)break;
    out.append("\nframe=").append(safe(frame.getClassName(),96)).append(':').append(safe(frame.getMethodName(),48)).append(':').append(frame.getLineNumber());
   }
  }
  return out.substring(0,Math.min(1536,out.length()));
 }
 private static String basename(String value){if(value==null)return "NONE";String normalized=value.replace('\\','/');return safe(normalized.substring(normalized.lastIndexOf('/')+1),64);}
 private static String safe(String value,int limit){if(value==null)return "NONE";String text=value.substring(0,Math.min(limit,value.length())).replaceAll("[^a-zA-Z0-9_.$-]","_");return text.isEmpty()?"NONE":text;}
}
