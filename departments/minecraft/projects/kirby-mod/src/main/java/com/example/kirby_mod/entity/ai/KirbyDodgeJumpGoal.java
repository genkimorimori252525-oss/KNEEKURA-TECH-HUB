package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.KirbySize;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ThrownTrident;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.EnumSet;
import java.util.List;

public class KirbyDodgeJumpGoal extends Goal {

    private static final int SIM_TICKS = 20;
    private static final double SCAN_HORIZ = 8.0D;
    private static final double SCAN_VERT = 4.0D;
    private static final double JUMP_RAISE = 0.5D;
    private static final double JUMP_ALT_HEIGHT = KirbySize.NORMAL.toDimensions().height;
    private static final double DODGE_IMPULSE = 0.42D;
    private static final double ARROW_GRAVITY_PER_TICK = 0.05D;

    private final KirbyEntity kirby;

    public KirbyDodgeJumpGoal(KirbyEntity kirby) {
        this.kirby = kirby;
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        if (kirby.getKirbySize() != KirbySize.NORMAL) return false;
        if (kirby.getCombatState() != CombatState.NONE) return false;
        if (kirby.getFlightState() != KirbyEntity.FlightState.GROUND) return false;
        if (!kirby.onGround()) return false;
        if (kirby.tickCount % 4 != 2) return false;
        return hasJumpDodgeable();
    }

    @Override
    public boolean canContinueToUse() {
        return kirby.getFlightState() == KirbyEntity.FlightState.DODGE_JUMP
                && !kirby.onGround();
    }

    @Override
    public void start() {
        kirby.setFlightState(KirbyEntity.FlightState.DODGE_JUMP);
        kirby.setDeltaMovement(0, DODGE_IMPULSE, 0);
        kirby.hasImpulse = true;
    }

    @Override
    public void tick() {
        // 物理任せ
    }

    @Override
    public void stop() {
        if (kirby.getFlightState() == KirbyEntity.FlightState.DODGE_JUMP) {
            kirby.setFlightState(KirbyEntity.FlightState.GROUND);
        }
    }

    private boolean hasJumpDodgeable() {
        AABB scan = kirby.getBoundingBox().inflate(SCAN_HORIZ, SCAN_VERT, SCAN_HORIZ);
        List<Projectile> projs = kirby.level().getEntitiesOfClass(Projectile.class, scan,
                p -> p.isAlive() && p.getOwner() != kirby
                        && p.getDeltaMovement().lengthSqr() > 0.01D);
        if (projs.isEmpty()) return false;

        AABB stand = kirby.getBoundingBox();
        AABB jumpAlt = new AABB(stand.minX, stand.minY + JUMP_RAISE, stand.minZ,
                stand.maxX, stand.minY + JUMP_RAISE + JUMP_ALT_HEIGHT, stand.maxZ);

        for (Projectile p : projs) {
            Vec3 pos = p.position();
            Vec3 vel = p.getDeltaMovement();
            boolean isArrowLike = (p instanceof AbstractArrow) || (p instanceof ThrownTrident);
            double gPerTick = isArrowLike ? ARROW_GRAVITY_PER_TICK : 0.0D;
            boolean hitsStand = false;
            boolean hitsJumpAlt = false;
            double vx = vel.x, vy = vel.y, vz = vel.z;
            double px = pos.x, py = pos.y, pz = pos.z;
            for (int t = 1; t <= SIM_TICKS; t++) {
                vy -= gPerTick;
                px += vx;
                py += vy;
                pz += vz;
                if (stand.contains(px, py, pz)) {
                    hitsStand = true;
                    break;
                }
                if (jumpAlt.contains(px, py, pz)) {
                    hitsJumpAlt = true;
                }
            }
            if (hitsStand && !hitsJumpAlt) return true;
        }
        return false;
    }
}
