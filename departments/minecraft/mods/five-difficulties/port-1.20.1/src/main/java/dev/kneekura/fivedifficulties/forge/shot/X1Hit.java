package dev.kneekura.fivedifficulties.forge.shot;

import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;

/** 1.7.10 collision helpers that 1.20 changed. */
public final class X1Hit {
    private X1Hit() {}

    /**
     * {@code AxisAlignedBB.calculateIntercept} as in 1.7.10: the nearest point where the segment crosses a face of the
     * box. Unlike 1.20's {@code AABB.clip}, a start point inside the box still hits where the segment leaves it
     * (only a segment wholly inside the box misses).
     */
    public static Optional<Vec3> intercept(AABB box, Vec3 start, Vec3 end) {
        Optional<Vec3> r = box.clip(start, end);
        if (r.isEmpty() && box.contains(start)) r = box.clip(end, start);
        return r;
    }
}
