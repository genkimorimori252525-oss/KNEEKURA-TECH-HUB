package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.boss.EnderDragonPart;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.function.Supplier;

/**
 * Port of X1 {@code EntityNuclearShot} (お空の核弾). Its damage is size × 8 every tick; it hits every
 * entity on its path without stopping, cancels other users' shots by their full damage, and only a
 * block inside one of its three centre lines removes it. While a player holds it unfired (the Nuclear
 * Control Rod, not ported yet) it grows in front of them and explodes if the rod is not in hand.
 */
public class NuclearShotEntity extends THShotEntity {
    /** THKaguyaItems.nuclear_control_rod (arrives with the items; null until then). */
    public static Supplier<Item> controlRod = () -> null;

    /** Already released (the spell card sets it before the first tick). */
    public boolean shootingFlag;

    public NuclearShotEntity(EntityType<? extends NuclearShotEntity> type, Level level) {
        super(type, level);
    }

    public NuclearShotEntity(Level level, LivingEntity user, Vec3d pos, Vec3d angle, float slope, Vec3d rotate,
                             float rotationSpeed, int rotationEnd, double firstSpeed, double limitSpeed,
                             double acceleration, Vec3d gravity, X1ShotData shot) {
        this(PortRegistries.NUCLEAR_SHOT.get(), level);
        initShot(user, pos, angle, slope, rotate, rotationSpeed, rotationEnd, firstSpeed, limitSpeed, acceleration,
                gravity, shot.shotId(), shot.size, shot.damage, shot.delay, shot.end, shot.special, false);
        this.shootingFlag = false;
    }

    @Override
    public void tick() {
        if (this.level().isClientSide) return;
        Entity owner = this.getOwner();
        if (owner == null) {
            this.discard();
            return;
        }
        X1ShotMotion m = motion();
        if (owner instanceof Player player && m != null) {
            if (player.isUsingItem() && !shootingFlag) {
                Vec3d v = X1Danmaku.getVecFromAngle(-this.getYRot() + 20F, -this.getXRot(), 0.3D + getShotSize() / 2.0D);
                this.xo = getX();
                this.yo = getY();
                this.zo = getZ();
                this.setPos(player.getX() + v.x(), X1Danmaku.getPosYFromEye(player, -0.1D) + v.y(), player.getZ() + v.z());
                m.yaw = -player.getYRot();
                m.pitch = -player.getXRot();
                this.setYRot(m.yaw);
                this.setXRot(m.pitch);
                if (getShotSize() < 6.00F) setShotSize(getShotSize() + 0.06F);
                if (!holdingRod(player)) explodeAndDie();
                return;
            } else if (!shootingFlag) {
                if (!holdingRod(player)) {
                    explodeAndDie();
                    return;
                }
                this.tickCount = 1;
                m.setVector();
                m.acceleration = 0.2D;
                shootingFlag = true;
            }
        }
        shotDamage = getShotSize() * 8.0F;
        super.tick();
    }

    private static boolean holdingRod(Player player) {
        ItemStack held = player.getInventory().getSelected();
        Item rod = controlRod.get();
        return !held.isEmpty() && rod != null && held.is(rod);
    }

    private void explodeAndDie() {
        this.level().explode(this, getX(), getY(), getZ(), getShotSize(), Level.ExplosionInteraction.TNT);
        this.discard();
    }

    // EntityTHShot.hitCheck with EntityNuclearShot.hitEntityCheck / onImpact.
    @Override
    protected void hitCheck(X1ShotMotion m) {
        double half = this.getShotSize() / 2.0D;
        Vec3 pos = this.position();
        Vec3 sizeOffset = toMc(m.angle).scale(half);
        Vec3 start = pos.subtract(sizeOffset);
        Vec3 end = pos.add(toMc(m.motion)).add(sizeOffset);
        BlockHitResult block = clip(start, end);
        if (block.getType() != HitResult.Type.MISS) end = block.getLocation();

        // hitEntityCheck: every entity on the path is hit, then the block hit (if any) is processed.
        float hitSize = this.getShotSize() * 0.5F;
        AABB search = this.getBoundingBox().expandTowards(toMc(m.motion)).inflate(hitSize);
        for (Entity e : this.level().getEntities(this, search, this::isNuclearCandidate)) {
            if (dev.kneekura.fivedifficulties.forge.shot.X1Hit.intercept(e.getBoundingBox().inflate(hitSize), start, end).isPresent()) onImpactEntity(e, m);
            if (this.isRemoved()) return;
        }
        boolean isHit = false;
        if (block.getType() != HitResult.Type.MISS) {
            onImpactBlock(block, m); // inside hitEntityCheck
            isHit = onImpactBlock(block, m); // and again by hitCheck with the returned position
        }
        if (!isHit) {
            probe(pos.add(0, -half, 0), pos.add(0, half, 0), m);
            probe(pos.add(-half, 0, 0), pos.add(half, 0, 0), m);
            probe(pos.add(0, 0, -half), pos.add(0, 0, half), m);
        }
    }

    private void probe(Vec3 start, Vec3 end, X1ShotMotion m) {
        BlockHitResult hit = clip(start, end);
        if (hit.getType() != HitResult.Type.MISS && !blockHitSpecialProcess(hit, m)) this.discard();
    }

    private boolean isNuclearCandidate(Entity e) {
        Entity owner = this.getOwner();
        X1ShotMotion m = motion();
        boolean userHittable = m != null && USER_HITTABLE_SPECIALS.contains(m.special);
        // EntityTHFairy users never hit fairies: arrives with the X1 mobs.
        return e.isPickable()
                && (userHittable || e != owner)
                && !(e instanceof SakuyaTimeControllerEntity)
                && !(e instanceof Animal) && !(e instanceof Villager)
                && (e instanceof LivingEntity || e instanceof EnderDragonPart || e instanceof THShotEntity);
    }

    private void onImpactEntity(Entity hit, X1ShotMotion m) {
        Entity owner = this.getOwner();
        if (!(hit instanceof THShotEntity other)) {
            entityHitSpecialProcess(hit, m); // its result is not used: the nuclear shot flies on
            if (hit != owner) {
                DamageSource source = this.damageSources().indirectMagic(this, owner == null ? this : owner);
                hit.hurt(source, shotDamage);
            }
        } else if (owner != other.getOwner()) {
            float damageA = this.shotDamage;
            this.shotDamage -= other.shotDamage;
            other.shotDamage -= damageA;
        }
    }

    /** EntityNuclearShot.onImpact for a block: note the inverted test (special 0 keeps flying). */
    private boolean onImpactBlock(BlockHitResult hit, X1ShotMotion m) {
        if (blockHitSpecialProcess(hit, m)) {
            this.delete();
            return true;
        }
        return false;
    }
}
