package dev.kneekura.fivedifficulties.forge;

import dev.kneekura.fivedifficulties.forge.entity.HomingAmuletProjectile;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THSetLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.item.THLaserItem;
import dev.kneekura.fivedifficulties.forge.item.HomingAmuletItem;
import dev.kneekura.fivedifficulties.forge.item.SakuyaStopWatchItem;
import dev.kneekura.fivedifficulties.forge.item.SakuyaWatchItem;
import dev.kneekura.fivedifficulties.forge.item.THShotItem;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
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

    public static final RegistryObject<EntityType<THLaserEntity>> TH_LASER =
            ENTITIES.register("th_laser", () -> EntityType.Builder.<THLaserEntity>of(THLaserEntity::new, MobCategory.MISC)
                    .sized(0.1F, 0.1F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":th_laser"));

    public static final RegistryObject<EntityType<THSetLaserEntity>> TH_SET_LASER =
            ENTITIES.register("th_set_laser", () -> EntityType.Builder.<THSetLaserEntity>of(THSetLaserEntity::new, MobCategory.MISC)
                    .sized(0.1F, 0.1F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":th_set_laser"));

    // X1 ItemTHLaser subtypes (damage 0 middle, 1 short, 2 long).
    public static final RegistryObject<Item> LASER = ITEMS.register("laser", () -> new THLaserItem(0, new Item.Properties()));
    public static final RegistryObject<Item> SHORT_LASER = ITEMS.register("short_laser", () -> new THLaserItem(1, new Item.Properties()));
    public static final RegistryObject<Item> LONG_LASER = ITEMS.register("long_laser", () -> new THLaserItem(2, new Item.Properties()));
    public static final java.util.List<RegistryObject<Item>> LASER_ITEMS = java.util.List.of(LASER, SHORT_LASER, LONG_LASER);

    // ---- P11 spell cards ----
    private static final DeferredRegister<SoundEvent> SOUNDS =
            DeferredRegister.create(ForgeRegistries.SOUND_EVENTS, FiveDifficultiesPort.MOD_ID);
    private static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, FiveDifficultiesPort.MOD_ID);

    /** X1 sounds.json events (the X1 bundle ships no audio for them). */
    public static final RegistryObject<SoundEvent> SOUND_SPELLCARD = sound("spellcard");
    public static final RegistryObject<SoundEvent> SOUND_MASTERSPARK = sound("masterspark");
    public static final RegistryObject<SoundEvent> SOUND_SUKIMA = sound("sukima");
    public static final RegistryObject<SoundEvent> SOUND_DOWN = sound("down");

    private static RegistryObject<SoundEvent> sound(String name) {
        return SOUNDS.register(name, () -> SoundEvent.createVariableRangeEvent(
                new ResourceLocation(FiveDifficultiesPort.MOD_ID, name)));
    }

    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity>> SPELL_CARD =
            ENTITIES.register("spell_card", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity::new, MobCategory.MISC)
                    .sized(0.4F, 0.4F).clientTrackingRange(8).updateInterval(1)
                    .build(FiveDifficultiesPort.MOD_ID + ":spell_card"));

    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.SpellCardCircleEntity>> SPELL_CARD_CIRCLE =
            ENTITIES.register("spell_card_circle", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.SpellCardCircleEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.SpellCardCircleEntity::new, MobCategory.MISC)
                    .sized(0.5F, 0.5F).clientTrackingRange(8).updateInterval(1)
                    .build(FiveDifficultiesPort.MOD_ID + ":spell_card_circle"));

    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.ShotMaterialEntity>> SHOT_MATERIAL_ENTITY =
            ENTITIES.register("shot_material", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.ShotMaterialEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.ShotMaterialEntity::new, MobCategory.MISC)
                    .sized(1.2F, 1.2F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":shot_material"));

    // ---- P12 spell-card entities (X1 registerModEntity names in comments) ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.MusouFuuinEntity>> MUSOU_FUUIN =
            ENTITIES.register("musou_fuuin", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.MusouFuuinEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.MusouFuuinEntity::new, MobCategory.MISC)
                    .sized(0.1F, 0.1F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":musou_fuuin"));

    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.MiniHakkeroEntity>> MINI_HAKKERO =
            ENTITIES.register("mini_hakkero", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.MiniHakkeroEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.MiniHakkeroEntity::new, MobCategory.MISC)
                    .sized(0.4F, 0.4F).clientTrackingRange(8).updateInterval(5)
                    .build(FiveDifficultiesPort.MOD_ID + ":mini_hakkero"));

    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.SukimaEntity>> SUKIMA =
            ENTITIES.register("sukima", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.SukimaEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.SukimaEntity::new, MobCategory.MISC)
                    .sized(0.6F, 1.8F).clientTrackingRange(8).updateInterval(5)
                    .build(FiveDifficultiesPort.MOD_ID + ":sukima"));

    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity>> NUCLEAR_SHOT =
            ENTITIES.register("nuclear_shot", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity::new, MobCategory.MISC)
                    .sized(0.1F, 0.1F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":nuclear_shot"));

    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.DanmakuCreeperEntity>> DANMAKU_CREEPER =
            ENTITIES.register("danmaku_creeper", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.DanmakuCreeperEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.DanmakuCreeperEntity::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.7F).clientTrackingRange(8).updateInterval(1)
                    .build(FiveDifficultiesPort.MOD_ID + ":danmaku_creeper"));

    // ---- P13 danmaku-weapon items ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.DragonNeckJewelEntity>> DRAGON_NECK_JEWEL =
            ENTITIES.register("dragon_neck_jewel", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.DragonNeckJewelEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.DragonNeckJewelEntity::new, MobCategory.MISC)
                    .sized(1.0F, 1.0F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":dragon_neck_jewel")); // X1 "BrilliantDragonBullet"

    public static final RegistryObject<Item> MINI_HAKKERO_ITEM = ITEMS.register("mini_hakkero",
            () -> new dev.kneekura.fivedifficulties.forge.item.MiniHakkeroItem(new Item.Properties()));
    public static final RegistryObject<Item> NUCLEAR_CONTROL_ROD = ITEMS.register("nuclear_control_rod",
            () -> new dev.kneekura.fivedifficulties.forge.item.NuclearControlRodItem(new Item.Properties()));
    public static final RegistryObject<Item> DRAGON_NECK_JEWEL_ITEM = ITEMS.register("dragon_neck_jewel",
            () -> new dev.kneekura.fivedifficulties.forge.item.DragonNeckJewelItem(new Item.Properties()));

    // ---- P13b ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.OnmyoudamaEntity>> ONMYOUDAMA =
            ENTITIES.register("onmyoudama", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.OnmyoudamaEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.OnmyoudamaEntity::new, MobCategory.MISC)
                    .sized(0.3F, 0.3F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":onmyoudama")); // X1 "Onmyoudama"

    public static final RegistryObject<Item> HAKUREI_MIKO_STICK = ITEMS.register("hakurei_miko_stick",
            () -> new dev.kneekura.fivedifficulties.forge.item.OharaibouRItem(new Item.Properties()));

    // ---- P13c ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.MiracleCircleEntity>> MIRACLE_CIRCLE =
            ENTITIES.register("miracle_circle", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.MiracleCircleEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.MiracleCircleEntity::new, MobCategory.MISC)
                    .sized(2.0F, 0.01F).clientTrackingRange(8).updateInterval(1)
                    .build(FiveDifficultiesPort.MOD_ID + ":miracle_circle")); // X1 "MiracleCircle"

    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.SanaeWindEntity>> SANAE_WIND =
            ENTITIES.register("sanae_wind", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.SanaeWindEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.SanaeWindEntity::new, MobCategory.MISC)
                    .sized(1.0F, 1.0F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":sanae_wind")); // X1 "SanaeWind"

    public static final RegistryObject<Item> WIND_MIKO_STICK = ITEMS.register("wind_miko_stick",
            () -> new dev.kneekura.fivedifficulties.forge.item.OharaibouSItem(new Item.Properties()));

    // ---- P13d ----
    public static final RegistryObject<Item> GAP = ITEMS.register("gap",
            () -> new dev.kneekura.fivedifficulties.forge.item.GapItem(new Item.Properties()));
    public static final RegistryObject<Item> GAP_FOLDING_UMBRELLA = ITEMS.register("gap_folding_umbrella",
            () -> new dev.kneekura.fivedifficulties.forge.item.GapFoldingUmbrellaItem(new Item.Properties()));

    // ---- P14 bonus items ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.THItemEntity>> TH_ITEM =
            ENTITIES.register("th_item", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.THItemEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.THItemEntity::new, MobCategory.MISC)
                    .sized(1.2F, 1.2F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":th_item")); // X1 "THItem"

    /** X1 power_item damage 0 / 1 (THKaguyaItems.power_up_item_small / big). */
    public static final RegistryObject<Item> POWER_ITEM_SMALL = ITEMS.register("power_item_small",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> POWER_ITEM_BIG = ITEMS.register("power_item_big",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> POINT_ITEM = ITEMS.register("point_item",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> BOMB_ITEM = ITEMS.register("bomb_item",
            () -> new Item(new Item.Properties().stacksTo(64)));
    public static final RegistryObject<Item> EXTEND_ITEM = ITEMS.register("extend_item",
            () -> new Item(new Item.Properties().stacksTo(8)));

    public static final RegistryObject<Item> SHOT_MATERIAL = ITEMS.register("shot_material",
            () -> new dev.kneekura.fivedifficulties.forge.item.ShotMaterialItem(new Item.Properties()));

    /** One item per registered X1 spell card (X1: one item, damage value = spell card ID). */
    public static final java.util.Map<Integer, RegistryObject<Item>> SPELL_CARD_ITEMS = new java.util.LinkedHashMap<>();

    static {
        dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCards.registerAll();
        for (var entry : dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardRegistry.sorted()) {
            SPELL_CARD_ITEMS.put(entry.id(), ITEMS.register("spell_card_" + entry.key(),
                    () -> new dev.kneekura.fivedifficulties.forge.spellcard.SpellCardItem(entry.id(), new Item.Properties())));
        }
    }

    /** X1 THKaguyaCore.tabSpellCard */
    public static final RegistryObject<CreativeModeTab> SPELL_CARD_TAB = TABS.register("spell_cards",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.thKaguyaSpellCard"))
                    .icon(() -> new ItemStack(SPELL_CARD_ITEMS.values().iterator().next().get()))
                    .displayItems((params, out) -> SPELL_CARD_ITEMS.values().forEach(i -> out.accept(i.get())))
                    .build());

    private static RegistryObject<Item> shotItem(String name, int x1Type) {
        return ITEMS.register(name, () -> new THShotItem(x1Type, new Item.Properties()));
    }

    private PortRegistries() {}

    public static void register(IEventBus modBus) {
        ITEMS.register(modBus);
        ENTITIES.register(modBus);
        dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardDeclaration.bombItem = () -> BOMB_ITEM.get();
        dev.kneekura.fivedifficulties.forge.entity.OnmyoudamaEntity.mikoStick = () -> HAKUREI_MIKO_STICK.get();
        dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity.controlRod = () -> NUCLEAR_CONTROL_ROD.get();
        modBus.addListener((net.minecraftforge.event.entity.EntityAttributeCreationEvent event) ->
                event.put(DANMAKU_CREEPER.get(), net.minecraft.world.entity.monster.Creeper.createAttributes().build()));
        SOUNDS.register(modBus);
        TABS.register(modBus);
    }
}
