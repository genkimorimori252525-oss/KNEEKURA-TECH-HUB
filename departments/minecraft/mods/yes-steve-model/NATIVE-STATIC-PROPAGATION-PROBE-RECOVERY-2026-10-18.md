# Bounded static constant-propagation experiment

Outcome: INCOMPLETE, not an automatic proof of the initialization path. [Receipt](NATIVE-STATIC-PROPAGATION-PROBE-2026-10-18.json), [fixed input ranges](NATIVE-STATIC-PROPAGATION-MANIFEST-2026-10-18.tsv), [experiment script](tools/ghidra/YsmStaticPropagationProbe.java).

## Purpose and observed result

The preceding scalar/interval proofs establish useful oracle values, but repeating all arithmetic by hand is slow. This experiment tested Ghidra 12.1.4's existing SymbolicPropogator on the bounded DT_INIT prologue, with an initially symbolic RSP and unknown registers left unknown.

The final retained script reproduced 87 before-instruction records and 400 visited bytes. It matched the first predicate at 0x174d06f (ZF=0), then stopped at 0x16668ff because CF remained symbolic. The register/context output also lost precise values across overlapping stack accesses. No unknown input was filled with zero and no unresolved branch was silently chosen.

Ghidra represents some constants, including the first zero flag, in its SuspectConst space. The experiment uses the framework's documented isConstant predicate rather than equating only the ordinary constant space with a known value. This does not convert the later symbolic CF into a constant. The first oracle value is independently supported by the already retained scalar proof.

This result describes this bounded configuration. It is not a claim that all Ghidra analyses fail on the binary, nor a bug report, nor a contradiction of the separate byte-interval proof. It shows that this configuration cannot replace that proof end-to-end.

## Analysis-only adaptation

Machine CALL instructions are treated as direct branch transfers for this static flow experiment, while retaining their preceding original stack p-code. This avoids applying an ordinary calling-convention summary to the known stack-rewriting thunks. Original native bytes are unchanged. The script overrides only temporary analysis instruction/control objects and processes a read-only project without saving changes.

It stops on a return, unknown predicate, unsupported predicate kind, oracle disagreement or its instruction budget. It is intentionally an experiment for the supplied prologue ranges, not a general deobfuscator. The source does not implement a CPU emulator and does not execute the target library or perform external calls.

## Reproduction

Use the same pinned Ghidra/JDK and static project as the cross-check. In headless process mode, pass -readOnly -noanalysis, the repository tools/ghidra script path, and:

```text
-postScript YsmStaticPropagationProbe.java <NATIVE-STATIC-PROPAGATION-MANIFEST-2026-10-18.tsv> <external-output.tsv>
```

The retained script was compiled and run against the actual static project; its output reproduced the same first match and unknown-CF stop. Raw context traces remain outside Git. Do not label a normal tool exit as successful whole-path recovery: the evidence status is explicitly INCOMPLETE.

## Next option, not yet executed

A separate user approval was requested for a narrowly bounded, isolated-memory simulation of the Linux DT_INIT path: no host MOD/JNI execution, no external/OS calls, and a stop at the first non-stack write or 10,000 instructions. That simulation has NOT been run by this cohort. Until approval, continue only static inspection/preparation and preserve the earlier uncertainty about initializer effects and data stability.
