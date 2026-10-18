# Resource parser escape → worker per-model skip

2026-10-18. BOUNDED_WORKER_LSDA_AND_CONTROL_FLOW. [Independent review: conditional static acceptance](NATIVE-RESOURCE-FAILURE-WORKER-REVIEW-2026-10-18.md). This extends the accepted native-parser-exceptions helper result only through the resource user-function route and worker35d250. It is not a universal model loader or controller error contract.

## Result

An exception escaping the resource user-function parser call370a03 follows cleanup-only unwind edges through helper3742d0 and materializer36d8c0 into a per-model catch in worker35d250. If ordinary unwinding, destruction and catch processing complete normally, the worker destroys the temporary native model, sets local status4 and advances to the next model when one remains. The failed model does not reach this worker's post-materialization record append. Previously appended records are not cleared by this catch path.

Thus helper failure does not imply atomic rejection of the entire worker batch. It also does not guarantee later worker completion, successful Java publication, preservation of every external side effect, or renderer-visible retention. A later error, cancellation, cleanup failure or outer completion failure can still intervene.

## Exact exception coverage rather than adjacent-code inference

Original ELF GNU_EH_FRAME header at VA185656c (file16bd56c) is011b033b, with8680 encoded table entries. FDE187d128 covers worker35d250..35e20e; CIE1867a70 has zPLR augmentation; worker LSDA is1450ac.

Three independently decoded edges:

- helper3742d0: checker call374392 is in [37438f,374397), landing374498, action0. This is the already-inspected local cleanup then322a00 at3744ae, conditioned normal cleanup.
- materializer36d8c0: resource helper call370a03 is in [3709f3,370a08), landing372eea, action0. Landing saves the exception in RBX, jumps3733f1, performs wrapper/collection cleanup and converges373504. Cleanup calls at37350c,373519,373526,373533,373540 precede RBX→RDI373545 and resume call322a00 at373548. This is an outward cleanup-only route, not a local recovery return. Destructors/callback cleanup are not assumed infallible.
- worker35d250: materializer call is35d54b (35d548 merely loads RDX). LSDA covers [35d53d,35d550), landing35de5e, action3. The action chain at1451cc has bytes0100027d: filter2 chains to filter1; type1's encoded type entry is zero, a catch-all. The conclusion does not require identifying filter2's type, since both selector branches take the same local status continuation.

## Worker catch and status

Landing35de5e saves selector/exception and jumps35def1. It restores local registers, reaches35df03, loads the current native model from stack+a0, conditionally destroys it via345030 at35df13 and frees its0x5d0 allocation at35df20. It then enters catch handling at35df28. Selector2 branch calls311020 at35df3b, sets EBX=4 at35df40, ends catch35df45 and jumps35dcd2. The other branch calls311020 at35df57, sets EBX=4 at35df5c, ends catch35df61 and makes the same jump. The meaning/content of311020 is not newly assigned.

Shared cleanup35dcd2..35dd18 disposes current-item resources. At35dd1d, `test $3,%bl` evaluates zero for4; the stop branch35dd28 is not taken. The worker increments the item index35dd2e, compares against its saved bound35dd31, and loops35dd39→35d310 if more items remain, otherwise proceeds to its ordinary completion region35e075. This establishes a possible continuation after this caught error, not a guarantee of future success. Status1 (the earlier cancellation path) has different low bits and must not be conflated with4.

## Normal record retention and what it does not prove

The current item's post-materialization path begins only after the return from35d54b. It reads the resulting Java local reference and, when nonnull, requests a global reference at35d569. That reference is moved into the new0x88-byte record at35d741 (capacity available) or35d84d (growth path). The vector's logical end advances at35d943, or the growth branch installs the replacement vector and end at35dbf6/35dbf9. These are native staging records, not a proven final Java model-map commit.

The selected materializer-failure landing route does not run that current-item append or any vector clear. Earlier appended records remain in the staging vector across this catch continuation under the ordinary fixed-state/no-external-mutation premise. No whole-batch transaction, later callback completion or renderer publication is established. Java/native constructors already called before the failure can have effects outside the temporary model cleanup; they are not proven rolled back.

Outer worker exception completion35e143..35e18f is a different path. Its360570 handoff must not be cited as the direct destination of this materializer failure. Its full future/promise semantics are not needed here and are not claimed.

## Controller route boundary

Do not apply this resource proof indiscriminately to controller construction. The selected controller-data parser calls have cleanup-only pads, but intermediate365a10 has an actual catch around365b39 (landing365ee9/action3). Its transformation/rethrow semantics and complete downstream cleanup require a separately scoped chain; they remain outside this resource-only conclusion. No new controller equivalence or fallback contract is declared.

## Evidence

verify.py parses original ELF program headers, GNU unwind search table, selected CIE/FDE augmentation and LSDA callsite/action records. It checks original SO SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22,14 hashed code/metadata windows,11 named byte assertions plus one resource-resume assertion, and exact unwind edges. receipt.json is compact; lsda-callsites.json contains worker callsite metadata only. Original code/disassembly remains outside Git. This authored metadata parser executes no original YSM body. No assets, target Java/native execution, network, CI,403 retry or Git edits occurred.

The preceding [parser exception boundary](NATIVE-PARSER-EXCEPTION-BOUNDARY-2026-10-18.md) supplies the Java facade/caught-fallback versus pending-exception distinction. Existing NATIVE-SOURCE-ACQUISITION supplies the native model lifetime context. Whole-project/source-artifact confidence remains unchanged.

Published integrity receipt: [worker evidence](NATIVE-RESOURCE-FAILURE-WORKER-EVIDENCE-2026-10-18.json).
