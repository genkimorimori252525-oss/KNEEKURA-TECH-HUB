# Minecraft 1.20.1 Vanilla Foundation Map

Status: **IMPLEMENTED MAP PIPELINE — exact full-map artifact is generated from a pinned local Forge ANCHOR IndexSnapshot**

The Vanilla Foundation Map is the durable discovery layer for Minecraft Java 1.20.1 inside KNEEKURA TECH HUB.

It answers questions such as:

- where is a class or subsystem?
- what package/subsystem owns it?
- what does it extend/implement?
- which other Minecraft classes does its classfile structurally reference?
- which exact captured artifact/root/stage supplied that class?
- are duplicate class variants present?

It is designed so an implementation AI can discover `PathfindingRenderer`, `GoalSelector`, `Brain`, `PathFinder`, or an unfamiliar Vanilla class **from the captured 1.20.1 environment first**, rather than starting with internet search.

## What is persisted

The map is a content-addressed derived artifact in the existing Minecraft CAS.

It contains a compact index of `net/minecraft/**` classes from one exact Source Intelligence `IndexSnapshot`:

- exact owner/internal class name;
- package and primary subsystem;
- classfile hash;
- origin root / scope / stage / namespace;
- superclass;
- interfaces;
- bounded JVM `CONSTANT_Class` reference candidates;
- duplicate/ambiguous variants;
- package/subsystem counts;
- readiness anchors and coverage.

The full Minecraft/Forge JAR or decompiled source tree is **not** copied into Git.

## Evidence boundary

"Vanilla" in this map means the `net/minecraft/**` classes present in the exact captured **Minecraft 1.20.1 + Forge ANCHOR** development profile.

That may include Forge-patched Minecraft classes.

Therefore every variant keeps its origin/stage and the map does **not** claim:

- pristine Mojang source-byte identity;
- exact runtime-loaded byte identity;
- a complete dynamic call graph;
- resolved reflection/Mixin behavior.

Those require their own evidence.

## Build

First prepare/import an exact 1.20.1 Forge profile through the existing Source Intelligence path.

Then:

```bash
python -m kneekura_tech_hub.minecraft \
  --store .kneekura-cache/minecraft \
  foundation-map build \
  --index <INDEX_SNAPSHOT_ID> \
  --max-classes 20000
```

The returned `foundation_map_id` is immutable and tied to that exact IndexSnapshot.

Building the map does **not** run Gradle, resolve dependencies, download artifacts or start Minecraft. Those actions must already have happened through the explicit profile preparation path.

## Search

```bash
python -m kneekura_tech_hub.minecraft \
  --store .kneekura-cache/minecraft \
  foundation-map search \
  --map <FOUNDATION_MAP_ID> \
  --query Pathfinding
```

Optional subsystem filter:

```bash
foundation-map search --map <ID> --query Renderer --subsystem client.debug
```

## Inspect one class

```bash
foundation-map inspect \
  --map <FOUNDATION_MAP_ID> \
  --owner net/minecraft/client/renderer/debug/PathfindingRenderer
```

The result includes exact captured variants and incoming/outgoing structural-reference candidates.

## Subsystem inventory

```bash
foundation-map subsystems --map <FOUNDATION_MAP_ID>
```

Initial subsystem taxonomy includes:

- `ai.goal`
- `ai.behavior`
- `ai.memory`
- `ai.sensing`
- `ai.navigation`
- `ai.control`
- `pathfinding`
- `client.debug`
- `entity`
- `world.level`
- `server`
- `client`
- `network`
- `commands`
- `data`
- `resources`
- `core`

The taxonomy is a navigation aid, not a statement that Minecraft has only these subsystems.

## Readiness anchors

A full AI-oriented Foundation Map checks for a small set of discovery anchors, including:

- `Mob`
- `GoalSelector`
- `Brain`
- `PathNavigation`
- `MoveControl`
- `PathFinder`
- `NodeEvaluator`
- `Path`
- `Node`
- `PathfindingRenderer`
- `GoalSelectorDebugRenderer`
- `BrainDebugRenderer`
- `DebugPackets`

Missing or conflicting anchors make the map `PARTIAL`; they are not silently filled from web knowledge.

## Why this exists next to Source Intelligence

Source Intelligence is the general engine.

The Foundation Map is a **version-pinned, Minecraft-shaped navigation layer** built from that engine. It provides stable subsystem names and a compact class graph without creating a second canonical knowledge database.

The map can be regenerated whenever the exact Forge profile changes. Its content hash changes with the inputs.

## Relation to Vanilla AI research

The AI research under `departments/minecraft/vanilla-ai/` stores durable engineering conclusions.

The Foundation Map stores discoverability/provenance.

A normal workflow is:

```text
Foundation Map
   ↓ discover exact class / neighbors
Source Intelligence
   ↓ inspect source / bytecode / mappings
Vanilla AI research
   ↓ preserve verified engineering understanding
Decision Observatory
   ↓ expose useful runtime decision state
```

This prevents internet search results from becoming the hidden primary index for Minecraft 1.20.1.
