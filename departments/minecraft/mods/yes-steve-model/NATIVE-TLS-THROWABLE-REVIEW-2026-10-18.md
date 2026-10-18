# Independent TLS Throwable retention review

Verdict: conditional static acceptance of the local retention/replacement/queued-release mechanism. This Java global-reference wrapper is distinct from the previously reviewed native completion-error reference.

## Exact original behavior

Capture 0x41a330 calls JNI ExceptionOccurred at +0x78 and, for a non-null local result, NewGlobalRef at +0xa8 (0x41a380). Original TLS lookup uses 0xd14e80, resolved through original relocations to __tls_get_addr. The wrapper is at TLS+0xf8 and its stored reference is wrapper+0x20 = TLS+0x118.

0x41a3bd loads the prior reference, then 0x41a3c4 stores the new value before the old non-null value is passed to the prior wrapper invocation at 0x41a3e8. The new wrapper invocation target becomes 0x3451f0 at 0x41a40e. A null ExceptionOccurred result also joins the replacement logic with a null value and no-op new invocation target; NewGlobalRef success is not independently guaranteed. There is no basis for assuming the old and new reference survive every allocation, callback or cleanup failure.

Lazy initialization clears the wrapper and passes destructor 0x41a2c0, wrapper address and DSO argument to 0x2aa2d0 at 0x41a50a. That wrapper calls imported __cxa_thread_atexit_impl. The return value is ignored, and the initialized flag is set before the call. This establishes an attempted thread-exit destructor registration, not successful registration on every path.

Destructor 0x41a2c0 passes a non-null wrapper+0x20 value through the wrapper's invocation slot at 0x41a2e5, then clears the slot at 0x41a2e8 and disposes its function wrapper. The clear is after ordinary invocation return, not an unconditional first action.

Installed invocation 0x3451f0 loads the reference, checks guard 0xd35988, and returns immediately when the guard is nonzero. Otherwise it constructs pair(reference, null task), obtains the queue, and attempts submission at 0x345220. Successful submission can notify via imported sem_post at 0x345243. There is no deletion-completion wait. The queue consumer's guard-permitted nonzero-first-word path calls JNI +0xb0 at 0x41c873, independently identified as DeleteGlobalRef from the local JNI header. Queue submission, consumption and thread-exit behavior remain conditional; no immediate or eventual release guarantee, nor a definite leak, is established.

## Concrete consumer and rethrow boundary

The diagnostic branch in 0x3cda10 compares the native code with 0x3c at 0x3cdb01, looks up this same TLS object, and reads TLS+0x118 at 0x3cdb27. A non-null reference is passed as the receiver to 0x36d530 at 0x3cdb61 using method metadata from manager 0xd356e0+0x80. That adapter is the previously established CallObjectMethodV route; its result goes through pending-exception checking and string conversion. These instructions establish a concrete diagnostic use of the retained Java object, rather than a JNI Throw call of that same object. The final worker receipt pins the existing member-index entry for instance java/lang/Object.toString()Ljava/lang/String;; its source hash and recorded identity were checked without rerunning metadata recovery. Original callers 0x3c4c5e→0x3cef00 and 0x3cef48/0x3cef66→0x3cda10 establish a diagnostic route including nested native error records. The current TLS cell is not shown to be an identity-preserving field of each such record. No exhaustive absence-of-rethrow claim is made.

## Verification and limits

`review_tls_throwable.py` verifies six original PT_LOAD windows, 15 instruction assertions, three original dynamic-symbol import chains (__tls_get_addr, __cxa_thread_atexit_impl, sem_post), and JNI table offsets. `tls-throwable-receipt.json` records hashes and limits. Only static reads, disassembly and authored checks were used. No target execution, assets, downloads, network, CI or Git edits.

Final worker report wording is conditionally accepted. Its 12 original windows were independently crosschecked, and report/receipt hashes are pinned in the review receipt.
