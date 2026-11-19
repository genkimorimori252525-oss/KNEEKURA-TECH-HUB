package org.kneekura.bedrockwither.entity.ai;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.MoveControl;

/**
 * Flying movement adapter for the public Bedrock Wither movement.basic contract.
 *
 * Vanilla Java FlyingMoveControl applies its constructor maxTurn to pitch only
 * and hard-codes yaw to 90 degrees per tick. The pinned Bedrock Wither exposes
 * minecraft:movement.basic max_turn=180, which is documented as the maximum
 * number of degrees the mob may turn per tick. This adapter applies that same
 * public limit to both yaw and pitch while preserving Java's flying movement
 * primitive and hover-in-place behavior.
 */
public final class BedrockFlyingMoveControl extends MoveControl {
    public static final float PUBLIC_MAX_TURN_DEGREES = 180.0F;

    public BedrockFlyingMoveControl(Mob mob) {
        super(mob);
    }

    @Override
    public void tick() {
        if (this.operation == Operation.MOVE_TO) {
            this.operation = Operation.WAIT;
            this.mob.setNoGravity(true);

            double dx = this.wantedX - this.mob.getX();
            double dy = this.wantedY - this.mob.getY();
            double dz = this.wantedZ - this.mob.getZ();
            double distanceSqr = dx * dx + dy * dy + dz * dz;

            if (distanceSqr < (double) MIN_SPEED_SQR) {
                this.mob.setYya(0.0F);
                this.mob.setZza(0.0F);
                return;
            }

            float targetYaw = (float) (Mth.atan2(dz, dx) * (double) (180F / (float) Math.PI)) - 90.0F;
            this.mob.setYRot(this.rotlerp(
                    this.mob.getYRot(),
                    targetYaw,
                    PUBLIC_MAX_TURN_DEGREES
            ));

            float speed = (float) (this.speedModifier * this.mob.getAttributeValue(
                    this.mob.onGround() ? Attributes.MOVEMENT_SPEED : Attributes.FLYING_SPEED
            ));
            this.mob.setSpeed(speed);

            double horizontal = Math.sqrt(dx * dx + dz * dz);
            if (Math.abs(dy) > (double) 1.0E-5F || Math.abs(horizontal) > (double) 1.0E-5F) {
                float targetPitch = (float) (-(Mth.atan2(dy, horizontal)
                        * (double) (180F / (float) Math.PI)));
                this.mob.setXRot(this.rotlerp(
                        this.mob.getXRot(),
                        targetPitch,
                        PUBLIC_MAX_TURN_DEGREES
                ));
                this.mob.setYya(dy > 0.0D ? speed : -speed);
            }
        } else {
            // Preserve the existing Wither hover-in-place policy.
            this.mob.setYya(0.0F);
            this.mob.setZza(0.0F);
        }
    }
}
