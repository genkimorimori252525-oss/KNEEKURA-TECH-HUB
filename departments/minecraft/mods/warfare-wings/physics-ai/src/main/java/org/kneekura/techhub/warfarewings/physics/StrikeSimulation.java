package org.kneekura.techhub.warfarewings.physics;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Source-only attack-profile observer and phased flight controller.
 * Attack windows signify feasible geometric *approaches*, never releases or hits.
 * Engineering thresholds do not imply archival/history/weapon envelopes.
 */
public final class StrikeSimulation {
    public static final String EVIDENCE = "SOURCE_MICROKERNEL+GEOMETRY_ONLY_NO_RELEASE_NO_HITS";
    private StrikeSimulation() {}

    public enum Phase { APPROACH, WINDOW, PULL_OUT, EGRESS, RETURN_HOME, COMPLETE, TIMEOUT }

    /** Explicit experimental tolerances, in blocks/ticks. */
    public record Geometry(double lateralRadius, double beforeTargetRadius,
                           double levelMinAgl, double levelMaxAgl,
                           double torpedoMinAboveSea, double torpedoMaxAboveSea,
                           double divePullOutAgl, int egressTicks, double homeRadius) {
        public Geometry {
            if (!positive(lateralRadius) || !positive(beforeTargetRadius)
                    || !positive(levelMinAgl) || !positive(levelMaxAgl)
                    || levelMaxAgl < levelMinAgl
                    || !positive(torpedoMinAboveSea) || !positive(torpedoMaxAboveSea)
                    || torpedoMaxAboveSea < torpedoMinAboveSea
                    || !positive(divePullOutAgl) || egressTicks < 1
                    || !positive(homeRadius)) throw new IllegalArgumentException("invalid geometry");
        }
        public static final Geometry LAB = new Geometry(36, 44, 45, 260, 12, 35, 90, 70, 45);
    }

    public record Plan(String id, String aircraftId, TacticalAirAI.Mission mission,
                       Vec3 initialPosition, Vec3 initialVelocity, double yawDeg,
                       Vec3 strikePoint, Vec3 home, double seaSurfaceY,
                       World terrain, int maxTicks, Geometry geometry) {
        public Plan {
            if (id == null || id.isBlank() || aircraftId == null || aircraftId.isBlank()
                    || initialPosition == null || initialVelocity == null
                    || strikePoint == null || home == null || mission == null
                    || terrain == null || geometry == null || maxTicks < 1 || maxTicks > 3000
                    || !Double.isFinite(seaSurfaceY) || !Double.isFinite(yawDeg))
                throw new IllegalArgumentException("invalid strike plan");
            check(initialPosition);check(initialVelocity);check(strikePoint);check(home);
            if (mission != TacticalAirAI.Mission.LEVEL_BOMB
                    && mission != TacticalAirAI.Mission.DIVE_BOMB
                    && mission != TacticalAirAI.Mission.TORPEDO
                    && mission != TacticalAirAI.Mission.STRAFE)
                throw new IllegalArgumentException("strike requires attack-profile mission");
            Vec3 along = new Vec3(strikePoint.x()-initialPosition.x(),0,
                    strikePoint.z()-initialPosition.z());
            if (along.length() < 30) throw new IllegalArgumentException("approach too short");
        }
    }

    public record Report(String scenario, String aircraft, TacticalAirAI.Mission mission,
                         int ticks, Phase terminalPhase, boolean timedOut,
                         int firstWindowTick, int crossedTargetPlaneTick,
                         int firstPullOutTick, int recoveredPullOutTick,
                         int firstHomeTick, double closestHorizontalToStrike,
                         double closest3dToStrike, double lateralAtCrossing,
                         double minTerrainClearance, double minSeaSurfaceClearance,
                         double maxSeaSurfaceClearance, int groundTouchTicks,
                         int windowTicks, int safetyOverrideTicks,
                         double distanceToHome, double finalAltitude, double finalSpeedBps,
                         double pathBlocks, Map<Phase,Integer> phaseTicks,
                         State finalState, String evidence) {}

    /**
     * Immutable stage memory for a strike aircraft flown *inside* SquadronCommand.
     * No second microkernel is run: all observations are based on the squadron's
     * one authoritative State per aircraft and its actual accumulated ticks.
     */
    public record SquadronPhase(
            Phase phase, long phaseStartedTick, long firstWindowTick,
            long crossedTargetTick, long firstPullOutTick, long recoveredTick,
            long reachedHomeTick, double lastProgress, double lowestPullOutY,
            Map<Phase,Integer> phaseTicks) {
        public SquadronPhase {
            if (phase == null || phaseTicks == null || phaseStartedTick < 0)
                throw new IllegalArgumentException("squadron phase state");
            phaseTicks = Map.copyOf(phaseTicks);
        }
        public static SquadronPhase initial() {
            return new SquadronPhase(Phase.APPROACH,0,-1,-1,-1,-1,-1,
                    0,Double.POSITIVE_INFINITY,Map.of());
        }
    }
    public record SquadronDirective(SquadronCommand.MissionOrder order, SquadronPhase next) {}

    /**
     * One mission-stage decision from *observed* current state. Use the
     * returned order with SquadronCommand.advance once, in the same tick.
     * Source objectives and elapsed flight phases are geometry only.
     */
    public static SquadronDirective squadronDirective(Plan plan, SquadronPhase prior, State current) {
        if (plan == null || prior == null || current == null)
            throw new IllegalArgumentException("squadron directive");
        check(current.position()); check(current.velocity());
        Vec3 position = current.position(), strike = plan.strikePoint();
        Vec3 axis = new Vec3(strike.x()-plan.initialPosition().x(),0,
                strike.z()-plan.initialPosition().z()).normalize();
        double progress = projected(position,plan.initialPosition(),axis);
        double goalProgress = projected(strike,plan.initialPosition(),axis);
        double horizontal = horizontalDistance(position,strike);
        double terrainHeight = plan.terrain().groundHeight(position.x(),position.z());
        double agl = position.y()-terrainHeight;
        boolean valid = validAttackGeometry(plan,agl,position.y()-plan.seaSurfaceY());
        boolean aligned = Ia133Microkernel.forward(current.yawDeg(),current.pitchDeg())
                .dot(axis)>0.45;
        Phase phase = prior.phase();
        long since = prior.phaseStartedTick();
        long crossed = prior.crossedTargetTick(), window=prior.firstWindowTick();
        long pull=prior.firstPullOutTick(), recovered=prior.recoveredTick(), home=prior.reachedHomeTick();
        double low = prior.lowestPullOutY();
        long tick = current.tick();

        if (crossed == -1 && tick > 0 && prior.lastProgress() <= goalProgress
                && progress > goalProgress) crossed=tick;
        if (phase == Phase.APPROACH) {
            if (plan.mission() == TacticalAirAI.Mission.DIVE_BOMB
                    && (agl <= plan.geometry().divePullOutAgl()
                    || horizontal <= plan.geometry().beforeTargetRadius()*0.6)) {
                phase=Phase.PULL_OUT; since=tick; pull=tick; low=position.y();
            } else if (plan.mission() != TacticalAirAI.Mission.DIVE_BOMB
                    && horizontal <= plan.geometry().beforeTargetRadius()
                    && valid && aligned) {
                phase=Phase.WINDOW; since=tick; window=tick;
            } else if (progress >= goalProgress + plan.geometry().beforeTargetRadius()) {
                phase=Phase.EGRESS; since=tick;
            }
        } else if (phase == Phase.WINDOW) {
            if (crossed >= 0 && tick-crossed>=12
                    || progress > goalProgress+plan.geometry().beforeTargetRadius()
                    || horizontal > 2*plan.geometry().beforeTargetRadius()) {
                phase=Phase.EGRESS; since=tick;
            }
        } else if (phase == Phase.PULL_OUT) {
            low=Math.min(low,position.y());
            if (position.y()>=low+18 && agl>=plan.geometry().divePullOutAgl()
                    && current.velocity().y()>0.01) {
                phase=Phase.EGRESS; since=tick; recovered=tick;
            }
        } else if (phase == Phase.EGRESS && tick-since>=plan.geometry().egressTicks()) {
            phase=Phase.RETURN_HOME; since=tick;
        } else if (phase == Phase.RETURN_HOME
                && distance(position,plan.home())<=plan.geometry().homeRadius()) {
            phase=Phase.COMPLETE; since=tick; home=tick;
        }

        TacticalAirAI.Mission mission;
        Vec3 objective;
        switch (phase) {
            case APPROACH, WINDOW -> {
                mission=plan.mission();
                objective=switch(plan.mission()) {
                    case LEVEL_BOMB -> new Vec3(strike.x(),position.y(),strike.z());
                    case TORPEDO -> new Vec3(strike.x(),
                            plan.seaSurfaceY()+0.5*(plan.geometry().torpedoMinAboveSea()
                                    +plan.geometry().torpedoMaxAboveSea()),strike.z());
                    default -> strike;
                };
            }
            case PULL_OUT -> {
                mission=TacticalAirAI.Mission.PATROL;
                objective=position.add(Ia133Microkernel.forward(current.yawDeg(),0).scale(90))
                        .add(0,100,0);
            }
            case EGRESS -> {
                mission=TacticalAirAI.Mission.PATROL;
                objective=strike.add(axis.scale(150))
                        .add(0,Math.max(80,position.y()-strike.y()),0);
            }
            case RETURN_HOME, COMPLETE -> {
                mission=TacticalAirAI.Mission.PATROL;
                objective=plan.home();
            }
            default -> throw new IllegalStateException("unexpected squadron phase "+phase);
        }
        EnumMap<Phase,Integer> histogram = new EnumMap<>(Phase.class);
        histogram.putAll(prior.phaseTicks());
        histogram.merge(phase,1,Integer::sum);
        return new SquadronDirective(
                new SquadronCommand.MissionOrder(mission,objective),
                new SquadronPhase(phase,since,window,crossed,pull,recovered,home,
                        progress,low,Collections.unmodifiableMap(histogram)));
    }

    public static Report run(Path atlasCsv, Plan plan) throws IOException {
        if (atlasCsv == null || plan == null) throw new IllegalArgumentException("plan");
        List<AircraftAtlasMain.Entry> roster = AircraftAtlasMain.load(atlasCsv);
        if (roster.size() != 24) throw new IllegalArgumentException("expected 24 Atlas profiles");
        AircraftAtlasMain.Entry plane = roster.stream()
                .filter(e -> e.aircraftId().equals(plan.aircraftId()))
                .findFirst().orElseThrow(() -> new IllegalArgumentException("unknown source aircraft"));
        var profile = TacticalAirAI.Profile.fromAtlas(AircraftAtlasMain.evaluate(plane));
        // TacticalAirAI.Frame itself owns the authoritative compatibility gate.
        new TacticalAirAI.Frame(profile,plane.model(),State.airborne(plan.initialPosition(),
                plan.initialVelocity()),plan.mission(),plan.strikePoint(),plan.home(),
                null,null,null,1,1,plan.terrain().groundHeight(plan.initialPosition().x(),
                plan.initialPosition().z()),false,0);

        Vec3 axis = new Vec3(plan.strikePoint().x()-plan.initialPosition().x(),0,
                plan.strikePoint().z()-plan.initialPosition().z()).normalize();
        double targetProgress = projected(plan.strikePoint(),plan.initialPosition(),axis);
        State state = new State(0,plan.initialPosition(),plan.initialVelocity(),
                plan.yawDeg(),0,0,0,0,0,0,0,0,1,0,1,0,false,false);
        TacticalAirAI.Memory memory = TacticalAirAI.Memory.INITIAL;
        Geometry g = plan.geometry();
        Phase phase = Phase.APPROACH;
        int windowStart = -1, crossed = -1, pullStart = -1, recovered = -1, homeAt = -1;
        int windowTicks = 0, safetyOverrides = 0, groundTouches = 0, clock = 0;
        double minAg = Double.POSITIVE_INFINITY, minSea = Double.POSITIVE_INFINITY,
                maxSea = Double.NEGATIVE_INFINITY, nearestH = Double.POSITIVE_INFINITY,
                nearest3 = Double.POSITIVE_INFINITY, crossLateral = Double.NaN, travel = 0;
        double minimumDuringPullOut = Double.POSITIVE_INFINITY;
        int phaseBeganTick = 0;
        EnumMap<Phase,Integer> hist = new EnumMap<>(Phase.class);

        for (int tick=0; tick<plan.maxTicks(); tick++) {
            int nextTick = tick + 1;
            Vec3 from = state.position();
            double along = projected(from,plan.initialPosition(),axis);
            double horizontal = horizontalDistance(from,plan.strikePoint());
            double agl = from.y() - plan.terrain().groundHeight(from.x(),from.z());
            double surface = from.y() - plan.seaSurfaceY();
            boolean eligible = validAttackGeometry(plan,agl,surface);
            if (phase == Phase.APPROACH) {
                if (plan.mission() == TacticalAirAI.Mission.DIVE_BOMB
                        && (agl <= g.divePullOutAgl()
                        || horizontal <= g.beforeTargetRadius()*0.6)) {
                    phase=Phase.PULL_OUT; phaseBeganTick=tick; pullStart=nextTick;
                    minimumDuringPullOut=from.y();
                } else if (horizontal <= g.beforeTargetRadius() && eligible
                        && plan.mission() != TacticalAirAI.Mission.DIVE_BOMB) {
                    phase=Phase.WINDOW;phaseBeganTick=tick;
                } else if (along >= targetProgress + g.beforeTargetRadius()) {
                    phase=Phase.EGRESS;phaseBeganTick=tick;
                }
            } else if (phase == Phase.WINDOW) {
                if ((crossed != -1 && nextTick - crossed >= 12)
                        || along >= targetProgress + g.beforeTargetRadius()
                        || horizontal > 2*g.beforeTargetRadius()) {
                    phase=Phase.EGRESS;phaseBeganTick=tick;
                }
            } else if (phase == Phase.PULL_OUT) {
                minimumDuringPullOut=Math.min(minimumDuringPullOut,from.y());
                if (from.y() >= minimumDuringPullOut + 18
                        && agl >= g.divePullOutAgl() && state.velocity().y() > 0.01) {
                    phase=Phase.EGRESS;phaseBeganTick=tick;recovered=nextTick;
                }
            } else if (phase == Phase.EGRESS && tick-phaseBeganTick >= g.egressTicks()) {
                phase=Phase.RETURN_HOME;phaseBeganTick=tick;
            }
            if (phase == Phase.RETURN_HOME && distance(from,plan.home()) <= g.homeRadius()) {
                // The state sampled here already completed exactly "tick"
                // physical steps. No extra integration occurs on completion.
                phase=Phase.COMPLETE;homeAt=tick;
            }
            if (phase == Phase.COMPLETE) { clock=tick;break; }
            hist.merge(phase,1,Integer::sum);

            Vec3 objective;
            TacticalAirAI.Mission steeringMission;
            switch(phase) {
                case APPROACH, WINDOW -> {
                    steeringMission = plan.mission();
                    objective = switch(plan.mission()) {
                        case LEVEL_BOMB -> new Vec3(plan.strikePoint().x(),from.y(),plan.strikePoint().z());
                        case TORPEDO -> new Vec3(plan.strikePoint().x(),
                                plan.seaSurfaceY() + (g.torpedoMinAboveSea()+g.torpedoMaxAboveSea())*0.5,
                                plan.strikePoint().z());
                        default -> plan.strikePoint();
                    };
                }
                case PULL_OUT -> {
                    steeringMission=TacticalAirAI.Mission.PATROL;
                    // Climb in the aircraft's horizontal direction without turning
                    // toward the ground strike point after aborting the dive.
                    Vec3 ahead = Ia133Microkernel.forward(state.yawDeg(),0);
                    objective = from.add(ahead.scale(90)).add(0,100,0);
                }
                case EGRESS -> {
                    steeringMission=TacticalAirAI.Mission.PATROL;
                    objective=plan.strikePoint().add(axis.scale(150))
                            .add(0, Math.max(80,from.y()-plan.strikePoint().y()),0);
                }
                case RETURN_HOME -> {
                    steeringMission=TacticalAirAI.Mission.PATROL;
                    objective=plan.home();
                }
                default -> throw new IllegalStateException("unexpected phase");
            }
            var frame = new TacticalAirAI.Frame(profile,plane.model(),state,
                    steeringMission,objective,plan.home(),null,null,null,1,1,
                    plan.terrain().groundHeight(from.x(),from.z()),false,0);
            var env = new FlightSafetyPlanner.Environment(plan.terrain()::groundHeight,
                    List.of(),6);
            var flight = FlightControlLoop.step(new FlightControlLoop.Input(
                    frame,memory,null,env));
            if (flight.safety().override()) safetyOverrides++;
            State next = Ia133Microkernel.tick(plane.model(),state,flight.decision().controls(),
                    plan.terrain());
            check(next.position());check(next.velocity());
            double newH=horizontalDistance(next.position(),plan.strikePoint());
            double newAgl=next.position().y()-plan.terrain().groundHeight(
                    next.position().x(),next.position().z());
            double newSea=next.position().y()-plan.seaSurfaceY();
            minAg=Math.min(minAg,newAgl);
            minSea=Math.min(minSea,newSea);maxSea=Math.max(maxSea,newSea);
            nearestH=Math.min(nearestH,newH);
            nearest3=Math.min(nearest3,distance(next.position(),plan.strikePoint()));
            if (next.onGround() || newAgl<=0.000001) groundTouches++;
            travel+=distance(from,next.position());
            double progress = projected(next.position(),plan.initialPosition(),axis);
            if (crossed==-1 && along <= targetProgress && progress > targetProgress) {
                crossed=nextTick;
                Vec3 offset=next.position().add(plan.strikePoint().scale(-1));
                crossLateral=Math.abs(offset.x()*axis.z()-offset.z()*axis.x());
            }
            // Only observable geometry. No projectile or payload state exists here.
            double approachAlignment = Ia133Microkernel.forward(
                    next.yawDeg(),next.pitchDeg()).dot(axis);
            if (newH <= g.beforeTargetRadius() && approachAlignment > 0.45
                    && validAttackGeometry(plan,newAgl,newSea)
                    && (phase==Phase.WINDOW || phase==Phase.APPROACH)) {
                windowTicks++;
                if (windowStart==-1) windowStart=nextTick;
            }
            state=next;
            memory=flight.decision().nextMemory();
            clock=nextTick;
        }
        boolean timedOut=phase!=Phase.COMPLETE;
        if (timedOut) phase=Phase.TIMEOUT;
        return new Report(plan.id(),plan.aircraftId(),plan.mission(),clock,phase,timedOut,
                windowStart,crossed,pullStart,recovered,homeAt,nearestH,nearest3,
                crossLateral,minAg,minSea,maxSea,groundTouches,windowTicks,safetyOverrides,
                distance(state.position(),plan.home()),state.position().y(),
                state.velocity().length()*TICKS_PER_SECOND,travel,
                Collections.unmodifiableMap(new EnumMap<>(hist)),state,EVIDENCE);
    }

    private static boolean validAttackGeometry(Plan plan,double agl,double aboveSea) {
        Geometry g=plan.geometry();
        return switch(plan.mission()) {
            case LEVEL_BOMB -> agl>=g.levelMinAgl() && agl<=g.levelMaxAgl();
            case TORPEDO -> aboveSea>=g.torpedoMinAboveSea()
                    && aboveSea<=g.torpedoMaxAboveSea() && agl>0;
            case DIVE_BOMB -> agl>=g.divePullOutAgl()
                    && agl<g.levelMaxAgl();
            case STRAFE -> agl>10 && agl<g.levelMinAgl();
            default -> false;
        };
    }
    private static double projected(Vec3 p, Vec3 reference, Vec3 axis) {
        return (p.x()-reference.x())*axis.x()+(p.z()-reference.z())*axis.z();
    }
    private static double horizontalDistance(Vec3 a,Vec3 b) {
        return Math.hypot(a.x()-b.x(),a.z()-b.z());
    }
    private static double distance(Vec3 a,Vec3 b) { return a.add(b.scale(-1)).length(); }
    private static boolean positive(double value) { return Double.isFinite(value)&&value>0; }
    private static void check(Vec3 p) {
        if (p==null || !Double.isFinite(p.x()) || !Double.isFinite(p.y()) || !Double.isFinite(p.z()))
            throw new IllegalArgumentException("nonfinite vector");
    }
}
