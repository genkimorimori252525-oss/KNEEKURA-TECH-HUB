package dev.kneekura.fivedifficulties.core.x1;

/**
 * Port of X1 ShotData. Mutable on purpose: X1 pattern helpers temporarily overwrite
 * {@code color} for RANDOM / RAINBOW and restore it afterwards.
 */
public final class X1ShotData {
    public int form;
    public int color;
    public float damage;
    public float size;
    public int delay;
    public int end;
    public int special;

    public X1ShotData(int form, int color, float size, float damage, int delay, int end, int special) {
        this.form = form;
        this.color = color;
        this.damage = damage;
        this.size = size;
        this.delay = delay;
        this.end = end;
        this.special = special;
    }

    public static X1ShotData shot(int form, int color, float size, float damage, int delay, int end, int special) {
        return new X1ShotData(form % 32, color % 16, size, damage, delay, end, special);
    }

    public static X1ShotData shot(int form, int color, float size, float damage, int delay, int end) {
        return shot(form, color, size, damage, delay, end, 0);
    }

    public static X1ShotData shot(int form, int color, int delay, int end, int special) {
        return shot(form, color, X1ShotTables.SIZE[form % 32], X1ShotTables.DAMAGE[form % 32], delay, end, special);
    }

    public static X1ShotData shot(int form, int color) {
        return shot(form, color, 0, 80, 0);
    }

    /** EntityTHShot constructor stores form * 8 + colour. */
    public int shotId() {
        return form * 8 + color;
    }

    public X1ShotData copy() {
        return new X1ShotData(form, color, size, damage, delay, end, special);
    }
}
