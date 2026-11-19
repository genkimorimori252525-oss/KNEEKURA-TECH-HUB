package com.github.tartaricacid.touhoulittlemaid.sim.debug.decisionmixin;

import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugDecisionHooks;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.pathfinder.AmphibiousNodeEvaluator;
import net.minecraft.world.level.pathfinder.BlockPathTypes;
import net.minecraft.world.level.pathfinder.FlyNodeEvaluator;
import net.minecraft.world.level.pathfinder.NodeEvaluator;
import net.minecraft.world.level.pathfinder.SwimNodeEvaluator;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin(value={WalkNodeEvaluator.class,FlyNodeEvaluator.class,SwimNodeEvaluator.class,AmphibiousNodeEvaluator.class},remap=false)
public abstract class KneekuraDebugEvaluatorMalusMixin {
    @Redirect(method="*",at=@At(value="INVOKE",target="Lnet/minecraft/world/entity/Mob;getPathfindingMalus(Lnet/minecraft/world/level/pathfinder/BlockPathTypes;)F"),require=0)
    private float kneekura$originalVirtualMalus(Mob mob,BlockPathTypes type) {
        return KneekuraDebugDecisionHooks.originalMalus((NodeEvaluator)(Object)this,mob,type);
    }
}
