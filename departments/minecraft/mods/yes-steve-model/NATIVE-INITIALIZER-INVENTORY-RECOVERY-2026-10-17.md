# Linux initializer inventory and file-state assumption check

Status: PRIMARY_STATIC_REVIEW_ONLY. Independent semantic review NOT_RUN. [Reproducible inventory](NATIVE-INITIALIZER-INVENTORY-2026-10-17.json) is pinned to the exact release JAR and native-image SHA-256. No target image was loaded or executed.

## Important distinction

The native library has DT_INIT at 0x152eb19 and a 360-byte DT_INIT_ARRAY at 0xd163d8: 45 eight-byte slots. All 45 raw file slots contain zero, but each has exactly one symbol-zero R_X86_64_RELATIVE relocation supplying a nonzero target addend. Zero-filled raw slots therefore do NOT mean that the library has no initializer functions.

The inventory resolves those entries symbolically as load_bias + addend and verifies each target's file backing. It also records DT_FINI at 0x14f9be5 and two relocated FINI_ARRAY slots. These are entry-point metadata, not 45 recovered functions or proof that constructors completed.

For the loader semantics, the inspected [glibc 2.40 initializer source](https://github.com/bminor/glibc/blob/glibc-2.40/elf/dl-init.c) checks relocation state and calls DT_INIT before iterating DT_INIT_ARRAY. Its [x86-64 relocation implementation](https://github.com/bminor/glibc/blob/glibc-2.40/sysdeps/x86_64/dl-machine.h) uses load bias plus addend for R_X86_64_RELATIVE. This is a reference loader model; the actual user's loaded libc version and runtime execution were not inspected.

## Relocation check, not immutability proof

The table parser reads 8,857 ordinary RELA records and 257 PLT RELA records: 9,114 total. The observed types are 8,812 RELATIVE, 257 JUMP_SLOT, 38 GLOB_DAT, four R_X86_64_64 and three DTPMOD64. All have known eight-byte destinations in this bounded parser; unsupported relocation types/tables fail rather than being silently ignored.

Neither four-byte word at 0xd2cd48 nor at 0xd2cd4c overlaps these relocation-write intervals. This extends the earlier second-return cohort, where overlap for the second word had not yet been checked. It does NOT establish that initializers, native methods or another runtime writer preserve the file values. Keep both file-state assumptions on the concrete JNI return candidates.

## Bounded initializer prefixes

The tool captures one first-transfer prefix for DT_INIT and each of the 45 INIT_ARRAY entries, validating disassembler addresses and bytes. Among the 45 array entries, the first transfers are 25 CALL, nine JMP, six JE, four JNE and one RET. DT_INIT itself starts with a direct JMP. These counts describe prefixes only, not complete paths, function behavior or source-name recovery. Call-return continuations and constructor memory effects remain unresolved.

The separate exploratory DT_INIT direct-edge walk reached a conditional frontier, so DT_INIT cannot be treated as an inspected empty stub. Its full effects must be accounted for before treating file-state data as immutable. Raw exploratory disassembly stays outside Git.

## Verification and next step

Twelve inventory tests plus ten existing first-transfer parser tests passed; a fresh exact-JAR inventory replay matched. Cases include null termination, signed RELA addends, truncation, duplicate/non-relative initializer relocations, overlapping preceding writes, adjacent non-overlap, unknown relocation rejection and disassembly-byte disagreement. No whole-project CI or mapping promotion.

Next priority: use static data-flow analysis to identify writes to the two candidate data words and resolve the carried key for the third symbolic return. Preserve constructor ordering as a dependency. Do not replace unresolved initialization effects with a claim that zero relocation overlap proves runtime stability.
