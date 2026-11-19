package org.kneekura.sporeobserver;

import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.loading.FMLEnvironment;
import net.minecraftforge.fml.common.Mod;

/** Research-only observer: opt-in on disposable dedicated Forge servers. */
@Mod(SporeObserverMod.MODID)
public final class SporeObserverMod {
    public static final String MODID = "kneekura_spore_observer";

    public SporeObserverMod() {
        if (FMLEnvironment.dist == Dist.DEDICATED_SERVER &&
                Boolean.parseBoolean(System.getProperty("kneekura.spore.observe.enabled", "false"))) {
            MinecraftForge.EVENT_BUS.register(new SporeEvents());
        }
    }
}
