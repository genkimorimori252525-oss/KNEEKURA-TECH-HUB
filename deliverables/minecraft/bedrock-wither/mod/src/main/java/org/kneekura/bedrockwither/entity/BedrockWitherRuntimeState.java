package org.kneekura.bedrockwither.entity;

import net.minecraft.world.phys.Vec3;

/**
 * Java-side structural mirror of observable current BDS WitherBoss fields.
 *
 * This class deliberately does not assign Bedrock gameplay meaning to unknown values.
 * It gives runtime observation and later reconstruction a stable place to bind evidence.
 */
public final class BedrockWitherRuntimeState {
    private int maxShieldHealth;
    private int shieldHealth;
    private int destroyBlocksTick;
    private int healthThreshold;
    private int nativePhase;
    private boolean wantsToExplode;
    private boolean charging;
    private Vec3 chargeDirection = Vec3.ZERO;
    private int chargeFrames;
    private int preparingCharge;
    private int projectileCounter;
    private int spawningFrames;
    private int timeTillNextShot;
    private int fireRate;
    private float spinSpeed;
    private int stunTimer;
    private int framesTillMove;
    private boolean wantsMove;
    private boolean pathing;
    private int nativeMaxHealth;
    private int numSkeletons;
    private int maxSkeletons;
    private int movementTime;
    private int healthIntervals;
    private int lastHealthValue;
    private int delayShot;
    private int timeSinceLastShot;
    private float attackRange;
    private boolean secondVolley;
    private int mainHeadAttackCountdown;
    private int lastFiredHead = -1;

    public int maxShieldHealth() { return maxShieldHealth; }
    public void setMaxShieldHealth(int value) { maxShieldHealth = value; }

    public int shieldHealth() { return shieldHealth; }
    public void setShieldHealth(int value) { shieldHealth = value; }

    public int destroyBlocksTick() { return destroyBlocksTick; }
    public void setDestroyBlocksTick(int value) { destroyBlocksTick = value; }

    public int healthThreshold() { return healthThreshold; }
    public void setHealthThreshold(int value) { healthThreshold = value; }

    public int nativePhase() { return nativePhase; }
    public void setNativePhase(int value) { nativePhase = value; }

    public boolean wantsToExplode() { return wantsToExplode; }
    public void setWantsToExplode(boolean value) { wantsToExplode = value; }

    public boolean charging() { return charging; }
    public void setCharging(boolean value) { charging = value; }

    public Vec3 chargeDirection() { return chargeDirection; }
    public void setChargeDirection(Vec3 value) { chargeDirection = value == null ? Vec3.ZERO : value; }

    public int chargeFrames() { return chargeFrames; }
    public void setChargeFrames(int value) { chargeFrames = value; }

    public int preparingCharge() { return preparingCharge; }
    public void setPreparingCharge(int value) { preparingCharge = value; }

    public int projectileCounter() { return projectileCounter; }
    public void setProjectileCounter(int value) { projectileCounter = value; }

    public int spawningFrames() { return spawningFrames; }
    public void setSpawningFrames(int value) { spawningFrames = value; }

    public int timeTillNextShot() { return timeTillNextShot; }
    public void setTimeTillNextShot(int value) { timeTillNextShot = value; }

    public int fireRate() { return fireRate; }
    public void setFireRate(int value) { fireRate = value; }

    public float spinSpeed() { return spinSpeed; }
    public void setSpinSpeed(float value) { spinSpeed = value; }

    public int stunTimer() { return stunTimer; }
    public void setStunTimer(int value) { stunTimer = value; }

    public int framesTillMove() { return framesTillMove; }
    public void setFramesTillMove(int value) { framesTillMove = value; }

    public boolean wantsMove() { return wantsMove; }
    public void setWantsMove(boolean value) { wantsMove = value; }

    public boolean pathing() { return pathing; }
    public void setPathing(boolean value) { pathing = value; }

    public int nativeMaxHealth() { return nativeMaxHealth; }
    public void setNativeMaxHealth(int value) { nativeMaxHealth = value; }

    public int numSkeletons() { return numSkeletons; }
    public void setNumSkeletons(int value) { numSkeletons = value; }

    public int maxSkeletons() { return maxSkeletons; }
    public void setMaxSkeletons(int value) { maxSkeletons = value; }

    public int movementTime() { return movementTime; }
    public void setMovementTime(int value) { movementTime = value; }

    public int healthIntervals() { return healthIntervals; }
    public void setHealthIntervals(int value) { healthIntervals = value; }

    public int lastHealthValue() { return lastHealthValue; }
    public void setLastHealthValue(int value) { lastHealthValue = value; }

    public int delayShot() { return delayShot; }
    public void setDelayShot(int value) { delayShot = value; }

    public int timeSinceLastShot() { return timeSinceLastShot; }
    public void setTimeSinceLastShot(int value) { timeSinceLastShot = value; }

    public float attackRange() { return attackRange; }
    public void setAttackRange(float value) { attackRange = value; }

    public boolean secondVolley() { return secondVolley; }
    public void setSecondVolley(boolean value) { secondVolley = value; }

    public int mainHeadAttackCountdown() { return mainHeadAttackCountdown; }
    public void setMainHeadAttackCountdown(int value) { mainHeadAttackCountdown = value; }

    public int lastFiredHead() { return lastFiredHead; }
    public void setLastFiredHead(int value) { lastFiredHead = value; }
}
