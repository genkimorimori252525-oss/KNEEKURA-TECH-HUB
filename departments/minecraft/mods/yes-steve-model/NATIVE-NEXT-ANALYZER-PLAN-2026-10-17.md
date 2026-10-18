# Next native analysis pass: scoped data-dependency inspection

Status at capture: plan only. Ghidra has not been installed or run for this analysis. No target execution is proposed. Existing binutils/Python evidence remains usable without this optional engine.

## Current handoff boundary

The fixed Linux file-state return candidate is image-relative 0x12c3a51, conditional on the data word retaining file bytes. An additional local first-transfer inspection finds:

- Prefix 0x12c3a51 ends in a direct CALL at 0x12c3b1b to 0x12c4601.
- Prefix 0x12c4601 ends in JB at 0x12c4638, target 0x1186a8d.
- That JB follows a stack-memory word shift. Its condition has NOT been resolved here; do not inherit an older carry flag or assume a taken edge.

This is an inspection target, not a recovered JNI function or verified runtime path. The prior [file-state candidate](NATIVE-RETURN-FILE-CANDIDATE-RECOVERY-2026-10-17.md) and [return slice](NATIVE-RETURN-SLICE-RECOVERY-2026-10-17.md) retain all their assumptions. Preserve the original 65-test checkpoint rather than relabeling additional observations as tested behavior.

## Optional analyzer selection

[REA's official documentation](https://github.com/morluto/rea/blob/main/README.md) describes native analysis as using an existing Hopper, Ghidra or IDA backend. REA references alone are not an installed native decompiler. The proposed next backend is the official Ghidra release, used locally in headless static-analysis mode; no agent-account registration, paid agent invocation or target debugger is part of this plan.

Pinned release: [Ghidra 12.1.4](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build).

- Official asset: ghidra_12.1.4_PUBLIC_20260921.zip
- Size reported by the official release API: 569,649,598 bytes
- SHA-256: ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db
- [Tagged Getting Started](https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.1.4_build/GhidraDocs/GettingStarted.md) requires Java 21, not the Java 25 requirement currently shown on the development branch README. Do not install an unnecessary JDK upgrade by mixing release/development instructions.
- Review the official [security advisories](https://github.com/NationalSecurityAgency/ghidra/security/advisories) for the chosen version. Do not treat tool installation as a claim of perfect parser safety.

## Scope after installation is authorized

1. Keep the pinned package/tool cache, project database and raw output outside Git. Verify the distribution hash before running the analyzer. Keep original YSM JAR and native images unchanged.
2. Begin with the exact Linux ELF and previously proven file-backed ranges. Validate the imported memory map against PT_LOAD/file offsets; distinguish analysis-program image base from actual runtime load bias.
3. Disable broad automatic analysis initially. Export instruction/p-code evidence for the two selected prefixes and their direct data dependencies; avoid a full-library sweep for this small question.
4. Recheck the established constant branches and rewritten-return expression against the second engine. Treat disagreement as a blocker to promotion, not a reason to adjust evidence to match.
5. Track unknown input values, stack aliases, partial-register writes and flag definitions explicitly. The immediate question is the source of the word shifted before JB and whether it is constant under the existing assumptions.
6. If a condition depends on runtime-modified data, preserve that boundary. Do not run JNI initialization, emulate the native target, unpack protected payloads, patch protection or decode protected model assets as an implicit next step.
7. Publish derived evidence and reproducible narrow checks only. Installation success, a decompiler listing and a clean analysis run do not mean native semantics or Java-native bindings are recovered.

Stopping condition for this pass: the selected condition/data dependency is supported by exact evidence, or the unresolved dependency is precisely identified. This is a scoped pass within ongoing analysis, not a declaration that YSM deobfuscation is complete.

## Follow-up to the initial boundary

The [candidate stack-guard proof](NATIVE-CANDIDATE-STACK-GUARD-RECOVERY-2026-10-17.md) subsequently resolved the local JB as untaken using existing tools. Its fallthrough is 0x12c463e. This supersedes only the plan’s original local-condition question, not the broader runtime/data-dependency uncertainty or NOT_RUN status of Ghidra. A future analyzer pass should use the new frontier rather than repeat the resolved guard.

## Frontier update after bounded manual work

The earlier candidate guard and the second rewritten return now have separate evidence cohorts. Two subsequent guards lead to the symbolic third return at 0xf0aecb; concrete destination depends on the third decoded word/carried key. Start from these latest proofs rather than repeating the earlier branch work.

The initializer inventory now resolves 45 DT_INIT_ARRAY slots through RELATIVE addends and retains DT_INIT at 0x152eb19 as a separate dependency. Check writes to data words 0xd2cd48 and 0xd2cd4c before promoting file-state candidates to runtime claims. The absence of overlapping relocation records is insufficient. Ghidra installation remains subject to the outstanding user approval; no tool installation or target execution is implied by this plan.

## Approved and reproduced, October 18

The user approved the official installation on October 17. The [Ghidra cross-check](NATIVE-GHIDRA-CROSSCHECK-RECOVERY-2026-10-18.md) supersedes this plan's earlier installation-pending status. It verifies seven file-backed load segments and 73 selected ranges with automatic analysis disabled. Temporary October 17 outputs were absent after environment resumption; the retained October 18 evidence was freshly reproduced. The next unresolved work remains the third-return dependencies and initializer effects, not installation permission.
