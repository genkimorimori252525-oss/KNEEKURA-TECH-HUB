# Guarded independent CPU backend

## Results

The new Unicorn backend reproduces the strict Ghidra instruction prefix exactly:9,204 attempted/9,203 completed steps, same unknown-copy source read, all12 first-visit static oracle checks matching. With explicit virtual clock, heap and file models it crosses the previously incorrect SHR/JL branch at0x14fd6ea. First path difference is step 175,518: Unicorn takes0x176dca6, Ghidra falls through0x14fd6f0. This agrees with the independent host toy's overflow-flag result and explains the old bad read without treating it as target behavior.

Two authored proc-status fixtures (TracerPid0 and1234) each reached500,000 steps, including fopen and two fgets model calls. Their instruction paths remain identical through that window even though the copied line lengths differ. This is NOT a proof that the field is ignored or that both cases have the same final outcome. The separate unavailable-file scenario follows a different path and also reaches its500,000-step cap.

An extended TracerPid0 fixture run completes2,000,000 instruction/model steps under a120-second watchdog. It includes fopen, two fgets and fclose, five explicit clock samples, one424-byte virtual allocation and seven heap-write events. It reaches a repeated28-instruction CRC32-style loop and the step cap; no original-image write is applied. There are86,421 unique instruction addresses, not2,000,000 recovered functions. Initialization remains unfinished.

Detailed receipts and exact source/trace hashes are in NATIVE-UNICORN-GUARDED-2026-10-18.json. No host proc file or target imported library is accessed. Central map669 is unchanged, and no native/Java binding is promoted.

## Guard design

Unicorn normal write-hook cancellation is not a pre-write barrier. The backend therefore maps the original image read/execute-only, and treats each native instruction as a candidate transaction. Mapped private bytes written by the candidate are journaled. If a guard fails, those private bytes and the saved CPU context are restored before the instruction is retired; initialized/opaque-byte metadata is committed only for a successful instruction. This also protects allocation padding and cross-page private writes. Original-image protection stops an actual image store; rollback is not used to justify writable image pages.

Fault snapshots are canonical pre-instruction states after rollback, unlike Ghidra's earlier partial p-code snapshots. Do not compare them as if both were architectural post-instruction states. Modeled APIs validate their arguments and allowed return/destination ranges before committing their bounded effects. No host syscall or target-native function is invoked.

The model retains the explicit synthetic GP/flags state, analysis imagebase0, unrelocated imports, zero-filled ELF BSS, bounded private stack, max1MiB allocated heap, opaque byte-copy identities, selected clock inputs and authored file fixtures. Other file requests, unknown values, unsupported environmental instructions, invalid transfers and non-private writes stop. The optional file models are narrow fopen/fgets/fclose behavior, not a complete libc/OS model or errno implementation.

Twenty-four unit tests cover private stack effects, read-only image protection, rejected allocation-padding writes with rollback, mapped/unmapped boundary rollback, unknown/opaque reads, known overwrite, indirect-call rollback, syscall/segmented/privileged-environment refusal, the two verified ISA cases, known/opaque/directional/overlapping copies, selected clock values and disabled mode, malloc bounds, virtual file lifecycle and blocked file-buffer writes. Toy cases load no target image. Actual target runs separately pin the exact ELF hash and verify every loaded segment after stopping.

Original page mapping/protection was consolidated into contiguous permission runs. A single watchdog replaces a per-instruction timeout thread. The9204-step strict trace remains byte-identical after this optimization and completes in about 0.46 seconds in the observed environment. This is a local measured result, not a general performance guarantee.

## Reproduction

Install the pinned official Unicorn 2.1.4 wheel in an external venv as recorded in the preflight. Use that venv's Python:
- tools/test_native_unicorn_guarded_ysm_265.py:24 guard tests, no target input.
- tools/native_unicorn_guarded_ysm_265.py --image ORIGINAL_SO --out EXTERNAL_TRACE --mode strict --steps 10000
- The same tool with --mode proc-fixture --pid 0 (or 1234), or --mode proc-failure, selects explicit synthetic file inputs. --seed 1122334455667788 and --stride 3e8 are hexadecimal clock parameters.
- Resource arguments currently allow up to --steps 2000000 and --seconds 120. They are safe reversible analysis budgets, not permission to call real services or modify the original image.

Keep binaries, package/venv, raw traces and generated native fixture executables outside Git. The installed wheel's official source and hash are recorded in the preceding preflight.

## Next optimization under verification

The long tail repeatedly executes28 fixed instructions. Its table at0x170ec60 equals the standard reflected CRC32 table XOR0xa30cc68d in all 256 entries; the loop XORs that constant again each iteration. This identifies the recurrence, but no accelerated summary is enabled in this checkpoint. Next verify a block summary against full guarded CPU execution, including all registers, flags and temporary stack bytes, before using it to avoid millions of redundant interpreter steps. Do not merely skip the loop or claim an unverified checksum result.
