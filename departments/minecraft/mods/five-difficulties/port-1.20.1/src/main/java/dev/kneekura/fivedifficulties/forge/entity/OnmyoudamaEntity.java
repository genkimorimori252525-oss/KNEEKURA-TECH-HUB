package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.function.Supplier;

/**
 * Port of X1 {@code EntityOnmyoudama} (陰陽玉): charged in front of the player while the Hakurei
 * gohei is held (+0.06 size per tick up to 3), released with one tick of acceleration 1.0. Its damage is
 * size × 6. It hits nothing until it has been clear of its user for two ticks; after that it hits
 * everything, its user included (and hurts them).
 */
public class OnmyoudamaEntity extends THShotEntity {
    /** THKaguyaItems.hakurei_miko_stick */
    public static Supplier<Item> mikoStick = () -> null;

    private boolean shootingFlag;
    private boolean userHit;
    private int hitTimer;

    public OnmyoudamaEntity(EntityType<? extends OnmyoudamaEntity> type, Level level) {
        super(type, level);
    }

    public OnmyoudamaEntity(Level level, LivingEntity user, Vec3d pos, Vec3d angle, float slope, Vec3d rotate,
                            float rotationSpeed, int rotationEnd, double firstSpeed, double limitSpeed, double acceleration,
                            Vec3d gravity, int color, float size, float damage, int delay, int end, int special) {
        this(PortRegistries.ONMYOUDAMA.get(), level);
        initShot(user, pos, angle, slope, rotate, rotationSpeed, rotationEnd, firstSpeed, limitSpeed, acceleration,
                gravity, color, size, damage, delay, end, special, false);
        shootingFlag = false;
        userHit = false;
        hitTimer = 0;
    }

    @Override
    public void tick() {
        if (this.level().isClientSide) return;
        X1ShotMotion m = motion();
        if (m == null) {
            this.discard();
            return;
        }
        if (shootingFlag) m.acceleration = 0.0D;
        Entity owner = this.getOwner();
        if (owner == null) {
            this.discard();
            return;
        }
        if (owner instanceof Player player) {
            if (player.isUsingItem() && !shootingFlag) {
                Vec3d v = X1Danmaku.getVecFromAngle(-m.yaw, -m.pitch, 0.6D);
                this.setPos(player.getX() + v.x() * 2, X1Danmaku.getPosYFromEye(player, -0.1D) + v.y(), player.getZ() + v.z());
                m.yaw = -player.getYRot();
                m.pitch = -player.getXRot();
                syncRotation();
                if (getShotSize() < 3.00F) setShotSize(getShotSize() + 0.06F);
                if (!holdingStick(player)) this.discard();
                return;
            } else if (!shootingFlag) {
                if (!holdingStick(player)) {
                    this.discard();
                    return;
                }
                this.tickCount = 1;
                m.shotSpeed = 0.5D; // X1 sets it, but updateMotion keeps the (zero) motion speed
                m.setVector();
                m.acceleration = 1.0D;
                shootingFlag = true;
            }
        }
        shotDamage = getShotSize() * 6.0F;
        super.tick();
        if (this.isRemoved()) return;

        // A block above the ball (within its size) reflects it downward.
        Vec3 s1 = this.position();
        Vec3 s2 = s1.add(0, getShotSize(), 0);
        BlockHitResult up = this.level().clip(new ClipContext(s1, s2, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        if (up.getType() != HitResult.Type.MISS) {
            double blockY = up.getBlockPos().getY();
            double diveY = blockY - (getY() + getShotSize());
            this.setPos(getX(), blockY + getShotSize() + 0.01D + diveY, getZ());
            m.pitch *= -1.0F;
            m.setVector();
            m.motion = new Vec3d(m.motion.x(), m.motion.y() * 0.9D, m.motion.z());
        }
        if (!userHit) {
            if (!hitUserCheck(m, s1, s1.add(toMc(m.motion)))) {
                hitTimer++;
                if (hitTimer >= 2) userHit = true;
            }
        }
    }

    private static boolean holdingStick(Player player) {
        ItemStack held = player.getInventory().getSelected();
        Item stick = mikoStick.get();
        return !held.isEmpty() && stick != null && held.is(stick);
    }

    /** EntityTHShot.hitUserCheck: is the user on this tick's path (boxes grown by half the size)? */
    private boolean hitUserCheck(X1ShotMotion m, Vec3 from, Vec3 to) {
        float hitSize = getShotSize() * 0.5F;
        Entity owner = this.getOwner();
        AABB search = this.getBoundingBox().expandTowards(toMc(m.motion)).inflate(hitSize);
        for (Entity e : this.level().getEntities(this, search)) {
            if (e.equals(owner) && e.getBoundingBox().inflate(hitSize).clip(from, to).isPresent()) return true;
        }
        return false;
    }

    @Override
    protected boolean userHitCheck(Entity e) {
        return userHit;
    }

    @Override
    protected boolean isUserHit() {
        return true;
    }

    /** Turns back and slows, but returns false, so the ball is removed after the hit anyway. */
    @Override
    protected boolean entityHitSpecialProcess(Entity hit, X1ShotMotion m) {
        m.yaw *= -1.0F;
        m.pitch *= -1.0F;
        m.setVector();
        m.motion = m.motion.scale(0.8F);
        return false;
    }
}
