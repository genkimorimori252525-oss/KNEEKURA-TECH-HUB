# KNEEKURA-LAB History and Direction Changes

Status: historical record / architectural decision log  
Last updated: 2026-09-18 JST

This document records major changes in the purpose and architecture of KNEEKURA-LAB.
It exists so that past work remains understandable without forcing future designs to preserve old mechanisms merely because they already exist.

---

## 1. Original purpose

KNEEKURA-LAB began as an independent SimLab for observing, recording, replaying, and analyzing Minecraft / Touhou Little Maid / Reimu behavior.

A major early goal was to make verification easier than launching and operating a normal Minecraft client every time.

The project therefore developed an external Web Viewer and a set of capture / trace / replay systems around it.

The intended experience gradually became similar to a "water tank":

- define a controlled verification area;
- choose its size and environment;
- spawn an entity into it;
- observe behavior safely;
- collect reproducible evidence;
- inspect AI, network, animation, and render state;
- compare runs without depending on ordinary gameplay operation.

The Water Tank Studio work made this setup increasingly structured, with preset tank sizes, explicit run identity, controlled summon behavior, trace contracts, and evidence boundaries.

---

## 2. Why the Web-first verification machine was pursued

The Web Viewer had an attractive target:

> Open a lightweight verification environment quickly, without treating the full Minecraft client as the primary user interface.

If rendering and runtime state could be moved into a self-contained Viewer, the laboratory could theoretically be:

- quicker to open;
- lighter than a full Minecraft client;
- easier to automate;
- easier for an AI agent to inspect;
- independent from ordinary player controls;
- reproducible from saved traces and Render Packs.

This led to work such as:

- Viewer-side rendering;
- Render Pack / RenderFrame contracts;
- Golden Oracle comparison;
- LivePalette transport;
- YSM runtime capture;
- Capture Anchor / Capture Camera experiments;
- Molang and network evidence;
- stale/freshness handling;
- Same-Invocation capture design.

This work was not wasted. It exposed where the actual runtime authority lives and clarified many evidence contracts that remain useful.

---

## 3. What the project learned

The critical discovery was that high-fidelity Minecraft/YSM visualization is not naturally separable from the real client render path.

For YSM in particular, authoritative live pose information depends on the actual Minecraft/YSM render invocation.
If the relevant entity is not rendered through the real path, the same authoritative live render evidence does not simply exist for an external Viewer to consume.

As fidelity requirements increased, the "lightweight Web verification machine" therefore began to depend on an increasingly large chain:

```text
Minecraft real client
  -> entity tracking
  -> real render eligibility
  -> YSM geoRender
  -> runtime capture
  -> transport
  -> hub
  -> Web Viewer
  -> reconstructed display
```

This produced three fundamental problems.

### 3.1 Startup and resource cost did not disappear

Minecraft still had to be launched in order to obtain authoritative runtime rendering.

The Web system therefore did not remove the heavy runtime dependency that it was originally meant to hide.
Instead, it often added another application and another transport/render pipeline on top of it.

### 3.2 Complete Web reproduction was disproportionately expensive

A fully faithful migration of Minecraft/YSM rendering semantics into the Web Viewer would require continuous reimplementation of behavior already implemented by Minecraft, Forge, Touhou Little Maid, YSM, resource packs, shaders, render types, and related runtime code.

That work has poor leverage when the real client already renders the scene correctly.

### 3.3 Real-client relay still introduced fidelity and latency problems

Using the real client as the source and then relaying captured state to a Web renderer creates a second visualization path.

Even when the source data is correct, this path can introduce:

- transport delay;
- frame age;
- mismatched clocks;
- stale state;
- incomplete render semantics;
- reconstruction differences;
- additional failure modes unrelated to the Mod under test.

The laboratory can then spend more time debugging the observation system than debugging the target Mod.

---

## 4. Decision — 2026-09-18

The project judges the following goal to have failed as the primary architecture:

> "Use the Web itself as the lightweight visual verification machine that replaces the Minecraft client."

This is not a declaration that the existing Viewer, renderer research, Render Packs, Golden Oracle work, or traces were useless.

It means only that **the Web will no longer be treated as the authoritative visual execution environment for live Minecraft verification.**

The project now adopts a new boundary:

```text
Minecraft real client = verification machine / visual authority / tank
Web                 = remote control + evidence collection + analysis hub
AI                  = observer + experiment controller + debugger
```

Minecraft itself becomes the "water tank."

---

## 5. New architecture direction

### 5.1 Minecraft is the verification machine

The real Minecraft client is responsible for:

- authoritative world state;
- authoritative entity execution;
- authoritative TLM behavior;
- authoritative YSM rendering;
- camera-visible verification;
- physics and collision;
- block/world geometry;
- resource-pack and shader behavior.

The verification environment should still feel like Water Tank Studio.

The setup flow may retain concepts such as:

- Narrow / Normal / Wide / Custom verification area;
- explicit dimensions;
- generated test geometry;
- environment presets;
- fixed Mod configurations;
- entity presets;
- reproducible run IDs;
- resettable scenarios;
- controlled summon and placement;
- repeatable test positions.

The important change is that these are now realized **inside the real Minecraft environment**, rather than reproduced as a separate Web-rendered world.

### 5.2 Web becomes the control and evidence hub

The Web side should focus on tasks where it has clear leverage:

- start / stop / reset experiments;
- choose verification-area size and shape;
- select presets;
- summon or remove entities;
- issue safe experiment commands;
- inspect structured runtime state;
- browse logs and traces;
- compare runs;
- show warnings and failed evidence lanes;
- retain reports and artifacts;
- expose controls to an AI agent.

The Web is not required to duplicate Minecraft's renderer.

A Web visualization may still exist when useful, but it must be treated as a diagnostic visualization, replay, summary, or comparison surface — not automatically as the authoritative live image.

### 5.3 AI becomes an active experiment operator

A central goal of the new direction is autonomous debugging.

The AI should be able to understand the current Minecraft test state through structured telemetry and then manipulate the experiment through constrained, auditable operations.

Target capabilities include:

- query entities and their state;
- identify exact entities by UUID;
- inspect position, velocity, navigation, targets, goals, packets, Molang/YSM state, and render evidence where available;
- inspect nearby blocks and test-area geometry;
- place blocks at arbitrary allowed positions;
- construct arbitrary allowed shapes from blocks;
- clear or restore a verification area;
- teleport or reposition test entities when permitted;
- trigger test scenarios;
- observe the result;
- compare before/after evidence;
- iterate until a bug is localized or a hypothesis is rejected.

The intended loop is:

```text
AI hypothesis
  -> controlled world/action request
  -> Minecraft executes it
  -> probe records structured evidence
  -> Web hub stores/exposes evidence
  -> AI evaluates result
  -> next experiment
```

All mutations should be explicit, bounded to the active verification context where possible, and recorded so that autonomous debugging does not become unauditable world mutation.

---

## 6. What should be retained

The project should retain ideas and components that remain useful under the new boundary.

High-value concepts include:

- run identity;
- exact entity UUID tracking;
- evidence lanes rather than one generic "stale" flag;
- distinction between unknown / not-applied / not-rendered;
- M5 / M6 evidence discipline;
- network companion traces;
- safe shallow packet snapshots;
- reproducible fixtures;
- schema validation;
- scenario automation;
- controlled summon bounds;
- before/after state capture;
- source-of-truth labeling;
- Golden evidence where it is useful for regression tests;
- machine-readable logs;
- deterministic test-area setup.

These are laboratory concepts, not Web-renderer concepts.

They remain valuable even when Minecraft is the visual authority.

---

## 7. What should not be preserved merely because it exists

KNEEKURA-LAB must avoid a sunk-cost architecture.

Existing code is not automatically part of the future design.

In particular, live systems whose primary purpose is to reconstruct Minecraft/YSM's authoritative live rendering in a Web Viewer should be considered legacy/research unless they demonstrate a separate continuing value.

Examples may include parts of:

- live render reconstruction;
- Viewer-side YSM reproduction;
- capture paths needed only to feed that reproduction;
- camera machinery created only to keep the external live renderer supplied;
- live transport stages that exist only between real rendering and duplicated Web rendering.

These components should not be copied into the new architecture by default.

When an old component is considered for reuse, ask:

1. Does the new architecture need this responsibility?
2. Is there a simpler way now that Minecraft is the visual authority?
3. Does it improve debugging fidelity or merely preserve prior investment?
4. Can the useful contract or idea be retained without the old implementation?

Historical code may remain for reference until deliberate cleanup, but it must not silently become a compatibility burden.

---

## 8. Debugging-first Mod strategy

The new architecture makes in-game observability more important.

Future investigation should consider existing Forge 1.20.1 debugging/profiling Mods and libraries before implementing duplicate functionality.

Useful categories include:

- tick and CPU profiling;
- entity / block-entity cost inspection;
- networking diagnostics;
- NBT / capability inspection;
- entity UUID and runtime-state inspection;
- command/debug overlays;
- world and chunk diagnostics;
- memory/startup optimization for the development profile.

KNEEKURA should build custom probes only where generic tools cannot expose the TLM/YSM-specific information required by the laboratory.

Likely custom-probe territory includes:

- exact TLM AI state and goal transitions;
- exact tracked Reimu identity;
- YSM/Molang state;
- animation-controller evidence;
- YSM render-entry / render-complete milestones;
- test-specific network semantics;
- experiment receipts binding actions to resulting evidence.

The rule is:

> Prefer existing mature diagnostics for generic Minecraft information; reserve KNEEKURA code for information unique to the experiment.

More information usually makes debugging easier, but every probe also changes maintenance cost and can perturb timing.
Observability should therefore be structured, selective, and measurable rather than "log everything."

---

## 9. Quality rule for the transition

The goal is not to preserve the maximum amount of Water Tank Studio.

The goal is to preserve the maximum amount of **validated knowledge** while minimizing unnecessary architecture.

During migration:

- keep old evidence and history;
- keep reusable contracts;
- keep useful test concepts;
- keep code only when its responsibility survives;
- do not keep a subsystem solely because it took a long time to build;
- do not delete research before its useful findings are captured;
- do not let compatibility with an abandoned direction reduce the quality of the new design.

In short:

```text
Preserve lessons.
Preserve evidence.
Preserve useful contracts.
Do not preserve complexity for sentimental reasons.
```

---

## 10. New target

The long-term target is no longer "Minecraft recreated in a browser."

It is:

> A real Minecraft verification environment that can be configured, observed, and manipulated remotely, with enough structured evidence that an AI can autonomously design and execute debugging experiments.

The real client provides fidelity.

The Web provides reach and organization.

The probe provides information.

The AI provides iteration.

That is the new KNEEKURA-LAB direction from 2026-09-18 onward.
