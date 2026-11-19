# Bedrock Wither — Technology Adoption Ledger

This file is the boundary between research and product implementation.

Statuses:
- `REFERENCE`: useful background only.
- `CANDIDATE`: may be adopted after verification.
- `ADOPTED_CONCEPT`: concept accepted; implementation remains KNEEKURA-owned.
- `ADOPTED_IMPLEMENTATION`: concrete external implementation reuse approved with license/provenance recorded.
- `REJECTED`: deliberately not used.

| Source / technique | Status | Product use | Notes |
|---|---|---|---|
| Microsoft Bedrock Wither entity JSON | ADOPTED_CONCEPT | exposed target range, flight and dedicated goal semantics | Public behavior surface is incomplete; not full native implementation. |
| `wither_target_highest_damage` | ADOPTED_CONCEPT | explicit bounded threat ledger | Reimplemented independently for Java. |
| `wither_random_attack_pos_goal` | ADOPTED_CONCEPT | ordinary phase-1 reposition controller | Source-shaped target-relative path with explicitly provisional radius and Java navigation; no empirical equivalence claim. |
| Mojang `wither_skull*.json` at `46ba6ea9…` | ADOPTED_CONCEPT | custom normal/dangerous projectile contract | Uses exposed power 1.2/0.6, inertia 1.0, dangerous reflection gate, max resistance 4.0 and shared effect/explosion values. Java semantic gaps remain adaptation targets. |
| Java 1.20.1 `WitherBoss` | REFERENCE | API/behavior comparison and vanilla control | Not the behavioral superclass. |
| Vanilla `WitherSkull` | REFERENCE | Java API/impact-effect reuse only | Custom KNEEKURA skull entity now owns Bedrock launch speed, inertia, reflection gate and resistance cap. |
| BEStyleWither charge Goal decomposition | REFERENCE | engineering hint only | It does not define Bedrock timing, state ordering or dash constants. No upstream source copied. |
| BEStyleWither constants | REJECTED | none | Not evidence of exact Bedrock values. |
| BEStyleWither vanilla-Wither Mixin architecture | REJECTED | none | Risks Java AI leakage and attribution ambiguity. |
| KNEEKURA Tank observation pipeline | ADOPTED_CONCEPT | bounded comparative verification | Infrastructure remains owned outside this deliverable. |
| KNEEKURA Failure/Repair History format | ADOPTED_CONCEPT | own regression/repair records | Product incidents use `origin=OWN_DEVELOPMENT`. |
| Vanilla death lifecycle semantics | ADOPTED_CONCEPT | preserve killer/death-event identity while extending visuals | BEStyleWither Issue #4 demonstrates compatibility failure when a boss is artificially held alive for a delayed death effect. |

## Rule for future adoption

Before a new external technique changes product code, add:
- exact source/revision or runtime observation;
- license/provenance state;
- what is being adopted: concept vs code;
- adaptation risk;
- acceptance test that will detect an incorrect transfer.

No AI should infer permission to copy code from a research link alone.


## Reusable technique note

Cross-product patterns extracted from this work are maintained at:
`departments/minecraft/techniques/boss-combat-state-machines.md`

This product ledger remains authoritative for whether the Bedrock Wither actually adopts each pattern.


## Product evidence order

Bedrock behavior is implemented from:

1. pinned Mojang/Microsoft definitions;
2. direct Bedrock runtime measurement;
3. Bedrock-focused technical documentation;
4. community reports;
5. Java prior art such as BEStyleWither.

BEStyleWither is never sufficient by itself to set a Bedrock gameplay constant or phase rule.


## 2026-10-03 source-backed software completion

The user chose to complete code without empirical Bedrock/Tank measurements. Source-labelled provisional policies may therefore execute in the product; they do not become current-native or measured facts. [Audit and exact source links](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/SOURCE-AUDIT-2026-10-03.md) and [completion plan](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/SOURCE-COMPLETION-PLAN-2026-10-03.md) define the scope.

All following entries are independent `ADOPTED_CONCEPT` implementations, not copied upstream code. Mojang JSON/schema is the exposed contract; Java assets remain runtime references. The historical decompiled repository has unresolved game-version/provenance limitations, so no source text or binaries are redistributed and its numeric choices are explicitly provisional.

| Input and version | Adopted behavior | Adaptation / uncertainty | Acceptance surface |
|---|---|---|---|
| PeratX native goal, `ea30a251…` | horizontal target-relative repositioning; own-height destination; flight modifier 15; stop-shot delay 20; separate native-shaped aerial height 5/damping0.6/ascent0.5 | Java RNG/path navigation and finite path budget; FlyingMoveControl uses 180° pitch and 90° yaw per control update, not native yaw semantics; radius 10 is the official ordinary-stroll default used as an inherited-default fallback, not a recovered Wither initializer | ordinary entity ticks move, hover and emit the 3+1 volley; blocked/invalid paths recover |
| MinecraftWiki Wither, retained 2025-11 snapshot; current BDS second-volley field | phase-2 firing continues; charge follows alternate volleys | historical preparation/recovery 20; horizontal speed 2 is a bounded Java projection of native doubled X/Z motion, not a recovered 3-D trajectory | ordinary phase-2 firing, charge, motion, termination and resumed firing |
| Historical health/damage body `ea30a251…` | base rate 20; maxHP/6 interval; one strict-threshold halving per accepted damage event, Easy excluded; reset at phase boundary | corrected earlier `/3` misread; ties-even rounding and minimum 1 are declared Java choices; separate documented 75-HP NBT bucket is retained; phase-boundary cursor reset is a Java adapter to honor the reported second-phase stages | acceleration, healing, large-hit and reload policy; actual projectile gap independent of per-shot rate |
| BedrockWiki revision 692 | 3+1 identity; reported seven-second volley pause; approximately 20 active dash ticks; 15 damage corroborated by native body | modern exact interval not empirically established; historical active duration 10 is retained as a disagreement rather than silently substituted | sequence and boundary tests; exact selected-software-policy counters |
| MinecraftWiki 2025-11 half-health description | descend before one explosion; Normal/Hard three skeletons, Easy none | bounded Java descent and terminal fallback; power 7 historical/corroborated; exact modern ordering not claimed | ordinary descent, one-shot event, immunity, save recovery |
| MinecraftWiki 2025-11 attack-specific block description | charge cannot destroy obsidian, dangerous skull can | other uncertain block differences retain documented conservative Java exclusions | charge/projectile obsidian distinction and unbreakable collision recovery |
| Mojang projectile definition, pinned `46ba6ea9…`, format 1.26.50; official component docs | launch 1.2/0.6; zero gravity; air/liquid inertia 1; configured reflection immunity 0; owner grace 5 ticks; projectile-on-projectile reflection documented from 1.26.0 | same-root-vehicle grace and retained reflection-vector/speed policy are Java adapters; current repeated-reflector native rules unproved | actual tick collision/effect/heal path, liquid/air travel, timed owner collision, non-damaging reflection and Forge skipped impact |
| Mojang client/render controllers at `46ba6ea9…` | literal degree and floating Molang expressions; white and blue shield layers; partial ticks; unlit armor | Java bundled armor texture and explicit blue tint are substitutes, not Bedrock texture/appearance parity | production-used pure presentation math and shield/death visibility inputs |
| Entity-format oldid2689647, dated 2024-09-17 | native Phase=0 during death; AirAttack remains separate shield-visibility input | normalize older product death saves; retain Forge semantic death and cancellation | accepted first-phase death, NBT restoration and existing revival cases |
| Historical death body `ea30a251…` | 200 countdown, power 7, swell +1/28, overlay +0.005, decreasing flicker divisor initially 15 | source-derived visual policy; current exact equations/reward timing unproved; ordinary Forge rewards are not delayed or duplicated | ordinary death ticking, flicker persistence, terminal removal and 50-XP/one-star regression |
| MinecraftWiki 2025-11 Bedrock drops | dropped Nether Star has no timed despawn | Java unlimited-lifetime item flag; preserve normal loot capture/events and count | actual dropped item survives ordinary expiry duration and item NBT reload |

### Non-authoritative structural slots

Native `ShieldHealth`/`MAX_SHIELD_HEALTH` field existence does not establish a distinct damage pool. Their diagnostic mirror is not a new gameplay mechanic and does not block source-backed software completion. Shield behavior is the documented phase projectile immunity and separately synchronized AirAttack visibility. Do not invent a finite shield pool solely to make every mirrored field nonzero.


The pinned official `minecraft:persistent` component also requires a species-level Java custom-persistence override. It prevents ordinary distance/idle-random despawning even after old NBT loads a false persistence flag. Java's earlier Peaceful-removal branch remains unchanged. New and real-NBT-restored bosses are tested through `Mob.checkDespawn` with a distant registered eligible player.
