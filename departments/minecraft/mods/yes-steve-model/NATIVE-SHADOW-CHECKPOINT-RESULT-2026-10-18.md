# Bounded working-image state and restartable analysis

The opt-in tools/native_shadow_image_ysm_265.py keeps the exact original ELF file and immutable reference bytes separate from a simulated working image. It never loads the target as a host library or invokes its imports, real loader, file API or OS protection changes. The default native_unicorn_guarded backend remains read-only.

## Working-image guard

Only modeled, page-aligned, bounded protection requests over existing image pages change working-copy permissions. The latest overlapping request wins; restoration to read/execute revokes writing. Exact byte-range guards are intentionally more restrictive than page permissions. Existing executable segment bounds still constrain instruction fetches; heap/stack/metadata cannot become code.

Every candidate image write is journaled before the engine can apply it. Failure rolls back bytes and CPU context. Successful writes update a separate expected-image ledger, capped at8MiB of committed write bytes and1million events. The entire working image is checked against that ledger; immutable reference hashes and the original source file are checked separately. Reports explicitly distinguish a changed working view from unchanged reference/file. CRC summaries are conservatively disabled after the first committed working-image write.

The observed stores so far are eight-byte pointers at0xedf060 (virtual424-byte context at0x710000000000) and0xedf068 (virtual24-byte object at0x7100000001b0). No native instruction bytes have been changed by these two stores. Working-image changes are not runtime Java/native binding proof.

## Two harness corrections

CPUID leaf1 does not use ECX as a subleaf selector. The former restriction to input ECX0 incorrectly stopped a second leaf1 query with ECX0xec8150. The model now preserves the declared leaf1 output fixture regardless of input ECX, records the input, and still blocks other leaves. The AMD [CPUID specification](https://www.amd.com/content/dam/amd/en/documents/archived-tech-docs/design-guides/25481.pdf) distinguishes this standard function from functions with an ECX selector. No real CPU query is made.

The original ELF's first PT_LOAD is executable from address0 and contains actual protected code below0x1000. CALL0xf38 is a file-backed internal transfer, not an external import. A former blanket minimum-code-address0x1000 was too restrictive. Nonzero addresses in an original executable range are now eligible; address0, external memory and private heap/stack remain blocked. Exact bytes at0xf38 begin d0c366410fbbd2. A low-address authored fixture covers this correction.

## Checkpoints rather than repeated full-prefix execution

The optional --checkpoint-out and --resume-checkpoint arguments save/restore local JSON state: complete Unicorn CPU context, private bytes plus initialized/opaque masks, bounded heap/model state, immutable image signatures, protection history and working-image patches. No pickle or executable deserialization is used; decompression length and CPU version/layout are validated. Only consume this harness's trusted local checkpoints, outside Git. A state checkpoint is not proof that arbitrary future harness changes preserve prior semantics.

On resume, instruction/model invocation counters restart for the continuation; origin_completed records prior completed invocations. Other model counters inherit prior totals and must not be added a second time. Contextual/model extensions must be compatible with the captured state. A saved boundary reproduced exactly with one attempted instruction and zero completed instructions before adding its missing model.

## Lazy C++ allocation frontier

The stopped RET0x14f9c20 is part of an unrelocated lazy-binding path. Its verified stack contains zero resolver, zero link-map, relocation index, caller return. ELF JMPREL index250 is JUMP_SLOT0x184d7e8, symbol269 _Znwm; index205 is slot0x184d680, symbol225 _Znam. Only these pinned entries are modeled as bounded private allocation, with no actual dynamic linker or C++ call. Allocation exhaustion stops rather than fabricating a C++ exception.

Observed allocations after the original424-byte malloc are24,48 and2080 bytes. Returned storage starts unknown until actual guest/model writes initialize it. Next unresolved lazy index197 is JUMP_SLOT0x184d640, symbol218 memset. Its current arguments are destination0x710000000200, value0, size0x820. The next bounded model should initialize only that private allocation and preserve default rejection elsewhere.

## Validation and limits

102 scoped test methods pass, including17 working-image tests,12 checkpoint tests and6 lazy-import tests; the two CRC profiles additionally contain60 full-state differential cases. These are not independent semantic review or a completion percentage. Central mapping remains669 (405 CONFIRMED+264 HIGH), unchanged. Independent semantic review NOT_RUN.

Use the exact pinned ELF and external Unicorn2.1.4 venv. The shadow driver declares synthetic clock/proc0, image-only loader, module-open failure, page4096, protection-success and CPUID-zero inputs. It is a conditional scenario, not observed actual OS behavior. Optional --steps and --seconds retain caps4million/180. Keep originals, snapshots and full traces outside Git. The paired JSON retains trace/checkpoint hashes and the full-prefix versus resumed-state comparison.

## Full-prefix replay agrees with resumed state

A fresh current-driver run and the compatible checkpoint continuation chain both complete2,918,592 instruction/model invocations and reach the same memset frontier. All CPU context payload bytes, private-memory bytes, initialized/opaque masks, working-image patches, protection history, allocator/model state and cumulative completed count match. The diagnostic rollback count differs0 versus1 because an earlier unresolved-call boundary was probed; it is not target architectural state.

Four differing raw context bytes were traced to an unused memory-snapshot pointer in the pinned Unicorn header, not CPU payload. The [2.1.4 context layout](https://github.com/unicorn-engine/unicorn/blob/2.1.4/include/uc_priv.h#L401-L411) and [restore implementation](https://github.com/unicorn-engine/unicorn/blob/2.1.4/uc.c#L2411-L2443) show the separation. Checkpoints now explicitly select CPU-only mode and zero unused memory-snapshot header fields before serialization/restoration; no stale host memory pointer is used. The normalized context payload matches exactly, and122 exposed register fields were also independently compared with zero differences.

The comparison tool reports16 passing state checks. Restoring the sanitized checkpoint reproduces the same boundary with one attempted and zero completed instructions, without replaying the preceding2.9million steps. The newest source hashes in the receipt describe the validated final implementation; earlier trace files retain their own hashes and historical model boundaries.
