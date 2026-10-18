# JNI dependency metadata continuation

After 23 exact java.base method lookups, the isolated continuation reached FindClass(org/apache/commons/lang3/tuple/Pair). The original YSM JAR and java.base.jmod do not contain that class. The guard stopped rather than inventing it.

Minecraft 1.20.1's [official version manifest](https://piston-meta.mojang.com/v1/packages/a5cf661d31d9dfcd3d1645be80f43954f63f63b0/1.20.1.json) names org.apache.commons:commons-lang3:3.12.0 and supplies the [official library artifact](https://libraries.minecraft.net/org/apache/commons/commons-lang3/3.12.0/commons-lang3-3.12.0.jar). Download size and SHA-1 were checked against the manifest; independent SHA-256 is d919d904486c037f8d193412da0c92e22a9fa24230b9d67a57855c5c31c7e94e. Its 374 entries include Pair, class SHA-256 3297e3be25e160d36990475c65551ab32cd6c6c308c4f15c2eb26a1072364b8f.

The metadata fixture now accepts up to eight explicitly SHA-256-pinned dependency JARs, at most 128 MiB total. Platform shadowing and duplicate application class definitions are rejected instead of guessing a classloader order. JARs remain immutable external inputs; no Java bytecode, JVM body or library native code is executed on the host.

Adding an archive to a restored scenario requires --allow-java-source-extension, with --dependency ID SHA256 JAR. Existing source records must remain unchanged; all earlier class/method proofs are revalidated before accepting the extension. The checkpoint records the added-source provenance. Removal or replacement still rejects. Subsequent resumes require the same dependency argument but not the extension flag. This is an explicit richer classpath fixture, not a silent claim that all real classloaders behave identically.

The continued guest now successfully requests Pair and resolves its exact static of(Object,Object):Pair descriptor. Work remains active. These are metadata references, not recovered YSM RegisterNatives bindings. All 669 Java mapping entries remain unchanged.

The six-module affected suite passes 97 methods, including pinned-input/hash, ambiguity, platform shadowing, dependency lookup, explicit monotonic extension, unchanged prior proofs and checkpoint continuation. Archive fixtures use fixed ZIP timestamps to avoid time-dependent proof hashes. A worker also mistakenly ran broad discovery; its three errors were a missing --jar argument, absent YSM_SIM_INPUTS, and a new test's missing stopped-state fixture. The stopped-state fixture was corrected; the explicit affected suite is the accepted validation result. Broad discovery is not a success claim and should not be repeated for this task.

[Machine-readable receipt](NATIVE-JNI-DEPENDENCY-METADATA-2026-10-18.json) preserves exact dependency provenance and the 23 earlier method proofs. Original binaries, checkpoint payloads and raw traces remain outside Git. Overall semantic review is still NOT_RUN; the prior focused JNI guard review remains separate.
