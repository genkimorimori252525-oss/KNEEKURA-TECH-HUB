# Native parser exception bridge independent review

Verdict: CONDITIONAL_STATIC_ACCEPTANCE of the local helper-boundary result in ../../native-parser-exceptions/REPORT.md. Original ELF reads and static disassembly only; no target/JVM/native/assets execution, network, CI, or Git edits.

Fresh checks confirm all 12 retained code windows and 13 byte assertions against original SO SHA256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. ELF program headers supply exact file mappings. JNI offsets independently counted from the installed JDK21 jni.h: CallObjectMethodV35/+118; ExceptionCheck228/+720; ExceptionOccurred15/+78; ExceptionClear17/+88; NewGlobalRef21/+a8; DeleteLocalRef23/+b8 (offsets hexadecimal).

Accepted edges: 37435c→36d530→JNI+118; result-null branch374364→374472→374383 rejoins nonnull path before374392→41a560. Pending branch41a572→41a57c calls capture41a57f→41a330, then clear41a58a, payload code3c store41a5a7 and throw-like call41a5fa→2abe00. No null-result check bypass exists. Null without a pending exception can return normally. NewStringUTF-null earlier in3742d0 is a separate branch and is not established as universally safe.

Capture storage is TLS-backed: direct call41a39e→d14e80 jumps through GOT d30bc8, whose R_X86_64_RELATIVE addend is13d713c. That trampoline jumps through184d3e8, whose R_X86_64_JUMP_SLOT symbol is __tls_get_addr. The NewGlobalRef result is stored at TLS block+118 at41a3c4, within a wrapper rooted at+f8. This establishes attempted capture, not guaranteed NewGlobalRef success or preservation of the original Throwable under allocation/cleanup failures.

Nonreturning wording is accepted only as absence of an ordinary return to the helper continuation: 2abe00..2abe43 contains no ret, reaches unwind-like call3224e0, fallback handling2aacc0, then2abd1b and int3. The additionally inspected2abd1b..2abd29 likewise has no ret and ends call2abd00/int3. This does not name every C++ runtime symbol or prove the complete unwinder. ExceptionClear is not recovery: normal capture return is required to reach it, then payload allocation/construction can itself fail. The code3c path must not be described as guaranteed for every escaping Java error.

Immediate helper calls366358,366691,366abc,366bd8 and370a03 precede the reported ordinary factory/insertion continuations. The broad existing contracts supply later pair insertions3664d3 and3667e1; the new short windows do not independently encompass those two insertions. Catch tables/LSDA, final native-entry handling, rethrow identity, publication and global rollback remain unproved. A Java-caught fallback can continue normally, so native exception-check success is not parsing success.

Minor evidence hygiene note sent to author: initial3709e0 disassembly begins inside an instruction, though the relevant3709ef onward call/flag/insertion decoding is coherent. Author replaced the referenced window with3709ea and reran verification; independent checks also pass on the replacement. This does not change the conclusion.

Reproduce independent integrity and TLS/JNI checks with review.py. The receipt records the exact reviewed report hash and all window hashes. This review does not broaden the reused Java-classfile proof or certify whole-project equivalence.
