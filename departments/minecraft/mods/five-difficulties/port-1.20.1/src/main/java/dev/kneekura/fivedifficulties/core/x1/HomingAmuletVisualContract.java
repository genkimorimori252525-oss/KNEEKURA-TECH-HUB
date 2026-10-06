package dev.kneekura.fivedifficulties.core.x1;

/**
 * Exact static visual contract from X1 RenderHomingAmulet and canonical PNG metadata.
 *
 * Original asset bytes are intentionally not committed to the public TECH-HUB repository.
 */
public final class HomingAmuletVisualContract {
    public static final String SOURCE_SHOT_TEXTURE =
            "assets/thkaguyamod/textures/shot/HomingAmulet.png";
    public static final String SOURCE_SHOT_TEXTURE_SHA256 =
            "badfeba690c2dee69ddb38c9f3a0fe538643ca1d439121e95959fd7dfb93b4d9";
    public static final int SOURCE_SHOT_TEXTURE_WIDTH = 64;
    public static final int SOURCE_SHOT_TEXTURE_HEIGHT = 32;

    public static final String SOURCE_ITEM_TEXTURE =
            "assets/thkaguyamod/textures/items/homingAmulet.png";
    public static final String SOURCE_ITEM_TEXTURE_SHA256 =
            "650f71239534ef521bea3e1e29893ed1cb8302721854c44d0536b76be02f5773";
    public static final int SOURCE_ITEM_TEXTURE_WIDTH = 32;
    public static final int SOURCE_ITEM_TEXTURE_HEIGHT = 32;

    // RenderHomingAmulet samples only the left 32x32 half of the 64x32 shot texture.
    public static final float U_MIN = 0.0F;
    public static final float U_MAX = 0.5F;
    public static final float V_MIN = 0.0F;
    public static final float V_MAX = 1.0F;

    // For red (color 0), legacy renderer ignores ShotData.size for visual scale.
    public static final float RED_FIRST_PASS_SCALE = 0.5F;

    // Legacy code scales by 0.5, then multiplies current matrix again by 0.55.
    public static final float RED_SECOND_PASS_ADDITIONAL_SCALE = 0.55F;
    public static final float RED_SECOND_PASS_EFFECTIVE_SCALE =
            RED_FIRST_PASS_SCALE * RED_SECOND_PASS_ADDITIONAL_SCALE;

    public static final float RED_TINT_R = 1.0F;
    public static final float RED_TINT_G = 25.0F / 255.0F;
    public static final float RED_TINT_B = 25.0F / 255.0F;
    public static final float RED_TINT_A = 0.6F;

    public static final float BASE_Y_ROTATION_DEGREES = 180.0F;
    public static final float Y_ROTATION_PER_ANIMATION_TICK = -23.0F;

    public static final String BLEND_SOURCE = "ONE";
    public static final String BLEND_DESTINATION = "ONE_MINUS_SRC_COLOR";
    public static final boolean LIGHTING_ENABLED = false;
    public static final boolean CULL_ENABLED = false;

    private HomingAmuletVisualContract() {}
}
