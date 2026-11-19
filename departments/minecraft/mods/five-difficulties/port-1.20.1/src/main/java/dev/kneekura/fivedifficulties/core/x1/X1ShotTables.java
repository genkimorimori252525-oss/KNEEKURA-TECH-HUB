package dev.kneekura.fivedifficulties.core.x1;

/**
 * Literal constants from X1 DanmakuConstants / THShotLib / ItemTHShot / RenderTHShot.
 * Values are copied, not tuned.
 */
public final class X1ShotTables {
    private X1ShotTables() {}

    // DanmakuConstants colours. A shot ID stores form * 8 + colour, so only 0..7 survive spawning.
    public static final int RED = 0, BLUE = 1, GREEN = 2, YELLOW = 3, PURPLE = 4, AQUA = 5, ORANGE = 6, WHITE = 7;
    public static final int RANDOM = 8, RAINBOW = 9;
    public static final int[] RAINBOW_PATTERN = {RED, ORANGE, YELLOW, GREEN, AQUA, BLUE, PURPLE};

    // DanmakuConstants forms.
    public static final int FORM_SMALL = 0, FORM_TINY = 1, FORM_MEDIUM = 2, FORM_PEARL = 3, FORM_CIRCLE = 4,
            FORM_LIGHT = 5, FORM_SCALE = 6, FORM_BUTTERFLY = 7, FORM_SMALLSTAR = 8, FORM_STAR = 9, FORM_RICE = 10,
            FORM_CRYSTAL = 11, FORM_HEART = 12, FORM_KUNAI = 13, FORM_TALISMAN = 14, FORM_BIGLIGHT = 15,
            FORM_OVAL = 16, FORM_FAMILIAR = 17, FORM_ARROW = 18, FORM_PHANTOM = 26, FORM_AMULET = 27,
            FORM_KNIFE = 28, FORM_WIND = 29, FORM_BIG = 30, FORM_KISHITU = 31;

    // DanmakuConstants special-shot IDs (only those referenced by the port so far).
    public static final int SPECIAL_NONE = 0, HOMING01 = 10, DIFFUSION01 = 20, FALL01 = 30,
            BOUND01 = 40, BOUND02 = 41, BOUND03 = 42, BOUND04 = 43, FIRE = 60, EXPLOSION01 = 70, WIND01 = 180,
            GUNGNIR = 285;

    /** THKaguyaConfig "Laser Max Number" default. */
    public static final int LASER_MAX_NUMBER = 8;

    public static final double GRAVITY_DEFAULT = -0.03D;

    /** THShotLib.DAMAGE, indexed by form. */
    public static final float[] DAMAGE = {
            2.4F, 1.0F, 2.8F, 5.0F, 2.0F, 3.4F, 1.6F, 2.8F,
            1.6F, 3.0F, 1.2F, 1.8F, 3.2F, 2.6F, 1.0F, 6.8F,
            3.0F, 1.0F, 3.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F,
            0.0F, 0.0F, 0.0F, 5.0F, 2.6F, 4.0F, 5.0F, 5.0F};

    /** THShotLib.SIZE, indexed by form (hit size; 1.0 is about one block). */
    public static final float[] SIZE = {
            0.30F, 0.15F, 0.50F, 0.30F, 0.30F, 0.30F, 0.15F, 0.30F,
            0.25F, 0.50F, 0.15F, 0.15F, 0.50F, 0.15F, 0.15F, 0.60F,
            0.50F, 1.00F, 0.15F, 0.00F, 0.00F, 0.00F, 0.00F, 0.00F,
            0.00F, 0.00F, 0.00F, 0.40F, 0.30F, 1.00F, 0.90F, 0.90F};

    /** THShotLib.ways: ring sizes used by createSphereShot, indexed by requested way count. */
    public static final int[][] SPHERE_WAYS = {
            {0}, {1}, {1, 1}, {1, 0, 2, 0}, {1, 0, 3, 0}, {1, 3, 1}, {1, 4, 1}, {1, 5, 1}, {1, 3, 3, 1},
            {1, 5, 3, 0}, {1, 4, 4, 1}, {1, 6, 4, 0}, {1, 5, 5, 1}, {1, 3, 5, 3, 1}, {1, 3, 6, 3, 1},
            {1, 4, 5, 4, 1}, {1, 4, 6, 4, 1}, {1, 4, 7, 4, 1}, {1, 3, 5, 5, 3, 1}, {1, 3, 6, 6, 3},
            {1, 3, 6, 6, 3, 1}, {1, 5, 9, 5, 1}, {1, 3, 7, 7, 3, 1}, {1, 6, 9, 6, 1}, {1, 4, 7, 7, 4, 1},
            {1, 3, 5, 7, 5, 3, 1}, {1, 3, 5, 8, 5, 3, 1}, {1, 3, 5, 9, 5, 3, 1}, {1, 3, 6, 8, 6, 3, 1},
            {1, 3, 6, 9, 6, 3, 1}, {1, 4, 6, 8, 6, 4, 1}, {1, 3, 6, 11, 6, 3, 1}, {1, 3, 6, 12, 6, 3, 1},
            {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0}, {0},
            {1, 3, 6, 12, 12, 6, 3, 1}};

    // ItemTHShot tables, indexed by the X1 item damage value (0..18).
    public static final String[] ITEM_SHOT_NAMES = {
            "smallShot", "tinyShot", "mediumShot", "bigShot",
            "starShot", "smallStarShot", "circleShot", "scaleShot",
            "butterflyShot", "lightShot", "knifeShot", "heartShot",
            "kunaiShot", "talismanShot", "bigLightShot", "riceShot",
            "ovalShot", "crystalShot", "arrowShot"};
    /** ItemTHShot.shotTypeTrans: used only for the spawn distance (SIZE of this form). */
    public static final int[] ITEM_SHOT_TYPE_TRANS = {
            0, 1, 2, 30, 9, 8, 4, 6, 7, 5, 28, 12, 13, 14, 15, 10, 16, 11, 18};
    public static final float[] ITEM_SPEED = {
            0.50F, 0.50F, 0.40F, 0.25F, 0.50F, 0.50F, 0.50F, 0.55F, 0.30F, 0.50F,
            0.65F, 0.40F, 0.60F, 0.50F, 0.40F, 0.50F, 0.40F, 0.45F, 0.50F};
    public static final int[] ITEM_FORM = {
            FORM_SMALL, FORM_TINY, FORM_MEDIUM, FORM_BIG, FORM_STAR, FORM_SMALLSTAR, FORM_CIRCLE, FORM_SCALE,
            FORM_BUTTERFLY, FORM_LIGHT, FORM_KNIFE, FORM_HEART, FORM_KUNAI, FORM_TALISMAN, FORM_BIGLIGHT,
            FORM_RICE, FORM_OVAL, FORM_CRYSTAL, FORM_ARROW};
    /** ItemTHShot item-icon tint (pass 0). */
    public static final int[] ITEM_COLOR_R = {255, 0, 0, 255, 255, 0, 255, 255};
    public static final int[] ITEM_COLOR_G = {0, 0, 255, 255, 0, 255, 128, 255};
    public static final int[] ITEM_COLOR_B = {0, 255, 0, 0, 255, 255, 0, 255};

    /** THKaguyaConfig "Shot Max Number" default. */
    public static final int SHOT_MAX_NUMBER = 32;

    // RenderTHShot colour table (delay light, familiar).
    public static final float[] RENDER_COLOR_R = {224F / 255F, 0F, 0F, 224F / 255F, 224F / 255F, 0F, 1F, 1F};
    public static final float[] RENDER_COLOR_G = {0F, 0F, 224F / 255F, 224F / 255F, 0F, 224F / 255F, 128F / 255F, 1F};
    public static final float[] RENDER_COLOR_B = {0F, 224F / 255F, 0F, 0F, 224F / 255F, 224F / 255F, 0F, 1F};

    /** EntityTHShot.getShotForm / getShotColor from a synced shot ID. */
    public static int formOf(int shotId) {
        return (shotId - colorOf(shotId)) / 8;
    }

    public static int colorOf(int shotId) {
        return shotId % 8;
    }

    /** RenderTHShot forms drawn by renderNormalShot (billboarded sprite strip, column = colour). */
    public static boolean isNormalSpriteForm(int form) {
        return form == FORM_SMALL || form == FORM_TINY || form == FORM_MEDIUM || form == FORM_PEARL
                || form == FORM_CIRCLE || form == FORM_HEART || form == FORM_BIG;
    }
}
