# Controller materialization: code5b transformation and per-model failure

2026-10-18. CONTROLLER_TRANSFORM_RETHROW_STATIC. [Independent review: CONDITIONAL_STATIC_ACCEPTANCE](NATIVE-CONTROLLER-FAILURE-REVIEW-2026-10-18.md). This closes the controller-specific inner catch deliberately excluded from the preceding resource-worker report.

## Result

For the four selected controller expression paths, an escaping Java parser failure that becomes the native helper exception is not converted into a usable controller fallback by the intermediate native catch. Controller wrapper365a10 catches the escaping controller-data exception, constructs a new native error payload with16-bit code0x5b, and takes throw-like propagation on both selector branches. The three enclosing materializer callsites have cleanup-only unwind paths. If unwinding, cleanup, allocation and catch processing finish normally, propagation reaches worker35d250's already-proved per-model skip/continue path.

This differs from the Java facade catching an Exception and returning its ordinary fallback: that path has no escaping pending exception and may continue ordinary controller construction. Neither path is proof of successful expression evaluation. No guaranteed eventual batch completion, final Java/renderer publication or whole-model rollback follows.

## Exact original LSDA chain

All addresses are original ELF virtual addresses. verify.py derives mappings from program headers and parses GNU_EH_FRAME/FDE/CIE/LSDA metadata, rather than associating catches by disassembly proximity.

Controller-data function366110 (FDE187e3a8, LSDA145db8):
- animation expression366358: covered [366353,36635d), landing368627, action0;
- transition366691: [366684,366696), landing368653, action0;
- onEntry366abc: [366ab7,366ac1), landing368683, action0;
- onExit366bd8: [366bd3,366bdd), landing36865b, action0.

These are cleanup-only edges. The selected pads save the exception then jump respectively368cdf,368b64,368895,36885f. Their normal-returning cleanup branches converge on outward resume322a00 (with terminal failure paths retained), without a reachable normal return in the bounded cleanup CFG. Helper3742d0's own checker unwind edge/cleanup is reused from the preceding accepted helper/resource reports.

Controller wrapper365a10 (FDE187e354, LSDA145cb8): call365b39→366110 is covered [365b2e,365b3e), landing365ee9, action3. Its normal continuation would obtain collection metadata and invoke insertion wrapper364af0 at365b75. The exceptional path does not return there.

Materializer36d8c0 (FDE187f184, LSDA146720) calls365a10 at:
-36e74f, covered [36e73e,36e754), landing372cb8, action0;
-36f337, covered [36f326,36f33c), landing372c7f, action0;
-36fb37, covered [36fb26,36fb3c), landing372c72, action0.

Their cleanup branches converge outward to322a00, with no bounded normal-return path. This connects the controller-specific rethrow to the same worker materializer call35d54b already proved by [resource worker continuation](NATIVE-RESOURCE-FAILURE-WORKER-SKIP-2026-10-18.md): [35d53d,35d550)→landing35de5e/action3. That worker handler destroys/frees the temporary native model, sets status4, and `status & 3 == 0` advances to another item if present. The previous report's ordinary-handler and native-staging-only qualifications apply unchanged.

## What the controller catch actually builds

Landing365ee9 retains selector RDX and exception RAX, then enters wrapper cleanup365f49/365f51 before begin-catch-like call2aacc0 at365f5e. The returned caught-object pointer is saved in RBX. After exception-object allocation, selector==2 chooses the first branch; all other selectors choose the second.

Both paths request a0x58 payload and obtain a string-shaped value through a virtual call on the saved context (365f96 or365fff). We do not assign semantic text or a resource name to that value. They pass ESI=0x5b at365fad or366016 into329990. That helper stores SI directly into payload offset0 at3299a1, establishing the16-bit code independently of labels. It moves/copies the passed string and installs other fields.

The selector2 branch passes the caught-object pointer as RDX to4dbfc0 at365fc3. The other branch calls4db980 at366029 without that third argument. The former visibly reads caught-object+8/+10 and updates the new payload+28/+30; this is a native nested-data relationship, not proof of preserving the original Java Throwable identity, message, cause stack, or every diagnostic. No exact recovered C++ function names are required by the conclusion.

Both then supply typeinfo pointerd1d9e0 and destructor329a40 to throw-like helper2abe00, at365fdb or366041. Neither branch takes ordinary controller construction continuation. The earlier native checker constructs code3c; this catch constructs code5b. The report does not claim all failures always produce5b: string conversion, allocations, wrapper cleanup, constructors or catch machinery can themselves fail before those stores or throws.

## Normal construction and retention limits

The Java-catching facade fallback can flow through normal parser return and hence through Pair/array/state construction. By contrast, the escaping path traced here does not perform the failed controller-data result's normal insertion365b75. Other controller entries, Java objects, native temporary state or side effects may already have been created. The inner handler is not a proof of transactional rollback of that earlier work. The worker's later native staging-vector retention is the previously accepted local contract, not a guarantee of any final visible model collection.

The exact type2 name and full native error diagnostics are not needed: both selector branches construct5b and throw. Which branch a particular target runtime exception takes is not experimentally established. No original Java/native body, asset or callback was executed.

## Verification and provenance

Original SO SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. verify.py reuses the authored ELF/LEB reader from the earlier worker verifier without its artifact-writing portion, emits12 hashed code/metadata windows, verifies8 exact LSDA callsite edges and8 byte assertions, and checks8 cleanup/catch control-flow starts. Its CFG treats called cleanup helpers as returning normally; known resume/throw/terminate targets are terminal. This is static graph checking, not target execution, an unconditional destructor proof, or an independent review by itself. receipt.json contains compact metadata and terminal summaries; raw original code remains outside Git.

Prior helper and worker receipts supply the already-reviewed checker and outer catch links. No runtime403 retry, network, CI, assets or Git edits. Central mapping/source-artifact confidence remains unchanged.

Published integrity receipt: [controller failure evidence](NATIVE-CONTROLLER-FAILURE-EVIDENCE-2026-10-18.json). Independent reviewer additionally bound the original type2 RTTI to YSMException; the core two-branch result does not rely on runtime exception selection.
