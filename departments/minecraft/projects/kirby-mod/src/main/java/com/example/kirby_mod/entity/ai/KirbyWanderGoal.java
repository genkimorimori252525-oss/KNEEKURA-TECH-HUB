package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;
import com.example.kirby_mod.entity.CombatState;
import com.example.kirby_mod.entity.KirbyEntity;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;

import java.util.List;
import java.util.Locale;

/** Autonomous ground roaming that varies naturally between walking and running. */
public class KirbyWanderGoal extends WaterAvoidingRandomStrollGoal
        implements KirbyDebugInfoProvider {

    private static final double WALK_SPEED = 1.0D;
    private static final double RUN_SPEED = 1.35D;
    private final KirbyEntity kirby;
    private boolean active;
    private boolean runMode;
    private boolean lastPathSuccess = true;
    private double selectedSpeed;
    private String lastReason = "idle";

    public KirbyWanderGoal(KirbyEntity mob, double speedModifier) {
        super(mob, speedModifier);
        this.kirby = mob;
    }

    @Override
    public boolean canUse() {
        if (!canRoamOnGround()) return false;
        boolean selected = super.canUse();
        lastReason = selected ? "destination_selected" : "no_ground_destination";
        return selected;
    }

    @Override
    public boolean canContinueToUse() {
        return canRoamOnGround() && super.canContinueToUse();
    }

    @Override
    public void start() {
        active = true;
        runMode = KirbyAutonomyPolicy.chooseGroundMode(kirby.getRandom().nextFloat())
                == KirbyLocomotionMode.RUN;
        selectedSpeed = runMode ? RUN_SPEED : WALK_SPEED;
        lastPathSuccess = this.mob.getNavigation().moveTo(
                this.wantedX, this.wantedY, this.wantedZ, selectedSpeed);
        lastReason = lastPathSuccess
                ? (runMode ? "free_run_started" : "free_walk_started")
                : "ground_path_failed";
    }

    @Override
    public void stop() {
        super.stop();
        active = false;
        runMode = false;
        selectedSpeed = 0.0D;
        if (!"ground_path_failed".equals(lastReason)) lastReason = "roam_stopped";
    }

    public boolean isRunMode() {
        return active && runMode && lastPathSuccess;
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        lines.add("WanderGoal: active=" + active
                + " mode=" + (!active ? KirbyLocomotionMode.IDLE
                : runMode ? KirbyLocomotionMode.RUN : KirbyLocomotionMode.WALK)
                + " destination=" + String.format(Locale.ROOT, "(%.2f,%.2f,%.2f)",
                        this.wantedX, this.wantedY, this.wantedZ)
                + " speed=" + String.format(Locale.ROOT, "%.2f", selectedSpeed)
                + " pathSuccess=" + lastPathSuccess
                + " reason=" + lastReason);
        if (!lastPathSuccess) {
            lines.add("WARN WanderGoal path failed destination="
                    + String.format(Locale.ROOT, "(%.2f,%.2f,%.2f)",
                    this.wantedX, this.wantedY, this.wantedZ));
        }
        lines.add("WanderGoal thought=" + (active
                ? runMode ? "running_freely" : "walking_freely"
                : "waiting_for_next_free_roam"));
    }

    private boolean canRoamOnGround() {
        CombatState combat = kirby.getCombatState();
        return (combat == CombatState.NONE || combat == CombatState.KEEP_HOLDING)
                && kirby.getFlightState() == KirbyEntity.FlightState.GROUND
                && kirby.onGround()
                && !kirby.isInWater()
                && !kirby.isPassenger();
    }
}
