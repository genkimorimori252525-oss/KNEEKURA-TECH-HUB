# Collector wait, guard skip, and captured-vector lifetime

## Result

Two previously unresolved details can be narrowed from original native code:

1. The ordinary collector scheduler 0x41ce80 does not have the apparent timed/false wait escape for its actual arguments. On ordinary return through its wait loop, it has observed shared state+0x10 masked to 1. This is a completion-state barrier, not proof of successful Java callback or eventual progress.
2. Guard-set fallback 0x41d070 synchronously completes shared result state without invoking the task body and without submitting that task to the queue. It leaves the caller's task pointer intact; the two inspected builder callers then destroy that task. It is a callback-skip path, not inline collector execution or deferred dispatch.

For the selected normal queued-consumer path, task-body return precedes completion publication. This supplies the missing local lifetime ordering for the builder-frame vectors: the builder remains inside scheduler dispatch/wait while the body uses the captures. Guard fallback does not use the captured vectors. No universal queue-drain, all-state-writers, eventual progress or exception-safe lifetime proof is added.

## Fixed-argument wait proof

At 0x41cf74 the scheduler sets ECX=0; R8 and R9 are also zero at 0x41cf76/0x41cf79. It calls 0x2e3ec0 at 0x41cf7c. That helper tests CL at 0x2e3ed2 and branches directly to 0x2e3ff0 for zero. This path calls imported syscall at 0x2e3ffe, then sets EAX=1 at 0x2e4007 and returns at 0x2e4014. The helper's other, timed paths returning false are unreachable from these fixed arguments. This conclusion is conditional on ordinary helper/syscall return; it does not claim syscall success.

Back in the caller, 0x41cf81 reloads the state, masks the high waiter bit at 0x41cf84, compares with 1 at 0x41cf8a, and repeats while not-ready AND AL at 0x41cf90/0x41cf92. Since AL is 1 on this path, ordinary loop exit requires ready=1. The earlier pre-loop comparison at 0x41cf49–0x41cf56 enforces the same condition. State ownership is released only afterwards.

This corrects the earlier dossier sentence that this caller's wait can also exit on the helper's false result. It does not change that completion may represent skip or error rather than callback success. An unwind edge from [0x41cf6e,0x41cf81) goes to cleanup 0x41d051/action0, separately from ordinary return.

## Guard-set fallback closure

The guard at 0x41ce89/0x41ce92 selects 0x41d021, which loads the task pointer and tail-jumps to 0x41d070 at 0x41d02d. This occurs before the ordinary path clears caller ownership at 0x41ceec or submits anything.

Fallback loads task+8 as its shared-state pointer (0x41d078). It builds a small closure containing &task+8, invocation target 0x360430 and manager 0x339780, then calls 0x360450 at 0x41d0ad. Target 0x360430 takes the pointer at task+0x18, clears that slot at 0x36043a, and returns the moved pointer. It does not call the task's vtable slot0 and does not access captures at task+0x20/+0x28.

0x360450 installs its invocation closure via TLS and invokes imported pthread_once at 0x3604ff. The trampoline chain 0x2f86b0→TLS target 0x3606e0 dispatches the fixed member-function target 0x360690. That target calls the supplied 0x360430 closure through +0x18 at 0x3606a4, marks the local success flag at 0x3606a7, and installs the returned result into shared state+8 at 0x3606b3. On normal successful once-completion, 0x360450 tests that flag and exchanges state+0x10 with 1 at 0x360522, waking waiters if required. An already-completed/failed setup need not take this normal-return path; error/cleanup helpers are not presumed infallible.

The closure-manager call with EDX=3 reaches 0x339789→0x33979a and returns; it is not the task invocation. Fallback LSDA covers its completion call [0x41d0aa,0x41d0b2) with cleanup landing 0x41d0e1/action0. No execution or enqueue of the task body is present on this inspected fallback path.

The two builder caller continuations test their retained task pointers and call vtable+0x10 after scheduler return: the earlier task after 0x35a747 and the emitter at 0x35ac9c–0x35aca9. Original RELATIVE relocations map d1b590 to 0x35eeb0 and d1b5b8 to 0x345d20, the deleting-destructor paths. This discharges the retained task on ordinary fallback return; no later callback is scheduled by the fallback itself.

## Ordinary queued consumption and relevant alternate paths

The ordinary scheduler moves task ownership into a pair with a zero first word, clears the caller pointer at 0x41ceec, and attempts queue submission at 0x41cf05. Submission's successful simple path copies both words and clears the source task slot at 0x41bdb1. If the local task remains, 0x41cf32–0x41cf3d destroys it instead of invoking its body; readiness therefore cannot be equated to successful submission.

The consumer's zero-first-word/task-present path at 0x41c88c–0x41c8a2 calls 0x41cbf0. That function calls task vtable slot0 at 0x41cbfd. The already established relocations identify that slot as 0x35f620 for the array-alter task and 0x35ef10 for the per-record model emitter. Only after that body returns does it construct the same result-move closure and call 0x360450 at 0x41cc37. Thus this selected normal completion cannot publish ready before the collector body returns.

Original LSDA also establishes task-body call [0x41cbfd,0x41cbff)→0x41cc95/action1 and completion call [0x41cc32,0x41cc3c)→0x41cc6f/action1. These paths join the handler at 0x41cc98, which captures an exception and calls 0x360570 at 0x41ccb5. An exception reaching that handler has already left the task body. This report does not certify every exception-construction/cleanup path or assign final error consumption semantics.

A guard race is distinct: consumer guard==1 at 0x41c850–0x41c85c skips invocation via 0x41c8fc and reaches task destruction through 0x41c879→0x41c250. Destructor helper 0x3454e0 has a conditional remaining-result path that installs an error-bearing result and publishes ready at 0x345661/0x34566a. Its allocation/handler prerequisites are not guaranteed here. This is another reason ready is weaker than callback success, and stalled/error paths must not be described as unconditional queue drain.

## Lifetime conclusion and limits

The prior publication join established task captures of builder-frame vectors and their exact two task identities. For the inspected normal consumer completion, body access ends before ready publication, and the originating builder cannot pass the ordinary scheduler wait before observing ready. For the guard fallback, no body/capture use is performed and retained task cleanup follows in the same caller. These are bounded code-enforced ordering facts, not evidence that a real collector ran.

The shared-state allocation can outlive a task; this does not by itself extend the stack vectors' lifetime. Remaining universal questions include other state writers, transitive queue correctness, abnormal unwinds or termination, and whether a queue ever drains. No stored worker-completion exception consumption or Java map/tick ordering is inferred. Runtime remains blocked, and the main JNI frontier is untouched.

## Evidence

Original SO SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. `verify.py` passes 15 original-byte windows, 13 instruction assertions, four exact LSDA edges, four task-vtable relocations and two import chains. Imported pthread_once and syscall are resolved through original PLT/GOT RELATIVE trampolines to JUMP_SLOT symbol metadata; no identity is inferred merely from a function's shape. `receipt.json`, `lsda.json` and original code extracts remain outside Git. Only read-only original ELF/class metadata analysis and local evidence scripts were used; no target or guest execution, assets, network, CI or Git changes.

## Published review

[Independent conditional acceptance](NATIVE-COLLECTOR-WAIT-LIFETIME-REVIEW-2026-10-18.md), [review receipt](NATIVE-COLLECTOR-WAIT-LIFETIME-REVIEW-2026-10-18.json), [integrity evidence](NATIVE-COLLECTOR-WAIT-LIFETIME-EVIDENCE-2026-10-18.json). The reviewer additionally resolved the emitter state virtual +0x10 slot to an original RET-only target, excluding hidden task-body invocation at that selected call.
