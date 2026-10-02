package org.kneekura.staff;

import net.minecraft.world.item.Item;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

@Mod(StaffMod.MOD_ID)
public final class StaffMod {
    public static final String MOD_ID = "kneekura";
    private static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, MOD_ID);
    public static final RegistryObject<Item> STAFF = ITEMS.register("celestial_staff", CelestialStaffItem::new);
    public StaffMod() { ITEMS.register(FMLJavaModLoadingContext.get().getModEventBus()); }
}
