# Ghast original custom-flight reach — native-r40

Frozen TECH HUB producer `b4e9c53be948017bbb846efb0dd5f388ec9032cf`; Minecraft1.20.1 / Forge47.2.0 / Java17 with the unchanged pinned MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`. This is a MOD-loaded Forge observation of a Vanilla Ghast, not a pure-Vanilla process or complete flight/combat acceptance.

## Source contract and bounded implementation

[Movement source research](MOVEMENT-CONTROLS.md) pins the exact original private `Ghast$GhastMoveControl.canReach(Vec3,int):boolean`. One non-cancelling RETURN injection retains its actual argument vector/step count and boolean under the existing armed `control` channel. The observer does not invoke reach tests, collision queries, randomness, setters or control ticks. Exact selected Ghast/controller reference, cached UUID, SERVER thread and session/run/snapshot/process/Arena/revision/window/event/byte gates remain authoritative. No extra A* nodes, final destination, collision location or rejection reason are generated.

New tests first failed for the unsupported callback/consumer, then passed:116 Motion/Decision tests,0 skipped; genuine producer suppression guards; actual Gson→Node output; combined owner/camera/writer/runtime API regression; compilation of all bridge Java/Mixin sources against hash-checked genuine dependencies. Source `b4e9c53` has all three exact-HEAD GitHub CI runs SUCCESS: source push `37168982474`, source PR `37168984121`, pytest `37168984137` (3,149 passed /332 skipped /8 warnings). Later publications require their own exact HEAD checks.

## Private conditions and finalization

Run `run-20261004014742-e7faa5eb1537`; session `sess-20261004014742-e08106cfb1fb`; snapshot `snapshot-20261004014742-0cb8c2f6fcd1`; process epoch1; Arena epoch0. Selected Ghast UUID `55555555-6666-7777-8888-000000000001`. Runtime PID19864 and launcher14276 are both verified exited.

A fresh private copy of the user's original world was prepared under its exclusive world lock. Prelaunch NBT setup made a supported lit16×16 room with glass boundaries/open space above, a Survival player with high health/regeneration/night vision, and one persistent AI-enabled Ghast. Previous r39 world85 files and the exact post-setup/prelaunch85-file baseline were preserved. The original world and untouched control85-file manifests still match. This labeled fixture changes initial conditions; no gameplay AI/result callback was manually invoked. The open top does not contain flight: retained y ranges rise from232.36..250.61 in revision1 to328.33..351.38 in revision6. No canonical Tank resize, natural dynamic owner registration or raw camera acceptance is claimed.

Six12-second selections armed unchanged limits200 local ticks /256 events /512KiB /32 retained path nodes, channel `control`. All six reached EVENT_BUDGET before their requested window elapsed. Burst summary ticks use the local last-completed SERVER counter; table windows below use world gameTime. These clock domains must not be compared as the same counter.

Final2,574 unique canonical observations /EVIDENCE_COMPLETE /clean ACK /dropped0 /remaining queue0 /verified exit:

- Canonical SHA256 `bf62bb5c0597bf5ee9fc6c723e42292244a327ba9e171f958f5a35e070accffd`.
- Finalization SHA256 `75e525feffece887950187d065635dba94dd92cb6a0aaba630f3914f8be7bd4b`.
- JFR4,950,707 bytes, SHA256 `2a4d7b8f5518e736bdaecc88b53222b938f147ed5df559f8768dc21b9e50ce86`; valid private JFC was parsed before launch and actual textual start/stop receipts were verified. JFR is descriptive, not paired cost evidence.

## Actual custom-flight returns and Motion

Observation suffixes use the exact prefix **`obs:forge-runtime:19864:`**. Each revision has48 sampled state snapshots; all Motion points below are actual SERVER positions, never callback-vector endpoints. Derived traces use these positions without forward fill; this bounded trial yields0 Motion gaps in each revision.

| Revision | World-tick window | Original reach true /false | First /last reach suffix | Real Mob Motion samples | Original related groups /retained real projectile points | Post-budget Motion samples |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 40468..40703 | 17 /1 | 28 /325 | 47 | 2 /20 | 33 |
| 2 | 40708..40943 | 14 /2 | 497 /786 | 48 | 2 /25 | 33 |
| 3 | 40948..41183 | 17 /0 | 973 /1255 | 48 | 1 /44 | 35 |
| 4 | 41188..41423 | 20 /0 | 1392 /1683 | 48 | 0 /0 | 32 |
| 5 | 41428..41663 | 21 /0 | 1823 /2091 | 48 | 0 /0 | 32 |
| 6 | 41668..41903 | 20 /0 | 2196 /2464 | 48 | 0 /0 | 32 |

Total112 original reach returns:109 true and3 false. False suffix28/world tick40470 carries step count18; suffix497/tick40711 carries10; suffix512/tick40714 carries16. Subsequent same-tick original move-control returns29/498/513 expose `operation=WAIT`. These ordered records share subject/context but have no shared nested-invocation ID; the retained relationship remains temporal association. Original static branching explains the algorithm, without manufacturing a runtime selection cause or a blocked-cell location.

Actual finite acquisition also retains1,321 control-tick returns,5 accepted LargeFireball spawns,92 completed projectile-tick records (89 retained real positions; removed endpoints are not positions),3 base entity-impact returns and3 original hurt-call returns. Legacy `control` already includes its related-projectile observations; no new default channel or larger event budget was added. The actual hurt results at suffix129/625/1216 are true, requested damage6 with cached HP1024→1015/delta9. These are original direct-call/base-health facts, not whole explosion accounting or an inferred damage formula. Revision4–6 contain no retained projectile callbacks; absence is not a proven attack-selection reason.

All1,536 original-event records validate through the current production consumer. EVALUATION retains only the corresponding direct reach facts; CANDIDATE and SELECTION remain NOT_CAPTURED. RESULT is available from the actual projectile returns in revisions1–3 and NOT_CAPTURED in4–6. Declared base controller state, custom feasibility, sampled Mob movement and independent projectile traces stay separate. No conventional Path cache/frontier is fabricated for this custom flight.

## Omitted deep-capture interval

After each finite burst exhausts its event budget, sampling continues but original decisions are no longer captured. Production presentation replay of these exact same-revision tails yields `EVALUATION=NOT_CAPTURED` while Motion remains `AVAILABLE`, with33/33/35/32/32/32 actual points. For example, revision1's world40543..40703 tail starts at source338; revision3's41013..41183 tail starts at1268. No pre-budget reach result is carried forward into those tail windows, and no missing thought is reconstructed from movement.

This is an actual budget-exhausted acquisition interval, not a separate deliberate late-arm runtime trial or proof that no reach test executed then. Existing retained malformed/late-window/other-run/Arena/revision/UUID tests separately verify refusal to import old identities.

## Bounded browser replay and visible gap explanation

Committed renderer `e7ce5279b10b2cda823c457a8354e68669765be7` replays the unchanged r40 producer through three derived, private artifacts. The browser verifies all spatial layers default OFF. The active40468..40542 window has14 actual Mob points, direct EVALUATION AVAILABLE and two separately identified projectile groups; CANDIDATE and SELECTION stay NOT_CAPTURED. The post-budget40543..40703 window has33 actual points, EVALUATION NOT_CAPTURED and no detected trace gap; the visible text explicitly says this does not guarantee continuous acquisition.

A separate controlled read-only consumer input omits eight existing SERVER positions at40630..40670 (source suffixes418/423/427/431/436/440/445/451). It retains25 points and SOURCE_GAP40628..40673, with no segment across that gap. This is **CONTROLLED_READ_ONLY_INPUT_OMISSION_NOT_ACTUAL_NATIVE_MISSING_ROWS**: native acquisition and its canonical store are unchanged. Browser ELEVATION shows the broken trace and visible gap kind/tick range. Whole-window gap counts and at most four examples remain separate from the spatial cursor and age colors. The original r1 image, which lacked a visible explanation, is preserved; the r2 images show the correction. Two new runtime regressions cover gap scope, independent projectile identities, bounded examples and the no-continuity-guarantee text; the focused suite passes118 tests /0 skipped.

The browser also checks the active fixed-isometric Motion/projectile display with full UUID color legend; captured console warning/error list is empty. These three local views establish this bounded replay, not every camera/depth/palette case, native missing-position acquisition or a deliberately late-armed runtime trial. Private HTML/JSON/image hashes are retained in the additive browser receipt; artifacts remain outside Git.

## Measured limits and receipt corrections

Per-return builder timings for reach are bounded/descriptive: first window43.0µs minimum /58.8µs median /676.4µs maximum; other window medians31.8..34.7µs. Scope excludes final encoding/writer/GPU/capture. No negligible overhead or paired gameplay equivalence is inferred.

The initial private finalizer selected world-timed rows for presentation and omitted the six summaries, which lack gameTime, from its summary field. An additive read-only acquisition audit retains those exact summary IDs336/805/1267/1695/2107/2484,256 events each and their true EVENT_BUDGET status. Canonical and original finalizer receipts were preserved, not rewritten or reclassified. All worlds, JFR, full logs and detailed private receipts stay outside Git.

This establishes bounded original Ghast feasibility plus Motion/ranged components and a truthful packet after capture stops. It does not expose random-target selection, complete candidate population, the first collision step/cell, nested causal execution IDs, Phantom/custom-MOD steering, full combat, raw pixels/GPU, paired observer cost or canonical resize. [The remaining matrix](REMAINING-EXECUTION-MATRIX-2026-10-04.md) and full `/goal` remain active.
