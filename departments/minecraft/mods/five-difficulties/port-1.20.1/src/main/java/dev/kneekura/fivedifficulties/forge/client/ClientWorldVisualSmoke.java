package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.platform.NativeImage;
import dev.kneekura.fivedifficulties.core.timestop.TimeDomainMode;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.HomingAmuletProjectile;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import dev.kneekura.fivedifficulties.forge.timestop.SakuyaTimeStopRuntime;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.AccessibilityOnboardingScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.stream.Stream;

/**
 * P7b in-world client visual smoke, enabled only by FIVE_DIFFICULTIES_P7_WORLD_SMOKE=1.
 *
 * Unlike the P7 GUI screen, this goes through the real level renderer: it creates a
 * throwaway flat singleplayer world, fires live red Homing Amulets in front of a fixed
 * camera, then starts a live X1 FULL_STOP Watch controller and captures both frames.
 * Each frame gets a pixel assertion so an empty render can no longer pass.
 */
@Mod.EventBusSubscriber(
        modid = FiveDifficultiesPort.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.FORGE,
        value = Dist.CLIENT
)
public final class ClientWorldVisualSmoke {
    public static final String PASS_MARKER = "FIVE_DIFFICULTIES_P7B_WORLD_SMOKE_PASS";
    private static final String LEVEL_NAME = "five_difficulties_p7b_smoke";

    private enum Phase { BOOT, WAIT_WORLD, SETTLE, FIRE, SHOOT_HOMING, START_STOP, SHOOT_STOP, DONE }

    private static Phase phase = Phase.BOOT;
    private static int ticks;
    private static int bootTicks;
    private static String pendingShot;
    private static int shotWait;
    private static double baselineWarmFraction;
    private static double homingWarmDelta;
    private static double baselineSky;
    private static double stopSky;

    private ClientWorldVisualSmoke() {}

    private static boolean enabled() {
        return "1".equals(System.getenv("FIVE_DIFFICULTIES_P7_WORLD_SMOKE"));
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (!enabled() || phase == Phase.DONE || event.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        try {
            if (pendingShot != null) {
                awaitShot(mc);
                return;
            }
            switch (phase) {
                case BOOT -> boot(mc);
                case WAIT_WORLD -> {
                    if (mc.level != null && mc.player != null && mc.screen == null
                            && mc.getSingleplayerServer() != null) {
                        server(mc, ClientWorldVisualSmoke::stageCamera);
                        next(Phase.SETTLE);
                    } else if (++ticks > 20 * 120) {
                        fail("world did not open");
                    }
                }
                case SETTLE -> {
                    // let chunks render and lighting settle before the baseline frame
                    if (++ticks == 60) requestShot(mc, "p7b_baseline.png");
                    else if (ticks > 60) next(Phase.FIRE);
                }
                case FIRE -> {
                    server(mc, ClientWorldVisualSmoke::fireHoming);
                    next(Phase.SHOOT_HOMING);
                }
                case SHOOT_HOMING -> {
                    if (++ticks == 3) requestShot(mc, "p7b_homing.png");
                    else if (ticks > 3) next(Phase.START_STOP);
                }
                case START_STOP -> {
                    server(mc, ClientWorldVisualSmoke::startStop);
                    next(Phase.SHOOT_STOP);
                }
                case SHOOT_STOP -> {
                    if (++ticks == 12) requestShot(mc, "p7b_timestop.png");
                    else if (ticks > 12) finish(mc);
                }
                default -> {}
            }
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P7B_WORLD_SMOKE_FAIL", failure);
            phase = Phase.DONE;
            mc.stop();
        }
    }

    private static void next(Phase p) {
        phase = p;
        ticks = 0;
    }

    private static void boot(Minecraft mc) throws IOException {
        if (++bootTicks > 20 * 180) fail("title screen never became ready (screen=" + mc.screen + ")");
        if (mc.getOverlay() != null) return;
        // A fresh run directory opens the 1.20 accessibility onboarding screen first.
        if (mc.screen instanceof AccessibilityOnboardingScreen) {
            mc.options.onboardAccessibility = false;
            mc.options.save();
            mc.setScreen(new TitleScreen(true));
            return;
        }
        if (!(mc.screen instanceof TitleScreen) || bootTicks < 20) return;

        Path dir = mc.getLevelSource().getBaseDir().resolve(LEVEL_NAME);
        if (Files.exists(dir)) {
            try (Stream<Path> walk = Files.walk(dir)) {
                for (Path p : walk.sorted(Comparator.reverseOrder()).toList()) Files.delete(p);
            }
        }

        GameRules rules = new GameRules();
        rules.getRule(GameRules.RULE_DAYLIGHT).set(false, null);
        rules.getRule(GameRules.RULE_WEATHER_CYCLE).set(false, null);
        rules.getRule(GameRules.RULE_DOMOBSPAWNING).set(false, null);

        mc.createWorldOpenFlows().createFreshLevel(
                LEVEL_NAME,
                new LevelSettings(LEVEL_NAME, GameType.CREATIVE, false, Difficulty.PEACEFUL, true,
                        rules, WorldDataConfiguration.DEFAULT),
                new WorldOptions(1201L, false, false),
                access -> access.registryOrThrow(Registries.WORLD_PRESET)
                        .getHolderOrThrow(WorldPresets.FLAT).value().createWorldDimensions()
        );
        next(Phase.WAIT_WORLD);
    }

    private interface ServerStep { void run(ServerLevel level, ServerPlayer player); }

    private static void server(Minecraft mc, ServerStep step) {
        MinecraftServer server = mc.getSingleplayerServer();
        var uuid = mc.player.getUUID();
        server.execute(() -> {
            ServerLevel level = server.overworld();
            ServerPlayer player = server.getPlayerList().getPlayer(uuid);
            if (player == null) {
                FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P7B_WORLD_SMOKE_FAIL no server player");
                return;
            }
            step.run(level, player);
        });
    }

    // Fixed camera: stand at the origin of the flat world, look south (+Z), slightly down.
    private static void stageCamera(ServerLevel level, ServerPlayer player) {
        level.setDayTime(6000L);
        player.getAbilities().flying = true;
        player.onUpdateAbilities();
        player.connection.teleport(0.5D, -55.0D, 0.5D, 0.0F, 15.0F);
    }

    private static void fireHoming(ServerLevel level, ServerPlayer player) {
        Vec3 eye = player.getEyePosition().add(0.0D, -0.4D, 0.0D);
        for (int i = -2; i <= 2; i++) {
            Vec3 origin = eye.add(i * 0.6D, 0.0D, 2.5D);
            HomingAmuletProjectile shot = new HomingAmuletProjectile(level, player, origin,
                    new Vec3(i * 0.08D, 0.0D, 1.0D), false);
            level.addFreshEntity(shot);
        }
    }

    // Source is an armor stand in front of the camera, so the Watch controller and its
    // expanding dark field are on screen and the player (a non-source) is inside the field.
    private static void startStop(ServerLevel level, ServerPlayer player) {
        ArmorStand stand = EntityType.ARMOR_STAND.create(level);
        stand.moveTo(0.5D, -60.0D, 9.5D, 180.0F, 0.0F);
        stand.setInvisible(true);
        level.addFreshEntity(stand);
        SakuyaTimeControllerEntity controller = SakuyaTimeStopRuntime.startX1(
                level, stand, TimeDomainMode.FULL_STOP, 200, SakuyaControllerKind.WATCH_LIMITED);
        if (controller == null) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P7B_WORLD_SMOKE_FAIL controller refused");
        }
    }

    private static void requestShot(Minecraft mc, String name) throws IOException {
        Path file = screenshotPath(mc, name);
        Files.deleteIfExists(file);
        Screenshot.grab(mc.gameDirectory, name, mc.getMainRenderTarget(),
                message -> FiveDifficultiesPort.LOGGER.info("P7b screenshot: {}", message.getString()));
        pendingShot = name;
        shotWait = 0;
    }

    private static Path screenshotPath(Minecraft mc, String name) {
        return mc.gameDirectory.toPath().resolve("screenshots").resolve(name);
    }

    private static void awaitShot(Minecraft mc) throws Exception {
        Path file = screenshotPath(mc, pendingShot);
        if (!Files.isRegularFile(file) || Files.size(file) < 1024L) {
            if (++shotWait > 100) fail("screenshot not materialized: " + pendingShot);
            return;
        }
        byte[] png = Files.readAllBytes(file);
        double[] stats;
        try (NativeImage image = NativeImage.read(new ByteArrayInputStream(png))) {
            stats = analyze(image);
        }
        String name = pendingShot;
        pendingShot = null;

        double warmFraction = stats[0];
        double skyBlueMinusRed = stats[1];
        FiveDifficultiesPort.LOGGER.info("P7b frame {} warmFraction={} skyBlueMinusRed={} sha256={}",
                name, String.format("%.5f", warmFraction), String.format("%.1f", skyBlueMinusRed), sha256(png));

        switch (name) {
            case "p7b_baseline.png" -> {
                baselineWarmFraction = warmFraction;
                baselineSky = skyBlueMinusRed;
                require(skyBlueMinusRed > 40.0D, "baseline sky is not blue; camera staging failed");
            }
            case "p7b_homing.png" -> {
                homingWarmDelta = warmFraction - baselineWarmFraction;
                require(homingWarmDelta > 0.001D, "Homing Amulets not visible in world frame");
            }
            // X1 dark field uses ONE_MINUS_DST_COLOR/ZERO: everything inside it is colour-inverted,
            // so the blue sky must turn brown (blue - red flips sign).
            case "p7b_timestop.png" -> {
                stopSky = skyBlueMinusRed;
                require(skyBlueMinusRed < -40.0D, "dark time field did not invert the sky (baseline="
                        + baselineSky + " stop=" + skyBlueMinusRed + ")");
            }
            default -> {}
        }
        if (!"1".equals(System.getenv("FIVE_DIFFICULTIES_KEEP_SCREENSHOT"))) Files.deleteIfExists(file);
    }

    /**
     * [fraction of warm (amulet-coloured) pixels, mean blue-minus-red of the top fifth (sky)].
     * NativeImage pixels are ABGR.
     */
    private static double[] analyze(NativeImage image) {
        long n = 0, warm = 0, skyN = 0;
        double sky = 0;
        int skyRows = image.getHeight() / 5;
        for (int y = 0; y < image.getHeight(); y += 2) {
            for (int x = 0; x < image.getWidth(); x += 2) {
                int abgr = image.getPixelRGBA(x, y);
                int r = abgr & 0xFF, g = (abgr >> 8) & 0xFF, b = (abgr >> 16) & 0xFF;
                if (r > 180 && b < 120 && r >= g) warm++; // flat world is green/blue
                if (y < skyRows) {
                    sky += b - r;
                    skyN++;
                }
                n++;
            }
        }
        return new double[] { (double) warm / n, sky / skyN };
    }

    private static void finish(Minecraft mc) {
        FiveDifficultiesPort.LOGGER.info("{} homingWarmDelta={} skyBlueMinusRed baseline={} stop={}",
                PASS_MARKER, String.format("%.5f", homingWarmDelta),
                String.format("%.1f", baselineSky), String.format("%.1f", stopSky));
        phase = Phase.DONE;
        mc.stop();
    }

    private static String sha256(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }

    private static void fail(String what) {
        throw new IllegalStateException("P7b world smoke failed: " + what);
    }

    private static void require(boolean condition, String what) {
        if (!condition) fail(what);
    }
}
