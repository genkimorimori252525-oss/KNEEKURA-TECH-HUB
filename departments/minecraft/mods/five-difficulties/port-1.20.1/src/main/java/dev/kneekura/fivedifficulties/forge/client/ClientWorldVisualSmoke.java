package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.platform.NativeImage;
import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.timestop.TimeDomainMode;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.HomingAmuletProjectile;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1LaserSpawner;
import dev.kneekura.fivedifficulties.forge.timestop.SakuyaTimeStopRuntime;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
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

    private enum Phase { BOOT, WAIT_WORLD, SETTLE, FIRE, SHOOT_HOMING, P8_SPAWN, P8_SHOT, P9_SPAWN, P9_SHOT, P10_SPAWN, P10_SHOT, P11_SPAWN, P11_SHOT, P12_SPAWN, P12_SHOT, P15_OPEN, P15_SHOT, P16_SPAWN, P16_SHOT, P16B_SPAWN, P16B_SHOT, P17_SPAWN, P17_SHOT, START_STOP, SHOOT_STOP, DONE }

    private static final int[] P8_GRID_FORMS = {
            X1ShotTables.FORM_SMALL, X1ShotTables.FORM_MEDIUM, X1ShotTables.FORM_PEARL, X1ShotTables.FORM_CIRCLE,
            X1ShotTables.FORM_HEART, X1ShotTables.FORM_BIG};
    private static double baselineColourful;
    private static double shotsColourfulDelta;
    private static double formsColourfulDelta;
    private static double lasersColourfulDelta;
    private static double cardColourfulDelta;
    private static double p12ColourfulDelta;

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
                    else if (ticks > 3) next(Phase.P8_SPAWN);
                }
                case P8_SPAWN -> {
                    server(mc, ClientWorldVisualSmoke::spawnShotGrid);
                    next(Phase.P8_SHOT);
                }
                case P8_SHOT -> {
                    if (++ticks == 10) requestShot(mc, "p8_shots.png");
                    else if (ticks > 10) next(Phase.P9_SPAWN);
                }
                case P9_SPAWN -> {
                    server(mc, ClientWorldVisualSmoke::spawnFormGrid);
                    next(Phase.P9_SHOT);
                }
                case P9_SHOT -> {
                    if (++ticks == 10) requestShot(mc, "p9_forms.png");
                    else if (ticks > 10) next(Phase.P10_SPAWN);
                }
                case P10_SPAWN -> {
                    server(mc, ClientWorldVisualSmoke::spawnLasers);
                    next(Phase.P10_SHOT);
                }
                case P10_SHOT -> {
                    if (++ticks == 10) requestShot(mc, "p10_lasers.png");
                    else if (ticks > 10) next(Phase.P11_SPAWN);
                }
                case P11_SPAWN -> {
                    server(mc, ClientWorldVisualSmoke::declareCard);
                    next(Phase.P11_SHOT);
                }
                case P11_SHOT -> {
                    if (++ticks == 30) requestShot(mc, "p11_spellcard.png");
                    else if (ticks > 30) {
                        server(mc, (level, player) -> level.getEntitiesOfClass(net.minecraft.world.entity.Entity.class,
                                player.getBoundingBox().inflate(48), e -> e instanceof THShotEntity
                                        || e instanceof dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity
                                        || e instanceof dev.kneekura.fivedifficulties.forge.entity.SpellCardCircleEntity)
                                .forEach(net.minecraft.world.entity.Entity::discard));
                        next(Phase.P12_SPAWN);
                    }
                }
                case P12_SPAWN -> {
                    server(mc, ClientWorldVisualSmoke::spawnP12);
                    next(Phase.P12_SHOT);
                }
                case P12_SHOT -> {
                    if (++ticks == 20) requestShot(mc, "p12_entities.png");
                    else if (ticks > 20) {
                        server(mc, (level, player) -> {
                            level.getEntitiesOfClass(net.minecraft.world.entity.Entity.class, player.getBoundingBox().inflate(48),
                                    e -> !(e instanceof net.minecraft.world.entity.player.Player))
                                    .forEach(net.minecraft.world.entity.Entity::discard);
                        });
                        next(Phase.P15_OPEN);
                    }
                }
                case P15_OPEN -> {
                    server(mc, ClientWorldVisualSmoke::openCraftingTable);
                    next(Phase.P15_SHOT);
                }
                case P15_SHOT -> {
                    if (++ticks == 15) {
                        require(mc.screen instanceof DanmakuCraftingScreen, "the danmaku crafting screen is open, got " + mc.screen);
                        requestShot(mc, "p15_crafting.png");
                    } else if (ticks > 15) {
                        server(mc, (level, player) -> player.closeContainer());
                        next(Phase.P16_SPAWN);
                    }
                }
                case P16_SPAWN -> {
                    server(mc, ClientWorldVisualSmoke::spawnP16);
                    next(Phase.P16_SHOT);
                }
                case P16_SHOT -> {
                    if (++ticks == 12) requestShot(mc, "p16_items.png");
                    else if (ticks > 12) {
                        server(mc, (level, player) -> level.getEntitiesOfClass(net.minecraft.world.entity.Entity.class,
                                player.getBoundingBox().inflate(48), e -> !(e instanceof net.minecraft.world.entity.player.Player))
                                .forEach(net.minecraft.world.entity.Entity::discard));
                        next(Phase.P16B_SPAWN);
                    }
                }
                case P16B_SPAWN -> {
                    server(mc, ClientWorldVisualSmoke::spawnP16b);
                    next(Phase.P16B_SHOT);
                }
                case P16B_SHOT -> {
                    if (++ticks == 6) requestShot(mc, "p16_items2.png");
                    else if (ticks > 6) {
                        server(mc, (level, player) -> level.getEntitiesOfClass(net.minecraft.world.entity.Entity.class,
                                player.getBoundingBox().inflate(48), e -> !(e instanceof net.minecraft.world.entity.player.Player))
                                .forEach(net.minecraft.world.entity.Entity::discard));
                        next(Phase.P17_SPAWN);
                    }
                }
                case P17_SPAWN -> {
                    server(mc, ClientWorldVisualSmoke::spawnP17);
                    next(Phase.P17_SHOT);
                }
                case P17_SHOT -> {
                    if (++ticks == 20) {
                        server(mc, (level, player) -> level.getEntitiesOfClass(net.minecraft.world.entity.Mob.class,
                                player.getBoundingBox().inflate(32)).forEach(m -> FiveDifficultiesPort.LOGGER.info(
                                "P17 frame mob {} at {}", m.getType().getDescriptionId(), m.position())));
                        requestShot(mc, "p17_mobs.png");
                    }
                    else if (ticks > 20) {
                        server(mc, (level, player) -> level.getEntitiesOfClass(net.minecraft.world.entity.Entity.class,
                                player.getBoundingBox().inflate(48), e -> !(e instanceof net.minecraft.world.entity.player.Player))
                                .forEach(net.minecraft.world.entity.Entity::discard));
                        server(mc, (level, player) -> level.getServer().setDifficulty(Difficulty.PEACEFUL, true));
                        next(Phase.START_STOP);
                    }
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
        // Another window taking focus must not open the pause menu over the frames.
        mc.options.pauseOnLostFocus = false;
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

    // P8: every renderNormalShot form x 8 colours, static, plus one row still in its delay (light).
    private static void spawnShotGrid(ServerLevel level, ServerPlayer player) {
        Vec3d none = Vec3d.ZERO;
        Vec3d up = new Vec3d(0, 1, 0);
        Vec3d south = new Vec3d(0, 0, 1);
        for (int row = 0; row <= P8_GRID_FORMS.length; row++) {
            boolean delayed = row == P8_GRID_FORMS.length;
            int form = delayed ? X1ShotTables.FORM_SMALL : P8_GRID_FORMS[row];
            for (int color = 0; color < 8; color++) {
                Vec3d pos = new Vec3d(-2.3D + color * 0.8D, -53.0D - row * 0.62D, 6.0D);
                X1ShotData data = X1ShotData.shot(form, color, X1ShotTables.SIZE[form], X1ShotTables.DAMAGE[form],
                        delayed ? 400 : 0, 2000, 0);
                level.addFreshEntity(new THShotEntity(level, player, pos, south, 0F, up, 0F, 9999, 0, 0, 0, none, data));
            }
        }
    }

    // P9: the 18 remaining RenderTHShot forms, three rows of six, drifting slowly along +X so the
    // direction-dependent forms (kunai, arrow, rice, ...) are seen side-on.
    private static final int[] P9_FORMS = {
            X1ShotTables.FORM_SCALE, X1ShotTables.FORM_BUTTERFLY, X1ShotTables.FORM_SMALLSTAR, X1ShotTables.FORM_STAR,
            X1ShotTables.FORM_RICE, X1ShotTables.FORM_CRYSTAL,
            X1ShotTables.FORM_KUNAI, X1ShotTables.FORM_TALISMAN, X1ShotTables.FORM_OVAL, X1ShotTables.FORM_ARROW,
            X1ShotTables.FORM_AMULET, X1ShotTables.FORM_KNIFE,
            X1ShotTables.FORM_LIGHT, X1ShotTables.FORM_FAMILIAR, X1ShotTables.FORM_WIND, X1ShotTables.FORM_PHANTOM,
            X1ShotTables.FORM_BIGLIGHT, X1ShotTables.FORM_KISHITU};

    private static void spawnFormGrid(ServerLevel level, ServerPlayer player) {
        level.getEntitiesOfClass(THShotEntity.class, player.getBoundingBox().inflate(32), s -> true)
                .forEach(THShotEntity::discard);
        Vec3d east = new Vec3d(1, 0, 0);
        for (int i = 0; i < P9_FORMS.length; i++) {
            int form = P9_FORMS[i];
            int color = i % 8;
            Vec3d pos = new Vec3d(4.0D - (i % 6) * 1.6D, -53.4D - (i / 6) * 2.0D, 9.0D);
            X1ShotData data = X1ShotData.shot(form, color, X1ShotTables.SIZE[form] == 0F ? 0.5F : X1ShotTables.SIZE[form],
                    1.0F, 0, 2000, 0);
            level.addFreshEntity(new THShotEntity(level, player, pos, east, 0F, new Vec3d(0, 1, 0), 0F, 9999,
                    0.001D, 0.001D, 0D, Vec3d.ZERO, data));
        }
    }

    // P10: eight normal lasers, Spear the Gungnir, Laevateinn, a set laser and a laser in its delay.
    private static void spawnLasers(ServerLevel level, ServerPlayer player) {
        level.getEntitiesOfClass(THShotEntity.class, player.getBoundingBox().inflate(32), s -> true)
                .forEach(THShotEntity::discard);
        Vec3d east = new Vec3d(1, 0, 0);
        Vec3d up = new Vec3d(0, 1, 0);
        for (int color = 0; color < 8; color++) {
            staticLaser(level, player, new Vec3d(-4.5D, -52.8D - color * 0.45D, 8.0D), east, color, 0.15F, 9F, 0);
        }
        staticLaser(level, player, new Vec3d(-3.0D, -57.2D, 8.0D), east, 8 + 1, 0.2F, 6F, 0);   // Gungnir
        staticLaser(level, player, new Vec3d(-3.0D, -59.0D, 8.0D), east, 16, 0.6F, 6F, 0);      // Laevateinn
        staticLaser(level, player, new Vec3d(-1.0D, -51.6D, 8.0D), east, 3, 0.2F, 5F, 400);     // delay light
        ArmorStand stand = EntityType.ARMOR_STAND.create(level);
        stand.moveTo(5.0D, -60.0D, 9.0D, 0F, 0F);
        stand.setInvisible(true);
        stand.setNoGravity(true);
        level.addFreshEntity(stand);
        X1LaserSpawner.createLaserB(level, player, stand, new Vec3d(5.0D, -60.0D, 9.0D), up, east, 0F, 9999,
                X1LaserData.laser(5, 0.3F, 6F, 1F, 0, 2000), stand, 0.0D, 0.0D);
    }

    private static void staticLaser(ServerLevel level, ServerPlayer player, Vec3d pos, Vec3d dir, int shotId, float width,
                                    float length, int delay) {
        X1LaserData data = X1LaserData.laser(shotId / 8, shotId % 8, width, length, 1F, delay, 2000, 0);
        THLaserEntity laser = new THLaserEntity(level, player, player, pos, dir, 0F, new Vec3d(0, 1, 0), 0F, 9999,
                0D, 0D, 0D, Vec3d.ZERO, data);
        laser.setLaserLength(length);
        level.addFreshEntity(laser);
    }

    // P11: a stand-in player 9.5 blocks ahead declares card 2 at the camera player (its magic circle,
    // card and danmaku all come toward the camera).
    private static void declareCard(ServerLevel level, ServerPlayer player) {
        level.getEntitiesOfClass(THShotEntity.class, player.getBoundingBox().inflate(32), s -> true)
                .forEach(THShotEntity::discard);
        var user = net.minecraftforge.common.util.FakePlayerFactory.get(level,
                new com.mojang.authlib.GameProfile(java.util.UUID.fromString("00000000-0000-0000-0000-0000f9110b11"), "[FDP11-smoke]"));
        user.moveTo(0.5D, -58.0D, 10.0D, 180.0F, 0.0F);
        user.getAbilities().instabuild = true;
        dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardDeclaration.declare(level, user, player, 2, 0,
                dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardDeclaration.NORMAL, true);
    }

    // P12: Musou Fuuin orbs, a Mini Hakkero (in its laser delay), a gap and a nuclear shot in front of the camera.
    private static void spawnP12(ServerLevel level, ServerPlayer player) {
        for (int i = 0; i < 3; i++) {
            level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.MusouFuuinEntity(level, player,
                    new Vec3d(-3.0D + i * 1.4D, -53.0D, 8.0D), new Vec3d(0, 0, 1), 0F, new Vec3d(0, 1, 0), 0F, 9999,
                    0.0001D, 0.0D, 0.0D, Vec3d.ZERO, 2.0F, 9.0F, null));
        }
        ArmorStand stand = EntityType.ARMOR_STAND.create(level);
        stand.moveTo(-1.5D, -58.5D, 7.0D, 135F, 0F);
        stand.setInvisible(true);
        stand.setNoGravity(true);
        level.addFreshEntity(stand);
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.MiniHakkeroEntity(level, stand, null));
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.SukimaEntity(level, player, 2.5D, -58.0D, 9.0D,
                0F, 0));
        var nuclear = new dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity(level, player,
                new Vec3d(3.0D, -53.5D, 11.0D), new Vec3d(0, 0, 1), 0F, new Vec3d(0, 1, 0), 0F, 9999, 0.0001D, 0.0D,
                0.0D, Vec3d.ZERO, X1ShotData.shot(0, X1ShotTables.ORANGE, 1.6F, 10.0F, 0, 2000, 0));
        nuclear.shootingFlag = true;
        level.addFreshEntity(nuclear);
        // P13: a Dragon Neck Jewel held still (its own speed and gravity zeroed for the frame)
        var jewel = new dev.kneekura.fivedifficulties.forge.entity.DragonNeckJewelEntity(level, player,
                new Vec3d(0.5D, -54.5D, 6.0D), new Vec3d(0, 0, 1), 1F, 0.1F, 0.1F);
        jewel.motion().gravity = Vec3d.ZERO;
        jewel.motion().acceleration = 0.0D;
        jewel.motion().setSpeed(0.0001D);
        level.addFreshEntity(jewel);
        // P13b: a Yin-Yang Orb held still (not charged by a player: thrown by an armor stand owner)
        var orb = new dev.kneekura.fivedifficulties.forge.entity.OnmyoudamaEntity(level, stand,
                new Vec3d(-0.5D, -55.5D, 6.0D), new Vec3d(0, 0, 1), 0F, new Vec3d(0, 1, 0), 0F, 9999, 0.0001D, 0.0D,
                0.0D, Vec3d.ZERO, X1ShotTables.ORANGE, 1.2F, 10.0F, 0, 2000, 0);
        level.addFreshEntity(orb);
        // P13c: a stand-in player at the camera charges the wind gohei (pentagram ahead) beside a held-still wind.
        // (The camera player itself would release at once: its use key is not held.)
        var charger = net.minecraftforge.common.util.FakePlayerFactory.get(level, new com.mojang.authlib.GameProfile(
                java.util.UUID.fromString("00000000-0000-0000-0000-0000f9130c00"), "[FDP13c-smoke]"));
        charger.moveTo(player.getX(), player.getY(), player.getZ(), player.getYRot(), player.getXRot());
        charger.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,
                new net.minecraft.world.item.ItemStack(dev.kneekura.fivedifficulties.forge.PortRegistries.WIND_MIKO_STICK.get()));
        charger.startUsingItem(net.minecraft.world.InteractionHand.MAIN_HAND);
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.MiracleCircleEntity(level, charger, 0));
        var wind = new dev.kneekura.fivedifficulties.forge.entity.SanaeWindEntity(level, stand,
                new Vec3d(-3.5D, -57.0D, 8.0D), new Vec3d(0, 0, 1), 0F, new Vec3d(0, 1, 0), 0F, 9999, 0.0001D, 0.0D,
                0.0D, Vec3d.ZERO, 0, 1.0F, 1.0F, 0, 2000, 0);
        level.addFreshEntity(wind);
        // P14: a big power bonus falling in front of the camera
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.THItemEntity(level, 2.0D, -51.0D, 7.0D,
                Vec3d.ZERO, dev.kneekura.fivedifficulties.forge.entity.THItemEntity.ITEM_ID_BIGPOWER));
    }

    private static net.minecraftforge.common.util.FakePlayer p16User(ServerLevel level, int n, double x, double z,
                                                                     net.minecraft.world.item.Item held) {
        var u = net.minecraftforge.common.util.FakePlayerFactory.get(level, new com.mojang.authlib.GameProfile(
                java.util.UUID.fromString("00000000-0000-0000-0000-0000f916000" + n), "[FDP16-smoke" + n + "]"));
        u.moveTo(x, -60.0D, z, 180F, 0F);
        u.setYHeadRot(180F);
        u.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new net.minecraft.world.item.ItemStack(held));
        u.startUsingItem(net.minecraft.world.InteractionHand.MAIN_HAND);
        return u;
    }

    // P16 (2): knives stuck in the air, the parasol, the Hisou swords, the Kinkakuji ceiling and the broom.
    private static void spawnP16b(ServerLevel level, ServerPlayer player) {
        for (int c = 0; c < 4; c++) {
            var k = new dev.kneekura.fivedifficulties.forge.entity.SilverKnifeEntity(level,
                    new Vec3d(-2.5D + c, -59.0D, 4.0D), new Vec3d(0, 0, 1), 0.0D, c);
            k.setKnifeCount(-100000); // hold it still for the frame
            level.addFreshEntity(k);
        }
        var holder = p16User(level, 5, -3.0D, 9.0D, dev.kneekura.fivedifficulties.forge.PortRegistries.YUUKA_PARASOL.get());
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.YuukaParasolEntity(level, holder, 0));
        var swordUser = p16User(level, 6, 2.5D, 9.0D, dev.kneekura.fivedifficulties.forge.PortRegistries.HISOU_SWORD.get());
        for (int i = 1; i <= 8; i++) {
            level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.HisouEntity(level, swordUser, null, i, 0));
        }
        var ceiling = new dev.kneekura.fivedifficulties.forge.entity.KinkakuziEntity(level, 0.5D, -56.0D, 14.0D, player, 0.0D);
        ceiling.setNoGravity(true);
        level.addFreshEntity(ceiling);
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.MarisaBroomEntity(level, 0.5D, -60.5D, 6.0D));
    }

    // P17: the danmaku mobs in a row facing the camera (no AI, so they hold still).
    private static void spawnP17(ServerLevel level, ServerPlayer player) {
        level.getServer().setDifficulty(Difficulty.NORMAL, true); // X1 danmaku mobs remove themselves in peaceful
        net.minecraft.world.entity.EntityType<?>[] types = {
                dev.kneekura.fivedifficulties.forge.PortRegistries.TH_FAIRY.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.SUNFLOWER_FAIRY.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.TH_PHANTOM.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.CIRNO.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.WRIGGLE.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.TOZIKO.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.SAKUYA.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.SANAE.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.REIMU.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.MIKO.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.RINNOSUKE.get(),
                dev.kneekura.fivedifficulties.forge.PortRegistries.CURSED_DECOY_DOLL.get()};
        for (int i = 0; i < types.length; i++) {
            var e = types[i].create(level);
            if (!(e instanceof net.minecraft.world.entity.Mob mob)) continue;
            mob.moveTo(-10.5D + i * 2.0D, -59.0D, 12.0D, 180.0F, 0.0F);
            mob.setYHeadRot(180.0F);
            mob.yBodyRot = 180.0F;
            mob.setNoAi(true);
            mob.setNoGravity(true);
            level.addFreshEntity(mob);
        }
    }

    // P16: item-effect entities and the two hats on armour stands, facing the camera.
    private static void spawnP16(ServerLevel level, ServerPlayer player) {
        var scroll = p16User(level, 1, -3.0D, 9.0D, dev.kneekura.fivedifficulties.forge.PortRegistries.SORCERER_SUTRA_SCROLL.get());
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.MazinkyoukanEntity(level, scroll));
        var aja = p16User(level, 2, 3.0D, 9.0D, dev.kneekura.fivedifficulties.forge.PortRegistries.AJA_RED_STONE.get());
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.AjaRedStoneEffectEntity(level, aja));
        var seeker = p16User(level, 3, 0.5D, 9.0D, dev.kneekura.fivedifficulties.forge.PortRegistries.NAZRIN_PENDULUM.get());
        for (int i = 0; i < 12; i++) {
            level.setBlockAndUpdate(BlockPos.containing(-2 + i % 6, -61, 11 + i / 6),
                    net.minecraft.world.level.block.Blocks.GOLD_BLOCK.defaultBlockState());
        }
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.PendulumEntity(level, seeker, 0,
                net.minecraft.world.level.block.Blocks.GOLD_BLOCK.getDescriptionId()));
        var wall = p16User(level, 4, 1.5D, 12.0D, dev.kneekura.fivedifficulties.forge.PortRegistries.HAKUROUKEN.get());
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.HakurouReflecterEntity(level, wall));
        var frozen = EntityType.ZOMBIE.create(level);
        frozen.moveTo(-1.5D, -60.0D, 6.0D, 180F, 0F);
        frozen.setNoAi(true);
        level.addFreshEntity(frozen);
        level.addFreshEntity(new dev.kneekura.fivedifficulties.forge.entity.CirnoIceBoxEntity(level, frozen));
        for (int i = 0; i < 2; i++) {
            ArmorStand stand = EntityType.ARMOR_STAND.create(level);
            stand.moveTo(1.0D + i * 1.5D, -60.0D, 5.0D, 180F, 0F);
            stand.setNoGravity(true);
            stand.setItemSlot(net.minecraft.world.entity.EquipmentSlot.HEAD, new net.minecraft.world.item.ItemStack(i == 0
                    ? dev.kneekura.fivedifficulties.forge.PortRegistries.MARISA_HAT.get()
                    : dev.kneekura.fivedifficulties.forge.PortRegistries.SUWAKO_HAT.get()));
            level.addFreshEntity(stand);
        }
    }

    // P15: both tables in front of the camera; using the danmaku one opens its screen.
    private static void openCraftingTable(ServerLevel level, ServerPlayer player) {
        BlockPos shot = BlockPos.containing(-1.0D, -60.0D, 4.0D);
        BlockPos laser = BlockPos.containing(2.0D, -60.0D, 4.0D);
        level.setBlockAndUpdate(shot, dev.kneekura.fivedifficulties.forge.PortRegistries.DANMAKU_CRAFTING_TABLE.get().defaultBlockState());
        level.setBlockAndUpdate(laser, dev.kneekura.fivedifficulties.forge.PortRegistries.LASER_CRAFTING_TABLE.get().defaultBlockState());
        level.getBlockState(shot).use(level, player, net.minecraft.world.InteractionHand.MAIN_HAND,
                new net.minecraft.world.phys.BlockHitResult(Vec3.atCenterOf(shot), net.minecraft.core.Direction.UP, shot, false));
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
            case "p8_shots.png" -> {
                shotsColourfulDelta = stats[2] - baselineColourful;
                require(shotsColourfulDelta > 0.004D, "P8 shot grid not visible (colourful delta "
                        + shotsColourfulDelta + ")");
            }
            case "p10_lasers.png" -> {
                lasersColourfulDelta = stats[2] - baselineColourful;
                require(lasersColourfulDelta > 0.01D, "P10 lasers not visible (colourful delta " + lasersColourfulDelta + ")");
            }
            case "p15_crafting.png" -> {
                // the GUI background is opaque: the sky must be covered
                require(skyBlueMinusRed < 40.0D, "the crafting screen covers the view (sky " + skyBlueMinusRed + ")");
            }
            case "p12_entities.png" -> {
                p12ColourfulDelta = stats[2] - baselineColourful;
                require(p12ColourfulDelta > 0.01D, "P12 spell-card entities not visible (colourful delta "
                        + p12ColourfulDelta + ")");
            }
            case "p11_spellcard.png" -> {
                cardColourfulDelta = stats[2] - baselineColourful;
                require(cardColourfulDelta > 0.01D, "P11 spell card danmaku not visible (colourful delta "
                        + cardColourfulDelta + ")");
            }
            case "p17_mobs.png" -> {
                double p17Delta = stats[2] - baselineColourful;
                FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P17_CLIENT_FRAME colourfulDelta={}", String.format("%.5f", p17Delta));
            }
            case "p9_forms.png" -> {
                formsColourfulDelta = stats[2] - baselineColourful;
                require(formsColourfulDelta > 0.01D, "P9 form grid not visible (colourful delta "
                        + formsColourfulDelta + ")");
            }
            case "p7b_baseline.png" -> {
                baselineColourful = stats[2];
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
        long n = 0, warm = 0, skyN = 0, colourful = 0;
        double sky = 0;
        int skyRows = image.getHeight() / 5;
        for (int y = 0; y < image.getHeight(); y += 2) {
            for (int x = 0; x < image.getWidth(); x += 2) {
                int abgr = image.getPixelRGBA(x, y);
                int r = abgr & 0xFF, g = (abgr >> 8) & 0xFF, b = (abgr >> 16) & 0xFF;
                if (r > 180 && b < 120 && r >= g) warm++; // flat world is green/blue
                // saturated or near-white pixels: X1 shot sprites; flat grass and sky are neither
                int max = Math.max(r, Math.max(g, b)), min = Math.min(r, Math.min(g, b));
                if (max - min > 140 || min > 225) colourful++;
                if (y < skyRows) {
                    sky += b - r;
                    skyN++;
                }
                n++;
            }
        }
        return new double[] { (double) warm / n, sky / skyN, (double) colourful / n };
    }

    private static void finish(Minecraft mc) {
        FiveDifficultiesPort.LOGGER.info("{} homingWarmDelta={} p8ColourfulDelta={} skyBlueMinusRed baseline={} stop={}",
                PASS_MARKER + " p9ColourfulDelta=" + String.format("%.5f", formsColourfulDelta)
                        + " p10ColourfulDelta=" + String.format("%.5f", lasersColourfulDelta)
                        + " p11ColourfulDelta=" + String.format("%.5f", cardColourfulDelta)
                        + " p12ColourfulDelta=" + String.format("%.5f", p12ColourfulDelta),
                String.format("%.5f", homingWarmDelta), String.format("%.5f", shotsColourfulDelta),
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
