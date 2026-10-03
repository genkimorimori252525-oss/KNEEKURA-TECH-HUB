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

Remaining: damageable TF phase/formation, integrated Brain/pursuit/flight/missing-capture, native related drawing/pixels/GPU and paired observer effect, full remaining semantic/FRONTIER research, fresh whole-diff review and final exact-HEAD CI.
