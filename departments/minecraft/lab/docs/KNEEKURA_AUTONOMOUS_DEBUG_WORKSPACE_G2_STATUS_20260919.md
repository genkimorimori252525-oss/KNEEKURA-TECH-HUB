# KNEEKURA Autonomous Debug Workspace v1 — G2 Status

Date: 2026-09-19 JST

Primary plan:
- docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_PLAN.md
- docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_G1_STATUS_20260918.md

## Status

- G0 Asset Inventory: COMPLETE
- G1 Debug Launch implementation: CODE COMPLETE CANDIDATE
- G1 real-machine acceptance: PENDING
- G2 Observation Core implementation: CODE COMPLETE CANDIDATE
- G2 real-machine acceptance: PENDING

Do not call G2 complete until the actual Forge/Minecraft development workspace passes the
G2 smoke gate against a real target UUID.

## Implemented G2 observation boundary

Current evidence architecture includes:

- L0 client/server health heartbeats (`CLIENT_TICK` / `SERVER_TICK`);
- L1 delta/keyframe state observations;
- L2 causal/sampled event lanes;
- exact UUID scoping;
- runSnapshotId/processEpoch fencing;
- canonical Observation/Finding separation;
- client/server source authority;
- lane health, drop/error accounting and freshness;
- bounded ring-buffer coverage truth;
- immutable pre-roll capture manifests;
- clean Probe flush/ACK before stop;
- immutable EVIDENCE_COMPLETE / EVIDENCE_PARTIAL finalization.

## Current exact-target lanes

Client authority:

- TARGET_TRACKED
- ENTITY_STATE

Integrated-server authority:

- SERVER_TARGET_TRACKED
- SERVER_ENTITY_STATE
- AI_TARGET
- BRAIN_MEMORY
- RUNNING_BEHAVIORS
- NAVIGATION
- TLM_STATE
- REIMU_STATE when the target is recognized as Reimu

Sampled L2:

- BEHAVIOR_TRANSITION

BEHAVIOR_TRANSITION never claims the exact transition tick or reason. It records only the
change between consecutive running-behavior samples.

## One-command real-machine acceptance

General Maid/TLM target:

    npm run debug:g2-smoke -- <entity-uuid>

Strict Reimu target:

    npm run debug:g2-smoke -- <entity-uuid> --require-reimu

The command must leave both:

    <runDir>/g1-acceptance.json
    <runDir>/g2-acceptance.json

with result=PASS.

## G2 acceptance conditions

The G2 gate requires:

1. real DEBUG_READY;
2. complete T0-T8 startup timeline;
3. live runtime re-attestation;
4. fresh L0 `CLIENT_TICK` and `SERVER_TICK` heartbeats;
5. exact target UUID control bound to debugSessionId/runId/runSnapshotId/processEpoch;
6. fresh OBSERVED complete L1 rows for every required target lane;
7. correct source authority:
   - TARGET_TRACKED / ENTITY_STATE = CLIENT
   - AI/Brain/Navigation/TLM lanes = SERVER
8. target tracked on both client and server;
9. zero required-lane health failures and zero known drop/error evidence;
10. non-truncated canonical pre-roll capture;
11. clean Probe evidence shutdown ACK;
12. EVIDENCE_COMPLETE finalization.

The acceptance manifest is write-once.

## What is intentionally not required

BEHAVIOR_TRANSITION is not required to occur during the smoke interval. A valid AI may remain
stable. Its Java producer and evidence schema are validated by CI, while real transition
evidence will be collected by scenarios that actually provoke a behavior change.

G3 Arena creation/reset/mutation is also not part of G2. Until G3 exists, the operator must
provide an existing entity UUID in the Debug World.

## Current validation evidence

PR #24 merged the hardened G2 evidence foundation into main at:

    05cd9ca229112e711796a05df04bcf77fb338500

Its final self-hosted Windows push and pull-request CI runs passed the pinned reimu-mod Forge
bridge compile gate, Supervisor selftest, G2 evidence tests, existing Node contracts, and
headless Thin Viewer.

The new g2-smoke acceptance command is the remaining code increment before real-machine G2
acceptance can be executed.

## Remaining real-machine work

1. prepare/confirm debug-workspace/config.local.json;
2. ensure KNEEKURA_DEBUG_WORLD exists;
3. obtain the exact UUID of a real Maid/Reimu already in that world;
4. run debug:doctor;
5. run debug:g2-smoke against that UUID;
6. inspect g1-acceptance.json and g2-acceptance.json;
7. only after PASS, mark G1 and G2 real-machine acceptance complete.

After G2 acceptance, the next gate is G3 World/Entity Actions and resettable Arena control.
