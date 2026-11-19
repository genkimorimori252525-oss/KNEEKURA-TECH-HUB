package dev.kneekura.fivedifficulties.forge.entity;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.level.Level;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.FORM_LIGHT;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.GREEN;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RED;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.YELLOW;

/**
 * Port of X1 {@code EntityDanmakuCreeper} (ハナビーパー). Instead of exploding it bursts into three
 * spheres of light shots after its own 30-tick fuse; the vanilla tick only runs for the first 20
 * ignited ticks, so it freezes, bursts, then plays its 40-tick death while still alive.
 */
public class DanmakuCreeperEntity extends Creeper {
    private static final java.util.Random SHOT_RAND = new java.util.Random();
    private int timeSinceIgnited2;
    private final int fuseTime2 = 30;

    public DanmakuCreeperEntity(EntityType<? extends DanmakuCreeperEntity> type, Level level) {
        super(type, level);
    }

    @Override
    public void tick() {
        if (this.isAlive()) {
            timeSinceIgnited2 += this.getSwellDir(); // getCreeperState
            if (timeSinceIgnited2 >= fuseTime2) {
                timeSinceIgnited2 = -300;
                if (!this.level().isClientSide) {
                    burst();
                    this.level().playSound(null, getX(), getY(), getZ(), SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE,
                            4.0F, (1.0F + (this.level().random.nextFloat() - this.level().random.nextFloat()) * 0.2F) * 0.7F);
                }
            }
        }
        if (timeSinceIgnited2 >= -100 && timeSinceIgnited2 < 0) timeSinceIgnited2 = 0;
        if (timeSinceIgnited2 < -100 && timeSinceIgnited2 > -280 && this.getHealth() > 0F) x1DeathUpdate();
        if (timeSinceIgnited2 < 20 && timeSinceIgnited2 >= 0) super.tick();
    }

    private void burst() {
        float damage = 5.0F;
        int danmakuLevel = dev.kneekura.fivedifficulties.forge.X1Config.danmakuLevel();
        float size = 0.1F + danmakuLevel * 0.1F;
        int[] ways = {8, 12, 20, 32, 44};
        int way = ways[danmakuLevel];
        Vec3d angle = X1Danmaku.angle_Random(SHOT_RAND); // THShotLib.angle_Random uses THShotLib's own Random
        Vec3d pos = X1Danmaku.pos_Living(this);
        Vec3d gravity = X1Danmaku.gravity(0.0D, -0.02D, 0.0D);
        float d = this.isPowered() ? damage * 2F : damage;
        double firstSpeed = this.isPowered() ? 1.2D : 0.6D;
        X1Danmaku.createSphereShot(this, this, pos, angle, 0F, firstSpeed, 0.01D, 0.00D, gravity,
                X1ShotData.shot(FORM_LIGHT, GREEN, size, d, 0, 80), way, 0.0D, 0F);
        X1Danmaku.createSphereShot(this, this, pos, angle, 0F, 0.5D, 0.01D, 0.00D, gravity,
                X1ShotData.shot(FORM_LIGHT, RED, size, d, 0, 80), way, 0.0D, 0F);
        X1Danmaku.createSphereShot(this, this, pos, angle, 0F, 0.4D, 0.01D, 0.00D, gravity,
                X1ShotData.shot(FORM_LIGHT, YELLOW, size, d, 0, 80), way, 0.0D, 0F);
    }

    /** EntityDanmakuCreeper.onDeathUpdate: removed at deathTime 40 (vanilla 1.20 drops the XP on death). */
    private void x1DeathUpdate() {
        ++this.deathTime;
        if (this.deathTime == 40 && !this.level().isClientSide) {
            this.level().broadcastEntityEvent(this, (byte) 60); // explode particles
            this.remove(RemovalReason.KILLED);
        }
    }

    @Override
    protected void tickDeath() {
        x1DeathUpdate();
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putShort("Fuse", (short) 200);
    }
}
