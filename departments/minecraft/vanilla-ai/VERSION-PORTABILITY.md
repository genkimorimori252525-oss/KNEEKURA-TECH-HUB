# Vanilla AI version portability

Status: **ANCHOR CORE PINNED; MODERN VANILLA FRONTIER NOT YET PINNED/INSPECTED**

ANCHOR is the exact Minecraft 1.20.1 / Forge 47.2.0 / Mojmap development artifact in [the ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json). Its access-transformed flags, descriptors, debug transport and scheduler bodies are generation-specific.

| Area | Portable concept | Exact ANCHOR constraint | FRONTIER state |
| --- | --- | --- | --- |
| Goal | Priority/flags/registered/running/lifecycle | Mob parity cadence and exact WrappedGoal replacement semantics | Version-unverified |
| Brain | Memories, activities, sensor/behavior scheduler | Registered-memory access and TTL handling; exact public/private surfaces | Version-unverified |
| Path search | Open/closed/predecessor/cost/selected path | Exact descriptor, weighted relaxation, visited budget and evaluator cleanup | Version-unverified |
| Terrain | Type defaults, effective getter, evaluated-node cost | Vehicle inheritance and evaluator-specific acceptance | Version-unverified |
| Debug transport | Typed state plus client presentation | Older channel/buffer packet; key senders dormant | Modern typed payload names are cross-version vocabulary, not ANCHOR owners |
| Custom control | Selected target/controller/phase with actual motion | Ghast/Phantom/Slime-specific implementations | Version-unverified |

A later FRONTIER snapshot must pin Minecraft/loader/mappings/source or binary identity separately, then compare changed APIs, implementation behavior, dependencies, backport approach and unavailable/risky portions. Do not mix modern typed payload records or a modern MOD's re-enabled debug hook into the ANCHOR class ledger.

The existing Twilight Forest FRONTIER is a separately researched MOD track. It is not proof of modern Vanilla AI semantics, nor a substitute for a Vanilla FRONTIER snapshot.

Community reports remain hypotheses until tied to exact source or reproduced. No new community reproduction or modern Vanilla body inspection was performed for this dated ANCHOR acquisition.
