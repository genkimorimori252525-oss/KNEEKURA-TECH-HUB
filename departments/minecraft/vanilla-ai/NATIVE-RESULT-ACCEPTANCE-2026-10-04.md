# Native original-result acceptance

Date: 2026-10-04 (Asia/Tokyo). Bounded native evidence; full remaining `/goal` remains active. TECH HUB is canonical and LAB is its feature subtree.

## Frozen native-r16 generation

Producer `9c15f74659a567bad6f1bcfe838794721e5d20c4`, pinned MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`;8,444 source/output files hash-checked before launch. Genuine Forge/TF anchors remain those in the dated result research.

Original dedicated world85/85 SHA256 files matched before/after, read-only. Predecessor private world was preserved and checked. A fresh exact copy received labeled prelaunch setup:16×16 support floor at223, open room/glass boundary/glowstone, survival player with controlled high health/regeneration/night vision, actual-AI Skeleton with bow, angry Enderman and Ghast. Setup values are not gameplay results; Enderman/flight were not contained by this room.

Offline `RegionFile` inspection padded one control-copy file from25,347 to28,672 bytes: original prefix identical,3,325 appended zero bytes. Original85 files were unchanged. The inspected copy was preserved; an uninspected control-v2 was reverified byte-identical for future paired trials.

Native-r16: **1,224 unique observations**, `EVIDENCE_COMPLETE`, drop0/queue0/clean writer ACK/verified process exit. Canonical SHA256 `cc3d2fff298865fb75e301b41ec769c301fb77cf12ea90f1a985415360ca2160`; retained derivation left it unchanged. Private raw/world data and filesystem paths are not committed.

## Actual results

| Scenario | Direct evidence | Established | Limit |
| --- | --- | --- | --- |
| Skeleton/revision1 | `obs:forge-runtime:37940:112`, tick40473 | Accepted Arrow spawn and44 completed original tick samples, exact projectile UUID/spawn reference | Full shot history/decision reason not inferred |
| Arrow block impact | `obs:forge-runtime:37940:155`, tick40481 | Base `onHit` returned after BLOCK dispatch | Block hit/miss of living target; no entity/HP damage receipt |
| Enderman/revision2 | `obs:forge-runtime:37940:471`, `:597`, `:719`, ticks40622/40654/40686 | Three actual `randomTeleport` true returns; three typed `EXPLICIT_TELEPORT` gaps citing those callbacks between retained SERVER points | Already outside high room before selection; initial escape not reconstructed. Returned y near−59, not contained high-room acceptance |
| Ghast/revision3 | `obs:forge-runtime:37940:1124`, tick40846 | Accepted LargeFireball spawn and5 completed original tick samples | Impact/explosion damage not captured |

All actual projectile/teleport payloads passed the production typed validator unchanged. Both related traces use independent projectile UUIDs and original source IDs; spawn/hit/teleport coordinates never become additional sampled tick points. Selected-Mob native draw submissions do not establish related-projectile native drawing or framebuffer pixels.

**Native-r16 captured no `CONTROL_PROJECTILE_HURT_RETURN`.** Synthetic source/Gson tests do not fill that generation's gap. Native-r17/r18 below establish separate original-call outcomes. Raw pixels/GPU and paired observer-effect acceptance remain open.

## Finite-window diagnosis

All three `control` bursts stopped at256 events with `EVENT_BUDGET` before the requested200 ticks ended. Move/look/jump callbacks consumed most of the budget; Ghast spawn was event232. A missing later result cannot distinguish gameplay from a closed capture window.

The next source generation adds an optional `projectile` channel with unchanged identity/reference/window/event/byte limits. It captures projectile callbacks without movement/teleport controls. Legacy `control` retains the projectile family; CLI defaults remain unchanged; ordinary selection does not arm a burst. Native-r17/r18 test this separate generation; r16 is not relabeled.

## Frozen native-r17/r18 projectile-only generation

Producer `7a744b2eb7b3ae9a81f700494a535f1b76b6341c`, same pinned MOD/genuine artifacts. Each trial starts from a fresh original-control-v2 copy with separately labeled private setup and actual AI enabled. Skeleton alone (r17) and Ghast alone (r18) avoid unrelated hostile interactions. Original85 hashes remain equal after both runs; each preceding private world is preserved. Exact85-file post-setup/prelaunch baselines are retained for later paired trials and were not opened by `RegionFile`.

Five explicit finite windows per trial use `projectile` only, 200 ticks /256 events /512KiB /32 nodes; none reaches the event cap. A new selection revision closes the earlier window rather than combining its projectiles with the next burst.

| Trial | Finalized evidence | Original projectile facts | Retained positions |
| --- | --- | --- | --- |
| r17 Skeleton | 1,060 unique observations, drop0/queue0/cleanACK/verified exit; canonical SHA256 `9d4da64778d1f10b5141d5888fdfde64243b3cbe289217e831dee6cba0d568c2` | 23 accepted Arrow spawns, 157 completed-tick receipts, 23 ENTITY base-hit returns, 23 original hurt returns, all true with positive base-health delta | 23 independent UUID groups /134 real position samples across five presentations; 23 removal receipts are terminal references, not position samples |
| r18 Ghast | 911 unique observations, drop0/queue0/cleanACK/verified exit; canonical SHA256 `419783c7398b1599d6abaed6a50eaffd43d5b47760cbe4a92b8b82361f5c5ce8` | 1 accepted LargeFireball spawn, 25 completed-tick receipts, 1 ENTITY base-hit return, 1 original hurt true return | 1 independent UUID group /24 real positions; one removal receipt is terminal |

Both stores are `EVIDENCE_COMPLETE`, meaning clean finalized capture, not complete coverage of gameplay. Actual typed payloads validate unchanged. Source IDs and unchanged canonical hashes support derived traces; these traces do not claim all owner projectiles or continuous trajectories.

Representative r17 chain, revision1 /Arrow `942a26f6-0c26-41cc-af02-bb58989232c1`: accepted spawn `obs:forge-runtime:53980:30`, retained original tick positions `:31/:32/:33/:35/:39`, original hurt `:40`, base ENTITY hit `:41`, removal `:42`. The direct owner/projectile/burst/spawn-event fields link the receipts; adjacency alone is not the relationship proof. Each of all23 chains has its own source references. Target UUID is `380df991-f603-344c-a090-369bad2a924a`. Twenty hurt calls observed requested damage4 with cached HP1024→1018 (delta6); three observed requested damage5 with HP1024→1016.5 (delta7.5). Requested argument and observed HP delta remain distinct facts; final damage reason is `NOT_EXPOSED`. Controlled regeneration between calls is fixture setup, not a damage cancellation claim.

R18 chain, revision1 /LargeFireball `89bf998b-93a0-4d79-bf07-62cec1cb1604`: spawn `obs:forge-runtime:9376:60`, original hurt `:106`, base ENTITY hit `:107`. Requested damage6, actual true return, cached HP1024→1015 (delta9). This establishes the inspected original direct hurt call; the base hit callback precedes subclass explosion, so it does not establish the whole explosion or its later damage. Windows2–5 ended normally with zero projectile events; the missing later shots remain missing, not reconstructed hits/misses.

R17's five production retained presentations validated default-OFF related layers and unchanged canonical bytes. Related-projectile native overlay/pixels remain unverified. Owned-JVM JFR files were retained for both trials; these standalone runs are descriptive measurements, not same-initial-state paired observer-effect acceptance. Native cancelled/false hurt and custom attacks remain outside captured scenarios.

## Frozen native-r20/r21 TF generation

Producer `5c480ed1c6a21d6795197d4a7c3b4c5455dfa931` changes only documentation/templates after the previous runtime implementation. Genuine MOD/TF inputs remain pinned. Fresh original copies received separate prelaunch setup: r20 damageable actual-AI Snow Queen plus a natural Iron Golem; r21 six damageable actual-AI Knight Phantoms, numbers0..5 and shared `HomePos` through the genuine `GlobalPos` codec. These are controlled fixtures, not the official-world baseline or a live owner-authorized resize. All source/compiled-main guards passed.

Offline r19 setup failed at Vanilla registry initialization before entity output/native launch. Its failed world/logs were preserved; a fresh r20 copy added genuine `SharedConstants`/`Bootstrap` initialization. Preparation repair is not a native AI result.

| Trial | Finalized capture | Original returns /production consumption |
| --- | --- | --- |
| r20 Snow Queen | 4,734 unique observations; canonical SHA256 `0b892c5a031fc738e0a1593eba8c8c6df9ea4bbec179399fc5703ae8e736d44d` | 6 `setCurrentPhase` returns (DROP/BEAM/SUMMON twice),860 cached snapshots,24 separate exact-revision presentations |
| r21 Knights | 3,931 unique observations; canonical SHA256 `ae4f361200d56c4124f0b9536874d8fe9cc9cb1b44885d5a92de4665c8423dfe` | 22 `switchToFormation` returns across six separately selected UUIDs,720 cached snapshots,18 separate exact-revision presentations |

Both stores finalized `EVIDENCE_COMPLETE`, drop0/queue0/cleanACK/verified exit/original85 SHA unchanged. Actual SDK return contracts validate unchanged; constructor/load callbacks before arm do not count. Production derivation leaves canonical bytes unchanged. Post-setup baselines, predecessor worlds and owned-JVM descriptive JFR remain private.

R20 first sequence: `obs:forge-runtime:51448:1293` /tick41614 /revision7 /DROP, `:1650` /41939 /revision9 /BEAM, `:1682` /41972 /revision9 /SUMMON. Second: `:3275` /43424 /revision17 /DROP, `:4000` /44085 /revision21 /BEAM, `:4038` /44121 /revision21 /SUMMON. Each callback cites its own context; presentations do not join selection revisions. Actual first post-SUMMON state retains summonsRemaining6, successfulDrops2/maxDrops2 and damageWhileBeaming39. Exact `customServerAiStep` requires damageWhileBeaming≥25 for BEAM→SUMMON; other phases use their own minion/drop conditions. This source explanation does not replace `reasonStatus=NOT_EXPOSED` or establish the actual attacker from fixture placement.

R21 number0 callbacks `obs:forge-runtime:22756:60` and `:61` both request `CHARGE_PLUSX` at40487: two original calls, not proof of two changes. Number1 `:281` requests `WAITING_FOR_LEADER` at40686 and `:303` requests `CHARGE_PLUSX` at40706. Further retained calls include clockwise/anticlockwise/charge and `ATTACK_PLAYER_START`. Cached group/leader identity remain `NOT_EXPOSED`. Sequential member selection does not prove simultaneous broadcast, complete membership, leader identity or actual battle damage.

Six additional exact TF goal/home source blobs were hash-verified at `a7dd8f13c653e137f977f5ffaa870fcb20fc1625`: `HoverSummonGoal`, `HoverThenDropGoal`, `HoverBeamGoal`, `PhantomUpdateFormationAndMoveGoal`, `PhantomWatchAndAttackGoal`, `EnforcedHomePoint`. Bodies/blob/SHA256 receipts remain private. The formation Goal uses its original nearby list for lowest-number election/broadcast/charge; the observer does not replay that query. Direct complete coordination remains open.

## Frozen native-r22 controlled Ur-Ghast result

Producer `a3bad464bac3a30245b7b2ff2040768fe1897a3c`, unchanged runtime implementation/genuine artifacts. Fresh private original copy, actual AI enabled, Invulnerable=false, max health1024 and an explicitly labeled prelaunch POISON effect (id19 /amplifier1). No observer invokes phase/hurt or seeds a fake phase result. This controlled initial effect is not player-combat acceptance; a damage cause is not added to native `reasonStatus=NOT_EXPOSED`.

4,005 unique observations,868 cached snapshots,24 separate exact-revision production presentations; finalized `EVIDENCE_COMPLETE`, drop0/queue0/cleanACK/verified exit/original85 SHA unchanged. Canonical SHA256 `92c99a705b65a38a95b982fe011c127b2b5cc834a33e83a197a68dea11ad3bff` remains unchanged by production SDK/presentation derivation. Three actual `setInTantrum` returns: `obs:forge-runtime:35212:104` /tick40513 /revision1 /true; `:2075` /42685 /revision13 /false; `:2307` /42901 /revision14 /true. Cached counter depletion and post-callback reset18 are retained; the constructor/load setter is excluded. Individual windows are kept separate.

The cached custom-flight controller is the actual `twilightforest.entity.ai.control.NoClipMoveControl`, with original operation/cooldown/wanted coordinates. Candidate population and A* explanation remain `NOT_EXPOSED`; the observer does not manufacture a PathFinder result for this flight. Direct phase setter facts do not expose the entire battle, actual damage-source history or AI decision reason.

Owned-JVM JFR:7,564,015 bytes /8,672 exported selected CPU/thread/GC/write/execution events. First window has eight CPU samples, raw mean JVM user fraction0.132636748875/system0.032599914875,124 statistical execution samples/four observer frames. Producer-reported build/cached cost81 samples:median135,999ns/max266,289,900ns (includes the existing once-per-process resource proof). This is a descriptive window, not incremental observer cost; encoding/writer/Viewer, independent pre-call work, JFR overhead and GPU/OS attribution are not included in that producer timing. No negligible-overhead conclusion follows.

## Frozen native-r23 Villager Brain and native-r24 Zombie pursuit

Producer `d46cd30a86b7415fbf74be24e57724f542751a3a`, unchanged runtime implementation/genuine artifacts. Each trial starts from a separately preserved original copy with labeled private prelaunch setup. Both finalized `EVIDENCE_COMPLETE`, drop0/queue0/cleanACK/verified exit/original85 SHA unchanged. Production validation and presentation derivation leave canonical bytes unchanged.

| Trial | Finalized capture | Observed scope |
| --- | --- | --- |
| r23 adult Villager | 1,718 unique observations /480 cached snapshots; canonical SHA256 `6fb1f4198b20a505b922904fb4f4ee3aa27b81b82ace1870e5657a877004173f` | 256 original Brain/sensor callbacks and separately retained sampled activity/memory changes |
| r24 Zombie | 419 unique observations /80 cached snapshots; canonical SHA256 `724a1cef407aaa96173bb6ce90892ee2a0a7c7922b5509a0510635979137d809` | Actual player target,80 real motion samples and one original PathFinder search state/result pair |

R23 uses actual Villager AI, no seeded Brain memories or edited POI blocks, natural daylight cycle starting11500, and the existing controlled player/health fixture. Callback counts: SENSOR_SCAN_RETURN8, BEHAVIOR_TRY_START_RETURN150, BEHAVIOR_TICK_OR_STOP_RETURN60, BEHAVIOR_STOP_RETURN20, BRAIN_TICK_RETURN18. The finite brain/sensor burst closes at256 events; subsequent sampled state does not reconstruct missing callback history. Activity samples change from core+idle (`obs:forge-runtime:11004:18`, tick40428) to core+rest (`:445`, tick40813). This is sampled temporal association, not an original causal transition.

The production memory-change query retains96 items: walk_target38, path40, look_target11 and cant_reach_walk_target_since7. For example, `:90` /tick40433 → `:161` /40438 observes walk_target/path absent→present; nested values remain `NOT_EXPOSED`, exactChangeTickKnown=false. Motion retains128 actual positions with explicit truncation. INPUT/STATE/EVALUATION/EXECUTION have available evidence; CANDIDATE/SELECTION/RESULT remain `NOT_CAPTURED`.

R24 uses actual Zombie AI without seeded target, a survival player and52 bounded private prelaunch oak-fence cells with alternating end gaps. Fences preserve eye-level visibility while obstructing navigation; this setup is not an original-world resize. Actual target `obs:forge-runtime:46408:22`, tick40448, is player `380df991-f603-344c-a090-369bad2a924a`, alive with observed lineOfSight=true and distanceSqr101.44094318989548. Original search `:148` and result `:149` retain32 bounded frontier nodes with `PARTIAL` coverage, resultPresent=true, Path resultNodeCount19 and **canReach=false**. Neighbor evaluation remains `NOT_EXPOSED`; this is not successful target arrival.

The80 real motion samples run from `:21` /tick40448 /[4.5001112779960755,224,7.298680418275718] to `:413` /40843 /[13.920788032767453,224,10.416192413018171]. The sampled polyline length43.69285738014613 and net displacement9.923105942962257 describe those retained points over395 ticks, not continuous motion or a complete pursuit. No gaps were detected within these80 samples. The path-only burst ends normally with two callbacks; a missing candidate/cost explanation stays missing.

## Windows owner directory identity diagnosis

The existing `KneekuraDebugScopedOwnerGate.windowsDirectoryKey` fallback was exercised through the genuine compiled gate and hash-checked existing Forge/JNA dependencies on Windows/JDK17. Both C: and K: NTFS private directories returned nonzero volume/file identities stable across repeated reads. Earlier environment failures do not establish that the current Windows implementation is unavailable. This read-only diagnostic does not establish live owner installation, capture authorization, pixels or performance acceptance; those require separate runs through the normal registered owner flow.

Remaining: direct Knight coordination/battle, native related drawing/pixels/GPU and paired observer effect, full remaining semantic/FRONTIER research, fresh whole-diff review and final exact-HEAD CI. Brain, pursuit and custom-flight examples above establish their bounded observed layers only.
