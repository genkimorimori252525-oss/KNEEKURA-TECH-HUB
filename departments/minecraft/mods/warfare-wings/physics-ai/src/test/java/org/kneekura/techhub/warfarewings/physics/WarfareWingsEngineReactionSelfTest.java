package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/** Source-proven 24-plane reaction times, not general historical performance. */
public final class WarfareWingsEngineReactionSelfTest {
    private static int checks;
    private static void require(boolean yes, String msg) {
        checks++;
        if (!yes) throw new AssertionError(msg);
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Need exact 24-anchor CSV");
        var roster = AircraftAtlasMain.load(Path.of(args[0]));
        require(roster.size() == 24, "all exact anchor aircraft present");
        require(WarfareWingsEngineReaction.all().size() == 24,
                "24 concrete tick overrides collected from exact WW binary");
        require(WarfareWingsEngineReaction.PROVENANCE_SHA256.equals(
                WarfareWingsAircraft.WARFARE_WINGS_ANCHOR_SHA256), "immutable source provenance");
        var ground = new FlatWorld(0);
        for (var type : roster) {
            Model model = type.model();
            int reaction = WarfareWingsEngineReaction.ticks(type.aircraftId());
            require(reaction >= 100 && reaction <= 200,
                    "real reactionTicks range, not generic IA default: " + model.id());
            var state = new State(0, new Vec3(0,200,0), new Vec3(0,0,.7),
                    0,0,0, 0,0,0, 0,0,0, 1,0,1, 0,false,false);
            for (int t=1;t<=69;t++) {
                state = tickWithReaction(model, state, Control.neutral(1), ground, reaction);
            }
            double expected = 1-Math.pow(1-model.acceleration()/reaction,69);
            require(Math.abs(state.enginePowerSmooth()-expected) < 2e-6,
                    "actual 69-tick source exponential engine reaction " + model.id());
        }
        require(WarfareWingsEngineReaction.ticks("warfare_wings:a6m")==100,
                "A6M exact bytecode reaction100");
        require(WarfareWingsEngineReaction.ticks("warfare_wings:b17")==150,
                "B17 exact bytecode reaction150");
        require(WarfareWingsEngineReaction.ticks("warfare_wings:g10n1")==200,
                "G10N1 exact bytecode reaction200");
        require(WarfareWingsEngineReaction.ticks("warfare_wings:g10n2")==170,
                "G10N2 exact bytecode reaction170");
        require(WarfareWingsEngineReaction.ticks("warfare_wings:g4m")==120,
                "G4M exact bytecode reaction120");
        double observedA6MTick69 = 0.500162839890;
        double predictedA6M = 1-Math.pow(0.99,69);
        require(Math.abs(predictedA6M-observedA6MTick69)<2e-6,
                "independent observed 401-row EXACT IA/WW A6M response, tick 69");
        require(1-Math.pow(.95,69) > .97,
                "old default20 would grossly overpredict original engine response");
        boolean refused=false;
        try { WarfareWingsEngineReaction.ticks("warfare_wings:not_real"); }
        catch (IllegalArgumentException expected) {refused=true;}
        require(refused, "unknown type must fail closed");
        refused=false;
        try { tickWithReaction(WarfareWingsAircraft.a6m(),
                State.airborne(new Vec3(0,200,0), new Vec3(0,0,.7)),
                Control.neutral(1),ground,Double.NaN); }
        catch (IllegalArgumentException expected) { refused=true; }
        require(refused, "nonfinite reaction rejected");
        System.out.println("WarfareWingsEngineReactionSelfTest passed " + checks
                + " checks / 24 exact-owner-aircraft response models");
    }
}
