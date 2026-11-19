package dev.kneekura.fivedifficulties.forge;

import com.mojang.authlib.GameProfile;
import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.ShotMaterialEntity;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardCircleEntity;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardDeclaration;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/** P11 dedicated-server scenario for the spell-card core and every ported card (FIVE_DIFFICULTIES_P11_RUNTIME_SCENARIO=1). */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P11SpellCardScenario {
    public static final String ENV = "FIVE_DIFFICULTIES_P11_RUNTIME_SCENARIO";
    /** X1 cards whose spellcard_main fires nothing (Spear the Gungnir; Hisouten only registers a special shot). */
    private static final Set<Integer> SILENT_CARDS = Set.of(7, 27);
    private static final Set<Integer> P12_CARDS = Set.of(0, 1, 8, 10, 15);

    private enum Phase { IDLE, COST, CARDS, BONUS, DONE }

    private static final class Lane {
        final X1SpellCardRegistry.Entry entry;
        final FakePlayer player;
        SpellCardEntity card;
        int maxShots;
        int removedAt = -1;

        Lane(X1SpellCardRegistry.Entry entry, FakePlayer player) {
            this.entry = entry;
            this.player = player;
        }
    }

    private static Phase phase = Phase.IDLE;
    private static ServerLevel level;
    private static final List<Lane> lanes = new ArrayList<>();
    private static int ticks;
    private static double bx, by, bz;
    private static final java.util.Map<UUID, Integer> SPAWNED = new java.util.HashMap<>();
    private static int materialsSpawned;
    private static Vec3d bonusAt;

    /** Count every shot / laser a lane's user spawns (neighbouring cards' danmakuRemove can clear them early). */
    @SubscribeEvent
    public static void onJoin(net.minecraftforge.event.entity.EntityJoinLevelEvent event) {
        if (!enabled() || event.getLevel().isClientSide) return;
        if (event.getEntity() instanceof THShotEntity s && s.getOwner() != null) {
            SPAWNED.merge(s.getOwner().getUUID(), 1, Integer::sum);
        } else if (event.getEntity() instanceof ShotMaterialEntity m && bonusAt != null
                && Math.abs(m.getY() - bonusAt.y()) < 1.0D && Math.abs(m.getZ() - bonusAt.z()) < 1.0D
                && m.getX() > bonusAt.x() - 1.0D && m.getX() < bonusAt.x() + 7.0D) {
            materialsSpawned++;
        }
    }

    private P11SpellCardScenario() {}

    private static boolean enabled() {
        return "1".equals(System.getenv(ENV));
    }

    private static FakePlayer player(int n, double x, double z) {
        FakePlayer p = FakePlayerFactory.get(level, new GameProfile(
                UUID.fromString(String.format("00000000-0000-0000-0000-0000f911%04d", n)), "[FDP11-" + n + "]"));
        p.moveTo(x, by, z, 0F, 0F); // facing +Z
        return p;
    }

    private static Husk husk(double x, double z) {
        Husk h = EntityType.HUSK.create(level);
        h.moveTo(x, by, z, 180F, 0F);
        h.setNoAi(true);
        h.setInvulnerable(true); // keep each card's target alive for the whole card
        require(level.addFreshEntity(h), "husk");
        return h;
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        // Declaring clears enemy danmaku within 40 of the user (X1), so stay well away from the P6-P10 areas
        // (all within ~35 of spawn) while remaining inside the always-ticking spawn chunks.
        bx = spawn.getX() - 70 + 0.5D;
        bz = spawn.getZ() + 70 + 0.5D;
        by = level.getHeight(Heightmap.Types.MOTION_BLOCKING, spawn.getX() - 70, spawn.getZ() + 70);
        runCostChecks();
        phase = Phase.COST;
    }

    // 1. Survival declaration: refused without enough levels, costs needLevel otherwise.
    private static void runCostChecks() {
        FakePlayer p = player(9999, bx - 40.0D, bz);
        husk(bx - 40.0D, bz + 6.0D);
        int id = 22; // Mishagujisama, need level 3
        ItemStack stack = new ItemStack(PortRegistries.SPELL_CARD_ITEMS.get(id).get());
        p.experienceLevel = 2;
        require(!X1SpellCardDeclaration.check(level, stack, p, id, X1SpellCardDeclaration.NORMAL, true),
                "declaration with 2 levels must be refused");
        p.experienceLevel = 5;
        require(X1SpellCardDeclaration.check(level, stack, p, id, X1SpellCardDeclaration.NORMAL, true),
                "declaration with 5 levels");
        require(p.experienceLevel == 2, "cost 3 levels, left " + p.experienceLevel);
        require(!X1SpellCardDeclaration.check(level, stack, p, id, X1SpellCardDeclaration.NORMAL, true),
                "a user with an active card cannot declare another");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P11_COST_PASS levelsLeft={}", p.experienceLevel);
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (!enabled() || event.phase != TickEvent.Phase.END || phase == Phase.IDLE || phase == Phase.DONE) return;
        try {
            ticks++;
            switch (phase) {
                case COST -> startCards();
                case CARDS -> tickCards();
                case BONUS -> tickBonus();
                default -> {}
            }
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P11_RUNTIME_SCENARIO_FAIL phase={}", phase, failure);
            phase = Phase.DONE;
            ScenarioShutdown.failed(level.getServer());
            throw failure;
        }
    }

    // 2. Every registered card, each with its own creative user and target, declared at once.
    private static void startCards() {
        int i = 0;
        for (X1SpellCardRegistry.Entry entry : X1SpellCardRegistry.all()) {
            if (P12_CARDS.contains(entry.id())) continue; // checked one at a time by P12 (time stop, own entities)
            double x = bx - 25.0D + (i % 6) * 10.0D;
            double z = bz + 10.0D + (i / 6) * 12.0D;
            FakePlayer p = player(i, x, z);
            p.getAbilities().instabuild = true;
            husk(x, z + 6.0D);
            ItemStack stack = new ItemStack(PortRegistries.SPELL_CARD_ITEMS.get(entry.id()).get());
            require(X1SpellCardDeclaration.check(level, stack, p, entry.id(), X1SpellCardDeclaration.NORMAL, true),
                    "declare " + entry.name());
            Lane lane = new Lane(entry, p);
            for (SpellCardEntity c : level.getEntitiesOfClass(SpellCardEntity.class, p.getBoundingBox().inflate(4.0D))) {
                if (c.user == p) lane.card = c;
            }
            require(lane.card != null && lane.card.getSpellCardNumber() == entry.id(), "card entity for " + entry.name());
            require(lane.card.circle != null, "player cards get a magic circle: " + entry.name());
            lanes.add(lane);
            i++;
        }
        phase = Phase.CARDS;
        ticks = 0;
    }

    private static void tickCards() {
        boolean allDone = true;
        for (Lane lane : lanes) {
            if (lane.removedAt < 0) {
                if (lane.card.isRemoved()) lane.removedAt = ticks;
                else allDone = false;
            }
        }
        if (!allDone) {
            require(ticks < 400, "cards still running after 400 ticks");
            return;
        }
        StringBuilder summary = new StringBuilder();
        for (Lane lane : lanes) {
            int end = lane.entry.create().getEndTime();
            int shots = SPAWNED.getOrDefault(lane.player.getUUID(), 0);
            require(lane.removedAt <= end + 3, lane.entry.name() + " ran " + lane.removedAt + " ticks, end " + end);
            require(lane.card.circle.isRemoved(), "circle removed with " + lane.entry.name());
            if (SILENT_CARDS.contains(lane.entry.id())) {
                require(shots == 0, lane.entry.name() + " fires nothing in X1, saw " + shots);
            } else {
                require(shots > 0, lane.entry.name() + " fired no danmaku");
            }
            summary.append(lane.entry.id()).append(':').append(shots).append(' ');
        }
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P11_CARDS_PASS cards={} shots={}", lanes.size(), summary.toString().trim());
        startBonus();
    }

    // 3. A shot whose (non-player) user dies leaves a shot material (it vanishes again without a player in 20).
    // A mob user (death animation, still present) and a user removed at once (1.20.1 getOwner() drops it).
    private static void startBonus() {
        Husk mob = EntityType.HUSK.create(level);
        mob.setNoAi(true);
        ArmorStand stand = EntityType.ARMOR_STAND.create(level);
        bonusAt = new Vec3d(bx + 40.0D, by + 3.0D, bz + 8.0D);
        int i = 0;
        for (net.minecraft.world.entity.LivingEntity owner : List.<net.minecraft.world.entity.LivingEntity>of(mob, stand)) {
            owner.moveTo(bx + 40.0D + i * 6.0D, by, bz + 8.0D, 0F, 0F);
            require(level.addFreshEntity(owner), "bonus owner");
            THShotEntity shot = new THShotEntity(level, owner, new Vec3d(bonusAt.x() + i * 6.0D, bonusAt.y(), bonusAt.z()),
                    new Vec3d(1, 0, 0), 0F, new Vec3d(0, 1, 0), 0F, 9999, 0D, 0D, 0D, Vec3d.ZERO,
                    X1ShotData.shot(X1ShotTables.FORM_SMALL, X1ShotTables.RED, 0, 200, 0));
            require(level.addFreshEntity(shot), "bonus shot");
            i++;
        }
        mob.kill();
        stand.kill();
        require(stand.isRemoved() && !mob.isRemoved(), "armor stand removed at once, husk still dying");
        phase = Phase.BONUS;
        ticks = 0;
    }

    private static void tickBonus() {
        if (materialsSpawned < 2) {
            require(ticks < 20, "shot materials after the shots' users died: " + materialsSpawned + " of 2");
            return;
        }
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P11_BONUS_PASS materials={} afterTicks={}", materialsSpawned, ticks);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P11_RUNTIME_SCENARIO_PASS");
        phase = Phase.DONE;
        ScenarioShutdown.finished(level.getServer(), ENV);
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P11 scenario failed: " + what);
    }
}
