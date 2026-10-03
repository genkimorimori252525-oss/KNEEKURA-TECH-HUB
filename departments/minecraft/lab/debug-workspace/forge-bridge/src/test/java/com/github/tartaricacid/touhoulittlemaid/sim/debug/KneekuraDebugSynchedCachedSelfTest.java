package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.SynchedEntityData;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;

public final class KneekuraDebugSynchedCachedSelfTest {
    public static void main(String[] args)throws Exception {
        // Serializer/bootstrap is outside this cached-read contract and is never called by the reader.
        var data=new SynchedEntityData(null);var accessor=new EntityDataAccessor<Byte>(0,null);
        Object before=KneekuraDebugDecisionSnapshot.read(SynchedEntityData.class,"itemsById",data);
        var items=(Int2ObjectMap<SynchedEntityData.DataItem<?>>)before;
        items.put(0,new SynchedEntityData.DataItem<Byte>(accessor,(byte)2));
        boolean dirty=data.isDirty();
        if(!Byte.valueOf((byte)2).equals(KneekuraDebugSynchedCached.read(data,accessor)))throw new AssertionError("cached genuine value");
        if(before!=KneekuraDebugDecisionSnapshot.read(SynchedEntityData.class,"itemsById",data)||dirty!=data.isDirty())throw new AssertionError("cached store mutated");
        try{KneekuraDebugSynchedCached.read(data,new EntityDataAccessor<Byte>(1,null));throw new AssertionError("missing accessor accepted");}
        catch(IllegalStateException expected){ }
        class CustomItem extends SynchedEntityData.DataItem<Byte> {
            int reads;
            CustomItem(){super(accessor,(byte)3);}
            @Override public Byte getValue(){reads++;return (byte)3;}
        }
        var custom=new CustomItem();items.put(0,custom);
        try{KneekuraDebugSynchedCached.read(data,accessor);throw new AssertionError("custom value getter accepted");}
        catch(IllegalStateException expected){ }
        if(custom.reads!=0)throw new AssertionError("custom callback replayed");
        System.out.println("Genuine Synched Data: cached value, no mutation, missing/custom item rejected without getter replay");
    }
}
