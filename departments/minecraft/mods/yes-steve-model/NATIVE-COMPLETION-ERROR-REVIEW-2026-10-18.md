# Independent stored-completion-error review

Verdict: bounded ownership release without a stored-payload rethrow on the inspected ordinary builder and collector continuations.

## Storage is separate from consumption

0x360570 constructs closure target 0x360610 and calls common completion 0x360450. Target 0x360610 retains the incoming pointer via 0x2abbb0 at 0x36063c, stores it at result+8 at 0x360653, releases the replaced pointer if non-null, and moves the result-holder out at 0x36066d–0x360675. The previously reviewed completion path installs this holder and publishes state readiness. The local implementation of 0x2abbb0 increments the pointer's -0x80 reference count; its inverse 0x2abbd0 decrements that count. These identities are supported by original instructions rather than presumed C++ symbol names.

## Actual ordinary continuations

Builder 0x35a432–0x35a4ae iterates 0x10-byte state/owner records, calls the state virtual +0x10 hook, polls masked state+0x10, and then calls 0x35e4f0. Its wait call 0x35a48b also fixes ECX=0, so the prior ordinary-return wait argument applies. The hook is the known no-op state entry. There is no result+8 exception read/rethrow in this wait-to-release sequence.

0x35e4f0 releases each record's control owner using its +8 reference counts. It invokes control virtual +0x10/+0x18 only when appropriate for release, or calls 0x329bd0, which performs the same dispose/deallocate virtual roles with the weak-count adjustment. Collector scheduler 0x41cf94–0x41d021 similarly releases control ownership after readiness; it does not fetch an error result for rethrow.

Original construction at 0x35cfb0 establishes the worker's same control, state and result vtables used by the collector. The exact relocated release chain is:

- Control slot 0xd1c090 → 0x345ef0: adjust to embedded state+0x10 and dispatch state slot 0.
- State slot 0xd1c0b8 → 0x345e70: dispatch non-null result+8 through result slot 0 and clear the stored result.
- Result slot 0xd1c0e8 → 0x2bf7c0: dispatch result virtual +0x10.
- Result slot 0xd1c0f8 → 0x345e50: call 0x2e4450, then release the result allocation.
- 0x2e4450 passes non-null result+8 to 0x2abbd0. On last reference, that helper invokes the stored object destructor pointer at object-0x68, calls allocation-release helper 0x2aaa20, and clears the local pointer. This is reference destruction, not an operation that rethrows the stored payload.
- Control slot 0xd1c098 → 0x345ee0 releases the control allocation; state hook 0xd1c0c8 → 0x2aade0 is RET.

## Limits

The conclusion concerns these original vtables and ordinary continuations only. A remaining owner may defer final destruction. The stored object's destructor is indirect and has not been proved infallible; cleanup failures or termination are not excluded. Other result consumers, earlier body logging, parser/controller catches, per-item skipping, and unrelated later throws are separate. No global claim that all errors are swallowed or that a Java caller always receives success is supported.

`review_completion_errors.py` checks 10 original PT_LOAD windows, 17 instruction assertions and six exact RELATIVE virtual-slot relocations. `completion-errors-receipt.json` records hashes and scope. Static parsing/disassembly only; no original target execution, downloads, network, assets, CI or Git edits.
