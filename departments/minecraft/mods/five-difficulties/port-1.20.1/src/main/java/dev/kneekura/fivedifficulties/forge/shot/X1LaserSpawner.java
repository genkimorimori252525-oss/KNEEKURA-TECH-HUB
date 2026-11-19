package dev.kneekura.fivedifficulties.forge.shot;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1LaserPatterns;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THSetLaserEntity;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;

import java.util.Random;

/** THShotLib laser bridge: X1 laser emitters feeding live {@link THLaserEntity} spawns. */
public final class X1LaserSpawner {
    private X1LaserSpawner() {}

    /** createLaserA family; {@code source} is the X1 source entity (never hit by the laser). */
    public static X1LaserPatterns patterns(ServerLevel level, LivingEntity user, Entity source) {
        return new X1LaserPatterns(new Random(), (pos, angle, first, limit, accel, gravity, laser) ->
                level.addFreshEntity(new THLaserEntity(level, user, source, pos, angle, 0F, new Vec3d(0, 1, 0), 0F,
                        9999, first, limit, accel, gravity, laser)));
    }

    /** THShotLib.createLaserB. */
    public static THSetLaserEntity createLaserB(ServerLevel level, LivingEntity user, Entity setting, Vec3d pos,
                                                Vec3d angle, Vec3d rotate, float rotateYawSpeed, int rotationEnd,
                                                X1LaserData laser, Entity set, double setLength, double setYOffset) {
        THSetLaserEntity entity = new THSetLaserEntity(level, user, setting, pos, angle, 0F, rotate, rotateYawSpeed,
                rotationEnd, laser, set, setLength, setYOffset);
        level.addFreshEntity(entity);
        return entity;
    }
}
