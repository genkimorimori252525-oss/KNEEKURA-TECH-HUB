package dev.kneekura.fivedifficulties.forge.shot;

import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.BlockHitResult;

import java.util.HashMap;
import java.util.Map;

/**
 * Port of X1 {@code SpecialShotRegistry} + {@code ISpecialShot}. EntityTHShot consults it before
 * its built-in switch: a registered special shot ID fully replaces the built-in handling.
 * (X1 instantiates the registered class per call; handlers here are stateless singletons.)
 */
public final class X1SpecialShotRegistry {
    public interface SpecialShot {
        /** specialShot_move: every tick. */
        void move(THShotEntity shot, X1ShotMotion motion, int id);

        /** specialShot_hitBlock: true keeps the shot alive. */
        boolean hitBlock(THShotEntity shot, X1ShotMotion motion, int id, BlockHitResult hit);

        /** specialShot_hitEntity: true keeps the shot alive. */
        boolean hitEntity(THShotEntity shot, X1ShotMotion motion, int id, Entity hit);
    }

    private static final Map<Integer, SpecialShot> SPECIAL_SHOTS = new HashMap<>();

    private X1SpecialShotRegistry() {}

    public static boolean register(SpecialShot handler, int id) {
        SPECIAL_SHOTS.put(id, handler);
        return true;
    }

    public static SpecialShot get(int id) {
        return SPECIAL_SHOTS.get(id);
    }

    public static int size() {
        return SPECIAL_SHOTS.size();
    }
}
