package kneekura.manual;

import com.google.gson.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** Pure bounded presentation contract; never opens NBT or grants world/control access. */
public final class ManualPresentation {
 private ManualPresentation(){}
 private static void require(boolean value,String why){if(!value)throw new IllegalArgumentException("MANUAL_GRID_"+why);}
 private static int integer(JsonElement e){require(e!=null&&e.isJsonPrimitive()&&e.getAsJsonPrimitive().isNumber(),"INTEGER");double d=e.getAsDouble();require(Double.isFinite(d)&&d==Math.rint(d)&&d>=Integer.MIN_VALUE&&d<=Integer.MAX_VALUE,"INTEGER");return (int)d;}
 public static void validate(JsonObject p){
  require(p.keySet().equals(Set.of("renderer","grid","brightness","recipeHash","min","max")),"FIELDS");
  require(p.get("grid").isJsonPrimitive()&&p.getAsJsonPrimitive("grid").isBoolean()&&p.get("grid").getAsBoolean(),"EXPLICIT_GRID");
  require(p.get("renderer").isJsonPrimitive()&&p.getAsJsonPrimitive("renderer").isString()&&p.get("renderer").getAsString().equals("tank-grid-v1"),"RENDERER");
  require(p.get("brightness").isJsonPrimitive()&&p.getAsJsonPrimitive("brightness").isString()&&p.get("brightness").getAsString().equals("NATIVE"),"NO_BRIGHTNESS_AUTHORITY");
  require(p.get("recipeHash").isJsonPrimitive()&&p.getAsJsonPrimitive("recipeHash").isString()&&p.get("recipeHash").getAsString().matches("[a-f0-9]{64}"),"RECIPE_HASH");
  var min=p.getAsJsonArray("min");var max=p.getAsJsonArray("max");require(min.size()==3&&max.size()==3,"BOUNDS");long volume=1;
  for(int i=0;i<3;i++){int lo=integer(min.get(i)),hi=integer(max.get(i));long size=(long)hi-lo;require(size>0&&size<=64,"SIZE");volume*=size;require(i==1?lo>=-63&&hi<=319:lo>=-29999983&&hi<=29999984,"WORLD_BOUNDS");}require(volume<=65536,"VOLUME");
 }
 private static String canonical(JsonElement e){
  if(e.isJsonObject()){var a=new ArrayList<String>();for(String key:new TreeSet<>(e.getAsJsonObject().keySet()))a.add(new JsonPrimitive(key)+":"+canonical(e.getAsJsonObject().get(key)));return "{"+String.join(",",a)+"}";}
  if(e.isJsonArray()){var a=new ArrayList<String>();for(var v:e.getAsJsonArray())a.add(canonical(v));return "["+String.join(",",a)+"]";}
  if(e.isJsonPrimitive()&&e.getAsJsonPrimitive().isNumber()){var n=e.getAsBigDecimal();return n.signum()==0?"0":n.stripTrailingZeros().toPlainString();}return e.toString();
 }
 public static void matchesSaved(JsonObject p,JsonObject saved)throws Exception{
  validate(p);require(saved.get("status").getAsString().equals("GEOMETRY_VERIFIED"),"SAVED_STATUS");var recipe=saved.getAsJsonObject("recipe");
  require(integer(recipe.get("v"))==1&&recipe.get("kind").getAsString().equals("tank_recipe")&&recipe.get("dimension").getAsString().equals("minecraft:overworld"),"SAVED_RECIPE");
  String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical(recipe).getBytes(StandardCharsets.UTF_8)));
  require(saved.get("recipeHash").getAsString().replaceFirst("^sha256:","").equals(hash)&&p.get("recipeHash").getAsString().equals(hash),"SAVED_HASH");
  var origin=recipe.getAsJsonObject("origin");var sizes=recipe.getAsJsonObject("dimensions");var min=p.getAsJsonArray("min");var max=p.getAsJsonArray("max");String[] xyz={"x","y","z"},whd={"width","height","depth"};
  for(int i=0;i<3;i++){int lo=integer(origin.get(xyz[i])),size=integer(sizes.get(whd[i]));require(integer(min.get(i))==lo&&(long)integer(max.get(i))==((long)lo+size),"SAVED_GEOMETRY");}
 }
 public static void verifyWorld(JsonObject p,Path world)throws Exception{Path file=world.resolve("kneekura-tank-owner.json");require(!Files.isSymbolicLink(file)&&Files.isRegularFile(file)&&Files.size(file)<=65536&&file.toRealPath().startsWith(world.toRealPath()),"SAVED_FILE");matchesSaved(p,JsonParser.parseString(Files.readString(file)).getAsJsonObject());}
}
