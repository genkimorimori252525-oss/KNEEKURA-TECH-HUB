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
                phase=Phase.COMPLETE;homeAt=nextTick;
            }
            hist.merge(phase,1,Integer::sum);
            if (phase == Phase.COMPLETE) { clock=tick;break; }

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
