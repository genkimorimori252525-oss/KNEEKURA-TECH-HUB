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
    public static final RegistryObject<Item> DANMAKU_CREEPER_SPAWN_EGG = ITEMS.register("danmaku_creeper_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(DANMAKU_CREEPER, 0x0FF080, 0xC0C000, new Item.Properties()));

    // ---- P16d entities ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.SpiritualStrikeTalismanEntity>> SPIRITUAL_STRIKE_TALISMAN_ENTITY =
            ENTITIES.register("spiritual_strike_talisman", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.SpiritualStrikeTalismanEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.SpiritualStrikeTalismanEntity::new, MobCategory.MISC)
                    .sized(0.2F, 0.2F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":spiritual_strike_talisman"));
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.MazinkyoukanEntity>> MAZINKYOUKAN_ENTITY =
            ENTITIES.register("mazinkyoukan", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.MazinkyoukanEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.MazinkyoukanEntity::new, MobCategory.MISC)
                    .sized(2.0F, 2.0F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":mazinkyoukan"));

    // ---- P16e entities ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.AjaRedStoneEffectEntity>> AJA_RED_STONE_EFFECT =
            ENTITIES.register("aja_red_stone_effect", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.AjaRedStoneEffectEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.AjaRedStoneEffectEntity::new, MobCategory.MISC)
                    .sized(2.0F, 0.0F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":aja_red_stone_effect"));

    // ---- P16f entities ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.PendulumEntity>> PENDULUM_ENTITY =
            ENTITIES.register("nazrin_pendulum", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.PendulumEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.PendulumEntity::new, MobCategory.MISC)
                    .sized(0.1F, 0.1F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":nazrin_pendulum"));

    // ---- P16g entities ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.CirnoIceBoxEntity>> CIRNO_ICE_BOX =
            ENTITIES.register("cirno_ice_box", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.CirnoIceBoxEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.CirnoIceBoxEntity::new, MobCategory.MISC)
                    .sized(1.8F, 1.8F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":cirno_ice_box"));
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.HakurouReflecterEntity>> HAKUROU_REFLECTER =
            ENTITIES.register("hakurou_reflecter", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.HakurouReflecterEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.HakurouReflecterEntity::new, MobCategory.MISC)
                    .sized(1.5F, 1.5F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":hakurou_reflecter"));

    // ---- P16j entities ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.SilverKnifeEntity>> SILVER_KNIFE_ENTITY =
            ENTITIES.register("silver_knife", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.SilverKnifeEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.SilverKnifeEntity::new, MobCategory.MISC)
                    .sized(0.1F, 0.1F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":silver_knife"));

    // ---- P16k entities ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.YuukaParasolEntity>> YUUKA_PARASOL_ENTITY =
            ENTITIES.register("yuuka_parasol", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.YuukaParasolEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.YuukaParasolEntity::new, MobCategory.MISC)
                    .sized(2.0F, 2.0F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":yuuka_parasol"));

    // ---- P16l entities ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.HisouEntity>> HISOU_ENTITY =
            ENTITIES.register("hisou", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.HisouEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.HisouEntity::new, MobCategory.MISC)
                    .sized(4.4F, 4.4F).clientTrackingRange(8).updateInterval(1).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":hisou"));

    // ---- P16n entities ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.KinkakuziEntity>> KINKAKUZI_ENTITY =
            ENTITIES.register("kinkakuzi", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.KinkakuziEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.KinkakuziEntity::new, MobCategory.MISC)
                    .sized(6.0F, 0.3F).clientTrackingRange(10).updateInterval(3).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":kinkakuzi"));

    // ---- P16o entities ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.MarisaBroomEntity>> MARISA_BROOM_ENTITY =
            ENTITIES.register("magic_broom", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.MarisaBroomEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.MarisaBroomEntity::new, MobCategory.MISC)
                    .sized(0.9F, 0.5F).clientTrackingRange(10).updateInterval(3).setShouldReceiveVelocityUpdates(true)
                    .build(FiveDifficultiesPort.MOD_ID + ":magic_broom"));

    // ---- P17a mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.THFairyEntity>> TH_FAIRY =
            ENTITIES.register("th_fairy", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.THFairyEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.THFairyEntity::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.5F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":th_fairy"));
    public static final RegistryObject<Item> TH_FAIRY_SPAWN_EGG = ITEMS.register("th_fairy_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(TH_FAIRY, 0xFFFF80, 0xC0C000, new Item.Properties()));
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.SunFlowerFairyEntity>> SUNFLOWER_FAIRY =
            ENTITIES.register("sunflower_fairy", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.SunFlowerFairyEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.SunFlowerFairyEntity::new, MobCategory.MONSTER)
                    .sized(0.9F, 1.7F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":sunflower_fairy"));
    public static final RegistryObject<Item> SUNFLOWER_FAIRY_SPAWN_EGG = ITEMS.register("sunflower_fairy_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(SUNFLOWER_FAIRY, 0xDDDD60, 0xA0A000, new Item.Properties()));
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.FamiliarEntity>> FAMILIAR =
            ENTITIES.register("familiar", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.FamiliarEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.FamiliarEntity::new, MobCategory.MISC)
                    .sized(0.6F, 0.6F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":familiar"));

    // ---- P17b mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.PhantomEntity>> TH_PHANTOM =
            ENTITIES.register("th_phantom", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.PhantomEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.PhantomEntity::new, MobCategory.MONSTER)
                    .sized(1.0F, 1.0F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":th_phantom"));
    public static final RegistryObject<Item> TH_PHANTOM_SPAWN_EGG = ITEMS.register("th_phantom_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(TH_PHANTOM, 0xFFFFF0, 0xFFFFFF, new Item.Properties()));

    // ---- P17c mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.RumiaEntity>> RUMIA =
            ENTITIES.register("rumia", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.RumiaEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.RumiaEntity::new, MobCategory.MONSTER)
                    .sized(1.0F, 1.8F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":rumia"));
    public static final RegistryObject<Item> RUMIA_SPAWN_EGG = ITEMS.register("rumia_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(RUMIA, 0x671503, 0xC0C010, new Item.Properties()));

    // ---- P17d mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.CirnoEntity>> CIRNO =
            ENTITIES.register("cirno", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.CirnoEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.CirnoEntity::new, MobCategory.MONSTER)
                    .sized(1.0F, 1.8F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":cirno"));
    public static final RegistryObject<Item> CIRNO_SPAWN_EGG = ITEMS.register("cirno_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(CIRNO, 0x00FFE0, 0x00E0E0, new Item.Properties()));

    // ---- P17e mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.WriggleEntity>> WRIGGLE =
            ENTITIES.register("wriggle", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.WriggleEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.WriggleEntity::new, MobCategory.MONSTER)
                    .sized(1.0F, 1.8F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":wriggle"));
    public static final RegistryObject<Item> WRIGGLE_SPAWN_EGG = ITEMS.register("wriggle_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(WRIGGLE, 0x15224F, 0x83C826, new Item.Properties()));

    // ---- P17f mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.TozikoEntity>> TOZIKO =
            ENTITIES.register("toziko", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.TozikoEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.TozikoEntity::new, MobCategory.MONSTER)
                    .sized(1.0F, 1.8F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":toziko"));
    public static final RegistryObject<Item> TOZIKO_SPAWN_EGG = ITEMS.register("toziko_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(TOZIKO, 0x60D683, 0x376E91, new Item.Properties()));

    // ---- P17g mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.SakuyaEntity>> SAKUYA =
            ENTITIES.register("sakuya", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.SakuyaEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.SakuyaEntity::new, MobCategory.AMBIENT)
                    .sized(1.0F, 1.8F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":sakuya"));
    public static final RegistryObject<Item> SAKUYA_SPAWN_EGG = ITEMS.register("sakuya_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(SAKUYA, 0xC1C1D6, 0x3053E7, new Item.Properties()));
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.SanaeEntity>> SANAE =
            ENTITIES.register("sanae", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.SanaeEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.SanaeEntity::new, MobCategory.AMBIENT)
                    .sized(0.6F, 1.7F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":sanae"));
    public static final RegistryObject<Item> SANAE_SPAWN_EGG = ITEMS.register("sanae_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(SANAE, 0x6BD245, 0x2937E0, new Item.Properties()));

    // ---- P17h mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.ReimuEntity>> REIMU =
            ENTITIES.register("reimu", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.ReimuEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.ReimuEntity::new, MobCategory.MONSTER)
                    .sized(1.0F, 1.8F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":reimu"));
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.MikoEntity>> MIKO =
            ENTITIES.register("miko", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.MikoEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.MikoEntity::new, MobCategory.MONSTER)
                    .sized(1.0F, 1.8F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":miko"));

    // ---- P17i mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.RinnosukeEntity>> RINNOSUKE =
            ENTITIES.register("rinnosuke", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.RinnosukeEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.RinnosukeEntity::new, MobCategory.AMBIENT)
                    .sized(0.6F, 1.8F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":rinnosuke"));
    public static final RegistryObject<Item> RINNOSUKE_SPAWN_EGG = ITEMS.register("rinnosuke_spawn_egg",
            () -> new net.minecraftforge.common.ForgeSpawnEggItem(RINNOSUKE, 0x373737, 0x2D2DE0, new Item.Properties()));

    // ---- P17j mobs ----
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.mob.CursedDecoyDollEntity>> CURSED_DECOY_DOLL =
            ENTITIES.register("cursed_decoy_doll", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.mob.CursedDecoyDollEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.mob.CursedDecoyDollEntity::new, MobCategory.MISC)
                    .sized(1.0F, 1.8F).clientTrackingRange(10)
                    .build(FiveDifficultiesPort.MOD_ID + ":cursed_decoy_doll"));

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

    // ---- P15 danmaku crafting table ----
    private static final DeferredRegister<net.minecraft.world.level.block.Block> BLOCKS =
            DeferredRegister.create(ForgeRegistries.BLOCKS, FiveDifficultiesPort.MOD_ID);
    private static final DeferredRegister<net.minecraft.world.inventory.MenuType<?>> MENUS =
            DeferredRegister.create(ForgeRegistries.MENU_TYPES, FiveDifficultiesPort.MOD_ID);

    /** X1 danmaku_crafting_table metadata 0 / 1. */
    public static final RegistryObject<net.minecraft.world.level.block.Block> DANMAKU_CRAFTING_TABLE =
            BLOCKS.register("danmaku_crafting_table", () -> new dev.kneekura.fivedifficulties.forge.crafting.DanmakuCraftingTableBlock(false));
    public static final RegistryObject<net.minecraft.world.level.block.Block> LASER_CRAFTING_TABLE =
            BLOCKS.register("laser_crafting_table", () -> new dev.kneekura.fivedifficulties.forge.crafting.DanmakuCraftingTableBlock(true));
    public static final RegistryObject<Item> DANMAKU_CRAFTING_TABLE_ITEM = ITEMS.register("danmaku_crafting_table",
            () -> new net.minecraft.world.item.BlockItem(DANMAKU_CRAFTING_TABLE.get(), new Item.Properties()));
    public static final RegistryObject<Item> LASER_CRAFTING_TABLE_ITEM = ITEMS.register("laser_crafting_table",
            () -> new net.minecraft.world.item.BlockItem(LASER_CRAFTING_TABLE.get(), new Item.Properties()));

    public static final RegistryObject<net.minecraft.world.inventory.MenuType<dev.kneekura.fivedifficulties.forge.crafting.DanmakuCraftingMenu>> DANMAKU_CRAFTING_MENU =
            MENUS.register("danmaku_crafting", () -> net.minecraftforge.common.extensions.IForgeMenuType.create(
                    (id, inv, buf) -> dev.kneekura.fivedifficulties.forge.crafting.DanmakuCraftingMenu.shot(id, inv)));
    public static final RegistryObject<net.minecraft.world.inventory.MenuType<dev.kneekura.fivedifficulties.forge.crafting.DanmakuCraftingMenu>> LASER_CRAFTING_MENU =
            MENUS.register("laser_crafting", () -> net.minecraftforge.common.extensions.IForgeMenuType.create(
                    (id, inv, buf) -> dev.kneekura.fivedifficulties.forge.crafting.DanmakuCraftingMenu.laser(id, inv)));

    // ---- P16a small items ----
    public static final RegistryObject<Item> HEAVENLY_PEACH = ITEMS.register("heavenly_peach",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1SmallItems.HeavenlyPeach(new Item.Properties()));
    public static final RegistryObject<Item> SWALLOW_COWRIE_SHELL = ITEMS.register("swallow_cowrie_shell",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1SmallItems.SwallowCowrieShell(new Item.Properties()));
    public static final RegistryObject<Item> CLOSED_THIRD_EYE = ITEMS.register("closed_third_eye",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1SmallItems.ClosedThirdEye(new Item.Properties()));
    public static final RegistryObject<Item> TENGU_FAN = ITEMS.register("tengu_fan",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1SmallItems.TenguFan(new Item.Properties()));
    public static final RegistryObject<Item> ONBASHIRA = ITEMS.register("onbashira",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1SmallItems.Onbashira(new Item.Properties()));
    public static final RegistryObject<Item> HOURAI_PEARL_RED = ITEMS.register("hourai_pearl_red",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> HOURAI_PEARL_BLUE = ITEMS.register("hourai_pearl_blue",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> HOURAI_PEARL_GREEN = ITEMS.register("hourai_pearl_green",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> HOURAI_PEARL_YELLOW = ITEMS.register("hourai_pearl_yellow",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> HOURAI_PEARL_PURPLE = ITEMS.register("hourai_pearl_purple",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> HOURAI_PEARL_AQUA = ITEMS.register("hourai_pearl_aqua",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> HOURAI_PEARL_ORANGE = ITEMS.register("hourai_pearl_orange",
            () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> HOURAI_PEARL_WHITE = ITEMS.register("hourai_pearl_white",
            () -> new Item(new Item.Properties()));

    // ---- P16b weapons ----
    public static final RegistryObject<Item> SPEAR_THE_GUNGNIR = ITEMS.register("spear_the_gungnir",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1Weapons.SpearTheGungnir(new Item.Properties()));
    public static final RegistryObject<Item> LAEVATEINN = ITEMS.register("laevateinn",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1Weapons.Laevateinn(new Item.Properties()));
    public static final RegistryObject<Item> ROUKANKEN = ITEMS.register("roukanken",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1Weapons.Roukanken(new Item.Properties()));
    public static final RegistryObject<Item> ROUKANKEN_SENPUUZIN = ITEMS.register("roukanken_senpuuzin",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1Weapons.RoukanSenpuuzin(new Item.Properties()));
    public static final RegistryObject<Item> DEATH_SCYTHE = ITEMS.register("death_scythe",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1Weapons.DeathScythe(new Item.Properties()));
    public static final RegistryObject<Item> REMORSE_ROD = ITEMS.register("remorse_rod",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1Weapons.Kaigo(new Item.Properties()));

    // ---- P16c shot items ----
    public static final RegistryObject<Item> SOUL_TORCH = ITEMS.register("soul_torch",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ShotItems.SoulTorch(new Item.Properties()));
    public static final RegistryObject<Item> YUYUKO_FAN = ITEMS.register("yuyuko_fan",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ShotItems.YuyukoFan(new Item.Properties()));
    public static final RegistryObject<Item> KAPPA_WATER_PISTOL = ITEMS.register("kappa_water_pistol",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ShotItems.KappaWaterPistol(new Item.Properties()));
    public static final RegistryObject<Item> IBUKI_GOURD = ITEMS.register("ibuki_gourd",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ShotItems.IbukiGourd(new Item.Properties()));

    // ---- P16d effect items ----
    public static final RegistryObject<Item> SPIRITUAL_STRIKE_TALISMAN = ITEMS.register("spiritual_strike_talisman",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1EffectItems.SpiritualStrikeTalisman(new Item.Properties()));
    public static final RegistryObject<Item> SORCERER_SUTRA_SCROLL = ITEMS.register("sorcerer_sutra_scroll",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1EffectItems.MazinKyoukan(new Item.Properties()));

    // ---- P16e aja red stone ----
    public static final RegistryObject<Item> AJA_RED_STONE = ITEMS.register("aja_red_stone",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1EffectItems.AjaRedStone(new Item.Properties()));

    // ---- P16f pendulum ----
    public static final RegistryObject<Item> NAZRIN_PENDULUM = ITEMS.register("nazrin_pendulum",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1EffectItems.Pendulum(new Item.Properties()));

    // ---- P16g swords ----
    public static final RegistryObject<Item> ICICLE_SWORD = ITEMS.register("icicle_sword",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1Weapons.IcicleSword(new Item.Properties()));
    public static final RegistryObject<Item> HAKUROUKEN = ITEMS.register("hakurouken",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1Weapons.Hakurouken(new Item.Properties()));

    // ---- P16h tools ----
    public static final RegistryObject<Item> BUDDHA_STONE_BOWL = ITEMS.register("buddha_stone_bowl",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ToolItems.BuddhaStoneBowl(new Item.Properties()));
    public static final RegistryObject<Item> BYOUKIHEIYU_MAMORI = ITEMS.register("byoukiheiyu_mamori",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ToolItems.ByoukiheiyuMamori(new Item.Properties()));
    public static final RegistryObject<Item> WALL_PASSING_CHISEL = ITEMS.register("wall_passing_chisel",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ToolItems.Kabenuke(new Item.Properties()));
    public static final RegistryObject<Item> SHIP_GHOST_DIPPER = ITEMS.register("ship_ghost_dipper",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ToolItems.Hisyaku(new Item.Properties(), false));
    public static final RegistryObject<Item> SHIP_GHOST_DIPPER_EMPTY = ITEMS.register("ship_ghost_dipper_empty",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ToolItems.Hisyaku(new Item.Properties(), true));

    // ---- P16i armour ----
    public static final RegistryObject<Item> FIRE_RAT_ROBE = ITEMS.register("fire_rat_robe",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ArmorItems.FireRatRobe(new Item.Properties()));
    public static final RegistryObject<Item> MARISA_HAT = ITEMS.register("marisa_hat",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ArmorItems.MarisaHat(new Item.Properties()));
    public static final RegistryObject<Item> KAPPA_CAP = ITEMS.register("kappa_cap",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ArmorItems.KappaCap(new Item.Properties()));
    public static final RegistryObject<Item> SUWAKO_HAT = ITEMS.register("suwako_hat",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ArmorItems.Kerobou(new Item.Properties()));

    // ---- P16j silver knives ----
    public static final RegistryObject<Item> SILVER_KNIFE_BLUE = ITEMS.register("silver_knife_blue",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ShotItems.SilverKnife(new Item.Properties(), 0));
    public static final RegistryObject<Item> SILVER_KNIFE_RED = ITEMS.register("silver_knife_red",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ShotItems.SilverKnife(new Item.Properties(), 1));
    public static final RegistryObject<Item> SILVER_KNIFE_GREEN = ITEMS.register("silver_knife_green",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ShotItems.SilverKnife(new Item.Properties(), 2));
    public static final RegistryObject<Item> SILVER_KNIFE_WHITE = ITEMS.register("silver_knife_white",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ShotItems.SilverKnife(new Item.Properties(), 3));

    // ---- P16k parasol ----
    public static final RegistryObject<Item> YUUKA_PARASOL = ITEMS.register("yuuka_parasol",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ShotItems.YuukaParasol(new Item.Properties()));

    // ---- P16l hisou sword ----
    public static final RegistryObject<Item> HISOU_SWORD = ITEMS.register("scarlet_perception_sword",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1Weapons.HisouSword(new Item.Properties()));

    // ---- P16m eye orb branch ----
    public static final RegistryObject<Item> THIRD_EYE = ITEMS.register("third_eye",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ToolItems.ThirdEye(new Item.Properties()));
    public static final RegistryObject<Item> BLOODTHIRSTY_YIN_YANG_ORB = ITEMS.register("bloodthirsty_yin_yang_orb",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ToolItems.BloodthirstyOnmyoudama(new Item.Properties()));
    public static final RegistryObject<Item> HOURAI_JEWELED_BRANCH = ITEMS.register("hourai_jeweled_branch",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1ToolItems.HouraiJeweledBranch(new Item.Properties()));

    // ---- P16n kinkakuzi ----
    public static final RegistryObject<Item> KINKAKUZI = ITEMS.register("kinkakuzi",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1EffectItems.Kinkakuzi(new Item.Properties()));

    // ---- P16o broom ----
    public static final RegistryObject<Item> MARISA_BROOM = ITEMS.register("magic_broom",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1EffectItems.MarisaBroom(new Item.Properties()));

    // ---- P17j mallet and doll ----
    public static final RegistryObject<Item> MIRACLE_MALLET = ITEMS.register("miracle_mallet",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1MalletItems.MiracleMallet(new Item.Properties()));
    public static final RegistryObject<Item> CURSED_DECOY_DOLL_ITEM = ITEMS.register("cursed_decoy_doll",
            () -> new dev.kneekura.fivedifficulties.forge.item.X1MalletItems.CursedDecoyDoll(new Item.Properties()));

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


    // ---- P18a Divine Spirit (X1 divine_spirit metadata 0..7, one block per colour) ----
    private static final DeferredRegister<net.minecraft.world.level.block.entity.BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(ForgeRegistries.BLOCK_ENTITY_TYPES, FiveDifficultiesPort.MOD_ID);
    public static final RegistryObject<net.minecraft.world.level.block.Block> DIVINE_SPIRIT_RED =
            BLOCKS.register("divine_spirit_red", () -> new dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock(0));
    public static final RegistryObject<Item> DIVINE_SPIRIT_RED_ITEM = ITEMS.register("divine_spirit_red",
            () -> new net.minecraft.world.item.BlockItem(DIVINE_SPIRIT_RED.get(), new Item.Properties()));
    public static final RegistryObject<net.minecraft.world.level.block.Block> DIVINE_SPIRIT_BLUE =
            BLOCKS.register("divine_spirit_blue", () -> new dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock(1));
    public static final RegistryObject<Item> DIVINE_SPIRIT_BLUE_ITEM = ITEMS.register("divine_spirit_blue",
            () -> new net.minecraft.world.item.BlockItem(DIVINE_SPIRIT_BLUE.get(), new Item.Properties()));
    public static final RegistryObject<net.minecraft.world.level.block.Block> DIVINE_SPIRIT_GREEN =
            BLOCKS.register("divine_spirit_green", () -> new dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock(2));
    public static final RegistryObject<Item> DIVINE_SPIRIT_GREEN_ITEM = ITEMS.register("divine_spirit_green",
            () -> new net.minecraft.world.item.BlockItem(DIVINE_SPIRIT_GREEN.get(), new Item.Properties()));
    public static final RegistryObject<net.minecraft.world.level.block.Block> DIVINE_SPIRIT_YELLOW =
            BLOCKS.register("divine_spirit_yellow", () -> new dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock(3));
    public static final RegistryObject<Item> DIVINE_SPIRIT_YELLOW_ITEM = ITEMS.register("divine_spirit_yellow",
            () -> new net.minecraft.world.item.BlockItem(DIVINE_SPIRIT_YELLOW.get(), new Item.Properties()));
    public static final RegistryObject<net.minecraft.world.level.block.Block> DIVINE_SPIRIT_PURPLE =
            BLOCKS.register("divine_spirit_purple", () -> new dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock(4));
    public static final RegistryObject<Item> DIVINE_SPIRIT_PURPLE_ITEM = ITEMS.register("divine_spirit_purple",
            () -> new net.minecraft.world.item.BlockItem(DIVINE_SPIRIT_PURPLE.get(), new Item.Properties()));
    public static final RegistryObject<net.minecraft.world.level.block.Block> DIVINE_SPIRIT_AQUA =
            BLOCKS.register("divine_spirit_aqua", () -> new dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock(5));
    public static final RegistryObject<Item> DIVINE_SPIRIT_AQUA_ITEM = ITEMS.register("divine_spirit_aqua",
            () -> new net.minecraft.world.item.BlockItem(DIVINE_SPIRIT_AQUA.get(), new Item.Properties()));
    public static final RegistryObject<net.minecraft.world.level.block.Block> DIVINE_SPIRIT_ORANGE =
            BLOCKS.register("divine_spirit_orange", () -> new dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock(6));
    public static final RegistryObject<Item> DIVINE_SPIRIT_ORANGE_ITEM = ITEMS.register("divine_spirit_orange",
            () -> new net.minecraft.world.item.BlockItem(DIVINE_SPIRIT_ORANGE.get(), new Item.Properties()));
    public static final RegistryObject<net.minecraft.world.level.block.Block> DIVINE_SPIRIT_WHITE =
            BLOCKS.register("divine_spirit_white", () -> new dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock(7));
    public static final RegistryObject<Item> DIVINE_SPIRIT_WHITE_ITEM = ITEMS.register("divine_spirit_white",
            () -> new net.minecraft.world.item.BlockItem(DIVINE_SPIRIT_WHITE.get(), new Item.Properties()));
    /** By X1 metadata (colour index). */
    public static final java.util.List<RegistryObject<Item>> DIVINE_SPIRIT_ITEMS = java.util.List.of(
            DIVINE_SPIRIT_RED_ITEM,
            DIVINE_SPIRIT_BLUE_ITEM,
            DIVINE_SPIRIT_GREEN_ITEM,
            DIVINE_SPIRIT_YELLOW_ITEM,
            DIVINE_SPIRIT_PURPLE_ITEM,
            DIVINE_SPIRIT_AQUA_ITEM,
            DIVINE_SPIRIT_ORANGE_ITEM,
            DIVINE_SPIRIT_WHITE_ITEM);
    public static final RegistryObject<net.minecraft.world.level.block.entity.BlockEntityType<dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock.DivineSpiritBlockEntity>> DIVINE_SPIRIT_BLOCK_ENTITY =
            BLOCK_ENTITIES.register("divine_spirit", () -> net.minecraft.world.level.block.entity.BlockEntityType.Builder.of(
                    dev.kneekura.fivedifficulties.forge.block.DivineSpiritBlock.DivineSpiritBlockEntity::new,
                    DIVINE_SPIRIT_RED.get(),
                    DIVINE_SPIRIT_BLUE.get(),
                    DIVINE_SPIRIT_GREEN.get(),
                    DIVINE_SPIRIT_YELLOW.get(),
                    DIVINE_SPIRIT_PURPLE.get(),
                    DIVINE_SPIRIT_AQUA.get(),
                    DIVINE_SPIRIT_ORANGE.get(),
                    DIVINE_SPIRIT_WHITE.get()).build(null));
    public static final RegistryObject<EntityType<dev.kneekura.fivedifficulties.forge.entity.DivineSpiritEntity>> DIVINE_SPIRIT =
            ENTITIES.register("divine_spirit", () -> EntityType.Builder.<dev.kneekura.fivedifficulties.forge.entity.DivineSpiritEntity>of(
                            dev.kneekura.fivedifficulties.forge.entity.DivineSpiritEntity::new, MobCategory.MISC)
                    .sized(1.2F, 1.2F).clientTrackingRange(10).updateInterval(1)
                    .build(FiveDifficultiesPort.MOD_ID + ":divine_spirit"));
    public static final RegistryObject<Item> TOYOSATOMIMI_SWORD = ITEMS.register("toyosatomimi_sword",
            () -> new dev.kneekura.fivedifficulties.forge.item.MikoSwordItem(new Item.Properties()));

    private static RegistryObject<Item> shotItem(String name, int x1Type) {
        return ITEMS.register(name, () -> new THShotItem(x1Type, new Item.Properties()));
    }

    private PortRegistries() {}

    public static void register(IEventBus modBus) {
        BLOCKS.register(modBus);
        BLOCK_ENTITIES.register(modBus);
        MENUS.register(modBus);
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
