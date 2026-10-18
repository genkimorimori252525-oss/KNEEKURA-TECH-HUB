# Bounded virtual Forge Path review

Date: 2026-10-18 UTC. Result: bounded pass after three fixes.

This report records a focused code/semantics review and independent authored tests. It does not establish original-target execution or installation success.

## Exact reviewed files

- `departments/minecraft/mods/yes-steve-model/tools/native_forge_path_fixture_ysm_265.py`
  - SHA256 `d1e13fd0dcf40619c3e37be6b01d55359062e4646a8615fca9e63e179f1d4503`
- `departments/minecraft/mods/yes-steve-model/tools/test_native_forge_path_fixture_ysm_265.py`
  - SHA256 `0cce9b4bde8ab42625cdda0b0f80331e0c5e98ba548805aa500ce239aa9607e0`
- `departments/minecraft/mods/yes-steve-model/tools/native_guarded_checkpoint_ysm_265.py`
  - SHA256 `8af39b8722c5c871a241aa96ad24dcdf2e38af6a80e4c8f636f3da1a0113d8b1`
- `departments/minecraft/mods/yes-steve-model/tools/native_jni_onload_ysm_265.py`
  - SHA256 `4a48b88d7bd9b5731c3aa0c4e54f6efd3c2bd2f66e28691ddb14477dc54539b5`

## Independent verification

The focused command below passed all 15 test methods in 1.584 seconds:

```text
PYTHONPATH=departments/minecraft/mods/yes-steve-model/tools ../ysm-local-inputs/tool-cache/unicorn-venv/bin/python -m unittest test_native_forge_path_fixture_ysm_265 -v
```

The final source hashes were rechecked when preparing this receipt. The independent run is the 15-method path module, not the separately reported larger test cohort.

## Found and fixed

### R1: fixed

Object ownership dispatch inspected unused RSI for receiver-free JNI calls, stopping ExceptionCheck, ExceptionClear and GetVersion when a live or deleted path reference remained in that register.

Ownership dispatch now restricts RSI inspection to reference-taking JNI slots; receiver-free calls pass through generic JNI handling.

Independently reproduced the original stop; final focused regression covers stale live/deleted registers and pending exceptions.

### R2: fixed

Released UTF storage was classified as unknown, allowing the inherited one-byte copy model to propagate it as opaque data and return instead of stopping.

Released borrow overlap is rejected before modeled copy and read_known; zero-count copy retains no-read semantics.

Independently reproduced original successful opaque copy; final regression covers active/released copies, unchanged rejection state, ordinary unknown copies and restored released borrows.

### R3: fixed

Coordinated replacement of mutable config and object dictionaries could change the original declared game path and pass reconfiguration and JNI calls.

A separate frozen PathDeclaration anchors the original canonical configuration, including provenance; runtime validation, reconfiguration, capture and established-instance restore compare against it. Serialized declaration consistency is also validated.

Independently reproduced coordinated mutation; inspected final anchor implementation and passed coordinated-tampering regression.

## Checked scope

- Separate explicit FMLPaths setup state and null absolutePath
- Bounded absolute normalized printable-ASCII virtual provider/path domain
- Source pins and owner/name/descriptor/staticness validation
- Typed enum, Path and String identity; local/global reference aliases and deletion
- Exact ASCII modified-UTF8 length, borrowing, release and stale reads/copies
- Frozen original configuration declaration
- Checkpoint schema, replay, borrow-storage and backend checks
- Explicit legacy path extension and unchanged default CONFIGDIR stop
- No newly modeled successful filesystem assumption

## Limits

- Authored direct JNI/model calls and authored classfiles only; test pins are substituted for those authored fixtures.
- No original checkpoint continuation or original guest instructions executed during this review; no native library/JVM, installers, assets or host filesystem operations tested.
- No independent batched-execution validation, full test discovery, CI, repository edits, merge or publication performed.
- No claim of successful Forge setup, existing directories, working installation, successful native initialization or downstream filesystem behavior.
- Checkpoint replay and declaration checks establish bounded internal consistency, not cryptographic checkpoint authenticity; fully rewritten coherent snapshots on a fresh instance are not authenticated by these checks.
- This receipt documents the completed focused review and hash recheck, not a new broader audit.
