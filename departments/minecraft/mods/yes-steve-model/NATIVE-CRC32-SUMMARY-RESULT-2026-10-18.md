# Verified masked CRC32 loop summary

The optional --accelerate-crc backend reaches a new DT_INIT frontier under the explicit proc-fixture pid0 and synthetic-clock scenario. It completes 1,201,609 instruction/model invocations, summarizes 4,675,025 loop iterations across nine blocks (130,900,700 logical instruction effects), then stops before the unrelocated dladdr import. These are distinct counters, not 130 million actually interpreted instructions or a completion percentage.

## Exact loop and equivalence

Entry 0x15f0d5e, exit 0x14728bf, 28 instructions per cycle. All 256 DWORDs at 0x170ec60 XOR 0xa30cc68d equal the reflected CRC32 table with polynomial 0xedb88320. Exact code bytes and table SHA are pinned in tools/native_crc32_loop_profile_ysm_265.py.

Acceleration requires the entire source to be known immutable original-image memory, the pinned table/code, count 2..16 MiB and a valid private stack. It computes N-2 recurrences, executes one full original cycle in a separate guarded reference CPU, then commits all registers, flags and the 32 fully initialized temporary stack bytes. The main CPU executes the final iteration normally. This preserves intermediate state rather than merely skipping a loop. Failed preconditions retain ordinary execution.

Eight CRC test methods pass, including 30 full-loop versus summary comparisons across ten lengths and three seeds. Every general register, RIP, EFLAGS and temporary stack byte matches, with zlib recurrence cross-checks. The existing 24 guard methods also pass. CRC differential fixtures contain small pinned target fragments executed only in emulation; the guard fixtures are authored toy instructions. No target code executes on the host CPU.

Equivalence assumes the declared per-read synthetic clock, independent of interpreted instruction count. A future instruction-time model must account for summarized logical steps.

## New frontier

The preserved canonical state stops at 0x13d8466, bytes ff25b4534700, JMP through GOT slot 0x184d820. ELF GLOB_DAT symbol 276 is dladdr. The slot is zero because relocations are deliberately disabled. RDI=0x162a5f8 queries an address within the image; RSI=0x700000007f70 is the proposed output buffer; RSP=0x700000007dc8 points to the caller return frame. This is an unresolved import boundary, not evidence of a native application crash.

The run includes six modeled clock reads, one virtual malloc, nine heap-write events, one fopen, two fgets and one fclose. Original image preservation passes; no host import, OS file operation or original-image write occurs. No native/Java bindings are promoted; central mapping remains 669. Independent semantic review NOT_RUN.

## Reproduction and next step

Use the external pinned Unicorn 2.1.4 venv and exact original ELF with tools/native_unicorn_guarded_ysm_265.py --image ORIGINAL_SO --out EXTERNAL_TRACE --mode proc-fixture --pid 0 --steps 2000000 --seconds 120 --accelerate-crc. Defaults are hexadecimal seed 1122334455667788 and stride 3e8. Run both test_native_unicorn_guarded_ysm_265.py and test_native_crc32_loop_profile_ysm_265.py.

The paired JSON preserves source/trace hashes and compact trace receipts. Keep originals and full traces outside Git. Next investigate a narrow, explicitly synthetic loader-metadata model for dladdr; never invoke host dladdr or infer actual runtime loader metadata. Initialization remains unfinished.
