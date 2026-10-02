# Recovery acceptance review — 2026-09-30

**U04 rendering is satisfied within the observed default/no-JAPPA configuration. M4 staff acceptance is NOT_RUN, and the overall plan remains incomplete.**

Repository checkpoint: `a57ffb32adc6a0e1f0a5d06cf45d58c407fe1679`. Minecraft 1.20.1, Forge 47.4.6, Java 17, Twilight Forest 4.3.2508, Gradle 8.8 and ForgeGradle 6.0.54. This is a minimized derived review; original evidence and outcomes remain unchanged.

## Original U04 criterion and scope

The original acceptance contract requires linking renderer/model/texture evidence with runtime observation and forbids treating GameTest alone as rendering success. The fixed U04 fixture additionally requires same-run screenshot/frame/camera, selected configuration and server interval. The existing static investigation traced both renderer/model branches and hydra4.png. This run supplies those missing runtime fields for the default branch. Exact-pixel inspection independently confirms visible Hydra geometry and texture. **Another Hydra run is not required for this scoped original criterion.**

The client observed `twilightforest.entity.boss.Hydra`, dispatcher-selected `HydraRenderer`, no JAPPA marker, and `twilightforest:textures/model/hydra4.png`. The retained registration route links this selection to `HydraModel`; the actual model instance was not reflected. JAPPA rendering remains NOT_RUN. No source/model repair, before/after comparison, combat, every-pose correctness or performance result is claimed.

## Captured views

| Capture | Actual view and visible result | Actual camera (x, y, z; yaw, pitch) | Frame | Server ticks |
|---|---|---|---|---|
| 014-hydra-front | front: Hydra body and three active heads visible. Highest central head is clipped by the top edge and partly overlaid by the boss bar; this is not a full-frontal framing claim. | 0.5, 65.61999988555908, -29.5; 0.0, 10.0 | 1239 | 1416–1420 |
| 018-hydra-oblique | side: Full side silhouette, tail, body, feet and head/neck geometry are within the frame. Heads overlap in side projection. | 30.5, 73.6180153316199, 0.5; 90.0, 10.0 | 2235 | 2464–2468 |
| 019-hydra-settled-oblique | oblique: Three active heads, body, feet and tail are visible. Boss bar overlaps the upper region; no claim of an unobstructed presentation image. | 23.5, 65.61999988555908, -24.5; 43.0, 12.0 | 2971 | 3251–3256 |

014’s high central head is clipped at the top, while 018 provides the complete side silhouette. Together with 019, the images establish a visible three-active-head Hydra without inventing a requirement for perfect frontal framing. Capture 016 retained the front camera after the server teleport and is excluded as a distinct side view. Actual observed camera values take precedence over command destinations.

All three retained payloads match the same contract/run/epoch, selected archive, frame, camera and PNG SHA-256. Intervals are explicitly non-atomic. The helper reports dispatcher selection and `visibility=NOT_ESTABLISHED`; the generic observation outcome remains `NOT_RUN`. The scoped visual PASS is this separate pixel review, not an altered observer or launch verdict.

## Provenance and execution limits

The original distribution SHA-256 is `0bdc89263616d1b35c32ef82c5e9c14cbd20368e2fe8b468c72a28320be7a778`. The selected runtime archive is the separately retained Tiny Remapper 0.11.2 derivation `69e27b79067a9ce3bff3da18abd7b09b1ef4bc99625c07ea0c09424712df72bb`, with receipt `c005d50d88496d977b9afea730ba0bd585f076cd04a67251381b384127d0243c`. The provider records SRG-to-Mojmap derivation; the exported namespace remains `unknown`. Original non-class resources are byte-identical. Source commit `a7dd8f13c653e137f977f5ffaa870fcb20fc1625` has resource correspondence only: compiled source-class equivalence and ForgeGradle equivalence are not established. The fixture marker’s compile artifact is distinct from the selected Twilight dependency. Target-code/dependency-byte identity does not attest every transformed loaded instruction.

Platform, daylight/weather controls, summon and the three camera commands completed PASS. The full requested staging list was not executed; initial creative mode came from the prepared world. See the JSON for individual command outcomes, server ticks and hashes. Dynamic game options are not continuously attested.

## Staff result

No staff-use gesture or staff-equipment command executed. The first creative-mode command completed with result 0 but retained UNKNOWN; its bare-UUID target failed player-only selector validation, so the dependent equipment sequence stopped. The control baseline held air, health 20, no Glowing/cooldown and zero client-use trace starts/completions. The invoker pair failed HTTP 409, with no retained specific exception proving its cause. The control Gradle daemon disappeared after joining. No uncertain command/input was retried. First use, client non-mutation, non-invoking control, cooldown repeat/expiry and dedicated synchronization all remain NOT_RUN.

## Bounds and closure

The batch started 2026-09-30T15:39:03.616235Z, with a 1,500-second absolute limit, 900 seconds for staff, 480 for Hydra and 120 reserved for cleanup. Each of four roles used one attempt; no retries or deadline extension occurred. Hydra launched at 2026-09-30T15:51:58.345612Z. Its receipt `b166d6044283da3d07ea7976a6713fe5a878c6e602c94c40f029c2ae566e16ec` remains **BLOCKED**, timed_out=true, completed=false and exit −9 after 457.369 process seconds. Visible frames captured before that termination remain usable for the scoped rendering review; graceful launch/gameplay completion is not claimed.

Controller cleanup recorded all execution threads closed and zero owned game processes at 2026-09-30T16:00:23.054579Z, 1279.438 seconds after batch start. The final actual-desktop probe at 2026-09-30T16:01:36.647979Z again found zero processes. Its SHA-256 is `f13c2b0034f090641cc37f863dac50ecda65199041fad7f3a1fba2a2f1ae55b6`.

## Minimized evidence references

Run `dc9d4c72-00fe-4ea9-942c-7ae41c52a0d4`; epoch `411d29f3-8aed-4382-bb14-0a2c97115ca2`; contract `90d6b667e1444fd89650d6b5110dd98b145ba74172024df364a2e52396d6a0a5`; selected target `ec8fdc231385b2ab7b5663b7d7537602b7854bd63a763e8a3f3d6329699165e9`; texture `1a9592e62e2762f1585d13292cac5bca338c606f4c60fa397bdaa96d2ce9a0ce`.

- 014-hydra-front: observation `20605e836279a390cde71263e4f22aafc4dc146459265665f990dfb4f5256b36`; PNG `d0d8796cb3d8ac3656165d3982efc62e56d196b417aefcf1e18cf3f4f6336f91`
- 018-hydra-oblique: observation `f80cc36bd9397684d3f40ac3e117194cf1f70beb0b0867459071d7b7b2c18510`; PNG `82b7f49b253cf4dbcc5c70ddff671ab19e65bd00fd8498cb399a49e1ff239872`
- 019-hydra-settled-oblique: observation `e009b1f44ac13cc51c757797fe7031d8512f88c156c90338f4e27374d37563d9`; PNG `9c277031c76363e5cb77c40208a661c08c6a7d10d1c98b7b996fb6ecc46710a6`

The [companion JSON](verification/RECOVERY-ACCEPTANCE-2026-09-30.json) retains precise profile/build/config/dependency hashes, observed poses, camera/frame/server intervals, individual command outcomes and execution receipts by hash. CAS bytes and contract identities were checked. Capture calls were authenticated by the live observer path; this review does not claim independent HMAC re-verification from retained decoded payloads. Raw paths, logs, receipts, images, session files, credentials and machine process/window identifiers are excluded. Original raw evidence was not changed.

## Subsequent offline corrections

The [frozen repair summary](verification/recovery-offline-repairs-2026-09-30.json)
records 110 passing diagnostic/authentication/deadline regressions and 14 passing
independently rerun command-fixture tests using the actual Minecraft parser.
Signed bounded error categories preserve UNKNOWN and no-retry semantics without
raw exception text. The two fixed player commands retain their exact UUID scope.
These changes were not part of the live run above; runtime acceptance after them
remains NOT_RUN. Fresh resource-limited staff preparation is separate from these
source checks, and no new game launch is authorized by this report.

The [separate recovery failure history](history/2026-09-30-recovery/FAILURE-REPAIR-HISTORY.md) retains the three distinct staff failures and final offline repairs through the existing adapter, with zero canonical writes.
