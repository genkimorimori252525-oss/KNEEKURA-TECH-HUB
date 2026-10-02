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
| `wither_random_attack_pos_goal` | CANDIDATE | phase-1 reposition controller | Exact movement/timing still requires observation. |\n| Mojang `wither_skull*.json` at `46ba6ea9…` | ADOPTED_CONCEPT | custom normal/dangerous projectile contract | Uses exposed power 1.2/0.6, inertia 1.0, dangerous reflection gate, max resistance 4.0 and shared effect/explosion values. Java semantic gaps remain adaptation targets. |
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
