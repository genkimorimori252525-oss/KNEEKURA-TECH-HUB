# Explicit virtual Forge Path continuation

## Result and scope

The reviewed generic receiver fixture passed the previous CONFIGDIR frontier under an explicitly declared synthetic state. One bounded guarded Unicorn continuation completed 21,066 original guest instructions, eight Path/reference/string JNI operations and four ExceptionCheck calls, then stopped at unmodeled secure_getenv("TMPDIR"). This is an emulated dataflow observation, not host-native execution, actual Forge setup, filesystem existence or JNI_OnLoad completion.

- Input checkpoint SHA256: `05122784aea6927c2a8f1d48a2fb16f98e73b0d3919ab48ea4b1725f76d106b1`
- Output checkpoint SHA256: `037e49c09fa15750aef36853a0b0bde9874e73ff3abb0e6944b29602c4c3e635`
- Bound: 100,000 instructions / 60 seconds, batch size 1. One cohort only.
- Stop: `UNMODELED_ENVIRONMENT_KEY`, PC `0x14f9c20`, caller return `0x311792`, key `TMPDIR` from original bytes at `0x421c6`.
- Two virtual detached workers remain pending and unexecuted; no pending Java exception.
- Pinned original artifacts, input checkpoint and reviewed source files unchanged.
- No new modeled file-operation or environment-success calls; host environment was not read.

## Explicit scenario

The provider is `virtual-unix-ascii-v1`; the declared state is `absolute-field-populated`, with synthetic game path `/fixture/ysm-game` and derived config path `/fixture/ysm-game/config`. This is not the user's installed directory. The legacy checkpoint had no Path model, so the extension is explicitly opted into; existing observed values cannot be retrofitted.

The generic chain is CONFIGDIR enum → absolutePath → normalize alias → local-reference deletion → toString → modified-UTF8 borrow/length/release. The string has 24 bytes; its borrow is released. Frozen object identity and original declaration are separate from reference handles. No instruction-address-specific return value is injected.

## Verification

The scoped Path/Forge/checkpoint/Java-metadata cohort passed 71 tests, including 15 Path tests. Independent review ran the 15 Path tests and closed three defects: stale unused-register dispatch, released UTF copying and coordinated mutation of the declared path. A separate final 15-test run also passed. These are authored model tests, not full original-target equivalence or whole-project review.

See the [focused review](NATIVE-FORGE-PATH-FOCUSED-REVIEW-2026-10-18.md), [review receipt](NATIVE-FORGE-PATH-FOCUSED-REVIEW-2026-10-18.json), [source-backed plan](NATIVE-FORGE-PATH-MODEL-PLAN-2026-10-18.md), and [continuation receipt](NATIVE-FORGE-PATH-CONTINUATION-2026-10-18.json). The continuation receipt records the exact command, input/source hashes, JNI ledger, workers and frontier. Large checkpoint/trace artifacts remain outside Git. Checkpoint validation establishes internal consistency, not cryptographic authenticity.

## Next bounded question

Trace native temporary-directory selection and its absence/fallback branches from the caller before declaring any environment fixture. An absent TMPDIR value, other environment keys, directory type checks and filesystem results are separate facts; none should be silently invented to pass the frontier. Keep strict unknown-operation stops.

## Import identity refinement

The original continuation receipt retains its historical operation label `getenv`. Static relocation analysis identifies the actual ELF symbol as `secure_getenv`: call `0x31178d` → PLT `0xd14e70` → slot `0xd30bc0` → RELATIVE addend `0x13d7136` → import slot `0x184d3e0`. This distinction matters for any future present-value scenario. An explicitly absent key can return null without asserting a secure-execution policy.
