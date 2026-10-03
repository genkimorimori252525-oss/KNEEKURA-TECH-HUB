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
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.ProjectileImpactEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.fml.common.Mod;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.BedrockWitherAttackType;
import org.kneekura.bedrockwither.entity.BedrockWitherBlockRules;
import org.kneekura.bedrockwither.registry.ModEntities;

@Mod.EventBusSubscriber(modid = BedrockWitherMod.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class BedrockWitherSkullEntity extends WitherSkull {
    // Official minecraft:projectile defaults, omitted by the pinned 1.26.50 skull JSON.
    private static final int OWNER_LAUNCH_IMMUNITY_TICKS = 5;
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
        if (this.level().isClientSide) {
            return;
        }

        Entity target = hitResult.getEntity();
        Entity owner = this.getOwner();
        float impactDamage = impactDamageFor(this.level().getDifficulty());

        boolean accepted;
        if (owner instanceof LivingEntity livingOwner) {
            accepted = target.hurt(
                    this.damageSources().witherSkull(this, livingOwner),
                    impactDamage
            );
            if (accepted) {
                if (target.isAlive()) {
                    this.doEnchantDamageEffects(livingOwner, target);
                } else {
                    // Historical Bedrock native WitherSkull::onHit heals the
                    // owning mob by 5 when its skull kills the target.
                    livingOwner.heal(5.0F);
                }
            }
        } else {
            accepted = target.hurt(this.damageSources().magic(), impactDamage);
        }

        if (accepted && target instanceof LivingEntity livingTarget) {
            int duration = witherDurationFor(this.level().getDifficulty());
            if (duration > 0) {
                livingTarget.addEffect(
                        new MobEffectInstance(MobEffects.WITHER, duration, 1),
                        this.getEffectSource()
                );
            }
        }
    }

    public static float impactDamageFor(Difficulty difficulty) {
        return switch (difficulty) {
            case PEACEFUL, EASY -> 5.0F;
            case NORMAL -> 8.0F;
            case HARD -> 12.0F;
        };
    }

    public static int witherDurationFor(Difficulty difficulty) {
        return switch (difficulty) {
            case PEACEFUL, EASY -> 0;
            case NORMAL -> 200;
            case HARD -> 800;
        };
    }

    @Override
    public void tick() {
        if (isRemoved()) return;
        super.tick();
        // Java 1.20.1 AbstractHurtingProjectile ignores getInertia() in water and
        // multiplies by a hard-coded 0.8F. Undo only that inherited drag; retain
        // ordinary fluid pushing (the pinned skull has isolated_physics=false).
        if (!isRemoved() && isInWater()) {
            setDeltaMovement(getDeltaMovement().scale(1.0D / (double) 0.8F));
        }
    }

    @Override
    protected boolean canHitEntity(Entity target) {
        // Replace Java's spatial leftOwner latch with the documented launch-time
        // grace. Keeping Java's same-vehicle exclusion during those five ticks is
        // an adapter for mounted shooters, not a claimed Bedrock riding rule.
        Entity owner = getOwner();
        return target.canBeHitByProjectile() && !target.noPhysics
                && (owner == null || tickCount >= OWNER_LAUNCH_IMMUNITY_TICKS
                || !owner.isPassengerOfSameVehicle(target));
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
        // Bedrock JSON exposes max_resistance=4.0, but that numeric value is
        // expressed in Bedrock explosion-resistance semantics. In Java's explosion
        // calculation the behaviorally equivalent dangerous-skull cap is 0.8,
        // matching current observed blue-skull terrain penetration and vanilla
        // Java's own WitherSkull adaptation boundary.
        if (!isDangerous()
                || !BedrockWitherBlockRules.canDestroy(
                        level,
                        pos,
                        state,
                        BedrockWitherAttackType.PROJECTILE
                )) {
            return resistance;
        }
        return Math.min(0.8F, resistance);
    }

    @Override
    protected void onHit(HitResult hitResult) {
        // Own the Bedrock explosion contract explicitly instead of inheriting
        // Java WitherSkull's hit lifecycle. Mojang Bedrock JSON:
        // fuse_length=0, power=1, causes_fire=false,
        // destroy_affected_by_griefing=true.
        if (!this.level().isClientSide && !isRemoved()) {
            // AbstractHurtingProjectile.tick calls onHit only. Dispatch the
            // entity/block callback ourselves; super.onHit would also run the
            // Java WitherSkull explosion and therefore double the explosion.
            if (hitResult instanceof EntityHitResult entityHit) {
                onHitEntity(entityHit);
            } else if (hitResult instanceof BlockHitResult blockHit) {
                onHitBlock(blockHit);
            }
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
        if (level().isClientSide || isRemoved() || !isDangerous() || isInvulnerableTo(source)) {
            return false;
        }
        // reflect_immunity defaults to zero seconds after launch. It is not a
        // repeated-reflector cooldown; no unsupported cooldown is invented here.
        return reflectFrom(source.getDirectEntity(), source.getEntity());
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void reflectIncomingProjectile(ProjectileImpactEvent event) {
        // Official component docs: since 1.26.0 *every* projectile can reflect a
        // reflect_on_hurt projectile on impact, even if it deals no damage. A
        // Java potion is one such case. Preserve the incoming impact lifecycle
        // and honor Forge cancellation/skip decisions made by earlier listeners.
        if (event.getImpactResult() != ProjectileImpactEvent.ImpactResult.DEFAULT) return;
        if (event.getRayTraceResult() instanceof EntityHitResult hit
                && hit.getEntity() instanceof BedrockWitherSkullEntity skull
                && !skull.level().isClientSide && !skull.isRemoved() && skull.isDangerous()) {
            skull.reflectFrom(event.getProjectile(), event.getProjectile().getOwner());
        }
    }

    private boolean reflectFrom(Entity direct, Entity attacker) {
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

        // Explicit Java adapter: incoming projectile motion, otherwise hitter
        // look, at the JSON dangerous launch speed (0.6). Current JSON/docs prove
        // the reflection gate, not this vector. Historical PeratX/source
        // ea30a251 (ProjectileComponent::hurt) instead uses normalized hitter view
        // at unit speed; that older body does not prove current 1.26.50 behavior.
        this.setDeltaMovement(reflectedDirection.normalize().scale(Kind.DANGEROUS.launchPower()));
        if (attacker != null) {
            this.setOwner(attacker);
        }
        this.markHurt();
        return true;
    }
}
