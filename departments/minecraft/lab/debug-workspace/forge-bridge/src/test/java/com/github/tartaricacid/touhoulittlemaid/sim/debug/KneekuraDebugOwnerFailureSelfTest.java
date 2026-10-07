package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.nio.file.AccessDeniedException;
import java.io.IOException;
public final class KneekuraDebugOwnerFailureSelfTest {
 public static void main(String[] args){
  var error=new AccessDeniedException("C:/private-secret/control/source.tmp","C:/private-secret/control/owner-status.json",null);
  var text=KneekuraDebugOwnerFailure.describe("STATUS",new IOException("credential-secret",error));
  if(!text.contains("AccessDeniedException")||!text.contains("source.tmp")||!text.contains("owner-status.json")||!text.contains("stage=STATUS"))throw new AssertionError("Denied operation lost");
  if(text.contains("private-secret")||text.contains("credential-secret")||text.contains("C:/"))throw new AssertionError("Raw message/path leaked");
  error.setStackTrace(new StackTraceElement[0]);if(!KneekuraDebugOwnerFailure.describe("STATUS",error).contains("AccessDeniedException"))throw new AssertionError("Null reason/stack unsupported");
  var large=new IOException("secret".repeat(1000));large.setStackTrace(java.util.stream.IntStream.range(0,100).mapToObj(i->new StackTraceElement("x".repeat(1000),"m".repeat(1000),"secret-source",i)).toArray(StackTraceElement[]::new));
  if(KneekuraDebugOwnerFailure.describe("x".repeat(1000),large).length()>1536)throw new AssertionError("Unbounded diagnostic");
  int[] written={0};if(!KneekuraDebugOwnerFailure.capture("STATUS",error,value->written[0]++)||written[0]!=1)throw new AssertionError("Diagnostic absent");
  if(KneekuraDebugOwnerFailure.capture("STATUS",error,value->{throw new IOException("disk failed");}))throw new AssertionError("Persistence failure accepted");
  System.out.println("PASS: 6 bounded owner diagnostics/redaction/persistence checks");
 }
}
