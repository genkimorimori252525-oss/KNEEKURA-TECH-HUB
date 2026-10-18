# Reproducible Ghidra static cross-check

Status: PRIMARY_STATIC_REVIEW_ONLY. Independent semantic review NOT_RUN. [Receipt](NATIVE-GHIDRA-CROSSCHECK-2026-10-18.json), [fixed instruction manifest](NATIVE-GHIDRA-MANIFEST-2026-10-18.tsv), and [memory manifest](NATIVE-GHIDRA-MEMORY-2026-10-18.tsv).

## Verified result

Ghidra 12.1.4 imported the exact Linux image at analysis image base zero with relocation application, external-library loading and automatic analysis disabled. All seven file-backed PT_LOAD segments matched their original file-byte hashes. This verifies imported file content, not runtime relocation or initialization effects.

The fixed 73 ranges contain 673 instruction occurrences, with 669 unique instruction addresses because some ranges overlap. GNU objdump 2.44 and Ghidra agreed on every address, length and instruction byte sequence. These 669 addresses are unrelated to the central Java mapping count; no mappings were added or promoted.

Selected raw p-code supports the previous local interpretation: NEG CX computes carry from nonzero input and zero from the result; JBE combines CF and ZF. RET 8 loads the return address from RSP and advances RSP twice by eight. OR clears carry/overflow and defines sign/zero; JG tests nonzero and matching sign/overflow. This is an additional decoder/lifter check, not independent semantic review or proof that the selected path executes at runtime.

The two imported data words remain file bytes 52ec51dc and a314743b. Constructor effects and runtime data stability are still unresolved. No target native library, JNI initializer or game code was executed; no native emulator was run.

## Installation and recovery

The user approved the official Ghidra installation and static-analysis use on October 17. Initial local analysis succeeded then, but its temporary tool/output directories were absent in the resumed environment on October 18. The results in this receipt were regenerated, not inferred from the earlier report. Scripts, manifests and derived evidence are now retained here; raw images, projects, lift text and tool archives stay outside Git.

Verified official packages:

- [Ghidra 12.1.4](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build), ghidra_12.1.4_PUBLIC_20260921.zip, 569649598 bytes, SHA-256 ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db.
- [Eclipse Temurin JDK 21.0.12.1+1](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.12.1%2B1), OpenJDK21U-jdk_x64_linux_hotspot_21.0.12.1_1.tar.gz, 207473347 bytes, SHA-256 ce79869e1307ed8ee1e2baa86a412b1eb5b75d10a01006d788a6f968bcfaee94.

The existing Java 21 runtime lacked a javac executable accepted by the launcher. A full JDK of the same Java version was installed in the private tool cache; system Java was not replaced. HOME, XDG config/cache/data and Java user.home are scoped to the external output directory. No global account or MCP configuration is needed.

## Reproduction

After obtaining the approved packages and checking their hashes, set GHIDRA_HOME and JAVA_HOME to their extracted directories, then run:

```sh
bash tools/ghidra/run-scoped-lift.sh /external/exact-ysm.jar /external/new-output-directory
```

The wrapper refuses an existing output directory and Git work-tree output, verifies the exact artifact/image, creates a fresh static project, lifts the fixed manifest, and writes a cross-check receipt. The Java script performs only static decoding/p-code generation; it does not populate or execute target functions. The Python checker checks completion, coverage, byte hashes, all selected instruction boundaries and both data words.

Eight negative/positive parser tests passed, and the exact-artifact replay matched. A fresh-project invocation of the wrapper is tested separately. No full-project CI was used.

## Import warnings and limits

With relocation application deliberately disabled, the loader emits 47 attempts to create a function at address zero for raw zero init/fini slots. These warnings are retained in the external log, not treated as valid function recovery. The preceding initializer inventory already resolves 45 init and two fini slots through relocation addends. There are also 233 unresolved external symbols because external libraries are intentionally not loaded. Neither condition prevents the byte-verified pseudo-disassembler lift, but both preclude claiming a fully analyzed executable.

Next: retain and verify the third-return scalar/data dependencies, then investigate initialization writes. Whole-library CFG recovery, native bindings, constructor side effects and runtime correctness remain open.
