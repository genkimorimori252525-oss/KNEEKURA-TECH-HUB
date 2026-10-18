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

## Forge ConfigValue and loader paths

The next exact references are ForgeConfigSpec$ConfigValue and FMLPaths. The declared fixture adds Forge universal and fmlloader from the same 1.20.1-47.4.0 profile; this is not a claim about the user's installed version.

The primary Forge download index publishes installer SHA-1 b73203963ea70aee0c38dc58de1f6d16a766605b. An independently public SJTUG mirror copy matches it. The installer is treated only as a ZIP data source; it is never run. Its original install_profile.json supplies each library's size and SHA-1, which were checked before metadata parsing:

- Forge universal: 2,776,081 bytes; SHA-256 2b0e97b22fd4d043dbbcc8e0a44ef0d58915689ed9224e4cd28d5c4976a16bcc.
- fmlloader: 267,079 bytes; SHA-256 d17c218af5c62fa4928019614aa8a5075279f8545efe21325baf46b80f4a5ac9.

The source-backed continuation verifies ForgeConfigSpec$ConfigValue.get():Object and FMLPaths.CONFIGDIR and absolutePath field descriptors. It retains the same two unexecuted detached workers and no pending Java exception. This required only explicit additive artifact inputs, not a successful-class stub, installer execution or another whole-project test run. Exact official checksum page, public mirror URLs, extracted library records and class/member proofs are in the receipt.

Sources: [Forge official download checksums](https://files.minecraftforge.net/net/minecraftforge/forge/index_1.20.1.html), [SJTUG public artifact index](https://mirror.sjtu.edu.cn/bmclapi/net/minecraftforge/forge/1.20.1-47.4.0/). The SHA-256 pins are locally calculated after validating the original distribution's SHA-1 chain. The mirror itself is not treated as the authority for version compatibility or the expected hashes.

The same verified installer profile also pins fmlcore (118,914 bytes, SHA-256 483f2d764a3a426f09a51cb37eb552830ffac8132da6bb3afbd7d825e6a34fd2). Adding it resolves the observed ModList.INSTANCE and fileById field descriptors. These private implementation references make the declared Forge profile material; do not generalize them to arbitrary Forge versions.

## First Forge metadata phase completed; runtime state boundary

The next missing class, net/minecraftforge/api/distmarker/Dist, is supplied by the original mergetool 1.1.5 API JAR. The verified installer version.json pins its size (2,572 bytes) and SHA-1 f3da18e12c696d35a47c82cbb2cc8b5aa15e1154. The mirror artifact matches both; locally calculated SHA-256 is 39d9a3d9277c1402b8e7b97f917ce278241cf1796312aec85b87f19a376dd99a. This is the sixth explicit dependency archive, read as metadata only.

The continuation resolves Dist.DEDICATED_SERVER and reaches GetStaticBooleanField for FMLEnvironment.production. The checkpoint unicorn-jni-dist-next1.checkpoint.json has SHA-256 af930823c9a03c87320194c0edc86b6ddf061bbf244834354538fc77ea65db74. It records 29 method proofs, 14 field proofs and 123 completed JNI gateway calls. The unresolved static-field read itself is not counted as completed. Both workers remain pending, detached and unexecuted; no pending Java exception exists.

This boundary is materially different from a missing class definition: classfile metadata proves a field exists, but does not establish its initialized runtime value. No guessed production flag, enum instance or successful object read has been substituted. Main-path continuation requires an explicit, evidence-informed runtime-state scenario. Independent isolated callback decoding can recover registration metadata without claiming that this boundary or real RegisterNatives has completed.
