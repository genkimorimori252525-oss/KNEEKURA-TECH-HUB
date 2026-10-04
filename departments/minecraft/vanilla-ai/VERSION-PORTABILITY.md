# Vanilla AI version portability

Status: **ANCHOR CORE PINNED; OFFICIAL VANILLA 1.21.1 FRONTIER PINNED WITH A BOUNDED METHOD COMPARISON**

ANCHOR is the exact Minecraft 1.20.1 / Forge 47.2.0 / Mojmap development artifact in [the ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json). Its access-transformed flags, descriptors, debug transport and scheduler bodies are generation-specific.

| Area | Portable concept | Exact ANCHOR constraint | FRONTIER state |
| --- | --- | --- | --- |
| Goal | Priority/flags/registered/running/lifecycle | Mob parity cadence and exact WrappedGoal replacement semantics | 1.21.1 WrappedGoal still requires interruptibility and strictly lower priority; obsolete newGoalRate field/setter absent |
| Brain | Memories, activities, sensor/behavior scheduler | Registered-memory access and TTL handling; exact public/private surfaces | Inspected schedule/expiry bodies preserve >20-tick schedule cadence and erase-before-TTL-tick ordering; not full Brain equivalence |
| Path search | Open/closed/predecessor/cost/selected path | Exact descriptor, weighted relaxation, visited budget and evaluator cleanup | Inspected outer/inner search preserves prepare/start/inner/done, budget-before-pop and 1.5 weighted heuristic; evaluator context API differs |
| Terrain | Type defaults, effective getter, evaluated-node cost | Vehicle inheritance and evaluator-specific acceptance | PathType replaces BlockPathTypes vocabulary; new PathfindingContext can use the ServerLevel PathTypeCache; an observer query can affect cache state |
| Debug transport | Typed state plus client presentation | Older channel/buffer packet; key senders dormant | 1.21.1 has typed payload owners, but inspected Path/Goal/Brain sender bodies still return immediately |
| Core/custom control | Selected target/controller/phase with actual motion | Six core controls and Ghast/Phantom/Slime-specific implementations | [Fourteen core-control method comparisons](FRONTIER-CONTROL-CACHE-2026-10-04.md) retain caller concepts but different attribute/step APIs; custom modern controls/runtime remain unverified |

## Exact modern snapshot and evidence boundary

[FRONTIER-1.21.1-BYTECODE-LEDGER-2026-10-04.json](FRONTIER-1.21.1-BYTECODE-LEDGER-2026-10-04.json) pins the official Mojang version manifest, client binary and official mappings independently of ANCHOR. Client SHA256 is `499f6897d1837516680f3114072d8106e11c9adcd933fe5cf051b551089b0c99`; mapping SHA256 is `140c47931cccc8fc9e4c22d7603e2d714d1a953a146f51ea7397d95c955536ec`. Both official SHA1/size values were verified before inspection. Twenty-six selected core owners have class/body hashes; thirteen method bodies across seven owners were compared. Other exported bodies are not automatically semantic coverage.

JDK17 javap inspected class-major65 bytes; this is read-only inspection, not execution. The official manifest requires Java21 to run1.21.1. No new Java installation or modern client launch occurred. This official Vanilla binary also excludes Forge/NeoForge transformations; the separately pinned NeoForge damage patch is loader-specific evidence, not the Vanilla body.

Modern `DebugPackets.sendPathFindingPacket`, `sendGoalSelector` and `sendEntityBrain` each contain only `return` in this binary. Typed `PathfindingDebugPayload`/`GoalDebugPayload`/`BrainDebugPayload` existence therefore does not establish an active producer, complete candidate population or ready-made observability. Modern mods that re-enable senders require their own exact snapshot and cost/permission design.

Modern `NodeEvaluator.prepare` constructs a PathfindingContext and clears node cache; `done` clears context/Mob references. The context uses ServerLevel's PathTypeCache when the Mob's level is a ServerLevel, otherwise direct static classification. Its query result is terrain type, not original neighbor acceptance or effective Mob cost. A separate [control/cache extension](FRONTIER-CONTROL-CACHE-2026-10-04.md) now pins eight owners, fourteen core-control comparisons and seven cache methods:4096-slot exact-position direct mapping, compute/replacement, exact-position invalidation and the sendBlockUpdated call before collision-shape comparison. The original26-owner/13-method ledger is preserved. Exhaustive invalidation/loaders, every evaluator/custom control and complete modern AI behavior remain outside these bounded comparisons.

## Backport strategy and risks

Keep shared contracts at optional stages, original-return facts, UUID/context/source IDs and sampled motion. Reuse those concepts while validating each version's owners/descriptors/access and loader transformations separately. Keep ANCHOR's actual BlockPathTypes/region APIs and independently armed bounded producers; importing modern PathType/context/payload classes is not a backport strategy. Do not expose an unmeasured cache-mutating terrain query as passive observation or reactivate all debug senders globally.

No ANCHOR producer/registration changes are made by this research. Modern runtime/hook acceptance, complete subclass behavior and loader interoperability remain unverified; no modern member locator enters the ANCHOR readiness map.

The existing Twilight Forest FRONTIER is a separately researched MOD track. It is not proof of modern Vanilla AI semantics, nor a substitute for a Vanilla FRONTIER snapshot.

Community reports remain hypotheses until tied to exact source or reproduced. The separately retained Paper reports suggest diagnostic scenarios, not ANCHOR causes; no new community gameplay reproduction is claimed.
