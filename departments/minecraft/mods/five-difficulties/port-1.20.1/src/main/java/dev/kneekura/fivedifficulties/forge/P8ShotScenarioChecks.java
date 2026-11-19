package dev.kneekura.fivedifficulties.forge;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.item.THShotItem;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
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

import java.util.List;

/**
 * P8 world-mutating dedicated-server scenario for the generic THShot backend,
 * enabled by FIVE_DIFFICULTIES_P8_RUNTIME_SCENARIO=1. Needs no private assets.
 */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P8ShotScenarioChecks {
    public static final String PASS_MARKER = "FIVE_DIFFICULTIES_P8_RUNTIME_SCENARIO_PASS";

    private enum Phase { IDLE, MOTION, END_TIME, HIT, ITEMS, DONE }

    private static Phase phase = Phase.IDLE;
    private static ServerLevel level;
    private static ArmorStand owner;
    private static THShotEntity shot;
    private static X1ShotMotion replica;
    private static int replicaAnimation;
    private static int replicaTicks;
    private static int phaseTicks;
    private static Husk target;
    private static float targetStartHealth;
    private static double baseX, baseY, baseZ;

    private P8ShotScenarioChecks() {}

    private static boolean enabled() {
        return "1".equals(System.getenv("FIVE_DIFFICULTIES_P8_RUNTIME_SCENARIO"));
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        int x = spawn.getX() - 24, z = spawn.getZ();
        baseX = x + 0.5D;
        baseZ = z + 0.5D;
        baseY = level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
        owner = EntityType.ARMOR_STAND.create(level);
        owner.moveTo(baseX, baseY, baseZ, 0F, 0F);
        owner.setNoGravity(true);
        require(level.addFreshEntity(owner), "owner armor stand");
        startMotion();
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (!enabled() || event.phase != TickEvent.Phase.END || phase == Phase.IDLE || phase == Phase.DONE) return;
        try {
            switch (phase) {
                case MOTION -> tickMotion();
                case END_TIME -> tickEndTime();
                case HIT -> tickHit();
                case ITEMS -> runItems();
                default -> {}
            }
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P8_RUNTIME_SCENARIO_FAIL", failure);
            phase = Phase.DONE;
            ScenarioShutdown.failed(level.getServer());
            throw failure;
        }
    }

    // 1. Live shot positions must equal the pure X1 kernel tick for tick (delay + acceleration + gravity).
    private static void startMotion() {
        Vec3d pos = new Vec3d(baseX + 1.5D, baseY + 8.0D, baseZ);
        Vec3d angle = new Vec3d(1, 0, 0);
        Vec3d rotate = new Vec3d(0, 1, 0);
        Vec3d gravity = new Vec3d(0, -0.01D, 0);
        X1ShotData data = X1ShotData.shot(X1ShotTables.FORM_SMALL, X1ShotTables.BLUE, X1ShotTables.SIZE[0],
                X1ShotTables.DAMAGE[0], 3, 80, 0);
        shot = new THShotEntity(level, owner, pos, angle, 0F, rotate, 0F, 9999, 0.1D, 0.5D, 0.15D, gravity, data);
        require(level.addFreshEntity(shot), "motion shot added");
        replica = new X1ShotMotion(pos, angle, rotate, 0F, 9999, 0.1D, 0.5D, 0.15D, gravity, 0);
        replicaAnimation = X1ShotMotion.initialAnimationCount(3);
        replicaTicks = 0;
        phase = Phase.MOTION;
        phaseTicks = 0;
    }

    private static void tickMotion() {
        X1ShotMotion.Hooks hooks = new X1ShotMotion.Hooks() {
            public boolean authoritative() { return true; }
            public int animationCount() { return replicaAnimation; }
            public void setAnimationCount(int value) { replicaAnimation = value; }
        };
        while (replicaTicks < shot.tickCount) replica.tick(++replicaTicks, hooks);
        require(shot.getX() == replica.position.x() && shot.getY() == replica.position.y()
                        && shot.getZ() == replica.position.z(),
                "tick " + shot.tickCount + " live=" + shot.position() + " x1=" + replica.position);
        require(shot.getAnimationCount() == replicaAnimation, "animation counter");
        if (shot.tickCount <= 3) {
            require(shot.getX() == baseX + 1.5D, "no movement during delay");
        }
        require(++phaseTicks < 60, "motion shot stopped ticking");
        if (shot.tickCount < 12) return; // 3 delay ticks + 9 moving ticks
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P8_MOTION_PASS ticks={} x={} y={} speed={}",
                shot.tickCount, shot.getX(), shot.getY(), replica.speed());
        shot.discard();

        X1ShotData data = X1ShotData.shot(X1ShotTables.FORM_TINY, X1ShotTables.RED, X1ShotTables.SIZE[1],
                X1ShotTables.DAMAGE[1], 0, 10, 0);
        shot = new THShotEntity(level, owner, new Vec3d(baseX + 1.5D, baseY + 8.0D, baseZ), new Vec3d(0, 0, 1),
                0F, new Vec3d(0, 1, 0), 0F, 9999, 0.05D, 0.05D, 0D, Vec3d.ZERO, data);
        require(level.addFreshEntity(shot), "end-time shot added");
        phase = Phase.END_TIME;
        phaseTicks = 0;
    }

    // 2. end=10 with delay 0: X1 removes the shot during tick 13 (end includes the +2 counter lag).
    private static void tickEndTime() {
        if (!shot.isRemoved()) {
            require(++phaseTicks < 40, "end-time shot never removed");
            return;
        }
        require(shot.tickCount == 13, "end=10 shot removed at tick " + shot.tickCount + ", X1 expects 13");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P8_END_TIME_PASS removedAtTick={}", shot.tickCount);

        target = EntityType.HUSK.create(level);
        target.moveTo(baseX + 7.0D, baseY, baseZ, 90F, 0F);
        target.setNoAi(true);
        require(level.addFreshEntity(target), "husk target");
        targetStartHealth = target.getHealth();
        X1ShotData data = X1ShotData.shot(X1ShotTables.FORM_SMALL, X1ShotTables.GREEN);
        shot = new THShotEntity(level, owner, new Vec3d(baseX + 1.5D, baseY + 1.0D, baseZ), new Vec3d(1, 0, 0),
                0F, new Vec3d(0, 1, 0), 0F, 9999, 0.5D, 0.5D, 0D, Vec3d.ZERO, data);
        require(level.addFreshEntity(shot), "hit shot added");
        phase = Phase.HIT;
        phaseTicks = 0;
    }

    // 3. Indirect-magic hit for the X1 SMALL damage with the X1 difficulty multiplier (owner is not a player).
    private static void tickHit() {
        if (!shot.isRemoved()) {
            require(++phaseTicks < 40, "hit shot never resolved");
            return;
        }
        float expected = shot.getShotDamageWithDifficulty();
        float dealt = targetStartHealth - target.getHealth();
        require(Math.abs(dealt - expected) < 1.0e-4F, "husk took " + dealt + ", X1 expects " + expected);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P8_HIT_PASS difficulty={} damage={} ticks={}",
                level.getDifficulty(), dealt, shot.tickCount);
        target.discard();
        phase = Phase.ITEMS;
    }

    // 4. ItemTHShot: each X1 DanmakuForm through a real item use spawns the X1 shot count.
    private static void runItems() {
        FakePlayer player = FakePlayerFactory.getMinecraft(level);
        player.moveTo(baseX, baseY + 20.0D, baseZ, -90F, 0F);
        int[][] cases = { // {DanmakuForm, Number, expected shots}
                {0, 3, 3}, {1, 7, 7}, {2, 5, 5}, {3, 8, 8}, {4, 8, 8}, {5, 6, 6}};
        THShotItem item = (THShotItem) PortRegistries.SMALL_SHOT.get();
        for (int[] c : cases) {
            ItemStack stack = new ItemStack(item, 4);
            CompoundTag tag = stack.getOrCreateTag();
            tag.putByte("DanmakuForm", (byte) c[0]);
            tag.putShort("Number", (short) c[1]);
            tag.putByte("Color", (byte) X1ShotTables.RAINBOW);
            player.setItemInHand(InteractionHand.MAIN_HAND, stack);
            item.use(level, player, InteractionHand.MAIN_HAND);
            List<THShotEntity> spawned = level.getEntitiesOfClass(THShotEntity.class,
                    player.getBoundingBox().inflate(4.0D), s -> s.getOwner() == player);
            require(spawned.size() == c[2], "form " + c[0] + " spawned " + spawned.size() + " expected " + c[2]);
            require(stack.getCount() == 3, "survival use consumes one shot item");
            spawned.forEach(THShotEntity::discard);
        }
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P8_ITEM_FORMS_PASS forms=6");
        FiveDifficultiesPort.LOGGER.info(PASS_MARKER);
        owner.discard();
        phase = Phase.DONE;
        ScenarioShutdown.finished(level.getServer(), "FIVE_DIFFICULTIES_P8_RUNTIME_SCENARIO");
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P8 scenario failed: " + what);
    }
}
