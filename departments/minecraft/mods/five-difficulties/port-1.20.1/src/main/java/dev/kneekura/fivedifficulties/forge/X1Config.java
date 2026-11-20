package dev.kneekura.fivedifficulties.forge;

import net.minecraftforge.common.ForgeConfigSpec;

/**
 * Port of X1 {@code THKaguyaConfig}: the same categories, keys, defaults and clamps. The "EntityID"
 * category has no meaning in 1.20 (entities are registered by name) and is not ported. Values read
 * before the config is loaded fall back to X1's defaults.
 */
public final class X1Config {
    public static final ForgeConfigSpec SPEC;

    private static final ForgeConfigSpec.BooleanValue USE_MASTER_SPARK, MASTER_SPARK_DESTROYS_BLOCKS,
            CAN_USE_WALL_PASSING_CHISEL, USE_TIME_STOP_EFFECT, USE_DEFAULT_GAP_SE, DANMAKU_ONE_KILL_MODE,
            SPAWN_DANMAKU_MOB, SPAWN_FAIRY, SPAWN_PHANTOM, SPAWN_BOSS, SPAWN_HANABEEPER, RECIPELESS_ITEMS_RECIPE;
    private static final ForgeConfigSpec.IntValue SHOT_MAX_NUMBER, LASER_MAX_NUMBER, SPELL_CARD_VOL, MASTER_SPARK_VOL,
            HISOUTEN_VOL, DOWN_VOL, FAIRY_SPAWN_RATE, DANMAKU_LEVEL, DANMAKU_ACCURACY;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();
        b.push("Limit");
        USE_MASTER_SPARK = b.define("Use Master Spark", true);
        MASTER_SPARK_DESTROYS_BLOCKS = b.define("Master Spark Destroys Blocks", true);
        CAN_USE_WALL_PASSING_CHISEL = b.define("Can Use Wall-Passing Chisel", true);
        SHOT_MAX_NUMBER = b.defineInRange("Shot Max Number", 32, 1, Integer.MAX_VALUE);
        LASER_MAX_NUMBER = b.defineInRange("Laser Max Number", 8, 1, Integer.MAX_VALUE);
        b.pop();
        b.push("Effect");
        USE_TIME_STOP_EFFECT = b.define("Appear Time stop effect", true);
        USE_DEFAULT_GAP_SE = b.define("Use default Gap(Sukima)SE", true);
        b.pop();
        b.push("SE vol");
        SPELL_CARD_VOL = b.defineInRange("Spell Card Vol", 50, Integer.MIN_VALUE, 500);
        MASTER_SPARK_VOL = b.defineInRange("Master Spark Vol", 50, Integer.MIN_VALUE, 500);
        HISOUTEN_VOL = b.defineInRange("Hisouten Vol", 20, Integer.MIN_VALUE, 500);
        DOWN_VOL = b.defineInRange("Down Vol", 50, Integer.MIN_VALUE, 500);
        b.pop();
        b.push("Danmaku");
        DANMAKU_ONE_KILL_MODE = b.define("Danmaku 1 Kill Mode", false);
        SPAWN_DANMAKU_MOB = b.define("Spawn Danmaku Mob", true);
        SPAWN_FAIRY = b.define("Spawn Fairy", true);
        SPAWN_PHANTOM = b.define("Spawn Phantom", true);
        SPAWN_BOSS = b.define("Spawn Danmaku Mob Boss", true);
        FAIRY_SPAWN_RATE = b.defineInRange("Fairy Spawn Rate(%)", 50, Integer.MIN_VALUE, Integer.MAX_VALUE);
        DANMAKU_LEVEL = b.defineInRange("Danmaku Level", 2, 0, 4);
        DANMAKU_ACCURACY = b.defineInRange("Hit Rate of Enemy Danmaku(row=0,high=100)", 80, Integer.MIN_VALUE, Integer.MAX_VALUE);
        b.pop();
        b.push("Other");
        SPAWN_HANABEEPER = b.define("Spawn Hanabeeper", false);
        RECIPELESS_ITEMS_RECIPE = b.define("Add Recipeless Items Recipe", false);
        b.pop();
        SPEC = b.build();
    }

    private X1Config() {}

    private static boolean get(ForgeConfigSpec.BooleanValue v, boolean fallback) {
        return SPEC.isLoaded() ? v.get() : fallback;
    }

    private static int get(ForgeConfigSpec.IntValue v, int fallback) {
        return SPEC.isLoaded() ? v.get() : fallback;
    }

    public static boolean usingMasterSpark() { return get(USE_MASTER_SPARK, true); }
    public static boolean masterSparkDestroysBlocks() { return get(MASTER_SPARK_DESTROYS_BLOCKS, true); }
    public static boolean canUseWallPassingChisel() { return get(CAN_USE_WALL_PASSING_CHISEL, true); }
    public static int shotMaxNumber() { return get(SHOT_MAX_NUMBER, 32); }
    public static int laserMaxNumber() { return get(LASER_MAX_NUMBER, 8); }
    public static boolean useTimeStopEffect() { return get(USE_TIME_STOP_EFFECT, true); }
    public static boolean useDefaultGapSE() { return get(USE_DEFAULT_GAP_SE, true); }
    /** SE volumes: the setting / 100 (X1 caps them at 500). */
    public static float spellCardVol() { return get(SPELL_CARD_VOL, 50) / 100F; }
    public static float masterSparkVol() { return get(MASTER_SPARK_VOL, 50) / 100F; }
    public static float hisoutenVol() { return get(HISOUTEN_VOL, 20) / 100F; }
    public static float downVol() { return get(DOWN_VOL, 50) / 100F; }
    public static boolean danmakuOneKillMode() { return get(DANMAKU_ONE_KILL_MODE, false); }
    public static boolean spawnDanmakuMob() { return get(SPAWN_DANMAKU_MOB, true); }
    public static boolean spawnFairy() { return get(SPAWN_FAIRY, true); }
    public static boolean spawnPhantom() { return get(SPAWN_PHANTOM, true); }
    public static boolean spawnBoss() { return get(SPAWN_BOSS, true); }
    /** X1 stores 100 − the configured percentage. */
    public static int fairySpawnRate() { return 100 - get(FAIRY_SPAWN_RATE, 50); }
    /** X1 assigns THKaguyaConfig.danmakuLevel at run time (Miko); like X1 it lives in memory only, not the file. */
    private static Integer danmakuLevelOverride;

    public static int danmakuLevel() { return danmakuLevelOverride != null ? danmakuLevelOverride : get(DANMAKU_LEVEL, 2); }

    public static void setDanmakuLevelInMemory(int level) { danmakuLevelOverride = level; }
    public static float danmakuAccuracy() { return get(DANMAKU_ACCURACY, 80); }
    public static boolean spawnHanabeeper() { return get(SPAWN_HANABEEPER, false); }
    public static boolean recipelessItemsRecipe() { return get(RECIPELESS_ITEMS_RECIPE, false); }
}
