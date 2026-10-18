# Guarded-dispatch optimization: exact-state comparison

## Outcome
- Both baseline and variant: 126/126 explicit own-byte tests passed; zero observed failures.
- Three baseline and three variant original-guest 100000-instruction replays all stopped at INSTRUCTION_BUDGET with attempted=completed=100000, rollbacks=0 and preservation success.
- All six FULL serialized checkpoint files are byte-for-byte identical (checkpoint-equality.json).
- Shared checkpoint SHA256: 56355b0fb10e61dd31e1ff3a2409b6ccf449d1012e9a2fa99f836c94302286a1.
- Median guarded run: baseline 1.766910 s, variant 1.578013 s; 10.69% lower elapsed time, 1.120x throughput.
- Median end-to-end process wall: baseline 3.199424 s, variant 3.134359 s; 2.03% lower elapsed time.

## Paired measurements
- Pair 1: baseline run 1.805326 s / process 3.692080 s; variant run 1.578013 s / process 3.361541 s; run reduction 12.59%.
- Pair 2: baseline run 1.766910 s / process 3.199424 s; variant run 1.649933 s / process 3.134359 s; run reduction 6.62%.
- Pair 3: baseline run 1.636013 s / process 2.963511 s; variant run 1.387780 s / process 2.710438 s; run reduction 15.17%.

## Interpretation and limitations
- This is a meaningful, bounded improvement in this prefix, with unchanged serialized state and existing differential guard coverage. The exact two-file diff was reviewed and adopted; adopted files were byte-compared with the tested external variant. It is not a multi-fold speedup and does not solve future semantic frontiers.
- Measurements are unprofiled with perf_counter around the unchanged run method. End-to-end includes process startup, artifact loading and checkpoint serialization. The instrumentation verifies actual loaded baseline/variant module paths.
- Sequential order was baseline/variant, variant/baseline, baseline/variant. Shared-host load varied; the middle pair overlapped the baseline own-byte suite. Other parent work may also contend. Treat the percentage as an observed sample, not a statistically isolated guarantee.
- check_oracle consumed 0.0538 s / 100000 calls in the earlier profile (~1.2% of run); pshufb decode 0.0490 s (~1.1%). The latter is not modified; its small share does not currently justify a new cache.
- No original guest/JVM/Java host execution or actual imports were performed. Every replay used existing guarded BatchedJni256 and matching immutable/hash-pinned source artifacts. Only the two reviewed changes are adopted into repository code. No full project tests ran.

## Exact changes
- _commit_native(next_pc=None): takes the existing code-hook address only for the hook call; outer completions keep their actual RIP read. All destination checks, sentinel logic, context saves, journals, pending-store commit ordering, model behavior and executable-write boundaries remain.
- check_oracle returns immediately when oracle_enabled is false, before allocating the cases dictionary. Enabled oracle checks are unchanged.
- Full patch: variant.diff. Variant modules are copies in this directory, selected with PYTHONPATH before repository tools.

## Explicit tests
- test_native_batched_cpu_ysm_265
- test_native_unicorn_guarded_ysm_265
- test_native_guarded_checkpoint_ysm_265
- test_native_pthread_once_fixture_ysm_265
- test_native_jni_fixture_ysm_265
- Batched suite includes JNI gateways/callback, target faults, partial stores, model boundaries, oracle faults, timeout rollback, checkpoints, and self-modifying-code batch edges.

## Reproduction and evidence
- benchmark.py; benchmark-results.json; benchmark.log; checkpoint-equality.json.
- baseline-tests.log and tests.log record both suites.
- baseline-[1-3] and variant-[1-3] .stdout/.stderr/.tsv/.checkpoint.json retain every replay result.
- Source input checkpoint: ../unicorn-jni-forge-universal-next1.checkpoint.json, same original SO/JVM/java.base/ysm.jar and commons-lang3, securejarhandler, Forge universal dependencies as ../profile-guarded-100k.py.
- Existing model/CRC counter history is not credited as newly executed instructions. Every replay actually attempted/completed exactly 100000 native guarded steps.

[Portable measurement receipt](NATIVE-GUARDED-DISPATCH-OPTIMIZATION-2026-10-18.json) retains times, source/adopted hashes and comparison outcome. Raw input artifacts, profiles, benchmark scripts and snapshots remain external. No guard, per-instruction snapshot, knownness/opaque-control check, rollback, model or code-write boundary was removed.
