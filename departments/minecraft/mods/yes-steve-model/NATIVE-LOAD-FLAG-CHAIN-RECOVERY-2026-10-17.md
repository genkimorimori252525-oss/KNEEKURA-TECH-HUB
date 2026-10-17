# Load-side flag chain: three further conditional edges

PRIMARY_STATIC_REVIEW_ONLY. Fixed Linux image SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. This adds three local flag proofs after the earlier parity predicate. Four load-side conditional edges are now justified under normal, unmodified execution assumptions; no complete native function or Java binding is recovered.

## 1. Inherited sign survives a rotate

The preceding proven DEC result 0xffac has SF=1. At 0x13b4244, the next sequence writes a register to stack, pushes a constant and performs a word ROR before JS at 0x13b4254. MOV/PUSH preserve the relevant flag, and ROR does not modify SF. Therefore JS takes 0x1311bc0. Undefined rotate OF is deliberately not used. The source rule is Intel's [rotate/MOV/PUSH instruction reference](https://cdrdv2-public.intel.com/782151/253667-sdm-vol-2b.pdf).

## 2. Bit-test carry survives a direct call

At 0x1311bc0, the fixed prefix establishes ESI=0x312f3a80 and then complements RSI. Its low 16 bits become 0xc57f. BTR SI,0x2f selects bit 15 (register-width modulo), whose old value is 1, so CF=1. A later MOV and the near CALL to 0xf28339 preserve CF. That callee's FIRST instruction is JB, so its taken edge is 0x129b910. No assumption about a later call return is needed. [Intel's BTR/CALL/Jcc specification](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf) supports the flag and bit-index rules.

## 3. A new constant carry controls JAE

The bounded direct-prefix route is 0x129b910 → 0x11f977a → 0x10bf89a. Before that last prefix's JAE, R10D is explicitly set to 0xd6bd2601. BTC R10D,0x22 selects bit 2, whose old value is 0. CF becomes 0; an intervening LEA preserves flags, so JAE at 0x10bf971 takes 0x12de5ac. This proof needs only that local constant/bit operation, not guessed values for the earlier stack/register arithmetic. The same [Intel Volume 2A](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf) documents BTC and Jcc. BTR/BTC leave several OTHER flags undefined; none of those flags are carried into a subsequent proof.

## New return frontier

From 0x12de5ac, first-transfer traversal reaches 0xfb88f7 → 0x11a3a95 → 0xfa14d0. The last prefix terminates with RET at 0xfa14e5. Before RET it pops R10 and writes through a register-indexed stack address. This is not evidence that RET returns to the most recent CALL's ordinary fallthrough: the current stack/register values and writes require separate analysis. The return target remains unresolved. The recorded seven additional prefixes are not function boundaries or a complete CFG.

The JSON binds each local sequence by exact bytes/hash, recalculates relative targets, checks file backing and records the connecting prefixes. Raw windows/disassembly remain outside Git. No native target execution, emulation, unpacking, binary patching, protected model decoding or security bypass was performed. Arithmetic and flag reasoning are explicit and limited to the fixed patterns.

## Verification and boundaries

Ten synthetic tests cover actual outcomes, modulo-index rules, opposite carry/sign cases and changed-sequence rejection. A five-part native static checkpoint recomputes the previous four scopes plus this chain. All predicates depend on ordinary successful execution of unchanged bytes, valid memory accesses and no external interference; actual library load/rewrite/runtime reachability remains unverified. Independent semantic review NOT_RUN, native bindings/whole implementations unresolved and central mapping unchanged.
