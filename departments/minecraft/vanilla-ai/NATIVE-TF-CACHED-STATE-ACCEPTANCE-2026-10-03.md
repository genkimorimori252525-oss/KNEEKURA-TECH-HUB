# Native pinned Twilight Forest cached-state acceptance

Scope: SDK cached-state/source-resource proof for four exact Boss UUIDs. This is not Boss battle, original MOD transition, complete candidate-population or controlled observer-effect acceptance.

## Exact generations

- Native producer: `f9e91b845cbae76ea5acffb49224f694f4e9966e`; MOD workspace `53a84d06578632b5d123e3c2bb631b611bf830d7`, precompiled 8,444 main classes verified before launch.
- Minecraft 1.20.1 / Forge 47.2.0 / Java 17; Twilight Forest 4.3.2508.
- Original TF JAR SHA256: `0bdc89263616d1b35c32ef82c5e9c14cbd20368e2fe8b468c72a28320be7a778`.
- Actual ForgeGradle mapped TF JAR SHA256: `7d7842c3c66d355c94bd726ef69ad14ac4f944061198927c3eb54a728e23580a`.
- Actual owning ModFile and ten class resources match the SDK descriptor. This proves the development resources, not post-Mixin resident bytecode attestation.
- Consumer's native-Gson normalization SHA256: `503fe00d373d1faf611dcfa7df712aba2fc12b88fed22a47721b5d373aa00d35`. Gson omitted null fields; an omitted nextState is normalized only when AUTOMATIC_SENTINEL is explicit. Missing target/head references remain NOT_CAPTURED. The immutable raw evidence is unchanged.

## Private fixture and startup

The private copied world contains four invulnerable, persistent, NoAI=true TF subjects. A held-world-lock readback proved exactly four added entities and all preceding entity NBT equal to the prior eight-Vanilla fixture. Original user saves remain read-only.

native-r9 stopped before launch on a clean-source guard; its test-created logs were preserved. native-r10 loaded TF but Forge's experimental-world confirmation synchronously reentered through Citadel before the first DirectoryLock closed. No READY/clean evidence acceptance was recorded. Its logs and degraded artifacts remain separate.

For native-r11, the existing Forge `Data.confirmedExperimentalSettings` flag was saved only in the disposable copy. The previous level.dat was retained, a held-world-lock reread proved all other level NBT unchanged, and the integrated server reached DEBUG_READY. No production save or observer/owner gate was changed.

## Retained results

Run `run-20261003104536-622d4b0d1762`; snapshot `snapshot-20261003104536-0f61309cc174`; process epoch 1, Arena epoch 0, runtime PID 2884.

| Selection | Revision | SDK rows | State fact | Example source observation |
|---|---:|---:|---|---|
| Default OFF, Hydra | 1 | 0 | — | — |
| Hydra | 2 | 48 | `twilightforest:hydra_heads` | `obs:forge-runtime:2884:60` |
| Snow Queen | 3 | 52 | `twilightforest:snow_queen_phase` | `obs:forge-runtime:2884:184` |
| Knight Phantom | 4 | 52 | `twilightforest:knight_formation` | `obs:forge-runtime:2884:380` |
| Ur-Ghast | 5 | 52 | `twilightforest:ur_ghast_custom_flight` | `obs:forge-runtime:2884:515` |
| Reset OFF | 6 | 0 | — | — |

All 204 SDK rows have AVAILABLE cached state and MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION. Retained adapters emit the expected namespaced fact and derived label. Hydra's seven local head containers, Snow Queen phase/counters, Knight's local formation, and Ur-Ghast's exact NoClipMoveControl fields remain distinct. Knight group/leader and Ur-Ghast A-star/candidate population remain NOT_EXPOSED.

683 canonical records, writer dropped 0, queue remaining 0, clean shutdown ACK, verified process exit, EVIDENCE_COMPLETE. Original user save manifest: all 85 file SHA256 values unchanged.

All four actual `evidence-decision --channel mod_state` CLI reads succeeded with exact revision/Arena/tick/source IDs. Canonical observations SHA256 remained `6587a52300cf1eade7974626d62492986d0461fb239a8d37b35193d36b590f5c`; finalization SHA256 remained `5d9467fba3e64142954f5f5096e5ec145b6fe4da5d5fa87dcc56ecc1c8e2cf36` before/after. The finalized run was not re-ingested by the read-only CLI.

Private retained report SHA256: `964b5971f307211ad2193557906144e0705719bb23e8badd05f92a586feef646`; raw SHA256: `fae13fab20b41d41e88a011acf89fab2b3a421ee545911d2fde9399229f4461d`. Private worlds/JARs/logs are not committed.

## Verification and limits

Motion/Decision tests: 69 passed / 0 skipped, including the failing-then-fixed native omitted-null regression. Portable source/API contracts and genuine all-bridge compilation passed for the native producer. GitHub source push/PR jobs and pytest passed at f9e91b8.

Observed capture-only median costs: Hydra 97,600 ns, Snow Queen 65,600 ns, Knight 57,000 ns, Ur-Ghast 80,600 ns. Hydra's maximum 21,142,600 ns includes initial source proof. These measurements exclude final encoding, writer and Viewer, and are not an OFF/ON controlled total-cost comparison. Original MOD callbacks, fights, group coordination, full representative behaviors and total observer-effect acceptance remain pending.
