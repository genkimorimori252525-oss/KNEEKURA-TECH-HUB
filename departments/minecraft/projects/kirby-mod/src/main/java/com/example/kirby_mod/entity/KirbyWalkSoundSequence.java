package com.example.kirby_mod.entity;

public final class KirbyWalkSoundSequence {

    public enum Gait {
        WALK(WALK_STEP_INTERVAL_SECONDS, NORMAL_PITCH),
        RUN(RUN_STEP_INTERVAL_SECONDS, RUNNING_PITCH),
        HELD_SMALL(HELD_SMALL_STEP_INTERVAL_SECONDS, NORMAL_PITCH),
        HELD_MIDDLE(HELD_MIDDLE_STEP_INTERVAL_SECONDS, NORMAL_PITCH),
        HELD_BIG(HELD_BIG_STEP_INTERVAL_SECONDS, NORMAL_PITCH);

        private final double stepIntervalSeconds;
        private final float pitch;

        Gait(double stepIntervalSeconds, float pitch) {
            this.stepIntervalSeconds = stepIntervalSeconds;
            this.pitch = pitch;
        }

        public double getStepIntervalSeconds() {
            return this.stepIntervalSeconds;
        }

        public float getPitch() {
            return this.pitch;
        }
    }

    public static final String WALK_1 = "kirby_walk_1";
    public static final String WALK_2 = "kirby_walk_2";
    public static final String WALK_3 = "kirby_walk_3";
    public static final int RESET_IDLE_TICKS = 30;
    public static final double WALK_STEP_INTERVAL_SECONDS = 0.3915D;
    public static final double RUN_STEP_INTERVAL_SECONDS = 0.192D;
    // Each mouth-full walk loop contains four ground-contact beats.
    public static final double HELD_SMALL_STEP_INTERVAL_SECONDS = 2.625D / 4.0D;
    public static final double HELD_MIDDLE_STEP_INTERVAL_SECONDS = 2.75D / 4.0D;
    public static final double HELD_BIG_STEP_INTERVAL_SECONDS = 2.75D / 4.0D;
    public static final float NORMAL_PITCH = 1.0F;
    public static final float RUNNING_PITCH = 1.12F;

    private int idleTicks = RESET_IDLE_TICKS;
    private double stepPhaseSeconds;
    private double stepIntervalSeconds = WALK_STEP_INTERVAL_SECONDS;
    private double speedScale;
    private int nextStep = 1;
    private String lastSoundName = "none";
    private float lastPitch = NORMAL_PITCH;
    private boolean moving;
    private boolean running;
    private boolean readyForStep = true;
    private Gait gait = Gait.WALK;

    public String tick(boolean moving, boolean running, double speedScale) {
        return tick(moving, moving && running ? Gait.RUN : Gait.WALK, speedScale);
    }

    public String tick(boolean moving, Gait gait, double speedScale) {
        this.moving = moving;
        updateGait(gait == null ? Gait.WALK : gait);
        this.running = moving && this.gait == Gait.RUN;
        this.speedScale = moving ? sanitizeSpeedScale(speedScale) : 0.0D;

        if (!moving) {
            if (this.idleTicks < RESET_IDLE_TICKS) {
                this.idleTicks++;
            }
            if (this.idleTicks >= RESET_IDLE_TICKS) {
                this.nextStep = 1;
            }
            this.stepPhaseSeconds = 0.0D;
            this.readyForStep = true;
            return null;
        }

        this.idleTicks = 0;
        if (this.readyForStep) {
            this.readyForStep = false;
            return playNextSound();
        }

        this.stepPhaseSeconds += this.speedScale / 20.0D;
        if (this.stepPhaseSeconds < this.stepIntervalSeconds) {
            return null;
        }

        this.stepPhaseSeconds -= this.stepIntervalSeconds;
        return playNextSound();
    }

    public int getIdleTicks() {
        return this.idleTicks;
    }

    public double getStepPhaseSeconds() {
        return this.stepPhaseSeconds;
    }

    public double getStepIntervalSeconds() {
        return this.stepIntervalSeconds;
    }

    public double getSpeedScale() {
        return this.speedScale;
    }

    public Gait getGait() {
        return this.gait;
    }

    public String getNextSoundName() {
        switch (this.nextStep) {
            case 1: return WALK_1;
            case 2: return WALK_2;
            case 3:
            default: return WALK_3;
        }
    }

    public String getLastSoundName() {
        return this.lastSoundName;
    }

    public float getLastPitch() {
        return this.lastPitch;
    }

    public boolean isMoving() {
        return this.moving;
    }

    public boolean isRunning() {
        return this.running;
    }

    private void updateGait(Gait nextGait) {
        if (this.gait == nextGait) {
            return;
        }
        double normalizedPhase = this.stepIntervalSeconds > 0.0D
                ? this.stepPhaseSeconds / this.stepIntervalSeconds
                : 0.0D;
        this.gait = nextGait;
        this.stepIntervalSeconds = nextGait.getStepIntervalSeconds();
        this.stepPhaseSeconds = normalizedPhase * this.stepIntervalSeconds;
    }

    private String playNextSound() {
        String soundName = getNextSoundName();
        this.lastSoundName = soundName;
        this.lastPitch = this.gait.getPitch();
        this.nextStep = this.nextStep == 1 ? 2 : (this.nextStep == 2 ? 3 : 2);
        return soundName;
    }

    private static double sanitizeSpeedScale(double speedScale) {
        if (!Double.isFinite(speedScale) || speedScale < 0.0D) {
            return 0.0D;
        }
        return Math.min(speedScale, 3.0D);
    }
}
