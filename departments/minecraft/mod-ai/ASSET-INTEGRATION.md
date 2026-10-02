# MOD-AI asset and client integration — approved scope, 2026-09-28

Status: active integration design; implementation and live acceptance are separate.
Parent: [MOD-AI design v1.4](../design/2026-09-28-mod-ai-environment/DESIGN.md).
Execution: [unified plan](../../../docs/superpowers/plans/2026-09-28-minecraft-mod-ai-unified.md).
Baseline: PR #73, `89cb81f412dd91df64785940569028e1a8be9920`.
Historical executable verification stays at `3fa14453327e7992231e3d479ac1d1eebbd96b3c`.

## Intent and decisions

Enable the existing coding AI to investigate, make assets, implement, build,
observe the actual game, repair, and retain evidence. The user selected
`sosadly/blockbench-mcp` and approved integration into TECH HUB, not a separate
product. User approval on 2026-09-28 authorizes merging the plans and beginning
implementation in this session; it does not authorize a main/parent-PR merge,
a visibility/credential change, a production-world change, or unlimited launches.

Use `departments/minecraft/mod-ai/` and `src/kneekura_tech_hub/minecraft/`.
The earlier conversational `labs/minecraft_mod/` tree and separate Planner,
Code Agent, Asset Agent and Verifier services are NOT additional subsystems.
These are roles of the existing host AI and small adapters. No new scheduler,
canonical database, autonomous development agent, or duplicate run manager.
Knowledge Core and the existing SourceSnapshot/Evidence/staging gates stay intact.

## Preserve the already implemented work

Reuse `storage.Store`, ProjectProfile, source/bytecode search, resolved-input
capture, registered execution, `contracts.prepare_contract`, authenticated
Observer, command receipts, and GameTest oracle. Server-side success remains
limited to its recorded disposable probe, not rendering or product correctness.
Do not reapply an older conversation ZIP or reproduce an already fixed command
success/outcome seam. Keep the foundation session and all old test ledgers.

## Provider evidence, not README promises

Selected asset backend: `sosadly/blockbench-mcp` at
`028cdd76589de2e2cea51bfd79495b50a3c7d1d2`.
`src/client.ts` uses GET `/ping` and POST `/command` with `{id, action, params}`;
the plugin declares protocol 1. Its bridge is desktop-only, loopback, and does
not attest the loaded source revision. Arbitrary `execute_script` is not a sandbox.
This initial slice speaks that bridge protocol, NOT a newly implemented MCP server.

Vibecraft remains a research reference, not an installed runtime driver.
At `fc02e08a485e1effa0e2251bc69934c213ce232f`, root `build.gradle` applies
NeoForge moddev with Java 21. `run-test.sh` references
`com.vibecraft.automated.VibecraftTestRunner`, but the documented
`src/test/java/com/vibecraft/automated/VibecraftTestRunner.java` returned 404.
The README's Fabric 1.21.8/RPA narrative is not Forge 1.20.1 compatibility evidence.
Use its idea of real input plus observations only after locating and checking
reusable code; do not count screenshots, Windows support or a repair loop as supplied.

Exact source references:
- https://github.com/sosadly/blockbench-mcp/blob/028cdd76589de2e2cea51bfd79495b50a3c7d1d2/src/client.ts
- https://github.com/sosadly/blockbench-mcp/blob/028cdd76589de2e2cea51bfd79495b50a3c7d1d2/plugin/blockbench_mcp.js
- https://github.com/marcusgreenwood/vibecraft/blob/fc02e08a485e1effa0e2251bc69934c213ce232f/build.gradle
- https://github.com/marcusgreenwood/vibecraft/blob/fc02e08a485e1effa0e2251bc69934c213ce232f/run-test.sh

## First vertical slice: one static Java item

A strict versioned ModSpec contains a namespaced asset ID, `java_item` kind,
visual brief, StyleProfile, reference CAS hashes and required views. Style pins
texture dimensions, palette and pixel-art shading. No filesystem destinations,
permissions, commands, script code or plugin installation settings belong in a spec.
Natural-language text is untrusted task data, never execution authority.

`prepare_request(store, profile=..., spec=..., index_id=...)` verifies captured profile identity,
complete coverage, Minecraft 1.20.1/Forge/exact 47.x/Java 17, and reference availability.
It records the immutable spec, style and profile in the EXISTING CAS. When an
existing index is supplied, verify its profile matches and pin that index too. It derives
relative export destinations from the resource ID; it writes no model/resource files.
Unknown/partial profiles cannot silently become confirmed targets. Exact Forge
version comes from the profile; 47.4.6 is not a forced upgrade of existing MODs.

The first supported export target is a static Java item model plus PNG and editable
`.bbmodel`. GeckoLib entity/item/armor and animations are later task-specific formats.
An inventory icon is not a worn armor mesh. A static Java JSON is not a GeckoLib
geometry/animation envelope. Do not add GeckoLib to a simple staff by default.

The provider boundary initially exposes only `/ping`, `get_status`, `list_formats`.
An explicit user-managed read-only registry enables probes. Imports, spec checks,
and planning do not contact the network. Fixed 127.0.0.1, bounded port/response/time,
no proxy/redirect, strict envelopes and response-ID matching, and no retries.
Probe responses are observations, NOT source attestation, visual review, or a
behavior PASS. Mutations and execute_script are unavailable in this slice.

## Subsequent write and export boundary

Before enabling geometry/texture/export calls, bind an exclusive disposable editor
project/session and managed staging directory, pin installed plugin bytes, and prove
path/overwrite/project-switch defenses in the writer or a narrow plugin shim.
A client-side policy does not sandbox another MCP client or the upstream plugin.
Default-off execute_script and plugin install/uninstall must be enforced, not merely
written in a prompt. Unknown completion after a write means UNKNOWN, not retry.

Generate -> structural checks -> bounded multi-view render -> host-AI review -> repair
-> export/capture. Keep native `.bbmodel`, output bytes and review references.
Quality follows silhouette, style, UV and in-game legibility, never a minimum cube
count or an automatically trusted upstream match-percent/complexity score.
Fix assertion requirements before generation; changing them is an explicit spec change.

Structural, visual, and runtime outcomes remain separate. A screenshot file alone
is not an aesthetic or behavior verdict. Missing, stale or mismatched evidence never
passes. Inventory, first/third-person transforms, particles, damage, cooldown,
network synchronization and performance require their own stated observations.

## Runtime and knowledge integration

Reuse the existing Forge observer's client capture source before adding a screenshot
system. Keep `run_id`, epoch, profile, built artifact, world and scenario identities.
Real user input must target the verified foreground game window and release keys on
failure. A command-based test cannot claim actual right-click coverage. Windows and
client/render/network/performance acceptance are not inferred from Linux server tests.
Do not launch a home self-hosted runner while the repository is public.

The actual Vineflower/tiny-remapper execution and new Core caller-path acceptance
remain required outstanding work; not provided by Blockbench or Vibecraft. Exercise
existing adapters when the pilot needs them and before declaring full acceptance.
Upstream research stays Twilight Forest first, Connector next. Record this integration's
own failures/repairs in the existing history format; no duplicate history database.

Stop expanding after one real MOD editing cycle and its declared acceptance. A missing
capability gets the smallest evidenced repair, not a speculative platform project.
