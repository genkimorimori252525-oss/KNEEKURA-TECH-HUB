package dev.kneekura.fivedifficulties.forge;

import dev.kneekura.fivedifficulties.forge.entity.HomingAmuletProjectile;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.item.HomingAmuletItem;
import dev.kneekura.fivedifficulties.forge.item.SakuyaStopWatchItem;
import dev.kneekura.fivedifficulties.forge.item.SakuyaWatchItem;
import dev.kneekura.fivedifficulties.forge.item.THShotItem;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.Item;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class PortRegistries {
    private static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.ITEMS, FiveDifficultiesPort.MOD_ID);
    private static final DeferredRegister<EntityType<?>> ENTITIES =
            DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, FiveDifficultiesPort.MOD_ID);

    public static final RegistryObject<Item> HOMING_AMULET =
            ITEMS.register("homing_amulet", () -> new HomingAmuletItem(false, new Item.Properties()));

    public static final RegistryObject<Item> DIFFUSION_AMULET =
            ITEMS.register("diffusion_amulet", () -> new HomingAmuletItem(true, new Item.Properties()));

    public static final RegistryObject<Item> SAKUYA_WATCH =
            ITEMS.register("sakuya_watch", () -> new SakuyaWatchItem(new Item.Properties()));

    public static final RegistryObject<Item> SAKUYA_STOPWATCH =
            ITEMS.register("sakuya_stopwatch", () -> new SakuyaStopWatchItem(new Item.Properties()));

    public static final RegistryObject<EntityType<HomingAmuletProjectile>> HOMING_AMULET_PROJECTILE =
            ENTITIES.register(
                    "homing_amulet_projectile",
                    () -> EntityType.Builder.<HomingAmuletProjectile>of(HomingAmuletProjectile::new, MobCategory.MISC)
                            .sized(0.4F, 0.4F)
                            .clientTrackingRange(8)
                            .updateInterval(1)
                            .setShouldReceiveVelocityUpdates(true)
                            .build(FiveDifficultiesPort.MOD_ID + ":homing_amulet_projectile")
            );

    public static final RegistryObject<EntityType<SakuyaTimeControllerEntity>> SAKUYA_TIME_CONTROLLER =
            ENTITIES.register(
                    "sakuya_time_controller",
                    () -> EntityType.Builder.<SakuyaTimeControllerEntity>of(SakuyaTimeControllerEntity::new, MobCategory.MISC)
                            .sized(1.0F, 1.0F)
                            .clientTrackingRange(6)
                            .updateInterval(1)
                            .setShouldReceiveVelocityUpdates(true)
                            .build(FiveDifficultiesPort.MOD_ID + ":sakuya_time_controller")
            );

    public static final RegistryObject<EntityType<THShotEntity>> TH_SHOT =
            ENTITIES.register(
                    "th_shot",
                    () -> EntityType.Builder.<THShotEntity>of(THShotEntity::new, MobCategory.MISC)
                            .sized(0.1F, 0.1F)
                            .clientTrackingRange(8)
                            .updateInterval(1)
                            .setShouldReceiveVelocityUpdates(true)
                            .build(FiveDifficultiesPort.MOD_ID + ":th_shot")
            );

    // X1 ItemTHShot subtypes. Value = X1 damage value.
    public static final RegistryObject<Item> SMALL_SHOT = shotItem("small_shot", 0);
    public static final RegistryObject<Item> TINY_SHOT = shotItem("tiny_shot", 1);
    public static final RegistryObject<Item> MEDIUM_SHOT = shotItem("medium_shot", 2);
    public static final RegistryObject<Item> BIG_SHOT = shotItem("big_shot", 3);
    public static final RegistryObject<Item> CIRCLE_SHOT = shotItem("circle_shot", 6);
    public static final RegistryObject<Item> HEART_SHOT = shotItem("heart_shot", 11);
    // P9: the remaining X1 ItemTHShot subtypes.
    public static final RegistryObject<Item> STAR_SHOT = shotItem("star_shot", 4);
    public static final RegistryObject<Item> SMALL_STAR_SHOT = shotItem("small_star_shot", 5);
    public static final RegistryObject<Item> SCALE_SHOT = shotItem("scale_shot", 7);
    public static final RegistryObject<Item> BUTTERFLY_SHOT = shotItem("butterfly_shot", 8);
    public static final RegistryObject<Item> LIGHT_SHOT = shotItem("light_shot", 9);
    public static final RegistryObject<Item> KNIFE_SHOT = shotItem("knife_shot", 10);
    public static final RegistryObject<Item> KUNAI_SHOT = shotItem("kunai_shot", 12);
    public static final RegistryObject<Item> TALISMAN_SHOT = shotItem("talisman_shot", 13);
    public static final RegistryObject<Item> BIG_LIGHT_SHOT = shotItem("big_light_shot", 14);
    public static final RegistryObject<Item> RICE_SHOT = shotItem("rice_shot", 15);
    public static final RegistryObject<Item> OVAL_SHOT = shotItem("oval_shot", 16);
    public static final RegistryObject<Item> CRYSTAL_SHOT = shotItem("crystal_shot", 17);
    public static final RegistryObject<Item> ARROW_SHOT = shotItem("arrow_shot", 18);

    /** All 19 X1 ItemTHShot subtypes, in X1 damage-value order. */
    public static final java.util.List<RegistryObject<Item>> SHOT_ITEMS = java.util.List.of(
            SMALL_SHOT, TINY_SHOT, MEDIUM_SHOT, BIG_SHOT, STAR_SHOT, SMALL_STAR_SHOT, CIRCLE_SHOT, SCALE_SHOT,
            BUTTERFLY_SHOT, LIGHT_SHOT, KNIFE_SHOT, HEART_SHOT, KUNAI_SHOT, TALISMAN_SHOT, BIG_LIGHT_SHOT,
            RICE_SHOT, OVAL_SHOT, CRYSTAL_SHOT, ARROW_SHOT);

    private static RegistryObject<Item> shotItem(String name, int x1Type) {
        return ITEMS.register(name, () -> new THShotItem(x1Type, new Item.Properties()));
    }

    private PortRegistries() {}

    public static void register(IEventBus modBus) {
        ITEMS.register(modBus);
        ENTITIES.register(modBus);
    }
}
