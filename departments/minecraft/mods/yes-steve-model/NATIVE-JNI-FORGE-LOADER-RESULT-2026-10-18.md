# Fresh JNI reaches Forge loader metadata

The fresh thread-enabled scenario passes the previously observed missing-thread-support branch. It creates and detaches **two virtual pending workers**, and main-thread mutex lock/unlock completes with owner released. Neither worker executes; their captured start/argument/lifecycle records remain in the checkpoint. The two actual once callbacks remain done with no pending callback frames. There is no pending Java exception at this frontier. This is progress past a fixture limitation, not successful overall JNI/runtime completion.

The next real FindClass request is cpw/mods/jarhandling/SecureJar. [MinecraftForge's official 1.20.1 build definition](https://github.com/MinecraftForge/MinecraftForge/blob/1.20.1/build.gradle) pins SecureJarHandler 2.1.10. The corresponding original artifact was obtained from [the project-used NeoForged public Maven repository](https://maven.neoforged.net/releases/cpw/mods/securejarhandler/2.1.10/), with its published SHA-256 verified. This does not assert the user's installed Forge version. An attempted separate Forge installer fetch returned HTTP403; no installer was run, and it is not part of the evidence chain.

- JAR size: 88,749 bytes; 57 entries.
- JAR SHA-256: 7ec9207f47bc8847a16566b9a3b4ced8d073c49592897eb30ce2aaf643fdfcab.
- SecureJar.class SHA-256: 4597855c58ead7bdf4827381568ad121250d26d5da21233145a56991baf26cc2.
- JAR manifest identifies version 2.1.10 and source commit96a7b6a8.

The declared metadata classpath is extended explicitly, preserving all earlier hashes/proofs. SecureJar and getPrimaryPath():java.nio.file.Path are now source-artifact verified. No Java class initializer or JVM/native body executes.

The generic metadata scanner had incorrectly treated module-info.class as an ordinary duplicate/platform class. Module descriptors are now excluded from that ordinary-class collision check and are rejected as class_info targets. Actual application/platform class shadowing checks remain intact. The two affected metadata/bridge modules pass 42 tests, including two independent modular archives plus java.base module metadata. No full-project verification was needed.

[Receipt](NATIVE-JNI-FORGE-LOADER-2026-10-18.json) records the frontier, pending workers, released mutex, completed once state and dependency provenance. Keep original JARs and raw snapshots outside Git. There are still no recovered RegisterNatives bindings; Java mapping remains669 entries. The new continuation is active, with worker execution and actual object/classloader semantics still separate unfinished work.
