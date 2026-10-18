# Deterministic loader view and ordered initializer sequence

Before invoking init-array callbacks, the working-image driver now applies8812 symbol-zero R_X86_64_RELATIVE entries at analysis base0. Every destination was verified inside an ELF writable PT_LOAD segment. Their total size is70496 bytes. Initial ELF writable permissions are modeled before target execution; later protection requests still override them. Original file/reference bytes remain unchanged and each working fixup enters the mutation ledger.

Only deterministic RELATIVE relocations are applied. Four R_X86_64_64,38 GLOB_DAT,257 JUMP_SLOT and3 TLS-module entries remain unresolved; imported functions are still narrow explicit models, not host calls. This remains a partial synthetic loader, not a fully linked live process.

## Verified sequence boundary

Under this loader view, DT_INIT again returns after exactly3,290,734 instruction/model invocations. The45 callback targets are re-derived from actual dynamic metadata/RELATIVE entries, not assumed from zero raw array slots. The sequence driver preserves working/private state, prepares declared zero caller inputs and an entry sentinel, checks callee-saved registers on return, and invokes callbacks in order. A stopped callback retains its frame and index for checkpoint continuation rather than starting over.

The first callback(index0, target0x2b8620) executes251 steps and reaches unsupported lazy index133: slot0x184d440, symbol143 __newlocale. Arguments are mask0x40, literal'C', base0. Callback0 has already committed126 additional working-image writes before the unsupported call. The latest ledger has8812 loader fixups plus128 runtime events(999 runtime bytes); these are preserved for continuation. Zero callbacks have completed; no later callbacks were skipped or counted complete.

## Current next model

The first dependency is GNU C-locale construction. Read the primary GNU libc API/layout/ctype sources and model only the required deterministic'C' behavior. Unspecified private libc fields must remain unknown, not silently zero-filled. Never call the host locale API or change host/global locale. Unsupported locales/items still stop. This is initializer support work, not a native/Java binding promotion.

## Tools and restart

- tools/native_elf_loader_view_ysm_265.py parses the exact artifact and applies validated fixed RELATIVE entries to the working view.
- tools/native_initializer_sequence_ysm_265.py runs DT_INIT then45 callbacks under a shared bounded process budget. --resume-checkpoint requires the relocated-view snapshot, preventing accidental mixing with older unrelocated scenarios.
- The private checkpoint records phase, active callback, completed indices, saved callee registers and in-progress frame.
- Loader fixups establish the fixed initial CRC input view. Summaries remain disabled after the first runtime image store, not merely after deterministic pre-execution relocation.

Eight new authored tests cover loader destination validation, duplicates, ordering, callback frame preservation and process budget boundaries. Existing scoped guards/checkpoints/CRC tests remain required. Raw traces, originals and snapshots stay outside Git. The paired JSON records exact source/trace/checkpoint hashes. Independent semantic review NOT_RUN; central map669 unchanged.
