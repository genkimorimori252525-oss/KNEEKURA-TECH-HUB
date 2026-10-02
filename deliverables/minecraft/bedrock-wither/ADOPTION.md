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
| `wither_random_attack_pos_goal` | CANDIDATE | phase-1 reposition controller | Exact movement/timing still requires observation. |
| Java 1.20.1 `WitherBoss` | REFERENCE | API/behavior comparison and vanilla control | Not the behavioral superclass. |
| Vanilla `WitherSkull` | CANDIDATE | projectile primitive when behavior matches | Boss cadence/ownership stays product-controlled. |
| BEStyleWither charge Goal decomposition | ADOPTED_CONCEPT | separate dash sequencing/controller | Technique only; no upstream source copied. LGPL-3.0 prior art remains linked in research. |
| BEStyleWither constants | REJECTED | none | Not evidence of exact Bedrock values. |
| BEStyleWither vanilla-Wither Mixin architecture | REJECTED | none | Risks Java AI leakage and attribution ambiguity. |
| KNEEKURA Tank observation pipeline | ADOPTED_CONCEPT | bounded comparative verification | Infrastructure remains owned outside this deliverable. |
| KNEEKURA Failure/Repair History format | ADOPTED_CONCEPT | own regression/repair records | Product incidents use `origin=OWN_DEVELOPMENT`. |

## Rule for future adoption

Before a new external technique changes product code, add:
- exact source/revision or runtime observation;
- license/provenance state;
- what is being adopted: concept vs code;
- adaptation risk;
- acceptance test that will detect an incorrect transfer.

No AI should infer permission to copy code from a research link alone.
