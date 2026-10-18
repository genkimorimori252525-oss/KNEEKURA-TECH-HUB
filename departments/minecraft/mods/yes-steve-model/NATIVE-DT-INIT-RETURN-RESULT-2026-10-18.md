# DT_INIT returns under the declared isolated scenario

A fresh full-prefix run completes3,290,734 native instruction/model invocations from DT_INIT0x152eb19 through final RET0x1d963d. The return reaches the declared sentinel0x7fff00000000 with RSP0x700000008010, exactly one popped entry return address. All12 static oracle checks pass. This is DT_INIT completion under the stated synthetic inputs, not whole-module initialization or proof of real game execution.

## Final private initialization and return guard

Lazy JMPREL index197 resolves JUMP_SLOT0x184d640, symbol218 memset. Its observed2080-byte array destination0x710000000200 is entirely inside the preceding private new[] allocation. The narrow model validates the caller/frame/slot identity, bounded size and private destination, fills bytes using the low byte of the value argument and returns the destination. Invalid/image destinations stop; zero length does not initialize unknown bytes. No actual libc call occurs.

The final return exposed a harness boundary issue: Unicorn may report a fetch of the unmapped return sentinel before the single-step wrapper observes RET completion. The guard now recognizes only an executed RET opcode with RIP equal to the sentinel and exact RSP=initialSP+8. It then retires that instruction as ENTRY_RETURN instead of rolling it back. Jumps to the sentinel or wrong stack positions still fail. This does not permit execution at the sentinel.

## Preserved evidence

- Two working-image pointer stores,16 bytes total:0xedf060 and0xedf068. Immutable reference bytes and original ELF file unchanged; working view matches the complete mutation ledger.
- One424-byte virtual malloc; three virtual C++ allocations24/48/2080 bytes; one private memset. Heap writes25 events.
- Two declared CPUID leaf1 inputs;23 modeled clock reads; five simulated working-image protection changes.
- Fifteen CRC summaries,23,591,981 iterations and528,156,776 logical loop-instruction effects. These are not actual interpreted instruction counts or a completion percentage.
- 111 scoped test methods pass, including new memset, true-return/wrong-return and checkpoint-counter tests;60 CRC full-state differential cases remain covered.

## Checkpoint accounting correction

Early checkpoint versions preserved architectural/private/image state but omitted CRC diagnostic counters. Their continuation traces could show zero CRC counters despite earlier summaries. New snapshots preserve those counters explicitly; older snapshots mark prior CRC diagnostic history incomplete rather than inventing totals. The fresh full run in this receipt has complete CRC history. This bookkeeping correction does not change the verified CPU/private-memory equivalence of the earlier checkpoint comparison.

The new completed-DT_INIT checkpoint can seed subsequent initializer work. Do not merely resume its sentinel RIP; prepare the next declared callback call frame. Keep all snapshots/full traces outside Git. The paired JSON records exact hashes and canonical completion receipts.

## Remaining work

45 ELF init-array callbacks are separate from DT_INIT and remain unexecuted. Their RELATIVE-resolved targets should be invoked in order using the preserved working state and explicit caller inputs, stopping at unsupported behavior. JNI_OnLoad/native method binding and rendering/Molang semantics remain separate unresolved goals. Central mapping669 unchanged; independent semantic review NOT_RUN.
