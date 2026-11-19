package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.platform.NativeImage;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Real Forge-client smoke used only when FIVE_DIFFICULTIES_P7_CLIENT_SMOKE=1.
 *
 * It verifies private canonical resources/model baking, opens a screen that
 * renders the same live visual primitives, writes a screenshot, records only
 * SHA/dimensions/size, deletes the PNG, then stops the client.
 */
@Mod.EventBusSubscriber(
        modid = FiveDifficultiesPort.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.FORGE,
        value = Dist.CLIENT
)
public final class ClientRuntimeSmoke {
    public static final String PASS_MARKER = "FIVE_DIFFICULTIES_P7_CLIENT_SMOKE_PASS";

    private record TextureReceipt(String sha256, int width, int height) {}

    private static final Map<ResourceLocation, TextureReceipt> TEXTURES = new LinkedHashMap<>();

    static {
        TEXTURES.put(id("textures/entity/homing_amulet.png"),
                new TextureReceipt("badfeba690c2dee69ddb38c9f3a0fe538643ca1d439121e95959fd7dfb93b4d9", 64, 32));
        TEXTURES.put(id("textures/item/homing_amulet.png"),
                new TextureReceipt("650f71239534ef521bea3e1e29893ed1cb8302721854c44d0536b76be02f5773", 32, 32));
        TEXTURES.put(id("textures/item/sakuya_watch.png"),
                new TextureReceipt("589e080353f2f1d56ec6af6547bc3cfbb3802de89e7797c03a2251083e8d0c8e", 16, 16));
        TEXTURES.put(id("textures/entity/sakuya_watch.png"),
                new TextureReceipt("b55d8af1138f2b7f5e3841afe7d5aecff78d57122f57ecb7a29af1036f76ff30", 64, 32));
        TEXTURES.put(id("textures/item/sakuya_stopwatch.png"),
                new TextureReceipt("ac6144bc483951782cbcf94cdc3339f07fbc1f49507a323264ee27a5f922e285", 16, 16));
        TEXTURES.put(id("textures/entity/sakuya_stopwatch.png"),
                new TextureReceipt("9c6b567304210c30b67d14dc925d058dc3eb5c961aae8918aee84bb7239955bd", 64, 32));
        TEXTURES.put(id("textures/entity/sakuya_time_dark.png"),
                new TextureReceipt("c0b1a2f92f0b3f366cdfcecf212de161eb853fd987d2790bd7d943b4dcde0d05", 64, 32));
    }

    private static int bootTicks;
    private static int screenshotWaitTicks;
    private static boolean validated;
    private static boolean screenshotRequested;
    private static boolean completed;

    private ClientRuntimeSmoke() {}

    private static boolean enabled() {
        return "1".equals(System.getenv("FIVE_DIFFICULTIES_P7_CLIENT_SMOKE"));
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (!enabled() || completed || event.phase != TickEvent.Phase.END) return;

        Minecraft minecraft = Minecraft.getInstance();

        try {
            if (!validated) {
                if (minecraft.getOverlay() != null || minecraft.screen == null) return;
                if (++bootTicks < 20) return;

                validateCanonicalClientResources(minecraft);
                minecraft.setScreen(new P7VisualSmokeScreen());
                validated = true;
                return;
            }

            if (!(minecraft.screen instanceof P7VisualSmokeScreen visual)) return;
            if (visual.renderFrames() < 6) return;

            Path screenshot = minecraft.gameDirectory.toPath()
                    .resolve("screenshots")
                    .resolve("p7_visual_smoke.png");

            if (!screenshotRequested) {
                Files.deleteIfExists(screenshot);
                Screenshot.grab(
                        minecraft.gameDirectory,
                        "p7_visual_smoke.png",
                        minecraft.getMainRenderTarget(),
                        message -> FiveDifficultiesPort.LOGGER.info("P7 screenshot callback: {}", message.getString())
                );
                screenshotRequested = true;
                screenshotWaitTicks = 0;
                return;
            }

            screenshotWaitTicks++;
            if (!Files.isRegularFile(screenshot) || Files.size(screenshot) < 1024L) {
                require(screenshotWaitTicks <= 100, "screenshot was not materialized");
                return;
            }

            byte[] png = Files.readAllBytes(screenshot);
            int width;
            int height;
            try (NativeImage image = NativeImage.read(new ByteArrayInputStream(png))) {
                width = image.getWidth();
                height = image.getHeight();
            }

            String screenshotSha = sha256(png);
            FiveDifficultiesPort.LOGGER.info(
                    "{} textures={} screenshot={}x{} bytes={} sha256={}",
                    PASS_MARKER,
                    TEXTURES.size(),
                    width,
                    height,
                    png.length,
                    screenshotSha
            );

            // Local private review may keep the PNG (it contains private X1 art, so CI never sets this).
            if (!"1".equals(System.getenv("FIVE_DIFFICULTIES_KEEP_SCREENSHOT"))) {
                Files.deleteIfExists(screenshot);
            }
            completed = true;
            minecraft.stop();
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P7_CLIENT_SMOKE_FAIL", failure);
            completed = true;
            minecraft.stop();
            throw failure instanceof RuntimeException runtime
                    ? runtime
                    : new IllegalStateException("P7 client smoke failed", failure);
        }
    }

    private static void validateCanonicalClientResources(Minecraft minecraft) throws Exception {
        for (Map.Entry<ResourceLocation, TextureReceipt> entry : TEXTURES.entrySet()) {
            ResourceLocation id = entry.getKey();
            TextureReceipt receipt = entry.getValue();
            Resource resource = minecraft.getResourceManager()
                    .getResource(id)
                    .orElseThrow(() -> new IllegalStateException("Missing canonical X1 client resource: " + id));

            byte[] bytes;
            try (InputStream stream = resource.open()) {
                bytes = stream.readAllBytes();
            }

            require(receipt.sha256().equals(sha256(bytes)), "SHA mismatch: " + id);
            try (NativeImage image = NativeImage.read(new ByteArrayInputStream(bytes))) {
                require(image.getWidth() == receipt.width() && image.getHeight() == receipt.height(),
                        "PNG dimensions: " + id + " expected=" + receipt.width() + "x" + receipt.height()
                                + " actual=" + image.getWidth() + "x" + image.getHeight());
            }
        }

        requireItemModel(minecraft, PortRegistries.HOMING_AMULET.get(), "Homing Amulet");
        requireItemModel(minecraft, PortRegistries.SAKUYA_WATCH.get(), "Sakuya Watch");
        requireItemModel(minecraft, PortRegistries.SAKUYA_STOPWATCH.get(), "StopWatch");
        for (var shotItem : PortRegistries.SHOT_ITEMS) {
            requireItemModel(minecraft, shotItem.get(), shotItem.getId().toString());
        }
        requireItemModel(minecraft, PortRegistries.DIFFUSION_AMULET.get(), "Diffusion Amulet");
        for (var laserItem : PortRegistries.LASER_ITEMS) {
            requireItemModel(minecraft, laserItem.get(), laserItem.getId().toString());
        }
        requireItemModel(minecraft, PortRegistries.SHOT_MATERIAL.get(), "Shot Material");
        requireResource(minecraft, id("textures/item/material/shot_material.png"));
        int cards = 0;
        for (var entry : dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardRegistry.sorted()) {
            requireItemModel(minecraft, PortRegistries.SPELL_CARD_ITEMS.get(entry.id()).get(), "spell card " + entry.name());
            requireResource(minecraft, id("textures/item/spellcard/" + entry.key() + ".png"));
            requireResource(minecraft, id("textures/item/spellcard/spellcard_lv" + entry.create().getNeedLevel() + ".png"));
            cards++;
        }
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P11_CLIENT_RESOURCES_PASS spellCards={} laserItems={}",
                cards, PortRegistries.LASER_ITEMS.size());
        requireResource(minecraft, id("textures/entity/mini_hakkero.png"));
        requireResource(minecraft, id("textures/entity/sukima.png"));
        minecraft.getEntityModels().bakeLayer(P12Renderers.HAKKERO_LAYER).getChild("plate1");
        minecraft.getEntityModels().bakeLayer(P12Renderers.HAKKERO2_LAYER).getChild("side7");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P12_CLIENT_RESOURCES_PASS spellCards={} hakkeroModels=2", cards);
        requireItemModel(minecraft, PortRegistries.MINI_HAKKERO_ITEM.get(), "Mini Hakkero");
        requireItemModel(minecraft, PortRegistries.NUCLEAR_CONTROL_ROD.get(), "Nuclear Control Rod");
        requireItemModel(minecraft, PortRegistries.DRAGON_NECK_JEWEL_ITEM.get(), "Dragon Neck Jewel");
        for (String t : new String[] {"item/mini_hakkero", "item/nuclear_control_rod", "item/dragon_neck_jewel",
                "entity/th_kaguya_terrain"}) {
            requireResource(minecraft, id("textures/" + t + ".png"));
        }
        requireItemModel(minecraft, PortRegistries.HAKUREI_MIKO_STICK.get(), "Hakurei Shrine Maiden Stick");
        requireResource(minecraft, id("textures/item/hakurei_miko_stick.png"));
        requireResource(minecraft, id("textures/entity/shot/onmyoudama.png"));
        requireItemModel(minecraft, PortRegistries.WIND_MIKO_STICK.get(), "Wind Shrine Maiden Stick");
        requireResource(minecraft, id("textures/item/wind_miko_stick.png"));
        requireResource(minecraft, id("textures/entity/miracle_circle.png"));
        requireItemModel(minecraft, PortRegistries.GAP.get(), "Gap");
        requireItemModel(minecraft, PortRegistries.GAP_FOLDING_UMBRELLA.get(), "Gap Folding Umbrella");
        for (String t : new String[] {"item/gap", "item/gap_folding_umbrella_base", "item/gap_folding_umbrella_ribbon",
                "entity/sukima"}) {
            requireResource(minecraft, id("textures/" + t + ".png"));
        }
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P13_CLIENT_RESOURCES_PASS items=7");
        for (var bonus : java.util.List.of(PortRegistries.POWER_ITEM_SMALL, PortRegistries.POWER_ITEM_BIG,
                PortRegistries.POINT_ITEM, PortRegistries.BOMB_ITEM, PortRegistries.EXTEND_ITEM)) {
            requireItemModel(minecraft, bonus.get(), bonus.getId().toString());
            requireResource(minecraft, id("textures/item/" + bonus.getId().getPath() + ".png"));
        }
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P14_CLIENT_RESOURCES_PASS bonusItems=5");
        requireItemModel(minecraft, PortRegistries.DANMAKU_CRAFTING_TABLE_ITEM.get(), "Danmaku Crafting Table");
        requireItemModel(minecraft, PortRegistries.LASER_CRAFTING_TABLE_ITEM.get(), "Laser Crafting Table");
        for (String t : new String[] {"gui/danmaku_crafting_table", "gui/laser_crafting_table",
                "block/danmaku_crafting_table", "block/laser_crafting_table"}) {
            requireResource(minecraft, id("textures/" + t + ".png"));
        }
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P15_CLIENT_RESOURCES_PASS tables=2");

        var root = minecraft.getEntityModels().bakeLayer(SakuyaTimeControllerModel.LAYER_LOCATION);
        root.getChild("watch_base");
        root.getChild("watch_center");
        root.getChild("watch_handle");
        root.getChild("watch_cover");

        FiveDifficultiesPort.LOGGER.info(
                "FIVE_DIFFICULTIES_P7_CLIENT_RESOURCES_PASS canonicalTextures={} watchLayer=ok itemModels=" + (4 + PortRegistries.SHOT_ITEMS.size()) + "",
                TEXTURES.size()
        );
    }

    private static void requireItemModel(Minecraft minecraft, Item item, String label) {
        BakedModel model = minecraft.getItemRenderer().getModel(new ItemStack(item), null, null, 0);
        require(model != null && model != minecraft.getModelManager().getMissingModel(),
                label + " resolved to missing item model");
    }

    private static void requireResource(Minecraft minecraft, ResourceLocation id) {
        require(minecraft.getResourceManager().getResource(id).isPresent(), "missing client resource " + id);
    }

    private static ResourceLocation id(String path) {
        return new ResourceLocation(FiveDifficultiesPort.MOD_ID, path);
    }

    private static String sha256(byte[] bytes) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        return HexFormat.of().formatHex(digest.digest(bytes));
    }

    private static void require(boolean condition, String description) {
        if (!condition) throw new IllegalStateException("P7 client smoke failed: " + description);
    }
}
