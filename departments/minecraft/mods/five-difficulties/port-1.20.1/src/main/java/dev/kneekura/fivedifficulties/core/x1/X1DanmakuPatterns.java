package dev.kneekura.fivedifficulties.core.x1;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Port of X1 {@code DanmakuPatternRegistry}: the fairy danmaku table, chosen once by the danmaku level (X1 reads
 * it at start-up). A form value is {@code form * 8 + colour} as in THShotLib's SMALL[] / LASER[] tables.
 */
public final class X1DanmakuPatterns {
    public record Pattern(int danmaku, int span, float speed, int form) {}

    public static final List<String> PATTERN = new ArrayList<>();
    public static final Map<String, Pattern> TABLE = new HashMap<>();
    private static int builtFor = Integer.MIN_VALUE;

    private X1DanmakuPatterns() {}

    private static int f(int form, int color) {
        return form * 8 + color;
    }

    private static void reg(String name, int danmaku, int span, float speed, int form) {
        TABLE.put(name, new Pattern(danmaku, span, speed, form));
        PATTERN.add(name);
    }

    /** setDanmakuPattern for the given danmaku level (rebuilt only when the level changes). */
    public static synchronized void ensure(int level) {
        if (builtFor == level) return;
        builtFor = level;
        PATTERN.clear();
        TABLE.clear();
        int R = X1ShotTables.RED, B = X1ShotTables.BLUE, G = X1ShotTables.GREEN, Y = X1ShotTables.YELLOW,
                P = X1ShotTables.PURPLE, A = X1ShotTables.AQUA, O = X1ShotTables.ORANGE;
        int SMALL = X1ShotTables.FORM_SMALL, TINY = X1ShotTables.FORM_TINY, MEDIUM = X1ShotTables.FORM_MEDIUM,
                CIRCLE = X1ShotTables.FORM_CIRCLE, CRYSTAL = X1ShotTables.FORM_CRYSTAL, KUNAI = X1ShotTables.FORM_KUNAI,
                BIG = X1ShotTables.FORM_BIG, LIGHT = X1ShotTables.FORM_LIGHT, LASER = 64;
        switch (level) {
            case 1 -> {
                reg("000", 0, 38, 0.3F, f(SMALL, B));
                reg("001", 2003, 50, 0.2F, f(SMALL, R));
                reg("002", 1902, 50, 0.2F, f(SMALL, G));
                reg("003", 5015, 40, 0.1F, f(SMALL, Y));
                reg("004", 5, 40, 0.2F, f(CIRCLE, P));
                reg("005", 3225, 50, 0.2F, f(TINY, A));
                reg("006", 4030, 50, 0.15F, f(CRYSTAL, O));
                reg("007", 300, 50, 0.20F, f(KUNAI, A));
                reg("064", 0, 38, 0.3F, f(LASER, R));
            }
            case 2 -> {
                reg("000", 0, 30, 0.3F, f(SMALL, B));
                reg("001", 2007, 50, 0.2F, f(SMALL, R));
                reg("002", 1804, 50, 0.2F, f(SMALL, G));
                reg("003", 5021, 40, 0.2F, f(SMALL, Y));
                reg("004", 7, 35, 0.2F, f(CIRCLE, P));
                reg("005", 3420, 45, 0.25F, f(TINY, A));
                reg("006", 4220, 50, 0.15F, f(CRYSTAL, O));
                reg("007", 400, 45, 0.25F, f(KUNAI, A));
                reg("064", 0, 30, 0.3F, f(LASER, R));
            }
            case 3 -> {
                reg("000", 0, 22, 0.4F, f(SMALL, B));
                reg("001", 2011, 40, 0.3F, f(SMALL, R));
                reg("002", 1608, 40, 0.4F, f(SMALL, G));
                reg("003", 5027, 40, 0.3F, f(MEDIUM, Y));
                reg("004", 11, 25, 0.4F, f(CIRCLE, P));
                reg("005", 3620, 35, 0.3F, f(SMALL, A));
                reg("006", 4415, 50, 0.25F, f(CRYSTAL, O));
                reg("007", 500, 40, 0.35F, f(KUNAI, A));
                reg("064", 0, 26, 0.4F, f(LASER, R));
            }
            case 4 -> {
                reg("000", 0, 3, 0.5F, f(SMALL, B));
                reg("001", 2015, 35, 0.4F, f(MEDIUM, R));
                reg("002", 1410, 30, 0.6F, f(MEDIUM, G));
                reg("003", 5027, 40, 0.4F, f(BIG, Y));
                reg("004", 19, 10, 0.6F, f(CIRCLE, P));
                reg("005", 3915, 24, 0.4F, f(LIGHT, A));
                reg("006", 4810, 35, 0.35F, f(CRYSTAL, O));
                reg("007", 700, 15, 0.45F, f(KUNAI, A));
                reg("064", 0, 20, 0.5F, f(LASER, R));
            }
            default -> {
                reg("000", 0, 999999, 0.0F, 0);
                reg("001", 1, 999999, 0.0F, 0);
                reg("002", 2, 999999, 0.0F, 0);
            }
        }
    }
}
