# AI Improvements — benchmark contract (none run yet)

Uses [軽量化 BENCHMARK-SPEC](../../BENCHMARK-SPEC.md). **All results: NOT_RUN**. This is a reproducibility plan, not a claim of improved performance.

## Paired A/B

**A:** Minecraft 1.20.1 + Forge + chosen full dependency closure, AI Improvements absent.  
**B1:** same world/JVM and baseline mods, AI Improvements installed with original defaults.  
**B2:** same baseline, `replace_look_controller=false`; selected look Goal removal toggles individually.  
**B3:** same baseline, `replace_look_controller=true`, selected removal toggles false, compare to isolate lookup math.

Collect exact Forge/JAR hashes and loaded config before every comparison. The historical 1.20 Forge source does not by itself verify compatibility with the requested 1.20.1 runtime; this is a gate before trials.

## Scenarios and metrics

| Workload | Scenario | Performance readings | Correctness checks |
|---|---|---|---|
| `SERVER_AI_VANILLA_DENSE` | repeatable batches of zombies, cows, chickens and fish | MSPT median/p95/p99, entity AI tick time, allocations/sec, heap+GC | matching entity/Goal eligibility; target acquisition and movement |
| `SERVER_AI_INVASION_ATTACKERS` | siege enemies with normal targets and wall/bridge AI; compare 1/10/50/100 active attackers | MSPT + planning cost + pathfinding count + profiling methods | successful attack, obstacle selection, retained Goal ownership, no stalling |
| `SERVER_AI_BOSS_AIM` | single/multiple rotating ranged bosses and independent aiming emitters | server tick phase time; optional client frame times | pitch/yaw error distribution, range accuracy, turn animations, targeting |
| `SERVER_AI_ENTITY_JOIN_STORM` | repeatedly spawn/despawn fixed batch with stable species ratio | event handler invocations, CPU per spawn, allocation count | exactly-once modifier application and repeat loading |
| `SERVER_AI_MIXED_MODS` | fixed combination of other custom Mob/Goal mods | MSPT, conflict errors, mixin reports | no deleted required Goal, no invalid custom LookControl override |

For each: warm-up (JIT/GC/chunks), repeated sampled runs, same fixed world seed and spawn pattern, Java+OS+hardware+heap, experiment version/config, raw profiler artifacts and source hashes. No device/capability-specific percentages are assigned without observations.

## Correctness acceptance required alongside performance

- `lookAngleDiff` within measured, explicitly chosen gameplay tolerance; separately analyze accuracy for near-zero and high-speed turn inputs.
- Targeted mobs can still find players, make expected attack decisions and face target where required.
- Disabled optional animal/look Goal changes are acknowledged gameplay changes, **not** "semantically equivalent optimizations."
- Third-party custom look controls and attack controllers remain untouched.
- Existing AI pathfinder safety, entity ownership, world cleanup and dimensional transitions unchanged as appropriate.
- Dedicated server and client variants tested separately; do not promote a single-simulation smoke test to cross-mod compatibility.

**Blocking status:** NOT_RUN. No "fast" or +X% claim in catalog until paired results and regressions are independently examined.
