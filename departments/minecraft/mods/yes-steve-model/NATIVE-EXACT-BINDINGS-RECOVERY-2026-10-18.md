# Exact YSM native bindings

Recovered from original descriptor stores and isolated guarded metadata callbacks. All 17 exact owner/name/descriptor triples match ACC_NATIVE declarations in the pinned original JAR. This is not runtime RegisterNatives success.

- 0x3c21a0 ← com/elfmcys/yesstevemodel/OoOo0ooo0o00O0oooO0oooOo.o0OOooo0o0OO00OoOOOo0o0O()Ljava/lang/Object; (callback 0x418540, flags 0, access 266)
- 0x3c2310 ← com/elfmcys/yesstevemodel/OoOo0ooo0o00O0oooO0oooOo.O00OOOooOoooOoo0o0o0oO0O()V (callback 0x418560, flags 0, access 266)
- 0x3c2920 ← com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00.Oo0Oo0o00O00Oo0OOoOOoooo(Ljava/lang/String;Ljava/lang/String;Ljava/util/function/Consumer;)V (callback 0x418580, flags 0, access 265)
- 0x3c5190 ← com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00.Oo0Oo0o00O00Oo0OOoOOoooo(Ljava/lang/Object;)Z (callback 0x4185a0, flags 0, access 266)
- 0x3c5500 ← com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00.Oo0Oo0o00O00Oo0OOoOOoooo([Ljava/util/UUID;[Ljava/lang/String;[Ljava/lang/String;Ljava/lang/Object;)V (callback 0x4185c0, flags 0, access 266)
- 0x3c6a40 ← com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00.Oo0Oo0o00O00Oo0OOoOOoooo(Ljava/util/UUID;Ljava/nio/ByteBuffer;)V (callback 0x4185e0, flags 0, access 265)
- 0x3bc7c0 ← com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo.Oo0Oo0o00O00Oo0OOoOOoooo()Ljava/lang/Object; (callback 0x418600, flags 2, access 265)
- 0x3bee40 ← com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO.o0OOooo0o0OO00OoOOOo0o0O(Ljava/nio/ByteBuffer;)V (callback 0x418620, flags 2, access 266)
- 0x3bf0c0 ← com/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0.O00OOOooOoooOoo0o0o0oO0O()V (callback 0x418640, flags 2, access 258)
- 0x3bf540 ← com/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0.Oo0Oo0o00O00Oo0OOoOOoooo(J)V (callback 0x418660, flags 2, access 266)
- 0x3c1160 ← com/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0.Oo0Oo0o00O00Oo0OOoOOoooo(J)V (callback 0x418680, flags 2, access 266)
- 0x3c1400 ← com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0.O00OOOooOoooOoo0o0o0oO0O()J (callback 0x4186a0, flags 2, access 266)
- 0x3c1600 ← com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0.Oo0Oo0o00O00Oo0OOoOOoooo(JLjava/nio/ByteBuffer;)Z (callback 0x4186c0, flags 2, access 266)
- 0x3c1850 ← com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0.o0OOooo0o0OO00OoOOOo0o0O(JLjava/nio/ByteBuffer;)I (callback 0x4186e0, flags 2, access 266)
- 0x3c20d0 ← com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0.Oo0Oo0o00O00Oo0OOoOOoooo(J)V (callback 0x418700, flags 2, access 266)
- 0x3c2100 ← com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0.o0OOooo0o0OO00OoOOOo0o0O(J)V (callback 0x418720, flags 2, access 266)
- 0x3bf750 ← com/elfmcys/yesstevemodel/ooOOo000OOO0ooO0oo0ooooO.Oo0Oo0o00O00Oo0OOoOOoooo(Lcom/mojang/blaze3d/vertex/VertexConsumer;Lcom/mojang/blaze3d/vertex/PoseStack$Pose;Lorg/joml/Matrix4f;ZLcom/elfmcys/yesstevemodel/OOoOoooOOooO0o0000o0O0o0;[F[FIIIIFFFFZ)V (callback 0x418740, flags 2, access 266)

## Find a native entry by its existing Java boundary

These groups come from exact tuple joins to the prior declaration inventory, not new guesses about native bodies. Read the linked boundary before invoking or reusing an entry.

- [Common setup/shutdown](COMMON-NATIVE-LIFECYCLE-EVIDENCE-2026-10-17.json):0x3c21a0,0x3c2310.
- [Server model synchronization](SERVER-MODEL-SYNC-JAVA-EVIDENCE-2026-10-17.json):0x3c2920,0x3c5190,0x3c5500,0x3c6a40.
- [Client compatibility initialization](CLIENT-COMPAT-INITIALIZATION-EVIDENCE-2026-10-17.json):0x3bc7c0.
- [Client model reception](CLIENT-MODEL-SYNC-STATE-EVIDENCE-2026-10-17.json):0x3bee40.
- [Native texture boundary](NATIVE-TEXTURE-JAVA-BOUNDARY-EVIDENCE-2026-10-17.json):0x3bf0c0(instance),0x3bf540(static).
- [GeoModel lifetime](LOCATOR-MATRIX-PREPARATION-EVIDENCE-2026-10-17.json):0x3c1160.
- [Audio decoder boundary](AUDIO-DECODER-JAVA-BOUNDARY-EVIDENCE-2026-10-17.json):0x3c1400,0x3c1600,0x3c1850,0x3c20d0,0x3c2100.
- [Rendering](JAVA-RENDER-BOUNDARY-EVIDENCE-2026-10-17.json):0x3bf750.

## Scope and reproducibility

[Exact evidence receipt](NATIVE-EXACT-BINDINGS-2026-10-18.json) preserves all source-payload, callback, classfile and pairing-instruction hashes. All seventeen recovered owner/name/descriptor/access/class-hash tuples also exactly match the pre-existing October17 declaration inventory. This cross-check does not use declaration order to infer addresses.

The input SO SHA-256 is15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. The independent callback scenarios clone unicorn-jni-fmlcore-next6.checkpoint.json (SHA-2565910f1c5b52de7aeb2313ae9885bc22fd385a27815885516287cd319e4271d84). They do not resume its interrupted JNI frame. Three independent clones decoded the sequence in bounded batches. The initial2M-instruction resource stop is preserved; all successful callbacks returned within4M instructions with ABI/callback-frame checks and known-byte guards intact. Two callbacks were additionally checked in reversed order in another clone; [receipt](NATIVE-BINDING-ORDER-CHECK-2026-10-18.json). That is not a claim about every permutation.

Exactly one binding,0x3bf0c0, is an instance native: its second JNI argument is jobject. The other16 are static and receive jclass. This distinction must be preserved by any wrapper or subsequent body analysis.

This completes the original-YSM declaration mapping for this JNI_OnLoad registration table only. Client startup has a separately recovered [five-descriptor LWJGL registration site](NATIVE-CLIENT-STARTUP-RECOVERY-2026-10-18.md), whose exact identities and [wrapper behavior](NATIVE-LWJGL-WRAPPERS-RECOVERY-2026-10-18.md) are tracked separately. Do not interpret this receipt as a census of all registration sites. It does not establish full implementation semantics, runtime registration, JNI_OnLoad completion, thread scheduling, actual Minecraft execution or overall deobfuscation. Java mapping remains669; no entry is automatically promoted. Independent semantic review of the complete project remains NOT_RUN.

## Reusable evidence/replay tool

Use tools/recover_native_bindings_ysm_265.py with --image ORIGINAL_SO --jar ORIGINAL_JAR --checkpoint NEXT6_CHECKPOINT --out NEW_EXTERNAL_DIRECTORY. --proof-only checks original source instructions without guest execution. --verify-receipt NATIVE-EXACT-BINDINGS-2026-10-18.json checks all seventeen saved records, their pinned observed plaintext hashes, original native declarations and static/instance ABI without guest execution. Omitting those flags requests the separately guarded callback replay. Input hashes and the demonstrated checkpoint are pinned; missing or changed inputs fail rather than inventing progress.

Fourteen bounded tests pass, including same-length valid-native substitution, source/hash/flag corruption, ABI/descriptor corruption and resource-versus-semantic stop handling. All seventeen saved bindings pass the final byte-only verifier. The refactored CLI's complete guest replay was not repeated: it uses one sequential clone whereas the original successful experiment used three batches. Saved-evidence verification is not independent decryption, and pinned observed plaintext hashes are recorded observations, not a new proof that initialization or registration succeeds.
