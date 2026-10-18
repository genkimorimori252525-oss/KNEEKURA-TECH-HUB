# Controller visitation order: bounded shipped-caller closure

2026-10-18. PRIMARY_STATIC_REVIEW_ONLY; independent review NOT_RUN. Resolves one missing reuse boundary: the ordinary shipped Java call paths that reach controller queue visitation and their ordering relative to player processing. It does not repeat or expand the prior beginning-point subtype proof.

## Finding

The normal processor schedule is **process controller A → visit A → process B → visit B → commit shared active bones**. There is no global process-all-controllers barrier before queue evaluation. Within a normally completed Bedrock processing call, all its active players finish processing before its queues are visited through the shipped direct-call paths. Hybrid forwarding and Bedrock child recursion preserve that local order.

The skipped-tick path is weaker: **shouldTick=false is not proof of a previous completed producer generation**. It skips process and visits currently retained state. Prior successful completion plus no intervening mutation is an additional premise. A model-dirty update can instead clear/reset the current state before visitation; it is performed even on a skipped tick. Polling still evaluates against the supplied evaluator and changes snapshots; cached queues are not immutable or side-effect-free.

For a faithful reuse implementation, preserve per-controller processing/visitation order and final shared-bone commit order. Do not parallelize all controllers or move all expression evaluation after their processing merely because the per-Bedrock-cohort proof is valid.

## Exact identities

All owners below have prefix `com/elfmcys/yesstevemodel/`. Candidate labels are navigation aids, not recovered original symbols.

- IAnimationController: `OoOoOO0O00oOoO0o0ooOO0oO`.
- AnimationProcessor: `OOOooo0o0OOOO0O0OOoOo0OO`.
- BedrockAnimationController: `O00Oo0oo0Ooo0oOOOo0OO0oO`.
- HybridAnimationController: `oO00oooOoOo0O0oOo000o0Oo`.
- CodedAnimationController: `oo000oooo0OOoo00O0o0OOOO`.
- The additional implementing class `oo0Oo0O00oooOoOo0O0oOOOo` is retained in the inventory; its visitor only conditionally invokes Consumer.accept and introduces no controller-visitation call.

Visitor name for all five declarations: `Oo0Oo0o00O00Oo0OOoOOoooo`, descriptor `(Ljava/util/function/Consumer;)V`.

Processor tick name: `Oo0Oo0o00O00Oo0OOoOOoooo`, descriptor `(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0O00Oo0o0oO0oo0oO00OOoO;ZZ)V`.

Controller process name: `Oo0Oo0o00O00Oo0OOoOOoooo`, descriptor `(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;Z)V`.

## Original-code evidence

### Shipped visitation callers

A fresh parse of all 955 original JAR classfiles identifies the interface family through class inheritance/interfaces, rather than searching an obfuscated name alone. Exactly three instruction callsites reference that family's visitor identity:

1. Processor tick at191: invokeinterface visitor.
2. Hybrid visitor at5: invokeinterface visitor on `activeController` field `Ooooo0oooO0oooOOOoO0000O`.
3. Bedrock visitor at29: invokevirtual the same visitor on child field `Ooo0O0000OO0OOO0o0Oo0oOO`.

No matching visitor MethodHandle occurs in parsed BootstrapMethods. This closes direct instruction and bootstrap-reference paths in this artifact only; it is not an all-runtime-callers proof.

### Per-controller sequence and commit

Processor tick loops at108, exits at115→199, and fetches each next controller at120. The dirty updateModel call is147. The shouldTick branch at153 jumps to168 when false; otherwise process is163. Both paths then obtain blendRotation at170, construct the consumer at186, and visit at191. Jump196→108 begins the next controller. After the loop, dirty clears at201; the active-bone loop starts213 and commit occurs580. There are no exception handlers in tick. A throwing process does not locally continue to visitation, but prior mutations are not rolled back and no completion token is stored here.

Bootstrap0 for the consumer at186 binds the processor method with descriptor `(Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;FZLcom/elfmcys/yesstevemodel/O0OO0Oo0Oo0O0oOO0OOoO000;)V`. That method calls rotation poll at36, applies its Optional callback at52, position poll58/callback71, and scale poll77/callback90. These operations occur during each controller's visit, before the next controller's process, rather than at final commit. This establishes ordered evaluation sites without assuming expression purity or proving what arbitrary callbacks can mutate.

### Bedrock and Hybrid

Bedrock process refreshes a holder condition305 then processes that player336. Its loop exit282→345 is after the full active-player iteration; dirty aggregation follows, clearing its flag479. No visitor call occurs inside that processing loop. In the child path, child process is269 followed by return272. Later the visitor delegates to child at29 and jumps32→79, so the local visitor does not also traverse its own queues on that branch. Otherwise it calls queue.shouldApply63 before Consumer.accept71.

Hybrid process first calls Bedrock process14 when isBedrock is true. Builtin state can select Coded at65 and processes Coded75; a nonbuiltin switch finalizes/reset Coded97/104 and assigns Bedrock112. The non-Bedrock path processes Coded125. All finish before the processor calls Hybrid visitor. Hybrid visitor itself only forwards to the then-current activeController. These normal-return paths have no exception handlers and do not certify external/reentrant field mutation safety.

### What shouldTick=false actually guarantees

The branch bypasses all controller process calls for this iteration, not just a time increment. Visitation still occurs. Therefore:

- With modelDirty=false, a previously completed normal producer call, and no intervening mutations/reentry/concurrency, retained queues are visited without advancing their player cohort first. This is the condition needed to reuse the prior completed-cohort premise.
- With modelDirty=true, updateModel147 occurs first. Bedrock's public list/map update delegates at19 to its list/data overload or clear26. The list/data overload calls clear at1. Bedrock clear writes state=null14, active-player count=0 at19, clears active queues26 and queue map33, then resets/clears players. After a normal reset without new process, its visitor's null-state test4→79 emits nothing. Hybrid updateModel may also change the active delegate before the skipped process. Thus 'skip tick always reuses the previous pose-producing controller state' is false.
- With an interrupted earlier operation, escaping callback, concurrent worker, or direct mutation, this caller sequence contains no verification that the retained cohort is complete. The known base frame gate sets currentFrameTicked before downstream processing, so a prior throwing invocation must not be upgraded to a completed generation merely by a later skipped-tick flag. This is a conditional static limitation, not a reproduced race or failure.
- Queue polling/snapshot application still occurs on skipped ticks. The proof does not promise that repeated visits produce identical numerical values, leave cached query objects untouched, or preserve arbitrary expression side effects.

## Provenance and verification

Fixed JAR `/workspace/scratch/d91451022177/ysm-local-inputs/ysm.jar`, SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. Only classfile code/metadata was read. No target Java/native/assets execution, asset decoding, download, CI or blocked-runtime retry.

Pinned source candidate revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`; four source files match that revision's Git blobs byte-for-byte. Source/artifact equivalence remains NOT_ESTABLISHED and SOURCE_ARTIFACT_DIVERGENCE remains in force. Current central correspondence map is unchanged at669.

[controller-visitation receipt](CONTROLLER-VISITATION-ORDER-EVIDENCE-2026-10-18.json) contains the three callsite identities, owner hashes, method digests, four source hashes and17 passing structural assertions, with no complete original method bodies. Counts are evidence scope, not completion or independent semantic review. `scan_visitation.py` reproduces the fresh original-class scan; `make_receipt.py` produces the compact receipt. Detailed original snapshots remain only in the Git-external `visitation-evidence.json` research file.

Limits: external classes, reflection, JNI invocation, dynamically synthesized handles, arbitrary callbacks, reentry and actual worker scheduling remain open. No statement here promotes all controllers to subtype-safe, or proves runtime success. The completed gap is the bounded shipped-caller ordering join, with the skipped-tick premise explicitly conditional.
