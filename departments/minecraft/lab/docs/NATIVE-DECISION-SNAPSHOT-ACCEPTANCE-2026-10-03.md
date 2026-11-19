# Native Decision component smoke — 2026-10-03

## Exact generation and retained evidence

- LAB producer/consumer source: `f5bb9413200de33fabef72ad5dd8f3b98cf0e436`, based on PR #79 head `57e52f9ef44c082daf7abbb0b0f5ada3a258a406`.
- Native MOD workspace source: `53a84d06578632b5d123e3c2bb631b611bf830d7`; 8,444 precompiled main-output files and their source generation were checked before the explicit debug source-set compile.
- Actual integrated Minecraft 1.20.1 / Forge 47.2.0 / Java 17 client reached `DEBUG_READY` in a dedicated copy of the true debug tank. The source generation remained frozen throughout gameplay.
- Run: `run-20261003072021-4fd592619851`; process epoch 1; snapshot `snapshot-20261003072021-674efab1aaab`; snapshot hash `cf6ad864b0b7216c350d3b975894f02130b781b095737ee8e7f74921aaeeba51`.
- Finalization: **`EVIDENCE_COMPLETE`**, 1,517 canonical observations; clean Probe flush ACK final sequence 1,517, writer drops 0, remaining queue 0.
- Raw JSONL SHA256: `3023f437bbdce728393bd27bfc80de2926b23b74bf9f095c9b362462c6c1a203` (3,836,751 bytes).
- Canonical JSONL SHA256: `905473aac6a5afdca2aa5d4eae4ef84948063f8e474d6dcb52ae3b2ff2129c9f` (3,971,843 bytes).
- Private retained report SHA256: `68171afb1256a8c44144900a510ed7baf66801dba3be832c30f240d09e31b608`. Worlds, raw rows, complete snapshots, JARs, machine paths and control identities remain outside Git.

The first stop receipt was `STOP_INCOMPLETE`. Subsequent authoritative inspection verified both launcher and runtime absent, preserving the prior clean flush ACK; finalization followed this reconciliation. The initial receipt and driver report were retained, rather than overwritten as successful.

The original true debug world was read-only. All 85 file SHA256 values matched its preexisting manifest after this trial; original size 11,613,055 bytes. Prior private worlds and generated packs were retained separately.

## Component coverage

Every armed case produced all five snapshot sections with `AVAILABLE` section status: Goal scheduler, Brain memory storage, Brain activities, declared navigation route and base movement/look/jump fields. Individual opaque memory values and active Brain execution mechanisms retain their own unavailable status. Availability of stored Brain fields does not establish that a Goal-based Mob executes Brain logic.

| Selected case | Decision snapshots | Actual retained position samples | Motion segments | Sampled Goal delta events | Capture p95 (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Reimu maid, OFF | **0** | 38 | — | — | — |
| Reimu maid, ON | 80 | 4 | 0 | 0 | 0.1894 |
| Zombie | 60 | 13 | 10 | 6 | 0.2221 |
| Skeleton | 56 | 12 | 9 | 7 | 0.1293 |
| Villager | 60 | 39 | 35 | 0 | 0.2047 |
| Ghast | 56 | 49 | 47 | 13 | 0.1008 |
| Phantom | 60 | 60 | 59 | 0 | 0.0829 |
| Slime | 60 | 27 | 20 | 10 | 0.0863 |
| Dolphin | 56 | 56 | 55 | 0 | 0.0930 |
| Enderman | 64 | 28 | 25 | 6 | 0.0924 |

Selection revisions 1–10 were filtered separately with exact UUID/run/process/Arena identity. Derived Decision observations and sampled Motion traces used the retained canonical source IDs. The stationary maid's four ON position samples remain four observations; missing/keyframe intervals were not forward-filled into fake measurements or connected across the ten-tick gap limit. Goal deltas cite both snapshots and their interval, retaining unknown exact transition tick/reason and temporal association.

Cost is **synchronous component capture only**, excluding writer, consumer, rendering and total server-tick cost. The first maid ON capture reached 8.0314 ms; this is not evidence of negligible observer effect. There was no controlled comparison of equivalent behavior windows across OFF/Motion/render/snapshot/burst modes.

## Fixture and acceptance limits

The eight Vanilla subjects were persistent/invulnerable entities inside the copied tank with AI enabled. This proves exact-subject component acquisition and common Decision/Motion derivation. It is **not** full acceptance of the eight requested behavior families:

- The Skeleton had no bow/attack fixture; ranged shot, projectile and hit correlation remain untested.
- Ghast/Phantom component and motion data do not prove a representative hostile flight/attack decision.
- The Dolphin was in the tank's air/floor space; swimming navigation was not exercised.
- Enderman teleport was not forced or independently witnessed.
- Original eligibility/lifecycle hooks, actual search frontier, decision burst, terrain/malus query, client Decision UI and controlled observer effect were absent from this generation.
- Twilight Forest was not installed. Its pinned static Boss-member ledger is separate research, not runtime adapter or Boss acceptance.

Startup took approximately twelve minutes. Repeated private loose-file resource writes on K: were the main observed delay. TacZ's supported ZIP gunpack format was prepared from all 2,568 exact JAR entries, every entry SHA-checked; its existing automatic-overwrite opt-out was set only in the dedicated private game directory. Touhou Little Maid's unconditional default-pack extraction remained unchanged. Earlier startup failures/timeouts produced zero observations and are excluded from acceptance.
