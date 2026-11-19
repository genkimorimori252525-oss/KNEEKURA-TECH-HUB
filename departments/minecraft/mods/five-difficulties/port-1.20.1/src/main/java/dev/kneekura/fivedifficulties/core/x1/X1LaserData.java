package dev.kneekura.fivedifficulties.core.x1;

/**
 * Port of X1 LaserData. Mutable: X1 laser emitters overwrite {@code color} for RANDOM / RAINBOW,
 * and {@code createLaserA} never restores it.
 */
public final class X1LaserData {
    /** DanmakuConstants laser forms: the shot ID is form * 8 + colour. */
    public static final int LASER_NORMAL = 0, LASER_GUNGNIR = 1, LASER_LAEVATAIN = 2, LASER_MASTER_SPARK = 3;

    public int form;
    public int color;
    public float damage;
    public float width;
    public float length;
    public int delay;
    public int end;
    public int special;

    public X1LaserData(int form, int color, float width, float length, float damage, int delay, int end, int special) {
        this.form = form;
        this.color = color;
        this.damage = damage;
        this.width = width;
        this.length = length;
        this.delay = delay;
        this.end = end;
        this.special = special;
    }

    public static X1LaserData laser(int form, int color, float width, float length, float damage, int delay, int end,
                                    int special) {
        return new X1LaserData(form, color, width, length, damage, delay, end, special);
    }

    /** The colour-only overloads use form 0 (normal laser); delay 0 / end 80 by default. */
    public static X1LaserData laser(int color, float width, float length, float damage, int delay, int end, int special) {
        return new X1LaserData(0, color, width, length, damage, delay, end, special);
    }

    public static X1LaserData laser(int color, float width, float length, float damage, int delay, int end) {
        return laser(color, width, length, damage, delay, end, 0);
    }

    public static X1LaserData laser(int color, float width, float length, float damage) {
        return laser(color, width, length, damage, 0, 80);
    }

    public int shotId() {
        return form * 8 + color;
    }

    public X1LaserData copy() {
        return new X1LaserData(form, color, width, length, damage, delay, end, special);
    }
}
