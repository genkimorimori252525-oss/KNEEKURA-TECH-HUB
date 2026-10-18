# ModList / fileById boundary: static contract

## Result

This boundary has a pinned producer and a single exact map key in the audited straight-line segment. It does not provide the actual singleton, installed-mod membership, or YSM archive path. No execution frontier was advanced.

ModList.INSTANCE is private static (not final), defaults to null, and is not assigned in <clinit>; that initializer only initializes LOGGER. ModList.of(List<ModFile>, List<ModInfo>) constructs a new ModList, then publishes INSTANCE at bytecode offset 9. Its get() simply returns INSTANCE. Normal Forge producer ModLoader.gatherAndInitializeMods waits for background scan completion (bytecode 39), maps LoadingModList.getModFiles through ModFileInfo.getFile, takes LoadingModList.getMods, and invokes ModList.of at bytecode 76. This publication does not prove mod initialization succeeded: later loadingExceptions branches can setLoadedMods(emptyList) and throw.

The constructor builds final fileById:Map<String,ModFileInfo> from its first argument: ModFile.getModFileInfo → cast ModFileInfo → getMods → flatMap(Collection.stream) → cast ModInfo → Collectors.toMap(ModInfo.getModId, ModInfo.getOwningFile). It is not a map of mod containers or archive filenames; multiple IDs from one file can share one owning value. Duplicate keys are rejected by the pinned collector rather than overwritten. Actual files/IDs remain runtime inputs, not classfile facts.

Crucially the native cached get method is java/util/HashMap.get(Object):Object, not Map.get. The pinned JDK 21 java.base Collectors.toMap(Function,Function) supplies HashMap::<init> through bootstrap #63; this supports HashMap compatibility for this pinned normal producer, not arbitrary Map substitutes. See Collectors-bytecode.json. HashMap.get returns a found node value, or null when absent; identity of the freshly created query String is not map membership.

## Native consumer

- 3d6b59: JNI GetStaticObjectField ModList.INSTANCE (manager d35588 +48); null branch 3da833.
- 3d6bdb: JNI GetObjectField ModList.fileById (+50); null branch 3da853.
- 3d6de7: NewStringUTF of exactly yes_steve_model, length 15. 3d6daf stores yes_stev; overlapping +7 store uses r15 initialized at 3d585f to ve_model, with NUL at +15. No other queried key is shown in this bounded chain.
- 3d6e87: cached HashMap.get (d356e0 +70), receiver fileById and query string argument. Wrapper 36d530 invokes JNI +118 CallObjectMethodV at 36d5ac. Result null branches at 3d6e8f to 3da893.
- 3d70c1: returned ModFileInfo.modFile (+58).
- 3d72b6: ModFile.jar:SecureJar (+60).
- 3d74a9: SecureJar.getPrimaryPath():Path (+68).
- 3d769b: Path.toAbsolutePath():Path (d356e0 +50).
- 3d788d: Path.toString():String (d356e0 +48).
- 3d7a63 passes String to 4192b0; 3d7a80 builds native path via 35c9c0 and moves its storage into d35258. No archive existence/open/read outcome follows from these identities.

ModFileInfo's constructor stores its input ModFile to modFile at bytecode 6. ModFile's four-argument constructor stores supplied SecureJar to jar at bytecode 11. Thus the next path is the discovered YSM owning archive's primary path, conditional on the complete supplied object graph, not CONFIGDIR or selected-temp.

## Evidence and limits

NATIVE-MODLIST-MAP-CONTRACT-2026-10-18.json contains complete cached member signatures, hashes, PCs and conditional/unavailable values. ModList/ModLoader/ModFileInfo/ModFile/ModInfo JSONs were extracted directly from pinned Forge classfiles. *-bytecode.json preserves decoded instruction offsets and BootstrapMethods. Collectors/HashMap were extracted from the pinned java.base.jmod, whose hash matches checkpoint metadata. checkpoint-members.json reads immutable unicorn-jni-forgeclient-next1.checkpoint.json; it establishes resolved member IDs, not live values. Original native windows are copied and objdump-disassembled; endpoints that split instructions are not used for claims. The 3d5500 window may start mid-instruction, but key constant 3d585f is a complete instruction corroborated by original bytes.

No JVM, native library, guest instruction, checkpoint continuation, host-user files, asset decoding, or filesystem scenario was used. Underlying classfile dumps, native windows and checkpoint receipts remain outside Git; this report and compact contract are published. Original artifacts and checkpoints remain unmodified. Stop before synthesizing initialized ModList, installed list, archive Path, or filesystem successes.
