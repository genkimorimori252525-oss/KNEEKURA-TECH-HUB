package dev.kneekura.fivedifficulties.forge.shot;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotPatterns;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import java.util.Random;

/** THShotLib bridge: X1 emission geometry feeding live {@link THShotEntity} spawns. */
public final class X1ShotSpawner {
    private X1ShotSpawner() {}

    public static X1ShotPatterns patterns(ServerLevel level, LivingEntity user) {
        return new X1ShotPatterns(new Random(),
                (pos, angle, slope, rotate, rotationSpeed, rotationEnd, first, limit, accel, gravity, shot) ->
                        level.addFreshEntity(new THShotEntity(level, user, pos, angle, slope, rotate, rotationSpeed,
                                rotationEnd, first, limit, accel, gravity, shot)));
    }

    /** THShotLib.pos_Living: eye height adjusted by pitch (half a block forward-down). */
    public static Vec3d posLiving(LivingEntity living) {
        double pitch = (double) living.getXRot() / 180.0D * Math.PI;
        double y = living.getY() + living.getEyeHeight() + Math.sin(pitch) * -0.5D + Math.cos(pitch) * -0.5D;
        return new Vec3d(living.getX(), y, living.getZ());
    }

    public static Vec3d pure(Vec3 v) {
        return new Vec3d(v.x, v.y, v.z);
    }
}
