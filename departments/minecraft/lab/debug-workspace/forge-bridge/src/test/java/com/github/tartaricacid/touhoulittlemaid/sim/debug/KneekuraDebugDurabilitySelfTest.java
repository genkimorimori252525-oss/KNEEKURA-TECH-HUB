package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.nio.file.*;
import java.io.*;
import java.util.concurrent.*;
public final class KneekuraDebugDurabilitySelfTest {
 public static void main(String[] args)throws Exception {
  Path file=Files.createTempFile("lab-durable-observation",".jsonl");String row="{\"arenaEpoch\":2,\"lane\":\"ARENA_RESET\"}";
  CompletableFuture<String> proof=new CompletableFuture<>();
  try(BufferedWriter writer=Files.newBufferedWriter(file)){KneekuraDebugDurability.write(file,writer,row,proof);}
  if(!proof.get().equals(KneekuraDebugActionJournal.sha256(row))||!Files.readString(file).equals(row+"\n"))throw new AssertionError("hash/proof must name exact persisted row bytes");
  CompletableFuture<String> failure=new CompletableFuture<>();BufferedWriter closed=Files.newBufferedWriter(file);closed.close();
  try{KneekuraDebugDurability.write(file,closed,row,failure);throw new AssertionError("closed writer falsely accepted");}catch(IOException expected){}
  if(!failure.isCompletedExceptionally())throw new AssertionError("failed disk write must reject proof");
  System.out.println("Durable observation self-test: 3 checks passed");
 }
}
