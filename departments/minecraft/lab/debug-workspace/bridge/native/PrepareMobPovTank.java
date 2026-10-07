package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import net.minecraft.nbt.*;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.storage.RegionFile;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import java.util.UUID;

/** Offline fixture only on a newly created private original-save copy. No runtime action channel. */
public final class PrepareMobPovTank {
 public static final UUID SUBJECT=UUID.fromString("11111111-2222-2222-3333-333344444444");
 private static ListTag vector(double... values){ListTag a=new ListTag();for(double n:values)a.add(DoubleTag.valueOf(n));return a;}
 private static ListTag rotation(float yaw,float pitch){ListTag a=new ListTag();a.add(FloatTag.valueOf(yaw));a.add(FloatTag.valueOf(pitch));return a;}
 public static void main(String[] args)throws Exception{
  net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
  Path root=Path.of(args[0]).toRealPath(),allowed=Path.of(args[1]).toRealPath();
  if(!root.startsWith(allowed)||root.equals(allowed)||Files.exists(root.resolve("fixture.json")))throw new IllegalStateException("NEW_PRIVATE_COPY_REQUIRED");
  Path world=root.resolve("game/saves/KNEEKURA_DEBUG_WORLD").toRealPath();if(!world.startsWith(root))throw new IllegalStateException("PRIVATE_WORLD_REQUIRED");
  try(FileChannel channel=FileChannel.open(world.resolve("session.lock"),StandardOpenOption.WRITE);var lock=channel.tryLock()){
   if(lock==null)throw new IllegalStateException("WORLD_RUNNING");
   CompoundTag level=NbtIo.readCompressed(world.resolve("level.dat").toFile()),data=level.getCompound("Data"),player=data.getCompound("Player");
   data.putBoolean("confirmedExperimentalSettings",true);player.put("Pos",vector(.6,232.2,.6));player.put("Motion",vector(0,0,0));player.put("Rotation",rotation(-45,35));player.putInt("playerGameType",3);
   CompoundTag abilities=player.getCompound("abilities");abilities.putBoolean("flying",true);abilities.putBoolean("mayfly",true);abilities.putBoolean("invulnerable",true);
   NbtIo.writeCompressed(level,world.resolve("level.dat").toFile());Path playerFile=world.resolve("playerdata/"+player.getUUID("UUID")+".dat");if(Files.exists(playerFile))NbtIo.writeCompressed(player,playerFile.toFile());
   Path entities=world.resolve("entities");boolean found=false;
   try(RegionFile region=new RegionFile(entities.resolve("r.0.0.mca"),entities,true)){
    ChunkPos pos=new ChunkPos(0,0);CompoundTag chunk;try(var input=region.getChunkDataInputStream(pos)){if(input==null)throw new IllegalStateException("SAVED_SUBJECT_CHUNK_MISSING");chunk=NbtIo.read(input);}
    for(Tag tag:chunk.getList("Entities",Tag.TAG_COMPOUND)){CompoundTag entity=(CompoundTag)tag;
     if(entity.hasUUID("UUID")&&entity.getUUID("UUID").equals(SUBJECT)){
      if(!entity.getString("id").equals("touhou_little_maid:reimu"))throw new IllegalStateException("SUBJECT_TYPE_MISMATCH");
      entity.put("Pos",vector(9.5,224,9.5));entity.put("Motion",vector(0,0,0));entity.put("Rotation",rotation(0,0));entity.putBoolean("NoAI",true);entity.putBoolean("NoGravity",true);entity.putFloat("Health",20);found=true;
     }
    }
    if(!found)throw new IllegalStateException("EXACT_SAVED_REIMU_MISSING");try(var output=region.getChunkDataOutputStream(pos)){NbtIo.write(chunk,output);}region.flush();
   }
   JsonObject scope=new JsonObject();scope.addProperty("scope",KneekuraDebugArenaController.SCOPE);scope.addProperty("dimension","minecraft:overworld");JsonArray blocks=new JsonArray();
   for(int x=7;x<12;x++)for(int y=224;y<227;y++)for(int z=7;z<12;z++){JsonArray cell=new JsonArray();cell.add(x);cell.add(y);cell.add(z);cell.add("minecraft:air");blocks.add(cell);}scope.add("blocks",blocks);
   JsonObject poses=new JsonObject(),pose=new JsonObject();pose.addProperty("x",9.5d);pose.addProperty("y",224d);pose.addProperty("z",9.5d);pose.addProperty("yaw",0f);pose.addProperty("pitch",0f);for(String key:new String[]{"vx","vy","vz"})pose.addProperty(key,0d);poses.add(SUBJECT.toString(),pose);scope.add("subjectPoses",poses);
   JsonObject fixture=new JsonObject();fixture.add("scope",scope);fixture.addProperty("baselineHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(scope)));fixture.addProperty("subjectUuid",SUBJECT.toString());
   fixture.addProperty("certainty","PREDICTED_TYPED_SCOPE_REQUIRES_NATIVE_OWNER_MATCH");fixture.addProperty("changes","PRIVATE_ONLY: spectator observer; saved Reimu pose/health/NoAI/NoGravity fixture. Tank geometry unchanged.");
   Files.writeString(root.resolve("fixture.json"),fixture+"\n",StandardOpenOption.CREATE_NEW);
  }
 }
}
