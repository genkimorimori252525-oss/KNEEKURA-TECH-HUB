package dev.kneekura.fivedifficulties.forge;

import net.minecraft.world.item.Item;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;

/**
 * Registry boundary for the preservation port.
 *
 * P0 intentionally registers no player-facing X1 content until the exact archive/assets are repinned.
 */
public final class PortRegistries {
    private static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.ITEMS, FiveDifficultiesPort.MOD_ID);

    private PortRegistries() {}

    public static void register(IEventBus modBus) {
        ITEMS.register(modBus);
    }
}
