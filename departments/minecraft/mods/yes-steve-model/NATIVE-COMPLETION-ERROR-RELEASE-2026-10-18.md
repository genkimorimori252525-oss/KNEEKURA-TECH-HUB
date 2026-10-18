# Stored completion errors: originating wait and release paths

## Finding

The inspected native worker and collector completion errors are stored in a shared result, but their originating continuations do not retrieve, log, or rethrow that stored payload. They wait for readiness and release ownership. If the inspected release is the last relevant owner, the original virtual destructor chain releases the stored exception reference and frees the result/state allocations. If other owners remain, destruction is deferred; no all-alias consumption or immediate destruction claim follows.

This resolves the narrow previously open distinction between readiness waiting and error-value consumption. It does not mean an operation succeeded, a callback ran, or the error was never logged elsewhere. Existing per-model native catches and Java builder logging remain separate paths.

## Error storage

The worker outer error-completion route captures its current exception through 0x2abc20 at 0x35e162 and calls 0x360570 at 0x35e16d. The collector's task-body/completion handler similarly calls 0x360570 at 0x41ccb5, following capture 0x41ccaa. These are the outer stored-completion routes, not the previously established materializer per-item skip handler.

0x360570 builds a closure targeting 0x360610 and calls the common once/completion helper 0x360450 at 0x3605a4. Within that closure:

* 0x360626 obtains the pending result object from owner+0x10.
* 0x36062a loads the captured exception pointer; if non-null, 0x36063c calls 0x2abbb0, whose original body increments the pointer's refcount at pointer−0x80.
* 0x360653 replaces result+8 with the retained pointer; 0x360661 releases any previous value through 0x2abbd0.
* 0x360669–0x360675 moves the result object out of owner+0x10 and clears that source slot.

The previously reviewed common helper installs that returned result in shared state+8 at 0x3606b3 and, on normal successful completion, exchanges shared state+0x10 with ready=1 at 0x360522. Failures in capture, allocation, once setup, or cleanup need not establish this state. This report uses the concrete field/call behavior rather than assigning generic future/get API names from shape.

## Exact state identity in both callers

Worker state creation is not inferred from a similar layout. Original constructor 0x35cfb0, called at 0x359dd0, installs control vtable d1c080 at 0x35cff5/0x35cffc, embedded state vtable d1c0b8 at 0x35d007/0x35d00e, and result vtable d1c0e8 at 0x35d05e/0x35d065. It returns the owner whose two-word state/control pair is copied at 0x359ddd–0x359dec to builder frame+0xf0/+0xf8. The builder moves that pair into its completion vector in the ordinary append at 0x35a24c–0x35a276 or growth path beginning 0x35a2f0.

Collector emitter construction independently installs the same three vtables at 0x35abfe/0x35ac05, 0x35ac0f/0x35ac16 and 0x35ac5c/0x35ac63. Thus the selected worker and collector release paths dispatch to the exact same result/state destructors.

## Worker originating continuation

Builder 0x35a432 loads the completion vector and iterates its 16-byte pairs. It reads each state pointer at 0x35a449, invokes state vtable+0x10 at 0x35a45b, and checks state+0x10 at 0x35a45e. Original relocation d1c0c8→0x2aade0 resolves that virtual call to a single RET. It cannot hide a stored-error fetch for this state.

The wait sets ECX=0 at 0x35a483 and uses the already reviewed untimed helper path, then repeats until masked state equals 1. After iterating the vector it calls 0x35e4f0 at 0x35a4a9. There is no read of shared state+8's stored result/error between the ready test and this release. The release routine walks each pair's control pointer, decrements reference counts, and dispatches disposal only for the appropriate last-owner conditions; it then frees vector storage. It contains no payload-based success/error branch, logging, or stored-exception rethrow.

Accordingly normal completion of this wait/release path can continue builder processing even when a worker's stored result contains an exception. This does not establish that every worker or later builder operation completes, or that earlier staging is rolled back.

## Collector originating continuation

The previously established 0x41ce80 wait uses the same state virtual no-op and ready flag. Its ordinary post-wait path 0x41cf94–0x41d020 releases the retained control reference by direct last-owner disposal or 0x329bd0. It does not fetch shared state+8's error value, inspect that exception, log it, or rethrow it as the completion payload.

A collector task-body exception can therefore be stored by its handler and allow the originating scheduler's normal wait/release return, provided error completion and cleanup finish normally. This is weaker than successful callback execution. Guard-set synchronous skip and guard-race destruction remain distinct readiness outcomes. No renderer or Java tick ordering is inferred.

## Last-owner destructor closure

Original RELATIVE relocation and code close the otherwise indirect release chain:

1. Control vtable d1c080+0x10 = d1c090→0x345ef0. It adjusts to embedded state at control+0x10 and calls its slot0. Control deallocation slot d1c098→0x345ee0 frees the allocation after disposal.
2. State slot d1c0b8→0x345e70 reads state+8 and calls the result's slot0 at 0x345e8a, then clears the state result pointer.
3. Result slot d1c0e8→0x2bf7c0 forwards to result vtable+0x10; d1c0f8→0x345e50 calls 0x2e4450 and frees the result allocation.
4. 0x2e4450 tests result+8 and, when non-null, tails to 0x2abbd0 at 0x2e4469. This is ownership release: 0x2abbd8 decrements pointer−0x80. Only on zero does it call the exception object's indirect destructor from pointer−0x68 at 0x2abbef, then 0x2aaa20 and clear the pointer.

This chain does inspect nullness/refcounts for destruction, so “never reads the pointer” would be inaccurate. It does not inspect the stored payload to choose application recovery, report the error, or rethrow the completion exception. The final exception destructor is indirect: its own side effects or failure are not certified, and destruction exceptions are not being equated with rethrowing the stored completion payload.

## Scope and evidence

Original SO SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. `verify.py` checks 18 original-byte windows, 15 instruction assertions and six exact virtual-slot relocations; `receipt.json` records them. Earlier worker/controller exception, native publication and collector-lifetime findings are reused rather than re-audited. Only original static code/ELF metadata was inspected, with no target or guest execution, assets, downloads, network, CI, or Git changes.

Remaining limits: other aliases or consumers of these states; abnormal failures before readiness; eventual queue/worker completion; final destructor behavior; whole-batch success or rollback. The conclusion is specific to these originating continuations and their resolved release chain. Runtime remains blocked and source/artifact divergence classifications are unchanged.

Published [independent conditional review](NATIVE-COMPLETION-ERROR-REVIEW-2026-10-18.md), [review receipt](NATIVE-COMPLETION-ERROR-REVIEW-2026-10-18.json) and [byte-backed evidence](NATIVE-COMPLETION-ERROR-EVIDENCE-2026-10-18.json).
