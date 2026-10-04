# Airborne offline observation adapter — 2026-10-04

Status: **OFFLINE_MODEL_OBSERVATION_ONLY / NOT_RUNTIME_EVIDENCE**.

## Purpose

This adapter bridges the executable Tier A / Tier B Airborne prototype into a structured observation shape that uses the same high-level decision vocabulary as PR #80 without pretending to be PR #80 runtime evidence.

It is intentionally separate from:
- `kneekura.mod-decision-snapshot/v1`;
- source-proven adapter descriptors/class hashes;
- retained observation IDs;
- Minecraft/Forge runtime identity.

## Why a separate schema is required

PR #80's source-specific Decision Adapter SDK accepts only exact source-proven SERVER `AI_DECISION` observations with:
- a pinned adapter descriptor;
- exact mapped artifact/class hashes;
- complete run/session/process/Arena identity;
- `OBSERVED` runtime records;
- retained source observation lineage.

The Airborne prototype is an offline deterministic model. Therefore it must not emit those claims.

Its schema is:

`kneekura.airborne-model-observation/v1`

with semantics:
- `OFFLINE_MODEL_STATE_ONLY`;
- `runtime_evidence: false`;
- `retained_evidence: false`;
- no source observation IDs;
- no runtime causal relation;
- no claim that a model route was adopted by Minecraft Navigation;
- no claim that model command velocity is actual motion.

## Decision-vocabulary mapping

The adapter retains the same seven stage names only to make future runtime mapping explicit:

| Stage | Tier A | Tier B |
| --- | --- | --- |
| INPUT | NOT_MODELED | NOT_MODELED |
| STATE | air/ground state, target, terminal failure | combat state, target, blocked count, terminal failure |
| CANDIDATE | landing reservation ID only | NOT_APPLICABLE |
| EVALUATION | real world clearance NOT_MODELED | latest collision probe UNKNOWN because not retained in snapshot |
| SELECTION | intent purpose + route generation | CHASE/CHARGE model state |
| EXECUTION | route mode + recovery count | model command velocity + recovery count |
| RESULT | reason code + terminal failure | reason code + terminal failure |

These are model facts, not source-observed runtime facts.

## Tier-specific capability boundaries

### Tier A

Available in the offline model:
- air/ground state;
- tactical intent;
- route mode/generation;
- landing reservation state;
- bounded recovery.

Partial:
- target memory: current visible flag can exist, but the snapshot does not export the full SEARCH deadline/history.

Not modeled:
- actual entity motion;
- real AABB/voxel clearance;
- actual Navigation adoption.

### Tier B

Available:
- combat state;
- target/target position;
- command velocity;
- blocked/recovery counters.

Not applicable in this simplified tier:
- route objects;
- landing reservation;
- air/ground transition state machine.

Not modeled:
- LOS memory;
- actual motion.

## Read-only boundary

`createAirborneModelObservation(snapshot, options)` and `createAirborneModelPacket(observation)`:
- make no world/API calls;
- have no action authority;
- do not modify the supplied snapshot/state machine;
- deep-freeze their output;
- reject malformed non-finite modeled vectors.

## Verification

The adapter-specific suite covers:
- separate non-runtime schema;
- read-only behavior;
- deep immutability;
- all seven stage names;
- empty source-observation lineage;
- route-vs-Navigation separation;
- missing visibility remaining NOT_MODELED;
- Tier-B route/landing/LOS capability boundaries;
- command velocity remaining distinct from actual motion;
- collision probe remaining UNKNOWN when not retained;
- malformed non-finite input rejection.

The prototype test command remains:

```bash
node --test tests/*.test.mjs
```

The repository's current GitHub `.github/workflows/test.yml` runs the Python pytest suite only. It does **not** automatically execute this Node test command. A green repository CI must therefore not be reported as proof of this adapter suite unless that workflow is explicitly extended later.

## Future real-runtime adapter

A future source-proven Airborne adapter may map retained Minecraft facts into PR #80 only after it has:
- exact target/source descriptor and class hashes;
- compatible runtime identity;
- explicit subject selection;
- retained observation IDs;
- bounded source-specific capture;
- observer effect/risk declaration;
- separate actual motion/navigation/terrain evidence.

The offline adapter is a design oracle/test model for that work, not evidence from it.
