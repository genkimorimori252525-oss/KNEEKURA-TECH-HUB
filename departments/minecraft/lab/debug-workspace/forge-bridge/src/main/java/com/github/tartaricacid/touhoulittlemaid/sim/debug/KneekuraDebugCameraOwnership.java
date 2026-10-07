package com.github.tartaricacid.touhoulittlemaid.sim.debug;
/** Cooperative client camera claim. A foreign operation cannot release another token. */
final class KneekuraDebugCameraOwnership {
 private static Object owner;
 private KneekuraDebugCameraOwnership(){}
 static synchronized boolean claim(Object token){
  if(token==null)throw new IllegalArgumentException("CAMERA_TOKEN_REQUIRED");
  if(owner!=null)return false;owner=token;return true;
 }
 static synchronized boolean owns(Object token){return token!=null&&owner==token;}
 static synchronized void release(Object token){if(token!=null&&owner==token)owner=null;}
 /** Raw evidence excludes derived overlays; ordinary/live presentation retains them. */
 static boolean derivedOverlayAllowed(boolean cardinalQuiescent,boolean povSnapshotPending){return cardinalQuiescent&&!povSnapshotPending;}
}
