# KNEEKURA Autonomous Debug Workspace v1 — G0 Asset Inventory

Status: G0 COMPLETE / implementation boundary
Date: 2026-09-18 JST

Primary plan: docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_PLAN.md
Adversarial audit: docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_ADVERSARIAL_AUDIT_20260918.md

## Purpose

G0 classifies existing KNEEKURA-LAB assets by responsibility before G1 implementation.

The rule is:

- retain knowledge and proven contracts;
- evolve components whose responsibility still exists;
- quarantine legacy live-Web rendering responsibility;
- do not delete research merely to make the tree look clean;
- do not let historical code define the new architecture by inertia.

## Classification vocabulary

### PRIMARY
Part of the new autonomous-debug runtime.

### RETAIN / EVOLVE
Useful contract or implementation, but not necessarily used unchanged.

### RESEARCH / REGRESSION
Useful for focused verification, offline analysis, or historical research; not the live path.

### LEGACY
Kept for history/compatibility until cleanup, but must not become a new dependency by default.

## Existing assets

### bridge/tlm-forge/src/main/java/.../sim/SimLab.java
Classification: RETAIN / EVOLVE

Why:
- proven debug-only enable gate through system properties;
- normal runtime remains effectively untouched while SimLab is disabled;
- run identity and output-root concepts already exist;
- contains real operational lessons about dev-classpath rebuild hazards.

Change direction:
- do not reuse its batch-run lifecycle as the new Supervisor;
- retain debug-only gating ideas;
- migrate identity, observation hooks, and scenario concepts into KNEEKURA Probe;
- remove the assumption that the visual laboratory is a headless/server-first SimLab.

Important known hazard:
The old runtime executes directly from mutable `build/classes/java/main`. A Gradle compile may clear/rewrite that directory while Minecraft is alive, causing late-loaded classes to fail with `NoClassDefFoundError`.

G1 therefore MUST NOT define fast restart as "compile into the same live classpath while Minecraft keeps running".

### bridge/tlm-forge/src/main/java/.../sim/trace/SimCh.java
Classification: RETAIN / EVOLVE

Keep:
- structured channels;
- machine-readable schema as the contract;
- explicit unknown/unattributed states;
- AI-decision causal intent;
- heartbeat concept.

Evolve:
- split raw evidence from AI Finding/Hypothesis;
- add provenance/epistemic metadata where required;
- support new Evidence Broker / lane health model.

### SimDelta
Classification: RETAIN / EVOLVE

Keep:
- change-only rows;
- periodic keyframes;
- entity-ID reuse protection.

Evolve:
- epoch fences;
- forced first keyframe after process/arena/resource/target epoch changes.

### Network Companion
Classification: RETAIN / EVOLVE

Keep:
- process-local trace;
- explicit run identity;
- packet/semantic milestones;
- shallow scalar payload capture.

Evolve:
- per-writer sequence and stronger cross-process causal IDs;
- finalization/completeness manifest;
- integration with Evidence Broker.

### M5/M6 and YSM probes
Classification: RETAIN / EVOLVE

Keep:
- command-intent != state-applied distinction;
- exact target identity;
- completeness/negative-evidence discipline.

Evolve:
- on-demand L3/L4 probes;
- trusted observer identity;
- render preconditions.

### SimArena / SimScenario
Classification: RETAIN CONCEPTS / PARTIAL EVOLUTION

Keep:
- controlled area;
- scenario setup;
- exact actors;
- deterministic fixture intent;
- visible cleanup logs.

Do not inherit automatically:
- old geometric limits;
- old batch completion model;
- old per-tick full-range scanning;
- assumptions created solely for Viewer replay.

New role:
- persistent Debug World + resettable Arena;
- explicit baseline fingerprint;
- typed world actions and verified receipts.

### simlab/serve.mjs
Classification: LEGACY LAUNCHER + RESEARCH UI SERVER

Useful lessons:
- process-specific kill instead of killing all Java;
- record child exit;
- preserve launch logs;
- do not trust stale DONE text;
- Gradle daemon reduced measured repeated configuration time;
- detached process lifetime matters.

Do not reuse as new architecture:
- Viewer HTTP server must not own Minecraft lifecycle;
- live rendering transport is no longer the primary path;
- process management must move to an independent Debug Supervisor.

### simlab/viewer/*
Classification: LEGACY live UI / RESEARCH

Retain:
- offline diagnostics;
- regression helpers;
- old traces;
- investigation tooling where still useful.

Do not use as:
- authoritative live rendering;
- primary Debug Workspace;
- source of Minecraft truth.

### Render Pack / RenderFrame / Golden Oracle
Classification: RESEARCH / REGRESSION

Retain for:
- focused rendering regression;
- evidence-grade visual comparisons;
- historical fidelity investigations.

Not required for normal autonomous-debug loop.

### LivePalette / Capture Camera / duplicated Web YSM rendering
Classification: LEGACY PRIMARY-PATH RESPONSIBILITY

Keep only for research/compatibility until deliberate cleanup.

No new live-debug feature may depend on these without a separate design justification.

## New assets required by G1+

These do not currently exist as a clean architecture boundary and will be added:

- `debug-workspace/` — independent Debug Supervisor / Orchestrator
- workspace registration/config contract
- dedicated debug runtime root
- debugSessionId / runId lifecycle
- launch timeline
- runtime attestation handshake
- Probe READY contract
- durable process state
- evidence/session directory ownership

## External Minecraft development workspace boundary

KNEEKURA-LAB no longer contains the old complete `runSim` Gradle wiring as its canonical launch path. The bridge reference archive explicitly says the old Gradle wiring was removed from the TLM main build.

Therefore G1 does not hard-code one repository-local Gradle task.

Instead the Debug Supervisor launches an explicitly registered real Minecraft development workspace.

Registration must provide:
- workspace path;
- launch command;
- arguments;
- debug working directory;
- environment / JVM properties as needed;
- READY handshake location/transport;
- expected runtime identity.

This lets KNEEKURA-LAB remain the laboratory while the real mod workspace remains the executable Minecraft source tree.

## G0 result

G0 is complete when the implementation obeys this boundary.

The next implementation slice is G1:
- create independent Supervisor;
- register one external debug workspace;
- create debugSession/run identity;
- isolate runtime/log directories;
- launch process;
- record T0-T8 timeline;
- wait for explicit Probe READY;
- reject stale state from previous runs.

No Viewer is required to complete G1.
