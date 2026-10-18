# Bone hierarchy, flattened order and parent-bank sizing

## Result

The source pointer vector consumed by `375e30` is constructed by a nonrecursive, LIFO depth-first traversal inside `36a6e0`. Parent wrappers precede their descendants, and each subtree occupies a contiguous interval, conditional on the ordinary finite rooted-forest structure and representable counts described below. The wrapper depth and descendant fields have actual producer evidence. Geometry payload `+0x50` carries maximum encountered depth plus one; the renderer grows its 112-byte parent-state bank to at least that many elements. The depth stored in each native descriptor is only eight bits, while the producer computes 32-bit depth. No depth-at-most-255 check is established by this scoped producer. This is an unresolved input/representation precondition, not a finding of an executable target defect.

Original SO SHA256: `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`.
No target, JVM or emulator execution. No repository modifications. `reproduce.py` verifies original bytes and produces twelve bounded objdump excerpts plus two original-ELF import chains. [Evidence receipt](NATIVE-BONE-HIERARCHY-EVIDENCE-2026-10-18.json) pins each range and its backing. Prior geometry receipt remains unchanged.

## Exact pointer identities and layout

Let A be the aggregate at `36a6e0` stack+0x160. Its source argument is saved at A+0. Original bone records occupy an input vector `[source+8,source+0x10)` with stride0x80 (`36a79f..36a7ab`, `36a82a..36a874`).

For each distinct source name, the routine allocates a0x70-byte hash node N at `36a87c..36a886`. The hash key is source bone pointer+0x40 and length+0x48, stored as N+0x10(pointer),N+8(length). The wrapper W is N+0x18, not N itself:

- W+0: pointer to original0x80-byte bone record, stored36a89c.
- W+8: parent wrapper, initially zero and later stored36aaa1.
- W+0x10: ordered children container header; sentinel W+0x18, root W+0x20, first W+0x28, last W+0x30, count W+0x38.
- W+0x40: flattened index, assigned36af92.
- W+0x44: 32-bit depth, initially zero via36a8c0 and assigned36ae30 for children.
- W+0x48: 32-bit descendant accumulator, zeroed36a8c7.

A+0x40/+0x48/+0x50 is the flattened pointer-vector begin/end/capacity. A+0x58 is the root ordered-container header. A+0x88 is a32-bit maximum-depth accumulator initialized to zero at36a794.

## Name resolution, roots and child order

`369c80` resolves length/pointer keys using exact-length byte equality. The original-ELF chain for its external equality call at d14780 resolves to bcmp. At36a8db the lookup checks an existing name before insertion; if found,36a8e9 branches to destruction of the newly allocated node, retaining the earlier entry. Therefore the flattened vector is not guaranteed to have one element per original input record when names repeat.

The second pass36a9fc..36aaad walks retained hash nodes. It reads the underlying bone's parent-name length+0x10 and pointer+8. Zero length inserts W into A's root container (`36aa20..36aa2e`). Nonzero length looks up the parent in the completed name map (`36aa50..36aa82`), inserts W into that parent's children container (`36aa8e..36aa98`), and stores the parent W at child W+8. Missing lookup/node enters36cba0, constructs an error with discriminator0x47 at36cbe9, and calls the exception path36cc14. The error's user-visible text is not decoded here.

`369810` is the ordered insertion helper. Keys are `(length,bytes)`; comparisons call d14770 on the minimum byte length, then compare lengths when the bytes match. Original-ELF import metadata resolves d14770 to memcmp. The helper stores a0x38-byte tree node with key length+0x20, key pointer+0x28, wrapper pointer+0x30 (`369941..369957`). Its count increment is369c19. `2ba620` is tree successor: descend right then leftmost, or ascend parent links.

Root enumeration starts from the root container's first node, pushes each node+0x30 wrapper to a temporary pointer vector, and advances with2ba620 (`36abd0..36ad4e`). Child enumeration does the same (`36ade5..36af68`). Both are ascending byte-lexicographic tree order; the temporary work vector is consumed from its end. Thus the resulting preorder visits roots and siblings in reverse byte-lexicographic name order, not original source-vector order. This order statement derives from the comparator/tree/LIFO instructions; no locale, Unicode collation or runtime test is assumed.

## Flattened preorder, depth and descendant count

The work vector initially contains all roots. At36ad88 the traversal pops its last pointer. For a popped wrapper W:

1. Read W+0x38, its immediate-child count. If nonzero, store its low32 bits into W+0x48 at36ada3.
2. Follow W+8 through ancestors and add that immediate-child count to every ancestor's32-bit W+0x48 (`36ada6..36adca`).
3. Compute childDepth=W.depth+1 as32-bit arithmetic (`36adcc..36add0`). Update A+0x88 with an unsigned maximum (`36add3..36ade4`). This update runs only for nodes with children, but each existing nonroot node has a parent, so it captures the largest generated depth; roots-only/empty leave zero.
4. Enumerate immediate children in tree order, assign each child.depth=childDepth at36ae30, and push them on the same LIFO work vector.
5. Set W.index to current flattened-vector element count (`36af80..36af92`), append W (`36ad70..36ad77`, or the growth path), and continue popping.

Children are pushed before the parent append, but are processed only on the following pop. Therefore the parent is appended first. Every child's pending siblings remain below newly pushed descendants, giving a depth-first preorder and contiguous subtree interval. Summing each encountered node's immediate-child count into all its ancestors counts each proper descendant exactly once in an ordinary rooted tree. The renderer's `start+descendantCount+1` interval and skip-by-descendants therefore have a concrete producer basis.

These deductions assume resolved unique retained names, a finite rooted forest, and representable arithmetic. This slice does not reject cycles explicitly, compare visited count with retained-node count, or establish that every retained component is reachable from a root. It also does not establish upstream input validation. Do not turn the preorder proof for reached rooted components into a whole-input validation guarantee.

## Width boundary and bank capacity

At3761c6 the descriptor producer uses `movzbl W+0x44`, then stores AL into native120-byte record+0x70. This is an explicit low-byte conversion from the32-bit producer field. At3761cf..3761d3 it copies W+0x48 as32 bits to record+0x6c. No comparison against255, clamp or rejection appears along the scoped depth assignment/flattening path. Counts and maximum depth also use32-bit arithmetic. No global numerical bound follows from this local absence.

At378b73,375e30 reads A+0x88. It increments this32-bit value at378c56 and stores it at control-block+0x60 (`378c8a`). The geometry payload begins at control-block+0x10, so this is payload+0x50=maxDepth+1.

The renderer reads its bank begin/end at d34b80/d34b88, computes their element count using112-byte stride, and compares it with payload+0x50 (`37bf83..37bfae`). A short bank takes37f6ab to3984d0. That helper resizes the d34b80/d34b88/d34b90 vector; allocation multiplies capacity by0x70 at39854c, preserves old112-byte elements, clears newly added bytes, and publishes new begin/end/capacity at3985d6..3985eb. Existing sufficient length is retained by this callsite. Hence the established storage provision is at least112*(maxDepth+1) logical bytes, subject to normal allocation/arithmetic preconditions, not a fixed112-byte total bank.

The ordinary parent-publication path checks nonzero descriptor descendant count at37cc05 before entering37cc1e. It reads bank[depth] and later writes bank[depth+1] at37d1e2 onward. A leaf bypasses this publication path. For reached finite trees with depths<=255 and representable counts, internal-node depth+1<=maxDepth, so the provisioned slots0..maxDepth cover these parent/child accesses. Other transform routes are covered by the separate renderer receipt, not newly certified wholesale here. If depth exceeds255, byte conversion prevents deriving semantic parent-index consistency from the32-bit maximum alone; no targetbug or runtime occurrence is claimed.

## Verification and limits

`reproduce.py`: PASS,12 original-byte ranges and2 complete original-ELF import chains. The script is analysis code and runs only original-file parsing and objdump, never the target. The prior geometry evidence SHA256 remains `d911035f40312c4fcd495f0446d73686b73f60963d0f22f9821478efc6432504`.

Unresolved: global depth limit and cycle/completeness validation, malformed/overflow cases, runtime allocation outcomes, and complete branch-specific renderer safety. The texture and geometry registries retain their distinct identities from the previous cohort.
