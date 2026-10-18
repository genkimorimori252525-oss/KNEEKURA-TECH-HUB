# Captured Java Throwable: TLS diagnostics and deferred release

## Bounded finding

The Java Throwable retained by 0x41a330 has two concrete static uses beyond capture:

* A native error formatter reads the current thread's TLS+0x118 when formatting native error code0x3c, invokes Object.toString on that reference, and uses the resulting string for diagnostics. This is a read, not a move/reset or proven identical Java rethrow.
* Replacement and attempted thread-exit cleanup call a deleter that queues a global-reference deletion item. JNI DeleteGlobalRef occurs only in the collector consumer when that item is actually processed. Cleanup invocation is not itself a successful-deletion guarantee.

This closes a local capture→diagnostic-consumer and capture→cleanup-request contract. Universal JNI entry/exit reset or identical Throwable rethrow remains open; this report does not infer a leak or all-thread lifetime property.

## Capture, overwrite and destructor registration

The earlier parser-exception report established ExceptionOccurred at0x41a341, attempted NewGlobalRef at0x41a380, then storage in TLS+0x118. The wrapper starts at TLS+0xf8, so the reference is wrapper+0x20.

Overwrite order matters:0x41a3bd saves the old reference,0x41a3c4 installs the new reference, and only then does0x41a3e8 invoke the old wrapper deleter if the old reference is non-null. The new wrapper's invocation target becomes0x3451f0 at0x41a40e and manager becomes0x326fc0 at0x41a405. No successful global-reference allocation check was added; an empty new result may replace a prior reference. The capture helper's null-ExceptionOccurred branch also supplies an empty representation.

Lazy initialization zeroes the wrapper and reference, sets TLS+0x120, and passes destructor0x41a2c0, wrapper address TLS+0xf8 and DSO handle to0x2aa2d0 at0x41a50a. Original import relocation resolves0x2aa2d0→0xd14e40 to __cxa_thread_atexit_impl. Its return is not checked before continuing at0x41a50f, so this is a registration attempt, not proof that eventual thread cleanup is registered or runs.

Destructor0x41a2c0 reads wrapper+0x20, invokes wrapper+0x18 at0x41a2e5 when non-null, then clears wrapper+0x20 at0x41a2e8 only after normal deleter return. It finally invokes the manager with operation3. The installed manager0x326fc0 returns without a Java call for that operation. Cleanup failures/termination are not assumed absent.

## Deferred global-reference release

Installed deleter0x3451f0 loads the reference through its argument and checks guard d35988. If nonzero,0x3451fc branches directly to return0x345262 without submitting a deletion item.

Otherwise it constructs a two-word pair `(reference, null task)` at0x345203/0x345207, obtains a queue through0x41ba10 and attempts submission with0x41bd80 at0x345220. A null queue or false submission follows return/cleanup without a direct JNI deletion. Successful submission may notify through sem_post at0x345243. The retry loop here is notification handling, not a deletion-completion wait. Original PLT/GOT relocation resolves d148f0 to sem_post.

The queue's simple successful path copies the pair and clears the source task slot at0x41bdb1. In the consumer, guard==1 can skip processing; otherwise nonzero first word at0x41c862/0x41c866 selects0x41c86b–0x41c873. It loads the consumer's JNI environment, retains the reference in RSI, and calls JNI table+0xb0, DeleteGlobalRef. This is distinct from zero-first-word model tasks, which invoke their task bodies through the separate branch.

The local contract is therefore release-request enqueue plus conditional collector deletion. No proof of successful submission, eventual drain, deletion timing, or shutdown behavior is obtained by merely seeing overwrite or thread cleanup. The guarded no-submission branch is recorded without converting it into a leak assertion.

## Concrete diagnostic consumer

Function0x3cda10 compares the supplied 16-bit native error code against0x3c at0x3cdb01. On that code it resolves the same TLS descriptor d2cf38, checks the initialization flag, and reads TLS+0x118 into RSI at0x3cdb27. Null value falls back to the ordinary formatting path. An uninitialized wrapper is initialized and a destructor registration is attempted at0x3ceab1–0x3ceae9, then the value is reread.

For a non-null retained reference, the formatter reads manager d356e0+0x80 and calls adapter0x36d530 at0x3cdb61. The existing compact member index resolves this exact member as instance java/lang/Object.toString()Ljava/lang/String;, with its original declared-JDK class metadata provenance. Adapter0x36d530 calls JNI CallObjectMethodV (+0x118) at0x36d5ac, so the retained reference is the receiver; ordinary virtual dispatch still applies. A non-null return is checked by0x41a560 at0x3cdb9c and converted through0x4192b0 at0x3cdbae for the native diagnostic string. This call can itself throw; no side-effect-free toString or recursion immunity is assumed.

An immediate original caller is formatter0x3cef00: it invokes0x3cda10 for the top code at0x3cef48 and iterates nested native error records, reading each code and following +0x28 links at0x3cef55–0x3cef72. The export worker's handled-error branch calls0x3cef00 at0x3c4c5e, passes its resulting diagnostics into0x3e12b0 at0x3c4c76, and rejoins the handled-error continuation at0x3c4c88. The existing export/reload dossier independently covers that downstream diagnostic/result callback path. This demonstrates a real original diagnostic use without expanding into all JNI exports.

The selected consumer uses the current same-thread TLS cell and does not clear or move it after formatting. Its lazy-init zero store is distinct from consumption. The native error record itself is not shown to own this Java global reference. Accordingly this does not establish that every code0x3c record, nested error or cross-thread result is paired with the exact Throwable originally responsible. The read/dispatch also does not call JNI Throw and cannot support an identical-Java-object rethrow claim.

## Provenance and limits

Original SO SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. `verify.py` checks12 original-byte windows,13 instruction assertions, two exact import chains and the existing d356e0+0x80 member identity; `receipt.json` records provenance. Candidate searches only selected bounded original-code consumers; they are not a completeness proof for all TLS readers/writers or aliases. Full original extracts remain outside Git.

Reused contracts: native parser capture, collector queue/lifetime, native export/reload diagnostics, and the native Java member compact index. No target/guest execution, assets, network, downloads, CI or Git edits occurred. Runtime remains blocked. Still open: universal JNI-entry rethrow/reset policy, identity preservation across native transformations or threads, successful allocation/registration, and global cleanup progress. These limits are not changed by proving the local diagnostic and deferred-release paths.

Published [independent conditional review](NATIVE-TLS-THROWABLE-REVIEW-2026-10-18.md), [review receipt](NATIVE-TLS-THROWABLE-REVIEW-2026-10-18.json), and [integrity evidence](NATIVE-TLS-THROWABLE-EVIDENCE-2026-10-18.json).
