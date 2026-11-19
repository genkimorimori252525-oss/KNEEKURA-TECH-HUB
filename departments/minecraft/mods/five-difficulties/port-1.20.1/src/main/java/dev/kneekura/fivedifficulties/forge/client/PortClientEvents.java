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
        event.registerEntityRenderer(PortRegistries.MUSOU_FUUIN.get(), P12Renderers.MusouFuuin::new);
        event.registerEntityRenderer(PortRegistries.DRAGON_NECK_JEWEL.get(), DragonNeckJewelRenderer::new);
        event.registerEntityRenderer(PortRegistries.ONMYOUDAMA.get(), OnmyoudamaRenderer::new);
        event.registerEntityRenderer(PortRegistries.MINI_HAKKERO.get(), P12Renderers.MiniHakkero::new);
        event.registerEntityRenderer(PortRegistries.SUKIMA.get(), P12Renderers.Sukima::new);
        event.registerEntityRenderer(PortRegistries.NUCLEAR_SHOT.get(), P12Renderers.NuclearShot::new);
        event.registerEntityRenderer(PortRegistries.DANMAKU_CREEPER.get(),
                net.minecraft.client.renderer.entity.CreeperRenderer::new); // X1 RenderCreeper
    }

    @SubscribeEvent
    public static void registerItemColors(net.minecraftforge.client.event.RegisterColorHandlersEvent.Item event) {
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
        event.registerLayerDefinition(P12Renderers.HAKKERO_LAYER, P12Renderers::createHakkeroLayer);
        event.registerLayerDefinition(P12Renderers.HAKKERO2_LAYER, P12Renderers::createHakkero2Layer);
    }
}
