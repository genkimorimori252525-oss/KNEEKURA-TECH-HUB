package dev.kneekura.fivedifficulties.core.x1;

/**
 * The arithmetic of X1's danmaku crafting table, statement by statement: {@code ContainerDanmakuCrafting}
 * / {@code ContainerDanmakuCraftingLaser.onCraftMatrixChanged} (the result) and {@code SlotDanmakuResult} /
 * {@code SlotLaserResult.onPickupFromSlot} (what each input slot loses when the result is taken).
 * Java's narrowing compound assignments on byte / short are X1's too.
 */
public final class X1DanmakuCrafting {
    private X1DanmakuCrafting() {}

    /** ItemTHShot.sellectbleColor: 1.7.10 dye damage → shot colour. */
    public static final int[] SELECTABLE_COLOR = {7, 0, 2, 0, 1, 4, 5, 7, 7, 4, 2, 3, 5, 4, 6, 7};

    /** What sits in the colour slot. */
    public enum ColorInput { NONE, DYE, GUNPOWDER, DIAMOND }

    /** Material NBT (null fields mean the material had no tag) and the counts in each input slot (0 = empty). */
    public static final class Inputs {
        public boolean laser;
        public int maxNumber;          // THKaguyaConfig.shotMaxNumber / laserMaxNumber
        public int materialCount;      // 0 = no material
        public boolean materialHasTag;
        public short number;
        public byte form;
        public byte speed;
        public byte color = 8;
        public int special;
        public byte gravity;
        public int wayCount, speedCount, gravityCount, boundCount, copyCount;
        public ColorInput colorInput = ColorInput.NONE;
        public int dyeDamage;
        public final boolean[] matrix = new boolean[9];
    }

    /** The result tag (and count); null when there is no result. */
    public record Result(short number, byte form, byte speed, byte color, int special, byte gravity, int count) {}

    public static Result result(Inputs in) {
        short way = 1;
        byte form = 0;
        byte addSpeed = 0;
        byte color = 8;
        byte gravity = 0;
        int special = 0;
        if (in.materialCount > 0 && in.materialHasTag) {
            way = in.number;
            form = in.form;
            addSpeed = in.speed;
            special = in.laser ? 0 : in.special;
            gravity = in.laser ? 0 : in.gravity;
            color = in.color;
        }
        if (in.speedCount > 0) {
            addSpeed += in.speedCount;
            if (addSpeed > 64 || addSpeed < 0) addSpeed = 64;
        }
        if (in.wayCount > 0) {
            way += in.wayCount;
            if (way > in.maxNumber || way < 0) way = (short) in.maxNumber;
        }
        if (!in.laser && in.gravityCount > 0) {
            gravity += in.gravityCount;
            if (gravity > 16 || gravity < 0) gravity = 16;
        }
        if (!in.laser && in.boundCount > 0) {
            int num = in.boundCount;
            if (special >= X1ShotTables.BOUND01 && special <= X1ShotTables.BOUND01 + 3) {
                special = (byte) (special + num);
            } else {
                special = X1ShotTables.BOUND01;
                num--;
                special += num;
            }
            if (special > X1ShotTables.BOUND01 + 3) special = X1ShotTables.BOUND01 + 3;
        }
        boolean[] m = in.matrix;
        if (pattern(m, "....#....")) form = 0;
        else if (pattern(m, ".#..#....")) form = 1;
        else if (pattern(m, "###......")) form = 2;
        else if (pattern(m, "####.####")) form = 3;
        else if (pattern(m, "#########")) {
            if (way > 2) form = 4;
        } else if (pattern(m, ".#.#.#.#.")) {
            if (way > 2) form = 5;
        } else if (pattern(m, ".........")) {
            // an empty grid keeps the material's form
        } else {
            form = -1;
        }
        switch (in.colorInput) {
            case DYE -> color = (byte) SELECTABLE_COLOR[in.dyeDamage % 16];
            case GUNPOWDER -> color = (byte) X1ShotTables.RANDOM;
            case DIAMOND -> color = (byte) X1ShotTables.RAINBOW;
            default -> {}
        }
        if (in.materialCount > 0 && !(form == 4 && way > 32) && form >= 0) {
            int copyNum = 1;
            if (in.copyCount > 0) {
                copyNum = in.copyCount + 1;
                if (copyNum > in.materialCount) copyNum = in.materialCount;
            }
            return new Result(way, form, addSpeed, color, special, gravity, copyNum);
        }
        return null;
    }

    private static boolean pattern(boolean[] m, String p) {
        for (int i = 0; i < 9; i++) if (m[i] != (p.charAt(i) == '#')) return false;
        return true;
    }

    /** How many items each input slot loses when the result is taken (decrStackSize clamps to the stack). */
    public record Uses(int matrixEach, int way, int speed, int gravity, int bound, int material, int copy) {}

    public static Uses uses(Inputs in) {
        int copyNum = 1 + (in.copyCount > 0 ? in.copyCount : 0);
        int oriNum = in.materialCount > 0 ? in.materialCount : 1;
        if (copyNum > oriNum) copyNum = oriNum;

        int wayUse = in.maxNumber;
        if (in.materialCount > 0) {
            if (in.materialHasTag) {
                int baseNum = in.number;
                if (in.wayCount > 0 && in.wayCount > wayUse - baseNum) wayUse = wayUse - baseNum;
            } else if (in.wayCount > 0) {
                if (in.wayCount > wayUse) wayUse--;
                else wayUse = in.wayCount;
            }
        }
        int speedUse = 64;
        if (in.materialCount > 0 && in.materialHasTag && in.speedCount > 0 && in.speedCount > 64 - in.speed) {
            speedUse = 64 - in.speed;
        }
        int gravityUse = 16;
        int boundUse = 4;
        if (!in.laser && in.materialCount > 0 && in.materialHasTag) {
            if (in.gravityCount > 0 && in.gravityCount > 16 - in.gravity) gravityUse = 16 - in.gravity;
            int baseBound = in.special - X1ShotTables.BOUND01 + 1;
            if (in.boundCount > 0 && in.boundCount > 4 - baseBound) boundUse = 4 - baseBound;
        }
        return new Uses(1, wayUse, speedUse, in.laser ? 0 : gravityUse, in.laser ? 0 : boundUse, copyNum, copyNum - 1);
    }
}
