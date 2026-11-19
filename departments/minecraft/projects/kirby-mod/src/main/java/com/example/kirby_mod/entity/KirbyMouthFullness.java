package com.example.kirby_mod.entity;

import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.LivingEntity;

public final class KirbyMouthFullness {

    private static final double ZOMBIE_REFERENCE_VOLUME = 0.6D * 0.6D * 1.95D;
    public static final double SMALL_POINT = 1.0D;
    public static final double MIDDLE_POINT = 5.0D;
    public static final double BIG_POINT = 10.0D;
    private static final double MIN_MOB_POINTS = 0.25D;

    private KirbyMouthFullness() {}

    public static double capturePoints(LivingEntity mob) {
        double volume = mob.getBbWidth() * mob.getBbWidth() * mob.getBbHeight();
        return Math.max(MIN_MOB_POINTS, volume / ZOMBIE_REFERENCE_VOLUME);
    }

    public static boolean fitsInMaximumMouth(LivingEntity mob) {
        return capturePoints(mob) <= BIG_POINT;
    }

    public static double clamp(double points) {
        return Math.max(0.0D, Math.min(BIG_POINT, points));
    }

    public static KirbySize animationSize(double points) {
        if (points <= 0.0D) return KirbySize.NORMAL;
        if (points < MIDDLE_POINT) return KirbySize.SMALL;
        if (points < BIG_POINT) return KirbySize.MIDDLE;
        return KirbySize.BIG;
    }

    public static EntityDimensions dimensions(double points) {
        double clamped = clamp(points);
        if (clamped <= SMALL_POINT) return interpolate(KirbySize.NORMAL, KirbySize.SMALL, clamped / SMALL_POINT);
        if (clamped <= MIDDLE_POINT) return interpolate(KirbySize.SMALL, KirbySize.MIDDLE,
                (clamped - SMALL_POINT) / (MIDDLE_POINT - SMALL_POINT));
        return interpolate(KirbySize.MIDDLE, KirbySize.BIG,
                (clamped - MIDDLE_POINT) / (BIG_POINT - MIDDLE_POINT));
    }

    public static float renderScale(double points) {
        return dimensions(points).width / KirbySize.NORMAL.width;
    }

    public static double easeOut(double progress) {
        double clamped = Math.max(0.0D, Math.min(1.0D, progress));
        double remaining = 1.0D - clamped;
        return 1.0D - remaining * remaining;
    }

    private static EntityDimensions interpolate(KirbySize from, KirbySize to, double t) {
        float width = (float) (from.width + (to.width - from.width) * t);
        float height = (float) (from.height + (to.height - from.height) * t);
        return EntityDimensions.scalable(width, height);
    }
}
