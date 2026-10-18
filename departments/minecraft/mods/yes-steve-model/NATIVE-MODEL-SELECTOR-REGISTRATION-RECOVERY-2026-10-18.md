# Ordered geometry selector registration

## Result
Original ELF metadata registers initializer `0x326ad0` as INIT_ARRAY element 9: DT_INIT_ARRAY=`0xd163d8`, size 360, relocation at `0xd16420` is R_X86_64_RELATIVE (8), addend `0x326ad0`. Normal fresh construction inserts exactly two native selectors, in numeric order: **1 → `main`**, **2 → `arm`**. This resolves the labels of the optional integer-map selection in `0x36d8c0`; it does not assign broader anatomical, Java enum, or rendering-mode semantics.

No original instructions were executed. This is a normal-construction static result, not a claim that a particular process reached initialization or retains this tree unchanged.

## Producer and ownership
`0x326ad4..0x326af2` tests guard `0xd35bd0` and calls `0x2abed0` before construction. `0x326af4..0x326b25` sets sentinel `0xd35ba8`, null root `0xd35bb0`, first/last pointers `0xd35bb8/0xd35bc0` to sentinel, and count `0xd35bc8` to zero.

First allocation is 0x40 bytes (`0x326b41..0x326b46`). Writes at `0x326b4b`, `0x326b52`, `0x326b5a..0x326b61`, `0x326b65` establish node key +0x20=1, label length +0x28=4, pointer +0x30=`0x42d46` (original `main\0`), flag +0x38=1. Insertion `0x326b7b` calls `0x2ba6d0`, then increments count.

The fresh-tree first node has key 1, so `0x326b90..0x326b94` takes insertion at `0x326be6`. Second 0x40 allocation writes key +0x20=2, length +0x28=3, pointer +0x30=`0x44c57` (original `arm\0`), flag +0x38=1 (`0x326c02..0x326c1c`); insertion `0x326c31` and count increment `0x326c36`. Normal resulting count is 2. Tree insertion helper source windows demonstrate parent/left/right/header links; unsigned key comparisons establish ascending traversal order. Duplicate-aware search branches exist in the generated construction code but do not introduce another fresh-construction key.

Node labels borrow immutable original literal spans; they are not dynamically copied Java strings. `0x326c3d..0x326c52` registers cleanup `0x326ec0`, object address `0xd35ba0`, DSO address `0xd2eb40`. Original import chain `0xd14710 → [0xd30810]=0x13d6e84 → [0x184d048]` resolves ELF symbol `__cxa_atexit`. Cleanup loads object+0x10 (tree root) and traverses child pointers +0x18/+0x10, freeing each 0x40 node (`0x326ec0..0x326f09`); labels are not freed. Guard completion jumps to `0x2abfe0`; exception cleanup is visible at `0x326c67..0x326c85`, with no completion guarantee asserted.

## Consumer joins
Prior selection receipt proves `0x36dd89` count allocation, `0x36dda5` first-node load, successor `0x2ba620`, node+0x20 model-map lookup, key-1 special arguments, and all-other-found-key arguments. This producer now grounds that key-1 branch as native label `main`, the second selector as native label `arm`. A missing model map key still produces a null array entry. This does not change either modern 0x348-stride vector path.

A second direct use proves labels are functional keys: `0x445e86` passes node+0x28 to `0x456ea0` against a separate string-keyed map. The latter reads length and pointer, hashes them, and in its linear path compares length and byte span (`0x456f18..0x456f2f`). `0x445e60` separately tests node+0x38 against 1; its semantic name remains unresolved. Numeric lookup at `0x460c8f..0x460cd5` searches the same tree by node+0x20, and the found branch `0x460d4a/0x460d65` reads matching label length/pointer. These uses independently support the key/label relation, without requiring a Java member decode.

## Evidence and limits
`reproduce.py` checks the full pinned image SHA256, exports ten instruction-aligned original-byte windows and source-backed objdump text, verifies INIT_ARRAY relocation, literal spans, cleanup import, and links the prior selection receipt by hash. `evidence.json` contains exact ranges, per-range hashes and file backing.

RIP-relative displacement candidates were used only to locate code, then verified as instructions and dataflow. The scan does not exclude arbitrary indirect mutations elsewhere. No Java class/field/enum association is proven in this bounded cohort. The exact native labels are sufficient to close the requested selector-provenance gap; further UI/API semantic mapping would require a separately scoped metadata or consumer trace.

Evidence: [NATIVE-MODEL-SELECTOR-REGISTRATION-EVIDENCE-2026-10-18.json](NATIVE-MODEL-SELECTOR-REGISTRATION-EVIDENCE-2026-10-18.json). [Exact collection selection](NATIVE-MODEL-GEOMETRY-SELECTION-RECOVERY-2026-10-18.md). Raw excerpts/reproduction scripts remain external.
