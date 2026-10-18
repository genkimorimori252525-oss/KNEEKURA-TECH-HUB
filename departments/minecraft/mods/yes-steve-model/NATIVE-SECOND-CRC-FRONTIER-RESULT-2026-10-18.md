# Second masked CRC loop and CPU-input frontier

The guarded DT_INIT trial reaches CPUID leaf1 at0x16b44ff after 1,882,413 completed native instruction/model invocations. Fifteen verified summaries cover 23,591,981 CRC iterations, equivalent to 528,156,776 loop-instruction effects. This is not the number of actually interpreted instructions or a completion percentage. All12 first-visit static oracle checks pass and the original image remains unchanged.

## Counterfactual protection return, never changed permissions

The optional --protection-result success-input supplies return value0 only. It does not call host mprotect or relax the emulator's original-image protection. failure-input supplies 32-bit -1. The probe only accepts page-aligned bounded requests over existing original-image pages, legal protection bits and the pinned thunk/slot/frame. The first attempted original-image write would still stop before application, with a separate attempted-write record. Five tests verify this, including a blocked write after a supplied success result.

Two observed requests are (0xec5000,0x510e52,7) and (0xede000,0x1070,7). The larger interval covers page padding plus the original ELF RX segment beginning0xec5e00 and ending0x13d5e52. This is a conditional continuation probe, not proof that real protection changes succeeded.

## Reusable second CRC profile

A second21-instruction loop begins0x1503f30 and exits0x14e880b. Table0x16c0498 XOR0x3f168d01 equals the reflected CRC32 table in all256 entries. Its source is RAX, accumulator EDI, table base RDX, count RCX;24 temporary stack bytes are fully initialized per cycle. Exact code/table hashes are pinned alongside the first profile. The common summary implementation now selects profile-specific registers, mask, cycle length and scratch extent.

The first profile's30 full-state differential cases still pass, and30 additional cases pass for the second profile. All general registers, RIP, EFLAGS and scratch memory match full-loop emulation; recurrence results match zlib. Negative tests reject modified code/table and mutable source. In total14 CRC test methods pass, together with24 guard,12 loader,5 platform and5 protection-probe methods.

Under the explicit success-input scenario, six second-profile blocks summarize source intervals beginning0xed08b4,0x136919c,0xedf070,0x318,0xec90a4 and0xec5e00. Their actual immutable source bytes, lengths and hashes are in the paired JSON. No checksum equality or target authenticity decision is inferred merely from computing these CRCs.

## Current frontier and reproduction

CPUID is still blocked. EAX=1 and ECX=0 at0x16b44ff; no real host CPU identity/features were consulted. Next inspect the feature consumer or supply explicitly declared leaf1 counterfactual inputs, retaining the guard before any original-image write. Initialization and native binding recovery remain unfinished; central mappings unchanged669, independent semantic review NOT_RUN.

Reproduce with the previous exact ELF/Unicorn command, adding --virtual-loader image-only --virtual-platform --protection-result success-input --accelerate-crc. Use --steps2000000 and --seconds120 as separate option/value arguments. Binaries/full traces remain external; the paired JSON records source/trace hashes. Earlier failure-input run reached the2million-step cap and is not evidence of final failure behavior.
