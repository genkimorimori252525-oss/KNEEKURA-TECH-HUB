package org.kneekura.bedrockwither.entity.projectile;

import net.minecraft.core.BlockPos;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.WitherSkull;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Explosion;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.kneekura.bedrockwither.registry.ModEntities;

public final class BedrockWitherSkullEntity extends WitherSkull {
    public enum Kind {
        NORMAL(1.2F, false),
        DANGEROUS(0.6F, true);

        private final float launchPower;
        private final boolean dangerous;

        Kind(float launchPower, boolean dangerous) {
            this.launchPower = launchPower;
            this.dangerous = dangerous;
        }

        public float launchPower() {
            return launchPower;
        }

        public boolean dangerous() {
            return dangerous;
        }
    }

    public BedrockWitherSkullEntity(EntityType<? extends WitherSkull> type, Level level) {
        super(type, level);
    }

    public static BedrockWitherSkullEntity create(
            Level level,
            LivingEntity owner,
            Vec3 origin,
            Vec3 direction,
            Kind kind
    ) {
        BedrockWitherSkullEntity skull = ModEntities.BEDROCK_WITHER_SKULL.get().create(level);
        if (skull == null) {
            throw new IllegalStateException("Failed to create Bedrock Wither skull entity");
        }

        skull.setOwner(owner);
        skull.setDangerous(kind.dangerous());
        skull.setPos(origin.x, origin.y, origin.z);

        Vec3 normalized = direction.normalize();
        if (normalized.lengthSqr() < 1.0E-8D) {
            normalized = owner.getLookAngle();
        }

        // Bedrock projectile component:
        // uncertainty = uncertainty_base(7.5) - difficultyLevel * multiplier(1).
        // Java's shoot() is an adaptation of that exposed inaccuracy contract.
        skull.shoot(
                normalized.x,
                normalized.y,
                normalized.z,
                kind.launchPower(),
                uncertaintyFor(level.getDifficulty())
        );

        return skull;
    }

    private static float uncertaintyFor(Difficulty difficulty) {
        return switch (difficulty) {
            case PEACEFUL -> 7.5F;
            case EASY -> 6.5F;
            case NORMAL -> 5.5F;
            case HARD -> 4.5F;
        };
    }

    @Override
    protected void onHitEntity(EntityHitResult hitResult) {
        // Do NOT call WitherSkull.onHitEntity(): Java adds 8/5 direct impact damage
        // and owner healing on kill. Current Bedrock wither_skull definitions expose
        // no impact_damage component; their entity-hit contract is the Wither effect
        // plus the projectile's immediate power-1 explosion handled by onHit().
        if (this.level().isClientSide) {
            return;
        }

        if (hitResult.getEntity() instanceof LivingEntity target) {
            int duration = switch (this.level().getDifficulty()) {
                case PEACEFUL, EASY -> 0;
                case NORMAL -> 200;
                case HARD -> 800;
            };

            if (duration > 0) {
                target.addEffect(
                        new MobEffectInstance(MobEffects.WITHER, duration, 1),
                        this.getEffectSource()
                );
            }
        }
    }

    @Override
    protected float getInertia() {
        // Both current Bedrock skull definitions expose inertia=1.0 and liquid_inertia=1.0.
        return 1.0F;
    }

    @Override
    public float getBlockExplosionResistance(
            Explosion explosion,
            BlockGetter level,
            BlockPos pos,
            BlockState state,
            FluidState fluid,
            float resistance
    ) {
        // Current Bedrock dangerous skull explosion has max_resistance=4.0.
        // Normal skull has no such cap.
        return isDangerous() ? Math.min(4.0F, resistance) : resistance;
    }

    @Override
    protected void onHit(HitResult hitResult) {
        // Own the Bedrock explosion contract explicitly instead of inheriting
        // Java WitherSkull's hit lifecycle. Mojang Bedrock JSON:
        // fuse_length=0, power=1, causes_fire=false,
        // destroy_affected_by_griefing=true.
        if (!this.level().isClientSide) {
            this.level().explode(
                    this,
                    this.getX(),
                    this.getY(),
                    this.getZ(),
                    1.0F,
                    false,
                    Level.ExplosionInteraction.MOB
            );
            this.discard();
        }
    }

    @Override
    public boolean isPickable() {
        // Current Bedrock dangerous skull exposes reflect_on_hurt=true; normal skull does not.
        return isDangerous();
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        if (!isDangerous() || this.isInvulnerableTo(source)) {
            return false;
        }

        Entity direct = source.getDirectEntity();
        Entity attacker = source.getEntity();

        Vec3 reflectedDirection = Vec3.ZERO;
        if (direct != null && direct != this && direct != attacker) {
            reflectedDirection = direct.getDeltaMovement();
        }
        if (reflectedDirection.lengthSqr() < 1.0E-8D && attacker instanceof LivingEntity livingAttacker) {
            reflectedDirection = livingAttacker.getLookAngle();
        }
        if (reflectedDirection.lengthSqr() < 1.0E-8D) {
            reflectedDirection = this.getDeltaMovement();
        }
        if (reflectedDirection.lengthSqr() < 1.0E-8D) {
            return false;
        }

        // Bedrock's public component proves reflection, but not the exact native
        // vector reconstruction. This direction policy is therefore an adaptation
        // pending direct Bedrock runtime measurement.
        this.setDeltaMovement(reflectedDirection.normalize().scale(Kind.DANGEROUS.launchPower()));
        if (attacker != null) {
            this.setOwner(attacker);
        }
        this.markHurt();
        return true;
    }
}
