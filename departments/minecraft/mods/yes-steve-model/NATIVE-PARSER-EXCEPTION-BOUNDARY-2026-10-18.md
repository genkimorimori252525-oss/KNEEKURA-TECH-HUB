# Native parser bridge: fallback versus escaping Java failure

2026-10-18. PRIMARY_STATIC_BYTE_BACKED_HELPER_BOUNDARY. Independent review CONDITIONAL_STATIC_ACCEPTANCE: [independent review](NATIVE-PARSER-EXCEPTION-REVIEW-2026-10-18.md) and [receipt](NATIVE-PARSER-EXCEPTION-REVIEW-2026-10-18.json). This closes one part of the explicitly open exceptional native/JNI boundary in NATIVE-CONTROLLER-JAVA-BRIDGE, without extending to whole-model rollback or renderer state publication.

## Result

The normal path after native parser helper `0x3742d0` is gated by a pending-Java-exception check even when the JNI result is null. A pending exception follows capture, JVM-clear, and native error-code `0x3c` throw-like construction; it does not follow this helper's ordinary return into its caller's expression insertion. By contrast, a Java parse exception caught by the already-verified facade may return its ordinary fallback with no pending exception and continue materialization. Native exception-check success therefore still does not certify parsing success.

This is a local control-flow result. It does not prove all previously constructed objects are rolled back, an older model is preserved, the native entry eventually rethrows the identical Java Throwable, or cleanup is universally exception-safe.

## Exact code join

Existing exact metadata identifies manager `d355b0+48` as original Java owner `com/elfmcys/yesstevemodel/OooOoOoOOOOo000oo0oo00oo`, method `Oo0Oo0o00O00Oo0OOoOOoooo(Ljava/lang/String;Z)Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;`. The prior original-classfile bridge establishes its unsafe call at bytecode3, Exception handler over [0,6), and fallback return93–96. Errors and failures in reporting can escape. That classfile conclusion is reused, not re-audited here.

1. Helper `3742d0` creates the input string at `3742ee` via JNI+538; resolves the parser member; loads parser receiver from wrapper+28; and calls `36d530` at `37435c`. That variadic adapter invokes JNI+118 (CallObjectMethodV) at `36d5ac`, then returns at `36d5b9` without its own exception test.
2. Nonnull result is wrapped by stores `37436a..37438b`. Null result takes `374364→374472`, installs the empty/no-op wrapper representation, then jumps `374486→374383`. Both paths reach `374392→41a560`. A null JNI result does not skip this test. The input NewStringUTF-null branch `3742f7→374458` instead rejoins string-wrapper construction and continues toward the parser invocation; this is not a claim of safe failure handling for every preceding JNI operation.
3. `41a560` calls JNI+720 (ExceptionCheck) at `41a56a`. Clear status falls through to return `41a57b`. Pending status branches `41a572→41a57c`, calls `41a330` at `41a57f`, then JNI+88 (ExceptionClear) at `41a58a`. Only if capture returns normally does that explicit clear execute.
4. `41a330` calls JNI+78 (ExceptionOccurred) at `41a341`. Its nonnull branch obtains a NewGlobalRef at `41a380`, resolves native state through `d14e80`, and stores the resulting reference at state+118 (`41a3c4`), with a wrapper rooted at state+f8. Existing-reference release and initialization branches are visible; no global-reference allocation-success check is claimed. Its null branch also installs an empty representation. This establishes attempted retention before clear, not guaranteed identity-preserving future rethrow or no-loss under allocation failure.
5. After clear, `41a560` allocates/builds an error payload carrying 16-bit code3c at `41a5a7`, passes it through `4db980`, and calls the existing throw-like helper `2abe00` at `41a5fa`. `2abe00` has no normal return in its extracted body; calls through exception/unwind machinery terminate at `2abd1b` or trap, and the `41a560` alternate cleanup branch calls `322a00`. The earlier archive-contract evidence independently labels this same target throw-like. We do not assign a recovered C++ symbol name or prove the complete unwinder.
6. Only the no-pending ordinary branch resumes `374397..3743e8`: releases the input local reference through `360270` (JNI+b8 at `360279`) and returns. Exceptional landing-pad code in `374498..3744e8` invokes wrapper cleanup and `322a00`, with no normal return visible there. Exact landing-pad coverage/LSDA and full transitive cleanup are not claimed.

## Immediate consumers and reuse meaning

The existing controller construction proof supplies four callsites, now included as fresh byte windows:
- Animation expression: helper call366358 before Pair factory3663c2 and array insertion3664d3; empty expression strings take a separate null-expression path.
- Transition condition: helper call366691 before factory3666d0 and array insertion3667e1.
- onEntry: helper call366abc before insertion366ad2.
- onExit: helper call366bd8 before insertion366bee.

The resource user-function path calls helper370a03 (flag1), before map insertion sequence370a08..370a3f. Controllers use flag0. This report introduces no new meaning for those flags.

For these ordinary continuations, escaping Java failure is not silently replaced with the facade's fallback by native helper3742d0. The native check does not distinguish successful parsing from a Java-caught failure that already returned fallback. Null with no pending exception is also not rejected here: it can leave this helper as an empty result wrapper. No claim is made that the exact facade ordinarily produces such a null. Consequently a reusable importer must preserve the three-way distinction: ordinary result/fallback, null with no pending exception, and pending-exception native nonlocal failure. Earlier expression outputs or native temporaries may already exist before failure; no transaction is established.

## Provenance and verification

`verify.py` reads only original ELF/code and original JAR native member; confirms exact embedded SO equality and SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22; checks the ELF LOAD mapping for every code window; emits12 hashed raw code windows and disassembly; and passes13 exact byte assertions. `receipt.json` preserves offsets, hashes and five reused contract hashes without original method bodies. Raw extracts stay outside Git. No YSM Java/native execution, JNI continuation, asset reading/decoding, runtime403 retry, network, CI or Git edit occurred.

Independent semantic review is separate from these integrity assertions. Central mapping and whole-project NOT_ESTABLISHED status are unchanged. Remaining meaningful boundary: final native-entry catch/Java rethrow and model publication/rollback, including whether already-retained native Throwable state is consumed; not resolved by this helper-only result.

Published byte-window integrity receipt: [NATIVE-PARSER-EXCEPTION-EVIDENCE-2026-10-18.json](NATIVE-PARSER-EXCEPTION-EVIDENCE-2026-10-18.json). Raw original extracts remain outside Git.
