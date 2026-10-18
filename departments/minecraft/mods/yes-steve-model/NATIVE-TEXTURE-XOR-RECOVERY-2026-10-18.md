# Texture source transform and normal-path reapplication

## Result

Helper `0x4df880` performs a length-preserving XOR of source bytes with generated 64-bit words, consumed in little-endian byte order. Upload `0x3bf0c0` applies it in place before either upload branch; `0x3a58e0` builds a fresh equivalent generator and reapplies it to the same source allocation on both normal returning branches. Given unchanged seed bytes and length, no intervening source-byte modification, valid storage, and normal completion, the second application restores every original byte: `(x XOR k) XOR k = x`. This is a conditional static result, not evidence of an observed runtime restoration.

The seed is concretely the receive-created node's 16 inline bytes at `node+0x48`, mixed with constant `0xd017cbba7b5d3581`. It is separate from the source allocation pointer at `node+0x18`. The generator and transformation require no source-dependent key update. No encryption, decompression, security strength, or protective/malicious intent label is needed to describe these operations.

## Provenance and verification

Original SO SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. `reproduce.py` verifies that hash, extracts eight original file-backed ranges with backing metadata, resolves two original ELF relative relocations, and checks authored synthetic-byte XOR algebra. [evidence receipt](NATIVE-TEXTURE-XOR-EVIDENCE-2026-10-18.json) pins the earlier texture and receive receipts; those receipts are unchanged. This cohort executes only Python analysis and objdump disassembly. It does not execute/emulate original machine code, read/extract original assets, run a JVM or GL, or edit the repository.

The synthetic checks are deliberately independent of the recovered word generator: invented words/bytes test involution over 18 lengths (including tails and a 312-word boundary), mutation-delta persistence, and 257 split positions. They prove algebra, not fidelity of an implementation of the target generator.

## Transform calling contract and state

System V arguments at `4df880`: RDI state, RSI source pointer, RDX source byte count, RCX destination pointer, R8 destination capacity. Zero count returns immediately at `4df88b/4df88e`, without dereferencing state or buffers. Nonzero count larger than capacity branches at `4df897/4df89a` to error construction `4dfaa2`; it does not truncate. The two texture callers pass identical source/destination pointers and identical count/capacity, so that guard passes for their supplied length.

State layout:
- `+0..+0x9bf`: 312 64-bit generator state words.
- `+0x9c0`: next word index.
- `+0x9c8`: cached eight-byte output word for a partial tail.
- `+0x9d0`: consumed-byte offset within that cached word; zero means no pending partial word in this path.

With fresh state (cached word/offset both zero), each full eight-byte block is loaded before its corresponding store: call `43bfe0` at `4df9b7`, XOR at `4df9bc`, store at `4df9bf`. Tail length `count & 7` obtains one additional word at `4df9dc`, caches it, stores consumed count, and XORs only the first 1..7 little-endian bytes (`4df9f1..4dfa8e`). No length or content expansion occurs. The initial `4df8a9..4df98c` branch consumes remaining bytes of a previously cached word before generating more. Texture calls do not reuse a partially consumed state: each allocates and initializes fresh state. Exact in-place buffers are supported by the load-before-store order; arbitrary partially overlapping source/destination buffers are not asserted safe.

## Word generator, without an inferred product name

`43bfe0..43c2b5` has no calls or external entropy reads. It accesses its state and fixed literal vectors. If index is at least312, it refreshes the 312-word state, then resets the index. The refresh combines neighboring words' high/low portions, shifts right one, XORs a word displaced by156, and conditionally XORs `0xb5026f5aa96619e9` based on the neighbor's low bit. The first156 updates use old displaced words; subsequent updates use already-updated wrapped words. The final update wraps to the updated first word. SIMD masks are preserved in the receipt: high `0xffffffff80000000`, low `0x7ffffffe` (bit0 is separately used for the conditional constant; it would be discarded by the shift).

The selected word at the old index is followed by index increment (`43c25f..43c26a`). Its output mixing is:
1. `x ^= (x >> 29) & 0x555555555`
2. `x ^= (x << 17) & 0x71d67fffeda60000`
3. `x ^= ((x & 0x07ffbf77) << 37)`
4. `x ^= x >> 43`

All operations are 64-bit, with truncation as in the instructions. This is an exact operation description; no algorithm-name or security-strength claim is required.

## Seed identity and deterministic reinitialization

Receive producer `3756af..3756b6` installs vtable `d1c4f8` at `node+0x40`. Original ELF R_X86_64_RELATIVE relocations identify:
- `d1c510` (vtable+0x18) addend `3608d0`: `lea rax,[rdi+8]; ret`.
- `d1c518` (vtable+0x20) addend `3a52b0`: `mov eax,16; ret`.

Thus, for this created representation, the two virtual calls return the address of the 16 inline bytes at node+0x48 and the value16. Loader application is a static relocation contract, not a verified live binding. Other hypothetical representations are outside this closure.

Upload calls those slots at `3bf24c/3bf259`; reapply calls them at `3a5903/3a5910` relative to wrapper=node+0x10, making wrapper+0x30 identical to node+0x40. Both call `573dd0(pointer,16,0xd017cbba7b5d3581)` (`3bf26c`, `3a5923`). The pinned complete mixer range contains integer arithmetic and reads from input plus stack, with no external calls or entropy accesses; the length16 branch reads the two input 64-bit words. Therefore equal input bytes yield equal return values. Its formal algorithm identity is not needed here.

Both callers seed word0 with that result and initialize words1..311 using:
`state[i] = 0x5851f42d4c957f2d * (state[i-1] XOR (state[i-1] >> 62)) + i`, modulo2^64.
Both set index312 and zero cached word/byte offset (`3bf2d8..3bf2ed`, `3a5988..3a5996`). The first generated output is therefore identical for equal seed material, and the deterministic state evolution yields the same entire byte stream for equal lengths.

The receive producer also applies this exact initialization and in-place helper at `375a51`, after populating the seed wrapper. This establishes a third application site in the received-texture lifecycle; it does not establish the original asset format or how upstream bytes were obtained.

## Source ownership and normal-path order

Upload uses pointer `node+0x18`, count `node+0x28` at `3bf2ee..3bf2ff`, then frees only its temporary0x9d8 generator at `3bf30c`. The selected source wrapper is node+0x10.
- If DWORD node+0x38 is1: call GL upload helper3a52c0 at3bf33d using that wrapper's data and stored dimensions.
- Otherwise: call opaque conversion4c8000, use its temporary output in3a52c0 at3bf37d, and free the temporary output pointer when nonnull.
- Both normally returning branches converge at3bf391 and call3a58e0 at3bf394 before the registry unlock path.

Reapply reads wrapper+8 (node+0x18) and wrapper+0x18 (node+0x28), passes the same pointer as source/destination and the same count as capacity (`3a599d..3a59ae`), then frees only the fresh0x9d8 generator. It does not free the source allocation, change the registry handle, or perform GL deletion. Native source release remains the distinct3bf540 lifecycle established in the earlier receipt.

A normal return from3a52c0 can include its zero-bound-texture early return; reapplication follows regardless of whether GL upload work was attempted. There is no GL-success test gating reapplication.

## Conditions and unresolved boundaries

Bit-for-bit restoration requires the same inline16 seed bytes, same source allocation/length, and no intervening modifications to the transformed source bytes. The inspected upload/reapply bodies do not write those seed bytes or pointer/length fields. The registry lock spans the selected path when the existing thread marker enables it, but this does not prove all possible aliases or writers are excluded. Opaque conversion4c8000 and external GL callees were not expanded to prove they never mutate the source. If an intervening operation changes a byte by XOR delta, reapplication preserves that delta relative to the initial byte; the synthetic check demonstrates this limitation.

Exception/unwind paths may include selected reapplication calls, but this cohort makes no universal finally/rollback guarantee. A failure before or during reapplication, invalid pointer/length, changed seed, or mutated source can defeat full restoration. The byte transform itself is length-preserving XOR; any format conversion belongs to separate callees and cannot be attributed to4df880.

## Subsequent parameter comparison

A [separate primary-source comparison](NATIVE-MT19937-64-COMPARISON-2026-10-18.md) establishes exact mt19937_64 engine parameter/seed-recurrence equivalence, including optimized masks. It does not identify target compiler/build provenance or confer cryptographic security. Texture-specific seed mixing and byte-tail caching remain separate surrounding operations.
