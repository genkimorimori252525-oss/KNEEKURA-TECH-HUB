# Twilight Forest ANCHOR Boss correspondence

The privately retained distributed artifact is `twilightforest-1.20.1-4.3.2508-universal.jar`, 23,332,091 bytes, SHA256 `0bdc89263616d1b35c32ef82c5e9c14cbd20368e2fe8b468c72a28320be7a778`. It is not installed in the native workspace.

[Selected class/member ledger](TF-ANCHOR-BOSS-BYTECODE-LEDGER-2026-10-03.json) contains eight exact class/disassembly hashes and selected member descriptors. Five source blobs at `TeamTwilight/twilightforest@a7dd8f13c653e137f977f5ffaa870fcb20fc1625` were independently Git-blob SHA1 checked. Whole sources, class bytes and javap bodies remain private.

| Owner | Verified static storage/member surface | Interpretation limits |
| --- | --- | --- |
| Hydra | `numHeads`, `hc` | Coordinator and per-head storage; not one Vanilla Goal list. |
| HydraHeadContainer | `headNum`, `prevState`, `currentState`, `nextState`, `ticksNeeded`, `ticksProgress`, `targetEntity`, `headEntity`; exact State enum | Sampled head state can cite a stored assigned target, but direct transition/attack execution needs original-call evidence. |
| SnowQueen | `PHASE_FLAG`, `BEAM_FLAG`, summon/drop/damage counters; `SUMMON`/`DROP`/`BEAM` enum, phase methods | Synchronized phase and its actions are distinct. Merely observing different phase snapshots cannot prove an exact transition invocation. |
| KnightPhantom | `number`, `ticksProgress`, `currentFormation`, `chargePos`; exact Formation enum | Local slot/formation clock is not proof of group leader/shared-target membership. Group claims require separately acquired exact subjects. |
| UrGhast | `DATA_TANTRUM`, `damageUntilNextPhase`, `nextTantrumCry`, tantrum/phase methods | Custom flight and phase state must remain separate; absent A* path cannot become a fabricated candidate route. |

This is **selected static source/member correspondence**. The JAR uses distributed SRG Minecraft members while named custom Boss members are retained. It does not establish complete source/class equivalence, deobfuscated development artifact identity, post-Mixin resident bytes, native adapter behavior, or FRONTIER compatibility. Adapter SDK/production capture follows proven Vanilla hooks; the ledger does not bypass that prerequisite.
