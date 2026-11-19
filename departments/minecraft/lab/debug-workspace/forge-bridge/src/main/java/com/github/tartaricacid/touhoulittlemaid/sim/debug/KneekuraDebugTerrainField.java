package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.pathfinder.BlockPathTypes;
import java.util.EnumMap;
import java.util.Map;
import java.util.function.LongSupplier;

/** Bounded observer query data. No Mob, navigation, effective-malus getter or search is called. */
public final class KneekuraDebugTerrainField {
    @FunctionalInterface public interface GroundSource { BlockPathTypes classify(BlockPos pos)throws Exception; }
    private KneekuraDebugTerrainField(){ }
    public static JsonObject capture(BlockPos center,int radius,int maxCells,long maxNanos,
            LongSupplier clock,GroundSource source,Map<?,?> ownOverrides) {
        if(center==null||radius<0||radius>3||maxCells<1||maxCells>49||maxNanos<1||maxNanos>50000000L
                ||clock==null||source==null)throw new IllegalArgumentException("INVALID_TERRAIN_QUERY_LIMITS");
        long started=clock.getAsLong();
        JsonObject data=new JsonObject();JsonArray cells=new JsonArray();data.add("cells",cells);
        data.addProperty("radius",radius);data.addProperty("requestedCellCount",(2*radius+1)*(2*radius+1));
        data.addProperty("classificationScope","STATIC_GROUND_NOT_SELECTED_EVALUATOR_ADMISSION");
        data.addProperty("effectiveMalusStatus","NOT_EXPOSED");
        data.addProperty("observerDeadlineScope","CHECKED_BETWEEN_CELLS_CANNOT_PREEMPT_ONE_CLASSIFIER_CALL");
        boolean truncated=false;
        outer:for(int dx=-radius;dx<=radius;dx++)for(int dz=-radius;dz<=radius;dz++) {
            long elapsed=clock.getAsLong()-started;
            if(cells.size()>=maxCells||elapsed<0||elapsed>=maxNanos){truncated=true;break outer;}
            JsonObject cell=new JsonObject();
            int x=Math.addExact(center.getX(),dx),z=Math.addExact(center.getZ(),dz);
            cell.addProperty("x",x);cell.addProperty("y",center.getY());cell.addProperty("z",z);
            cell.addProperty("observationRole","OBSERVER_QUERIED_GROUND_ONLY");
            cell.addProperty("effectiveMalusStatus","NOT_EXPOSED");
            cell.addProperty("evaluatedByPathfinderStatus","NOT_CAPTURED");
            try {
                BlockPathTypes type=source.classify(new BlockPos(x,center.getY(),z));
                if(type==null)throw new IllegalStateException("CLASSIFICATION_UNAVAILABLE");
                cell.addProperty("pathType",type.name());
                float defaultMalus=(Float)KneekuraDebugDecisionSnapshot.read(BlockPathTypes.class,"malus",type);
                if(Float.isFinite(defaultMalus))cell.addProperty("defaultTypeMalus",defaultMalus);
                else cell.addProperty("defaultTypeMalusStatus","NOT_EXPOSED");
                if(ownOverrides!=null&&ownOverrides.getClass()==EnumMap.class) {
                    Object own=ownOverrides.get(type);
                    if(own instanceof Float value&&Float.isFinite(value)) {
                        cell.addProperty("selectedMobOverride",value);cell.addProperty("selectedMobOverrideStatus","AVAILABLE");
                    }else cell.addProperty("selectedMobOverrideStatus",own==null?"NOT_PRESENT":"NOT_EXPOSED");
                }else cell.addProperty("selectedMobOverrideStatus","NOT_EXPOSED");
                cell.addProperty("status","AVAILABLE");
            }catch(Exception error) {
                for(String key:new String[]{"pathType","defaultTypeMalus","defaultTypeMalusStatus","selectedMobOverride","selectedMobOverrideStatus"})cell.remove(key);
                cell.addProperty("status","NOT_EXPOSED");cell.addProperty("detail",error.getClass().getSimpleName());
            }
            cells.add(cell);
        }
        data.addProperty("truncated",truncated);
        data.addProperty("status",truncated||cells.asList().stream().anyMatch(c->!c.getAsJsonObject().get("status").getAsString().equals("AVAILABLE"))?"PARTIAL":"AVAILABLE");
        return data;
    }
}
