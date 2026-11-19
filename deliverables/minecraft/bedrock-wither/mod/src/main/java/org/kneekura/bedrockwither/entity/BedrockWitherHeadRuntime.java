package org.kneekura.bedrockwither.entity;

public final class BedrockWitherHeadRuntime {
    private float yaw;
    private float pitch;
    private float oldYaw;
    private float oldPitch;
    private int nextUpdate;
    private int idleUpdates;

    public float yaw() { return yaw; }
    public void setYaw(float value) { yaw = value; }

    public float pitch() { return pitch; }
    public void setPitch(float value) { pitch = value; }

    public float oldYaw() { return oldYaw; }
    public void setOldYaw(float value) { oldYaw = value; }

    public float oldPitch() { return oldPitch; }
    public void setOldPitch(float value) { oldPitch = value; }

    public int nextUpdate() { return nextUpdate; }
    public void setNextUpdate(int value) { nextUpdate = value; }

    public int idleUpdates() { return idleUpdates; }
    public void setIdleUpdates(int value) { idleUpdates = value; }
}
