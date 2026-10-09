package com.example.kirby_mod.entity;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;

public enum KirbySize {
    NORMAL(2.025F, 2.025F),
    SMALL(2.475F, 2.475F),
    MIDDLE(3.6F, 3.375F),
    BIG(8.1F, 6.075F);

    private static final float MIDDLE_VOLUME_THRESHOLD = 4.0F;
    private static final float BIG_VOLUME_THRESHOLD = 100.0F;

    public final float width;
    public final float height;

    KirbySize(float width, float height) {
        this.width = width;
        this.height = height;
    }

    public EntityDimensions toDimensions() {
        return EntityDimensions.scalable(width, height);
    }

    public static KirbySize byId(int id) {
        KirbySize[] values = values();
        return id < 0 || id >= values.length ? NORMAL : values[id];
    }

    public static KirbySize forMob(Entity mob) {
        EntityDimensions dim = mob.getType().getDimensions();
        float volume = dim.width * dim.width * dim.height;
        if (volume >= BIG_VOLUME_THRESHOLD) return BIG;
        if (volume >= MIDDLE_VOLUME_THRESHOLD) return MIDDLE;
        return SMALL;
    }
}
