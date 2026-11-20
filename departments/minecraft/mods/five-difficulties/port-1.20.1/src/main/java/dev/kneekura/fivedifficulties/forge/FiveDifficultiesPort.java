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
        net.minecraftforge.fml.ModLoadingContext.get().registerConfig(
                net.minecraftforge.fml.config.ModConfig.Type.COMMON, X1Config.SPEC, "five_difficulties_port-common.toml");
        PortRegistries.register(modBus);
        net.minecraftforge.common.crafting.CraftingHelper.register(dev.kneekura.fivedifficulties.forge.crafting.RecipelessItemsCondition.SERIALIZER);
        PortNetwork.register();
        modBus.addListener((net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent e) ->
                e.enqueueWork(dev.kneekura.fivedifficulties.forge.item.X1ShotItems::registerDispenser));
        LOGGER.info("Five Difficulties X1 Preservation Port P2 bootstrap loaded");
    }
}
