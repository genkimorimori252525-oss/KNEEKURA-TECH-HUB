# Bedrock Wither — Current Status

Updated: 2026-10-02  
Lifecycle: **PROTOTYPE**  
Milestone: **BWR-M1 — standalone boss skeleton**

## Current truth

Completed:
- Bedrock behavior research/design is separated under `departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/`.
- Official/community/prior-art evidence is separated by confidence.
- BEStyleWither is a comparative implementation reference, not specification authority.
- Deliverables boundary and permanent product layout are established.
- Initial Forge 1.20.1 source scaffold is kept under `mod/`, not the research department.
- Standalone entity registration, boss bar, state enum/state-machine shell, flight navigation base, ambiguity-preserving threat ledger and read-only debug snapshot compile successfully.\n- Mojang current vanilla Wither definitions are pinned at `46ba6ea985fb5a92d79a9419198f10dda14c199d`; official collision/turn/immunity/undead-damage rules have replaced earlier Java-like scaffold assumptions.\n- A custom skull entity now encodes Mojang-exposed normal/dangerous projectile values; its exact post-change build result is still pending at this checkpoint.
- Dedicated product CI has a retained RED→GREEN history: BWR-0001 failed on a Java wildcard Optional boundary and the exact repaired source then built successfully.
- Reusable boss lifecycle/state-machine lessons are separated under `departments/minecraft/techniques/`.

Not yet established:
- client renderer/model;
- spawning/registration runtime acceptance;
- Bedrock reference measurements for TBD constants;
- Phase 1 skull cadence;
- 50% transition runtime;
- dash/destruction behavior;
- Tank comparative acceptance.

## Next action

1. add minimal GameTest smoke coverage for registration/state persistence/difficulty-health candidate behavior;
2. add a bounded client renderer placeholder, then the real three-head renderer/model;
3. wire damage observation into the threat ledger without selecting a metric until the Bedrock reference settles it;
4. only then implement targeting/phase-1 behavior;
5. replace `TBD_MEASURE` constants with direct Bedrock observations before claiming parity.

## Safety against stale handoff

Any document claiming later progress must update this file in the same product change or explicitly state why this status remains current.

Old plans/checkpoints do not override this file.
