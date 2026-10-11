package org.kneekura.techhub.warfarewings.physics;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Source-only multi-aircraft evaluation using the real SquadronCommand closed loop.
 * Distances, contacts and windows are geometric diagnostics, never simulated hits.
 */
public final class CombatSimulation {
    public static final String EVIDENCE = "SOURCE_MICROKERNEL+SCRIPTED_SCENARIO_NO_WEAPONS";
    private CombatSimulation() {}

    /** Diagnostics windows are scenario hypotheses, measured in Minecraft blocks. */
    public record Scenario(String id, List<SquadronCommand.AircraftSpec> aircraft,
                           int maxTicks, double objectiveRadius,
                           double protectionRadius, Map<String,String> escortAssets,
                           World world, SquadronCommand.Sensors sensors) {
        public Scenario {
            if (id == null || id.isBlank() || aircraft == null || aircraft.isEmpty()
                    || maxTicks < 1 || maxTicks > 2400 || !Double.isFinite(objectiveRadius)
                    || objectiveRadius <= 0 || !Double.isFinite(protectionRadius)
                    || protectionRadius <= 0 || escortAssets == null || world == null || sensors == null)
                throw new IllegalArgumentException("invalid combat scenario");
            aircraft = List.copyOf(aircraft);
            escortAssets = Collections.unmodifiableMap(new TreeMap<>(escortAssets));
            Map<String,SquadronCommand.AircraftSpec> roster = new TreeMap<>();
            for (var spec : aircraft) {
                if (spec == null || roster.putIfAbsent(spec.unitId(), spec) != null)
                    throw new IllegalArgumentException("duplicate/null unit");
            }
            for (var pair : escortAssets.entrySet()) {
                var escort = roster.get(pair.getKey());
                var asset = roster.get(pair.getValue());
                if (escort == null || asset == null
                        || !escort.team().equals(asset.team())
                        || escort.mission() != TacticalAirAI.Mission.ESCORT
                        || !pair.getValue().equals(escort.escortedUnitId()))
                    throw new IllegalArgumentException("invalid protection mapping");
            }
        }
    }

    public record UnitMetric(String id, double pathBlocks,
                             double minTerrainClearance, double minObjectiveDistance,
                             int objectiveWindowTicks, int firstObjectiveWindowTick,
                             int hostileContactTicks, int assignedTicks, int firingCandidateTicks,
                             int terrainOverrides, int collisionOverrides, int withdrawalTicks,
                             int groundedTicks,
                             double finalDistanceToObjective, double finalSpeedBps) {}

    public record PairMetric(String firstId, String secondId, double initialSeparation,
                             double closestApproachBlocks, int closestTick,
                             double finalSeparationBlocks, int dangerouslyCloseTicks) {}
    public record PairKey(String firstId, String secondId) implements Comparable<PairKey> {
        @Override public int compareTo(PairKey other) {
            int first = firstId.compareTo(other.firstId);
            return first != 0 ? first : secondId.compareTo(other.secondId);
        }
    }

    public record AssetMetric(String assetId, int threatWithinCorridorTicks,
                              int escortThreatAssignedTicks, double closestThreatBlocks,
                              double closestEscortBlocks, double finalObjectiveDistance,
                              boolean corridorBreached) {}

    public record Report(String scenarioId, long simulatedTicks, boolean timedOut,
                         Map<String,UnitMetric> units, Map<PairKey,PairMetric> pairs,
                         Map<String,AssetMetric> assets,
                         SquadronCommand.Snapshot finalSnapshot, String evidence,
                         List<String> failedOperationalGates) {
        public Report {
            failedOperationalGates = List.copyOf(failedOperationalGates);
        }
        /** Source-side safety qualification only; never a combat/victory judgment. */
        public boolean passesSafetyGates() { return failedOperationalGates.isEmpty(); }
    }

    private static final class UnitCounter {
        double path, minClearance = Double.POSITIVE_INFINITY, minObjective = Double.POSITIVE_INFINITY;
        int window, firstWindow = -1, contacts, assigned, fire, terrain, collision, withdrawal, ground;
    }
    private static final class PairCounter {
        final double initial;
        double min;
        int at, dangerouslyClose;
        PairCounter(double initial) { this.initial = initial; this.min = initial; }
        void sample(double separation,int tick) {
            if (separation < min) { min = separation; at = tick; }
            // Source-only 6-block proximity flag; not an actual Minecraft hitbox.
            if (separation < 6) dangerouslyClose++;
        }
    }
    private static final class AssetCounter {
        int threatTicks, escortsAssigned;
        double minThreat = Double.POSITIVE_INFINITY, minEscort = Double.POSITIVE_INFINITY;
    }

    public static Report run(Path atlasCsv, Scenario scenario) throws IOException {
        if (atlasCsv == null || scenario == null) throw new IllegalArgumentException("inputs");
        SquadronCommand commander = SquadronCommand.load(atlasCsv, scenario.aircraft(),
                scenario.world(), scenario.sensors());
        Map<String,SquadronCommand.AircraftSpec> roster = new TreeMap<>();
        for (var craft : scenario.aircraft()) roster.put(craft.unitId(), craft);
        List<String> ids = List.copyOf(roster.keySet());
        Map<String,UnitCounter> stats = new TreeMap<>();
        Map<PairKey,PairCounter> pairs = new TreeMap<>();
        Map<String,AssetCounter> assets = new TreeMap<>();
        for (var id : ids) stats.put(id,new UnitCounter());
        for (var asset : scenario.escortAssets().values()) assets.put(asset,new AssetCounter());
        var snapshot = commander.start();
        for (int i = 0; i < ids.size(); i++) for (int j = i+1; j < ids.size(); j++) {
            String a = ids.get(i), b = ids.get(j);
            pairs.put(new PairKey(a,b),new PairCounter(distance(snapshot,a,b)));
        }
        for (int tick = 0; tick < scenario.maxTicks(); tick++) {
            var step = commander.advance(snapshot);
            var current = step.next();
            for (var id : ids) {
                var metric = stats.get(id);
                var before = snapshot.units().get(id).aircraft();
                var after = current.units().get(id).aircraft();
                var spec = roster.get(id);
                var directive = step.commands().get(id);
                metric.path += separation(before.position(),after.position());
                double terrain = scenario.world().groundHeight(after.position().x(),after.position().z());
                double clearance = after.position().y() - terrain;
                metric.minClearance = Math.min(metric.minClearance,clearance);
                if (after.onGround() || clearance < 0.000001) metric.ground++;
                double toGoal = separation(after.position(),spec.objective());
                metric.minObjective = Math.min(metric.minObjective,toGoal);
                if (toGoal <= scenario.objectiveRadius()) {
                    metric.window++;
                    if (metric.firstWindow == -1) metric.firstWindow=tick+1;
                }
                if (directive.threatContactId() != null) metric.contacts++;
                if (directive.assignedTargetId() != null) metric.assigned++;
                if (directive.decision().firingWindowCandidate()) metric.fire++;
                if (directive.safetyClearance().reason() == FlightSafetyPlanner.Reason.TERRAIN_AHEAD)
                    metric.terrain++;
                if (directive.safetyClearance().reason() == FlightSafetyPlanner.Reason.MOVING_COLLISION_RISK)
                    metric.collision++;
                if (directive.decision().maneuver() == TacticalAirAI.Maneuver.RETURN_HOME)
                    metric.withdrawal++;
            }
            for (var entry : pairs.entrySet()) {
                var pair = entry.getKey();
                entry.getValue().sample(distance(current,pair.firstId(),pair.secondId()),tick+1);
            }
            for (var assetEntry : assets.entrySet()) {
                String assetId = assetEntry.getKey();
                var counter = assetEntry.getValue();
                var asset = current.units().get(assetId).aircraft().position();
                double minHostile = Double.POSITIVE_INFINITY;
                for (var other : roster.values()) {
                    double gap = separation(asset,current.units().get(other.unitId()).aircraft().position());
                    if (!other.team().equals(roster.get(assetId).team())) minHostile = Math.min(minHostile,gap);
                    else if (!other.unitId().equals(assetId)
                            && scenario.escortAssets().containsKey(other.unitId())
                            && scenario.escortAssets().get(other.unitId()).equals(assetId))
                        counter.minEscort = Math.min(counter.minEscort,gap);
                }
                counter.minThreat = Math.min(counter.minThreat,minHostile);
                if (minHostile <= scenario.protectionRadius()) counter.threatTicks++;
                for (var escort : scenario.escortAssets().entrySet()) {
                    if (!escort.getValue().equals(assetId)) continue;
                    var decision = step.commands().get(escort.getKey());
                    if (decision.assignedTargetId() != null) counter.escortsAssigned++;
                }
            }
            snapshot = current;
        }
        Map<String,UnitMetric> unitMetrics = new TreeMap<>();
        for (var id : ids) {
            var c=stats.get(id);
            var state=snapshot.units().get(id).aircraft();
            unitMetrics.put(id,new UnitMetric(id,c.path,c.minClearance,c.minObjective,
                    c.window,c.firstWindow,c.contacts,c.assigned,c.fire,c.terrain,c.collision,c.withdrawal,c.ground,
                    separation(state.position(),roster.get(id).objective()),
                    state.velocity().length()*TICKS_PER_SECOND));
        }
        Map<PairKey,PairMetric> pairMetrics = new TreeMap<>();
        for (var e : pairs.entrySet()) {
            var pair=e.getKey();
            var c=e.getValue();
            pairMetrics.put(pair,new PairMetric(pair.firstId(),pair.secondId(),c.initial,c.min,c.at,
                    distance(snapshot,pair.firstId(),pair.secondId()),c.dangerouslyClose));
        }
        Map<String,AssetMetric> assetMetrics = new TreeMap<>();
        for (var e : assets.entrySet()) {
            String id=e.getKey();var c=e.getValue();
            assetMetrics.put(id,new AssetMetric(id,c.threatTicks,c.escortsAssigned,
                    c.minThreat,c.minEscort,
                    separation(snapshot.units().get(id).aircraft().position(),roster.get(id).objective()),
                    c.threatTicks>0));
        }
        List<String> failedGates = new ArrayList<>();
        for (var pair : pairMetrics.values()) {
            if (pair.closestApproachBlocks() < 6.0 || pair.dangerouslyCloseTicks() > 0)
                failedGates.add("BODY_SEPARATION_LT6:" + pair.firstId() + ":" + pair.secondId());
        }
        for (var asset : assetMetrics.values()) {
            if (asset.corridorBreached())
                failedGates.add("ESCORT_PROTECTION_BREACHED:" + asset.assetId()
                        + ":intrusion_ticks=" + asset.threatWithinCorridorTicks());
        }
        for (var unit : unitMetrics.values()) {
            if (unit.groundedTicks() > 0)
                failedGates.add("GROUND_CONTACT:" + unit.id());
        }
        // Fixed horizon exhausts a *measurement budget*. It must never imply a defeat.
        return new Report(scenario.id(),snapshot.tick(),true,
                Collections.unmodifiableMap(unitMetrics),Collections.unmodifiableMap(pairMetrics),
                Collections.unmodifiableMap(assetMetrics),snapshot,EVIDENCE,failedGates);
    }
    private static double separation(Vec3 a,Vec3 b) { return a.add(b.scale(-1)).length(); }
    private static double distance(SquadronCommand.Snapshot snap,String a,String b) {
        return separation(snap.units().get(a).aircraft().position(),snap.units().get(b).aircraft().position());
    }
}
