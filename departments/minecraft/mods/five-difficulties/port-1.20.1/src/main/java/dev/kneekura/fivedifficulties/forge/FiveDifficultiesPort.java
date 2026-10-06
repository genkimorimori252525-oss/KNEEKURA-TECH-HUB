package dev.kneekura.fivedifficulties.forge;

import com.mojang.logging.LogUtils;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

@Mod(FiveDifficultiesPort.MOD_ID)
public final class FiveDifficultiesPort {
    public static final String MOD_ID = "five_difficulties_port";
    public static final Logger LOGGER = LogUtils.getLogger();

    public FiveDifficultiesPort() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        PortRegistries.register(modBus);
        PortNetwork.register();
        LOGGER.info("Five Difficulties X1 Preservation Port P0 bootstrap loaded");
    }
}
