package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.SynchedEntityData;

/** Cached server-thread store read; custom containers/items/accessors never execute callbacks. */
final class KneekuraDebugSynchedCached {
    private KneekuraDebugSynchedCached(){ }
    static Object read(Object data,Object accessor)throws ReflectiveOperationException {
        if(data==null||data.getClass()!=SynchedEntityData.class||accessor==null||accessor.getClass()!=EntityDataAccessor.class)
            throw new IllegalStateException("CUSTOM_SYNCHED_DATA_UNSUPPORTED");
        int id=(Integer)KneekuraDebugDecisionSnapshot.read(EntityDataAccessor.class,"id",accessor);
        Object values=KneekuraDebugDecisionSnapshot.read(SynchedEntityData.class,"itemsById",data);
        if(values==null||values.getClass()!=Int2ObjectOpenHashMap.class)throw new IllegalStateException("CUSTOM_SYNCHED_MAP_UNSUPPORTED");
        Object item=((Int2ObjectOpenHashMap<?>)values).get(id);
        if(item==null||item.getClass()!=SynchedEntityData.DataItem.class)throw new IllegalStateException("SYNCHED_ITEM_NOT_EXPOSED");
        if(KneekuraDebugDecisionSnapshot.read(SynchedEntityData.DataItem.class,"accessor",item)!=accessor)
            throw new IllegalStateException("SYNCHED_ACCESSOR_IDENTITY_CHANGED");
        return KneekuraDebugDecisionSnapshot.read(SynchedEntityData.DataItem.class,"value",item);
    }
}
