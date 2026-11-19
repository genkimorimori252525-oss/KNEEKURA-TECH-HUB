package dev.kneekura.fivedifficulties.forge;

import com.mojang.authlib.GameProfile;
import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.SakuyaControllerKind;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.forge.entity.DanmakuCreeperEntity;
import dev.kneekura.fivedifficulties.forge.entity.MiniHakkeroEntity;
import dev.kneekura.fivedifficulties.forge.entity.MusouFuuinEntity;
import dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity;
import dev.kneekura.fivedifficulties.forge.entity.SukimaEntity;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THSetLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardDeclaration;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardRegistry;
import dev.kneekura.fivedifficulties.forge.spellcard.cards.EntityCards;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Chicken;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.*;

/** P12 dedicated-server scenario for the cards with their own entities (FIVE_DIFFICULTIES_P12_RUNTIME_SCENARIO=1). */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P12SpellCardEntityScenario {
    public static final String ENV = "FIVE_DIFFICULTIES_P12_RUNTIME_SCENARIO";
    private static final int[] CARDS = {0, 1, 8, 10, 15};

    private enum Phase { IDLE, CARD, FAFRO, CREEPER, NUCLEAR, DONE }

    private static Phase phase = Phase.IDLE;
    private static ServerLevel level;
    private static double bx, by, bz;
    private static int ticks;
    private static final Map<String, Integer> SEEN = new HashMap<>();
    private static final StringBuilder SUMMARY = new StringBuilder();

    // card phase
    private static int cardIndex;
    private static net.minecraft.world.entity.LivingEntity user;
    private static Husk target;
    private static SpellCardEntity card;
    private static int removedAt;
    private static double musouMin;
    private static MiniHakkeroEntity hakkero;
    private static SakuyaTimeControllerEntity watch;
    // object phases
    private static DanmakuCreeperEntity creeper;
    private static int creeperBurstAt;
    private static NuclearShotEntity nuclear;
    private static Husk victim;
    private static int victimHitAt;

    private P12SpellCardEntityScenario() {}

    private static boolean enabled() {
        return "1".equals(System.getenv(ENV));
    }

    private static void seen(String key) {
        SEEN.merge(key, 1, Integer::sum);
    }

    private static int count(String key) {
        return SEEN.getOrDefault(key, 0);
    }

    @SubscribeEvent
    public static void onJoin(EntityJoinLevelEvent event) {
        if (!enabled() || event.getLevel().isClientSide || phase == Phase.IDLE || phase == Phase.DONE) return;
        Entity e = event.getEntity();
        if (Math.abs(e.getX() - bx) > 48 || Math.abs(e.getZ() - bz) > 48) return;
        if (e instanceof MusouFuuinEntity) seen("musou");
        else if (e instanceof NuclearShotEntity) {
            seen("nuclear");
            if (phase == Phase.FAFRO) event.setCanceled(true); // only its creation is under test here
        } else if (e instanceof THSetLaserEntity s) {
            if (s.getShotId() == 24) seen("spark");
        } else if (e instanceof THLaserEntity l) {
            if (l.getShotColor() == PURPLE) seen("purple_laser");
        } else if (e instanceof THShotEntity s) {
            if (s.getOwner() instanceof DanmakuCreeperEntity) seen("creeper_shot");
            else if (s.getShotForm() == FORM_STAR) seen("star");
            else if (s.getShotForm() == FORM_KNIFE && s.getShotColor() == GREEN && phase == Phase.CARD
                    && CARDS[cardIndex] == 8) seen("green_knife");
            else if (s.getShotForm() == FORM_KNIFE) seen("knife");
            else if (s.getShotForm() == FORM_CIRCLE && s.getShotColor() == AQUA) seen("aqua");
        } else if (e instanceof MiniHakkeroEntity) seen("hakkero");
        else if (e instanceof SakuyaTimeControllerEntity) seen("watch");
        else if (e instanceof SukimaEntity) seen("sukima");
        else if (e instanceof DanmakuCreeperEntity) seen("hanabeeper");
        else if (e instanceof Creeper) seen("creeper");
        else if (e instanceof Chicken) seen("chicken");
        else if (e instanceof ItemEntity item && item.getItem().is(Items.COD)) seen("cod");
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        // 70 blocks out on the side opposite P11, beyond the 40-block reach of declarations and the time stop.
        bx = spawn.getX() + 70 + 0.5D;
        bz = spawn.getZ() + 70 + 0.5D;
        by = level.getHeight(Heightmap.Types.MOTION_BLOCKING, spawn.getX() + 70, spawn.getZ() + 70);
        require(X1SpellCardRegistry.size() == 35, "X1 registers 35 spell cards, port has " + X1SpellCardRegistry.size());
        for (X1SpellCardRegistry.Entry e : X1SpellCardRegistry.all()) {
            require(PortRegistries.SPELL_CARD_ITEMS.containsKey(e.id()), "item for card " + e.id());
        }
        cardIndex = 0;
        startCard();
    }

    private static FakePlayer player(int n) {
        FakePlayer p = FakePlayerFactory.get(level, new GameProfile(
                UUID.fromString(String.format("00000000-0000-0000-0000-0000f912%04d", n)), "[FDP12-" + n + "]"));
        p.moveTo(bx, by, bz, 0F, 0F); // facing +Z
        p.getAbilities().instabuild = true;
        return p;
    }

    private static Husk husk(double x, double y, double z, boolean invulnerable) {
        Husk h = EntityType.HUSK.create(level);
        h.moveTo(x, y, z, 180F, 0F);
        h.setNoAi(true);
        h.setInvulnerable(invulnerable);
        require(level.addFreshEntity(h), "husk");
        return h;
    }

    private static void clearArea() {
        for (Entity e : level.getEntities((Entity) null, new AABB(bx - 48, by - 16, bz - 48, bx + 48, by + 64, bz + 48),
                e -> !(e instanceof net.minecraft.world.entity.player.Player))) {
            e.discard();
        }
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (!enabled() || event.phase != TickEvent.Phase.END || phase == Phase.IDLE || phase == Phase.DONE) return;
        try {
            ticks++;
            switch (phase) {
                case CARD -> tickCard();
                case FAFRO -> tickFafro();
                case CREEPER -> tickCreeper();
                case NUCLEAR -> tickNuclear();
                default -> {}
            }
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P12_RUNTIME_SCENARIO_FAIL phase={} card={}", phase,
                    phase == Phase.CARD ? CARDS[cardIndex] : -1, failure);
            phase = Phase.DONE;
            EntityCards.Fafrotskies.today = LocalDate::now;
            ScenarioShutdown.failed(level.getServer());
            throw failure;
        }
    }

    // ---- 1. the five cards, one at a time ----

    private static void startCard() {
        clearArea();
        SEEN.clear();
        int id = CARDS[cardIndex];
        user = player(id);
        // X1's watch resolves its user in the world and ends when no player is in range, so Satuzin Doll's
        // user joins the level (as the P6 scenario's does).
        if (id == 8) level.addNewPlayer((FakePlayer) user);
        target = husk(bx, by, bz + 6.0D, true);
        ItemStack stack = new ItemStack(PortRegistries.SPELL_CARD_ITEMS.get(id).get());
        require(X1SpellCardDeclaration.check(level, stack, user, id, X1SpellCardDeclaration.NORMAL, true), "declare " + id);
        card = null;
        for (SpellCardEntity c : level.getEntitiesOfClass(SpellCardEntity.class, user.getBoundingBox().inflate(4.0D))) {
            if (c.user == user) card = c;
        }
        require(card != null && card.getSpellCardNumber() == id, "card entity " + id);
        removedAt = -1;
        musouMin = Double.MAX_VALUE;
        hakkero = null;
        watch = null;
        phase = Phase.CARD;
        ticks = 0;
    }

    private static void tickCard() {
        int id = CARDS[cardIndex];
        int end = X1SpellCardRegistry.get(id).create().getEndTime();
        if (id == 0) {
            // the orbs home on the eyes; they start at the user, 6 blocks away
            for (MusouFuuinEntity m : level.getEntitiesOfClass(MusouFuuinEntity.class, target.getBoundingBox().inflate(48))) {
                musouMin = Math.min(musouMin, m.position().distanceTo(target.getEyePosition()));
            }
        }
        if (id == 1 && hakkero == null) {
            var found = level.getEntitiesOfClass(MiniHakkeroEntity.class, user.getBoundingBox().inflate(4));
            if (!found.isEmpty()) hakkero = found.get(0);
        }
        if (id == 8 && watch == null) {
            var found = level.getEntitiesOfClass(SakuyaTimeControllerEntity.class, user.getBoundingBox().inflate(8));
            if (!found.isEmpty()) watch = found.get(0);
        }
        if (removedAt < 0) {
            if (card.isRemoved()) removedAt = ticks;
            require(ticks < 400, "card " + id + " still running after 400 ticks");
            return;
        }
        if (ticks < removedAt + 12) return; // let late gaps fire / bursts land
        switch (id) {
            case 0 -> {
                require(removedAt <= end + 3, "Musou Fuuin ran " + removedAt);
                require(count("musou") == 17, "Musou Fuuin orbs " + count("musou") + " (X1: every 2nd tick of 15..48)");
                require(musouMin < 3.0D, "Musou Fuuin orbs never reached the target, min distance " + musouMin);
                SUMMARY.append(String.format("0:orbs=%d,min=%.2f ", count("musou"), musouMin));
            }
            case 1 -> {
                require(removedAt <= end + 3, "Master Spark ran " + removedAt);
                require(count("hakkero") == 1 && count("spark") == 1, "hakkero " + count("hakkero") + " spark " + count("spark"));
                require(hakkero != null && hakkero.isRemoved(), "Mini Hakkero gone at tick 109");
                require(count("star") == 7 * 69, "Master Spark stars " + count("star") + " (X1: 7 per tick of 30..98)");
                SUMMARY.append("1:hakkero=1,spark=1,stars=").append(count("star")).append(' ');
            }
            case 8 -> {
                require(count("watch") == 1 && watch != null, "Satuzin Doll time stop " + count("watch"));
                require(watch.getControllerKind() == SakuyaControllerKind.SPELL_CARD && watch.getSourceEntity() == user,
                        "spell-card time stop of the user");
                require(count("green_knife") > 0, "no green knives during the time stop (blue/red knives " + count("knife")
                        + ", card ran " + removedAt + ", end " + end + ", stop active " + watch.isActiveAt(
                        dev.kneekura.fivedifficulties.forge.timestop.SakuyaTimeStopRuntime.logicalTick(level)) + ")");
                require(removedAt > end + 3 && removedAt <= end + 61 + 5,
                        "Satuzin Doll end pushed by the time stop: ran " + removedAt + ", end " + end);
                level.removePlayerImmediately((FakePlayer) user, Entity.RemovalReason.DISCARDED);
                SUMMARY.append("8:stop=1,green=").append(count("green_knife")).append(",ran=").append(removedAt).append(' ');
            }
            case 10 -> {
                require(removedAt <= end + 3, "Hikouchuu Nest ran " + removedAt);
                require(count("sukima") > 60 && count("sukima") <= 160, "Hikouchuu Nest gaps " + count("sukima"));
                require(count("purple_laser") == count("sukima"),
                        "each gap fires one laser: gaps " + count("sukima") + " lasers " + count("purple_laser"));
                SUMMARY.append("10:gaps=").append(count("sukima")).append(",lasers=").append(count("purple_laser")).append(' ');
            }
            case 15 -> {
                require(removedAt <= end + 3, "Fafrotskies ran " + removedAt);
                require(count("aqua") == 10, "Fafrotskies shots " + count("aqua"));
                int outcomes = (count("knife") == 80 ? 1 : 0) + (count("cod") == 10 ? 1 : 0)
                        + (count("creeper") == 10 ? 1 : 0) + (count("chicken") == 10 ? 1 : 0);
                require(outcomes == 1, "one rolled outcome for all ten: knives " + count("knife") + " cod " + count("cod")
                        + " creepers " + count("creeper") + " chickens " + count("chicken"));
                SUMMARY.append("15:knives=").append(count("knife")).append(",cod=").append(count("cod"))
                        .append(",creepers=").append(count("creeper")).append(",chickens=").append(count("chicken"));
            }
            default -> {}
        }
        cardIndex++;
        if (cardIndex < CARDS.length) {
            startCard();
        } else {
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P12_CARDS_PASS {}", SUMMARY.toString().trim());
            startFafro();
        }
    }

    // ---- 2. every Fafrotskies outcome, the dated ones through the date seam ----

    private static final double[] PATTERNS = {50, 75, 85, 95, 50, 50};

    private static void startFafro() {
        clearArea();
        SEEN.clear();
        user = player(1500);
        spawnFafro(0, 4);
        phase = Phase.FAFRO;
        ticks = 0;
    }

    private static void spawnFafro(int from, int to) {
        for (int i = from; i < to && i < PATTERNS.length; i++) {
            THShotEntity s = X1Danmaku.createShotEntity(user, user, new Vec3d(bx + (i - 3) * 4.0D, by + 4.0D, bz + 4.0D),
                    new Vec3d(0, 1, 0), 0F, new Vec3d(0, 1, 0), 0F, 9999, 0.0001D, PATTERNS[i], 0.0D, Vec3d.ZERO,
                    X1ShotData.shot(FORM_CIRCLE, AQUA, 0.4F, 6.0F, 0, 3, EntityCards.Fafrotskies.SPECIAL_FAFUROTSKIES01));
            require(s != null, "fafrotskies shot " + i);
        }
    }

    private static void tickFafro() {
        if (ticks == 6) {
            require(count("knife") == 8 && count("cod") == 1 && count("creeper") == 1 && count("chicken") == 1,
                    "pattern outcomes: knives " + count("knife") + " cod " + count("cod") + " creeper " + count("creeper")
                            + " chicken " + count("chicken"));
            EntityCards.Fafrotskies.today = () -> LocalDate.of(2026, 12, 25);
            spawnFafro(4, 5);
        } else if (ticks == 12) {
            require(count("hanabeeper") == 1, "Dec 25 turns the shot into a Hanabeeper");
            EntityCards.Fafrotskies.today = () -> LocalDate.of(2027, 1, 2);
            spawnFafro(5, 6);
        } else if (ticks == 18) {
            require(count("nuclear") == 1, "Jan 1-3 turns the shot into a nuclear shot");
            EntityCards.Fafrotskies.today = LocalDate::now;
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P12_FAFROTSKIES_PASS knives=8 cod=1 creeper=1 chicken=1 dec25=hanabeeper jan2=nuclear");
            startCreeper();
        }
    }

    // ---- 3. Hanabeeper: bursts after its own 30-tick fuse instead of exploding, then dies ----

    private static void startCreeper() {
        clearArea();
        SEEN.clear();
        creeper = PortRegistries.DANMAKU_CREEPER.get().create(level);
        creeper.moveTo(bx, by, bz + 10.0D, 0F, 0F);
        creeper.setNoAi(true); // no swell goal resetting the state: it stays lit
        require(level.addFreshEntity(creeper), "hanabeeper");
        creeper.setSwellDir(1);
        creeperBurstAt = -1;
        phase = Phase.CREEPER;
        ticks = 0;
    }

    private static void tickCreeper() {
        if (creeperBurstAt < 0) {
            if (count("creeper_shot") > 0) creeperBurstAt = ticks;
            require(ticks < 60, "Hanabeeper never burst");
            return;
        }
        if (!creeper.isRemoved()) {
            require(ticks < creeperBurstAt + 120, "Hanabeeper still alive " + (ticks - creeperBurstAt) + " ticks after its burst");
            return;
        }
        require(level.getBlockState(BlockPos.containing(bx, by - 1, bz + 10.0D)).is(Blocks.AIR) == false,
                "Hanabeeper must not blow up the ground");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P12_CREEPER_PASS burstAt={} shots={} removedAfter={}",
                creeperBurstAt, count("creeper_shot"), ticks - creeperBurstAt);
        startNuclear();
    }

    // ---- 4. Nuclear shot: damage = size x 8, flies through what it hits, a wall stops it ----

    private static void startNuclear() {
        clearArea();
        SEEN.clear();
        Husk owner = husk(bx - 6.0D, by, bz + 20.0D, true);
        victim = husk(bx + 4.0D, by, bz + 20.0D, false);
        for (int y = 0; y < 6; y++) {
            level.setBlockAndUpdate(BlockPos.containing(bx + 12.0D, by + y, bz + 20.0D), Blocks.STONE.defaultBlockState());
        }
        nuclear = new NuclearShotEntity(level, owner, new Vec3d(bx, by + 3.0D, bz + 20.0D), new Vec3d(1, 0, 0), 0F,
                new Vec3d(0, 1, 0), 0F, 9999, 0.5D, 0.5D, 0.0D, Vec3d.ZERO, X1ShotData.shot(0, RED, 3.2F, 10.0F, 0, 70, 0));
        nuclear.shootingFlag = true;
        require(level.addFreshEntity(nuclear), "nuclear shot");
        victimHitAt = -1;
        phase = Phase.NUCLEAR;
        ticks = 0;
    }

    private static void tickNuclear() {
        if (victimHitAt < 0 && (!victim.isAlive() || victim.getHealth() < victim.getMaxHealth())) {
            victimHitAt = ticks;
            require(!nuclear.isRemoved(), "the nuclear shot flies on after hitting");
            require(nuclear.shotDamage == 3.2F * 8.0F, "damage is size x 8, got " + nuclear.shotDamage);
        }
        if (!nuclear.isRemoved()) {
            require(ticks < 60, "nuclear shot never stopped by the wall");
            return;
        }
        require(victimHitAt >= 0, "nuclear shot never hit the husk on its path");
        require(nuclear.getX() < bx + 12.0D, "stopped before passing the wall, x " + (nuclear.getX() - bx));
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P12_NUCLEAR_PASS hitAt={} stoppedAt={} x={}", victimHitAt, ticks,
                String.format("%.2f", nuclear.getX() - bx));
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P12_RUNTIME_SCENARIO_PASS");
        phase = Phase.DONE;
        ScenarioShutdown.finished(level.getServer(), ENV);
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P12 scenario failed: " + what);
    }
}
