# Tank observation A–D acceptance

2026-10-08. **A–D PASS in the bounded scenario below; E BLOCKED / NOT_RELEASED.** Independent review adopted with factual qualifications; all two Important implementation findings fixed with RED→GREEN regressions. No Critical/Minor findings. This is a Tank tooling result, not complete NaturalGhast gameplay or moving-POV acceptance.

## Native evidence

- Source: Tech Hub2e7821d6433a0cea789d025ce16c4b23e075fb6f; host7f14960999bc2955d85ae9d3619090ad37817c38, Forge1.20.1/47.4.10. Later changes are documentation and a pilot limitation-label correction; runtime changes remain represented by this pinned trial.
- Exact user-accepted JAR SHA2566c5d2156e9ad83d437d3106721221c13e5221531c1518a069274564364ab3bca, product source182fcb7. Clean product workspace dce89a7 includes development tooling; workspace registration and accepted artifact provenance are recorded separately. No product rebuild or auxiliary observer MOD.
- New private `observation-gYNOOY`, copied raw original fixture; interior `[0,224,0]..[52,248,52)`, independently unchanged action grant `[7,224,6]..[13,235,13)`.
- Two explicit room samples at server ticks67/86: COMPLETE, CANONICAL_STRUCTURED_EVIDENCE. Both contain real Player at world[9.5,224,3.5]/local[9.5,0,3.5] and registered Ghast at world[9.5,230,9.5]/local[9.5,6,9.5], body-contained. No Reimu row. All covered chunks loaded; no truncation. Sampled Ghast displacement0: active AI fixture, **no demonstrated movement** during this interval.
- One explicit fixed-v2 set, four640×480 PNGs/FOV70: north[26,236,1.5], east[50.5,236,26], south[26,236,50.5], west[1.5,236,26]. COMPLETE and RESTORED; actual scope/pose/matrix/image hash/state/reservation/owner/canonical linkage verified. Same original slot returns ALREADY_RECORDED.
- Qualitative inspection of all four raw images: inward room/grid views; Ghast visible east/south and outside north/west framing. Capture completeness does not imply every subject visible in every view. No AI perception or whole-Boss visual verdict.
- Clean shutdown ACK, dropped0/remaining0, VERIFIED_EXIT and EVIDENCE_COMPLETE. Seal has14 artifacts including7 observation scope/slot artifacts. Post-seal bundle read and one explicit derived contact-sheet HTML succeed without changing retained run.
- Original85 historic raw hashes/file count match before/after; exact accepted JAR unchanged.

Local report: `C:/Users/genki/.codex/artifacts/tank-observation-native-20261008/observation-gYNOOY/report.json`, SHA256010dc7a0448935953f4cf524cb655a7614bb5b45c35b3dc3fd0ed249937396e2. Private saves/raw artifacts stay local. Contact sheet: sibling `capture-contact-sheet.html`, DERIVED_ARTIFACT; original PNGs remain authoritative.

## Source checks and limits

Affected Node38/38 and existing owner/action/v1 visual/Mob compatibility67/67 PASS. Python observation/Mob plus explicit paired36-file Python/Node closure14/14 PASS. Wider Python78 PASS/2 SKIP/2 failed at Windows symlink setup WinError1314; application assertions in those two cases did not execute. Full pure Java runner also blocked by symlink privilege. Genuine mapped Forge compile and explicit bootstrap class existence PASS; scope JVM7/camera pose6 checks PASS. Local Markdown links/fences and diff whitespace checked separately after final edits.

Native missing-chunk/entity/passenger-depth/byte-limit, moved/dead/unloaded Mob, Player input/external-camera/world-change, multiplayer and full Boss behavior are NOT_RUN. Their source contracts are tested where available; source success is not native acceptance. E requires its own detached render-only implementation and native attack/use/hitResult proof; v1 remains spectator-only.

## Preserved failures and fixes

Fresh failed fixtures: UgMAlF (workspace revision mismatch, no launch); iZ68We (READY timeout, supervisor terminated its process tree); mEe2mj/3tCRdH (empty incremental debug-class output prevented offline helper compilation); WOGRSk (private launcher setup failed before READY). Original85 remained unchanged in every audited trial. No failed fixture or receipt was rewritten/deleted.

Use canonical `forge-bridge/src/main/java` as source root and verify real bootstrap classes after compilation. Switching a recursive source root to the canonical root left empty outputs while Gradle later reported UP-TO-DATE; one justified forced build restored actual classes. Private Gradle script was checked with `help` before the successful fresh launch; lazy run-task configuration handles Forge task creation order. Preserve those diagnostic rebuild reasons rather than adopting routine clean, skip-compilation or retry loops.

Review repairs: compare normalized UUID sets while preserving native raw order; gate native PASS on verified exit, clean ACK and complete seal. The original-slot reader and lifecycle guards retain their strict failure semantics.


To complete the privilege-dependent checks, use a symlink-capable environment and the camera worktree's Python dependencies: `python -m pytest tests/test_minecraft_experiment_control.py -q`. For the full pure JVM suite, set `JAVA_HOME` to JDK17 and `KNEEKURA_GSON_JAR` to an absolute genuine installed Gson JAR, then run `node departments/minecraft/lab/debug-workspace/bridge/owner-runtime-selftest.mjs` from the camera worktree root. No test assertion or security check should be removed to accommodate missing privileges.
