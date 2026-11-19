package org.kneekura.bedrockwither.entity;

import java.util.List;

/**
 * Client-independent presentation inputs from Mojang/bedrock-samples revision
 * 46ba6ea985fb5a92d79a9419198f10dda14c199d, wither.entity.json and
 * wither_boss_armor.render_controllers.json. Molang trigonometry is in degrees;
 * its division and remainder are floating point, even for integer-looking inputs.
 * These tests establish numeric contracts, not Bedrock texture or rendered parity.
 */
public final class BedrockWitherPresentation {
    private BedrockWitherPresentation() {}

    public record Scale(float xz, float y) {}
    public record ArmorPass(float u, float v, int packedLight, float red, float green, float blue) {}

    public static Scale scale(float swell) {
        float clamped = Math.max(0.0F, Math.min(1.0F, swell));
        float wobble = 1.0F + (float) Math.sin(Math.toRadians(swell * 5730.0D)) * swell * 0.01F;
        float adjustment = clamped * clamped;
        adjustment *= adjustment;
        return new Scale(2 * (1 + adjustment * 0.4F) * wobble, 2 * (1 + adjustment * 0.1F) / wobble);
    }

    public static float bodyRotation(float ageInTicks) {
        return (float) Math.cos(Math.toRadians((ageInTicks / 20.0D) * 114.6D));
    }

    public static boolean displayNormalSkin(int invulnerableTicks) {
        return invulnerableTicks <= 0 || (invulnerableTicks <= 80 && (invulnerableTicks / 5.0F) % 2.0F == 1.0F);
    }

    public static List<ArmorPass> armorPasses(boolean powered, int ticks, float partialTick, int sceneLight) {
        if (!powered) return List.of();
        double time = ticks + (double) partialTick;
        float scroll = (float) (time * 0.01D);
        float whiteU = (float) (Math.cos(Math.toRadians((time / 20.0D) * 22.92D)) * 3.0D);
        // Both controllers use ignore_lighting=true. Java's energy-swirl shader
        // also ignores light, but use fullbright inputs explicitly at the boundary.
        int fullbright = 0x00F000F0;
        // Texture/color adapter: re-use Java's bundled armor texture for both
        // passes; blue tint substitutes for the unredistributed Bedrock blue asset.
        return List.of(
                new ArmorPass(whiteU, scroll, fullbright, 0.5F, 0.5F, 0.5F),
                new ArmorPass(scroll, scroll, fullbright, 0.25F, 0.5F, 1.0F)
        );
    }
}
