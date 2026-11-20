package dev.kneekura.fivedifficulties.forge.client;

import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(
        modid = FiveDifficultiesPort.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.MOD,
        value = Dist.CLIENT
)
public final class PortClientEvents {
    private PortClientEvents() {}

    @SubscribeEvent
    public static void clientSetup(net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent event) {
        event.enqueueWork(() -> {
            net.minecraft.client.gui.screens.MenuScreens.register(PortRegistries.DANMAKU_CRAFTING_MENU.get(), DanmakuCraftingScreen::new);
            net.minecraft.client.gui.screens.MenuScreens.register(PortRegistries.LASER_CRAFTING_MENU.get(), DanmakuCraftingScreen::new);
            net.minecraft.client.renderer.item.ItemProperties.register(PortRegistries.REMORSE_ROD.get(),
                    new net.minecraft.resources.ResourceLocation(dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort.MOD_ID, "used"),
                    (stack, level, entity, seed) -> dev.kneekura.fivedifficulties.forge.item.X1Weapons.Kaigo.used(stack) ? 1F : 0F);
            net.minecraft.client.renderer.item.ItemProperties.register(PortRegistries.HOURAI_JEWELED_BRANCH.get(),
                    new net.minecraft.resources.ResourceLocation(dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort.MOD_ID, "charge_step"),
                    (stack, level, entity, seed) -> dev.kneekura.fivedifficulties.forge.item.X1ToolItems.HouraiJeweledBranch.iconStep(stack) / 10F);
        });
    }

    @SubscribeEvent
    public static void registerEntityRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(
                PortRegistries.HOMING_AMULET_PROJECTILE.get(),
                HomingAmuletRenderer::new
        );
        event.registerEntityRenderer(
                PortRegistries.SAKUYA_TIME_CONTROLLER.get(),
                SakuyaTimeControllerRenderer::new
        );
        event.registerEntityRenderer(PortRegistries.TH_SHOT.get(), THShotRenderer::new);
        event.registerEntityRenderer(PortRegistries.TH_LASER.get(), THLaserRenderer::new);
        event.registerEntityRenderer(PortRegistries.TH_SET_LASER.get(), THLaserRenderer::new);
        event.registerEntityRenderer(PortRegistries.SPELL_CARD.get(), SpellCardRenderers.Card::new);
        event.registerEntityRenderer(PortRegistries.SPELL_CARD_CIRCLE.get(), SpellCardRenderers.Circle::new);
        event.registerEntityRenderer(PortRegistries.SHOT_MATERIAL_ENTITY.get(), SpellCardRenderers.ShotMaterial::new);
        event.registerEntityRenderer(PortRegistries.TH_ITEM.get(), THItemRenderer::new);
        event.registerEntityRenderer(PortRegistries.MUSOU_FUUIN.get(), P12Renderers.MusouFuuin::new);
        event.registerEntityRenderer(PortRegistries.DRAGON_NECK_JEWEL.get(), DragonNeckJewelRenderer::new);
        event.registerEntityRenderer(PortRegistries.CURSED_DECOY_DOLL.get(), ctx -> new P17Renderers.Plain<>(ctx, new dev.kneekura.fivedifficulties.forge.client.mob.CursedDecoyDollModel(ctx.bakeLayer(P17Renderers.mobLayer("cursed_decoy_doll"))), "cursed_decoy_doll"));
        event.registerEntityRenderer(PortRegistries.RINNOSUKE.get(), ctx -> new P17Renderers.Plain<>(ctx, new dev.kneekura.fivedifficulties.forge.client.mob.RinnosukeModel(ctx.bakeLayer(P17Renderers.mobLayer("rinnosuke"))), "rinnosuke"));
        event.registerEntityRenderer(PortRegistries.REIMU.get(), ctx -> new P17Renderers.SimpleBoss<>(ctx, new dev.kneekura.fivedifficulties.forge.client.mob.ReimuModel(ctx.bakeLayer(P17Renderers.mobLayer("reimu"))), "reimu"));
        event.registerEntityRenderer(PortRegistries.MIKO.get(), ctx -> new P17Renderers.SimpleBoss<>(ctx, new dev.kneekura.fivedifficulties.forge.client.mob.MikoModel(ctx.bakeLayer(P17Renderers.mobLayer("miko"))), "miko"));
        event.registerEntityRenderer(PortRegistries.SAKUYA.get(), ctx -> new P17Renderers.SimpleBoss<>(ctx, new dev.kneekura.fivedifficulties.forge.client.mob.SakuyaModel(ctx.bakeLayer(P17Renderers.mobLayer("sakuya"))), "sakuya"));
        event.registerEntityRenderer(PortRegistries.SANAE.get(), ctx -> new P17Renderers.SimpleBoss<>(ctx, new dev.kneekura.fivedifficulties.forge.client.mob.SanaeModel(ctx.bakeLayer(P17Renderers.mobLayer("sanae"))), "sanae"));
        event.registerEntityRenderer(PortRegistries.TOZIKO.get(), ctx -> new P17Renderers.SimpleBoss<>(ctx, new dev.kneekura.fivedifficulties.forge.client.mob.TozikoModel(ctx.bakeLayer(P17Renderers.mobLayer("toziko"))), "toziko"));
        event.registerEntityRenderer(PortRegistries.WRIGGLE.get(), ctx -> new P17Renderers.SimpleBoss<>(ctx, new dev.kneekura.fivedifficulties.forge.client.mob.WriggleModel(ctx.bakeLayer(P17Renderers.mobLayer("wriggle"))), "wriggle").bright());
        event.registerEntityRenderer(PortRegistries.CIRNO.get(), ctx -> new P17Renderers.SimpleBoss<>(ctx, new dev.kneekura.fivedifficulties.forge.client.mob.CirnoModel(ctx.bakeLayer(P17Renderers.mobLayer("cirno"))), "cirno"));
        event.registerEntityRenderer(PortRegistries.RUMIA.get(), P17Renderers.Rumia::new);
        event.registerEntityRenderer(PortRegistries.TH_PHANTOM.get(), P17Renderers.Phantom::new);
        event.registerEntityRenderer(PortRegistries.TH_FAIRY.get(), P17Renderers.THFairy::new);
        event.registerEntityRenderer(PortRegistries.SUNFLOWER_FAIRY.get(), P17Renderers.SunFlowerFairy::new);
        event.registerEntityRenderer(PortRegistries.FAMILIAR.get(), P17Renderers.Familiar::new);
        event.registerEntityRenderer(PortRegistries.MARISA_BROOM_ENTITY.get(), P16Renderers.MarisaBroom::new);
        event.registerEntityRenderer(PortRegistries.KINKAKUZI_ENTITY.get(), P16Renderers.Kinkakuzi::new);
        event.registerEntityRenderer(PortRegistries.HISOU_ENTITY.get(), P16Renderers.Hisou::new);
        event.registerEntityRenderer(PortRegistries.YUUKA_PARASOL_ENTITY.get(), P16Renderers.YuukaParasol::new);
        event.registerEntityRenderer(PortRegistries.SILVER_KNIFE_ENTITY.get(), P16Renderers.SilverKnife::new);
        event.registerEntityRenderer(PortRegistries.CIRNO_ICE_BOX.get(), P16Renderers.CirnoIceBox::new);
        event.registerEntityRenderer(PortRegistries.HAKUROU_REFLECTER.get(), P16Renderers.HakurouReflecter::new);
        event.registerEntityRenderer(PortRegistries.PENDULUM_ENTITY.get(), P16Renderers.Pendulum::new);
        event.registerEntityRenderer(PortRegistries.AJA_RED_STONE_EFFECT.get(), P16Renderers.AjaRedStoneEffect::new);
        event.registerEntityRenderer(PortRegistries.SPIRITUAL_STRIKE_TALISMAN_ENTITY.get(), P16Renderers.SpiritualStrikeTalisman::new);
        event.registerEntityRenderer(PortRegistries.MAZINKYOUKAN_ENTITY.get(), P16Renderers.Mazinkyoukan::new);
        event.registerEntityRenderer(PortRegistries.ONMYOUDAMA.get(), OnmyoudamaRenderer::new);
        event.registerEntityRenderer(PortRegistries.MIRACLE_CIRCLE.get(), WindGoheiRenderers.MiracleCircle::new);
        event.registerEntityRenderer(PortRegistries.SANAE_WIND.get(), WindGoheiRenderers.SanaeWind::new);
        event.registerEntityRenderer(PortRegistries.MINI_HAKKERO.get(), P12Renderers.MiniHakkero::new);
        event.registerEntityRenderer(PortRegistries.SUKIMA.get(), P12Renderers.Sukima::new);
        event.registerEntityRenderer(PortRegistries.NUCLEAR_SHOT.get(), P12Renderers.NuclearShot::new);
        event.registerEntityRenderer(PortRegistries.DANMAKU_CREEPER.get(),
                net.minecraft.client.renderer.entity.CreeperRenderer::new); // X1 RenderCreeper
    }

    @SubscribeEvent
    public static void registerItemColors(net.minecraftforge.client.event.RegisterColorHandlersEvent.Item event) {
        event.register((stack, layer) -> dev.kneekura.fivedifficulties.forge.item.GapFoldingUmbrellaItem.tint(stack, layer),
                PortRegistries.GAP_FOLDING_UMBRELLA.get());
        for (var item : PortRegistries.SHOT_ITEMS) {
            event.register((stack, tintIndex) -> dev.kneekura.fivedifficulties.forge.item.THShotItem.tint(stack, tintIndex),
                    item.get());
        }
    }

    @SubscribeEvent
    public static void registerLayerDefinitions(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(
                SakuyaTimeControllerModel.LAYER_LOCATION,
                SakuyaTimeControllerModel::createBodyLayer
        );
        event.registerLayerDefinition(SilverKnifeModel.LAYER_LOCATION, SilverKnifeModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.mobLayer("cursed_decoy_doll"), dev.kneekura.fivedifficulties.forge.client.mob.CursedDecoyDollModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.mobLayer("rinnosuke"), dev.kneekura.fivedifficulties.forge.client.mob.RinnosukeModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.mobLayer("reimu"), dev.kneekura.fivedifficulties.forge.client.mob.ReimuModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.mobLayer("miko"), dev.kneekura.fivedifficulties.forge.client.mob.MikoModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.mobLayer("sakuya"), dev.kneekura.fivedifficulties.forge.client.mob.SakuyaModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.mobLayer("sanae"), dev.kneekura.fivedifficulties.forge.client.mob.SanaeModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.mobLayer("toziko"), dev.kneekura.fivedifficulties.forge.client.mob.TozikoModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.mobLayer("wriggle"), dev.kneekura.fivedifficulties.forge.client.mob.WriggleModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.mobLayer("cirno"), dev.kneekura.fivedifficulties.forge.client.mob.CirnoModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.RUMIA_LAYER, dev.kneekura.fivedifficulties.forge.client.mob.RumiaModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.FAIRY_LAYER, dev.kneekura.fivedifficulties.forge.client.mob.THFairyModel::createBodyLayer);
        event.registerLayerDefinition(P17Renderers.SUNFLOWER_FAIRY_LAYER, dev.kneekura.fivedifficulties.forge.client.mob.SunFlowerFairyModel::createBodyLayer);
        event.registerLayerDefinition(X1HatModels.MARISA_HAT, X1HatModels::createMarisaHat);
        event.registerLayerDefinition(X1HatModels.SUWAKO_HAT, X1HatModels::createSuwakoHat);
        event.registerLayerDefinition(P16Renderers.PARASOL_LAYER, P16Renderers::createParasolLayer);
        event.registerLayerDefinition(P16Renderers.HISOU_LAYER, P16Renderers::createHisouLayer);
        event.registerLayerDefinition(P16Renderers.KINKAKUZI_LAYER, P16Renderers::createKinkakuziLayer);
        event.registerLayerDefinition(P12Renderers.HAKKERO_LAYER, P12Renderers::createHakkeroLayer);
        event.registerLayerDefinition(P12Renderers.HAKKERO2_LAYER, P12Renderers::createHakkero2Layer);
    }
}
