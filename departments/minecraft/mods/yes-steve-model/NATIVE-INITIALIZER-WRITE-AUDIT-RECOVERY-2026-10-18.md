# Initializer-prefix writes and relocated import chains

Status: PRIMARY_STATIC_REVIEW_ONLY; independent semantic review NOT_RUN. [Evidence](NATIVE-INITIALIZER-WRITE-AUDIT-2026-10-18.json) revalidates the exact artifact and the retained 73-range Ghidra/GNU receipt before inspecting the 46 initializer prefixes.

## What this closes, and what it does not

The captured first-transfer prefixes contain 70 direct-address p-code write operations. None overlaps the 19-byte interval 0xd2cd48..0xd2cd5a used by the current file-state candidates. There are also 146 STORE operations whose addresses are not direct constants in this narrow classifier. Many represent stack operations, but this audit deliberately does not turn an unresolved address into an assumed-safe write.

This is NOT an absence-of-writes proof for the library. Subsequent initializer blocks, callees, DT_INIT's obfuscated continuation, indirect stores, and other runtime writers remain unresolved. The watched data is still in a writable load segment. File-state immutability and actual runtime reachability remain unproven.

## Two-hop import resolution

Two apparent local jump stubs are not unnamed functions. Their exact bytes and relocation records give these chains:

- 0xd14710 -> RIP-relative slot 0xd30810 -> R_X86_64_RELATIVE addend 0x13d6e84 -> RIP-relative slot 0x184d048 -> JUMP_SLOT dynamic symbol 10, __cxa_atexit. Eleven initializer first-transfer sites use this original stub.
- 0xd14e70 -> slot 0xd30bc0 -> RELATIVE addend 0x13d7136 -> slot 0x184d3e0 -> JUMP_SLOT dynamic symbol 130, secure_getenv. One captured initializer first-transfer site uses it.

Reading the first slot's symbol index as an import name would incorrectly produce an empty string: RELATIVE relocations have symbol index zero and must be followed through their addend. The tool rejects unexpected relocation kinds, ambiguous slots and unnamed/defined symbols rather than guessing.

These are declared import identities, not verification of the runtime library binding or interposition behavior. The [glibc reference implementation](https://github.com/bminor/glibc/blob/glibc-2.40/stdlib/cxa_atexit.c) registers an exit/unload callback; registration does not mean the callback runs during this initializer. Do not follow those callback bodies as immediate initializer calls without separate evidence.

## Shared-runtime attribution hint

The initializer prefix at 0x2aaae0 loads RDI with the string at 0x46267, which is GLIBCXX_TUNABLES, before calling the secure_getenv import. Its direct writes in this prefix initialize storage around 0xd30e20..0xd30e5f, not the watched candidate bytes.

The inspected [GCC 14.3 libsupc++ exception-pool source](https://github.com/gcc-mirror/gcc/blob/releases/gcc-14.3.0/libstdc%2B%2B-v3/libsupc%2B%2B/eh_alloc.cc) contains the matching environment-variable lookup in pool construction. This supports a shared C++ exception-runtime attribution hypothesis. It does not establish the exact compiler version, full function equivalence or the effects of its continuation. No central YSM mapping is promoted from this comparison.

## Reproduction and next work

Run tools/native_initializer_write_audit_ysm_265.py with --jar, --lift (the external retained 73-range lift), --out and optionally --check. Eight tests cover RIP-relative slot decoding, refusing other branch encodings, direct RAM output, constant/unknown STORE addresses, read-versus-write classification, and interval boundaries. Exact-artifact replay matches.

Next priority is the unresolved DT_INIT/data-writing callees, not repeatedly analyzing callback registration as if it were immediate model loading. Maintain the distinction between known direct writes, unresolved stores, imported API metadata and full constructor effects. No target execution, native emulator, full-project CI or confidence promotion occurred.
