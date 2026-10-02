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
- Initial Forge 1.20.1 source scaffold is being kept under `mod/`, not the research department.

Not yet established:
- clean Forge compilation of this new product scaffold;
- client renderer/model;
- spawning/registration runtime acceptance;
- Bedrock reference measurements for TBD constants;
- Phase 1 skull cadence;
- 50% transition runtime;
- dash/destruction behavior;
- Tank comparative acceptance.

## Next action

1. finish/compile the standalone entity skeleton;
2. add read-only debug snapshot;
3. add minimal GameTest smoke coverage;
4. only then implement targeting/phase-1 behavior;
5. replace `TBD_MEASURE` constants with direct Bedrock observations before claiming parity.

## Safety against stale handoff

Any document claiming later progress must update this file in the same product change or explicitly state why this status remains current.

Old plans/checkpoints do not override this file.
