# YSM 2.6.5 renderer backend continuation

Primary static review. Original ELF SHA-25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22 and JAR SHA-25625b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f are verified by build_receipt.py. This cohort preserves prior transform/normal receipts. No target/JVM execution or emulation was used here. Separate metadata-decoder evidence, when supplied, is an independent guarded scenario. Independent semantic review NOT_RUN.

## Useful result

Code6 is concretely the Java-array compatibility path: wrapper384a50 installs native producer388a20, copies12 floats and2 ints per vertex to Java arrays, then invokes a static Java callback. Code1 concretely writes native vertex memory obtained from a Java direct buffer. Codes2–5 are raw vertex variants selected by an integer field and one cached boolean; their names must come from metadata identities, not strides.

## Selector398e50

Arguments: JNI environment, mutable JNI object-holder whose object is+20, forceLegacy integer. Third argument nonzero returns6 immediately (398e5b→3996f7).

With forceLegacy false:
- Optional wrapperA managerd355d8 must have byte+32 exactly1, then IsInstanceOf against its+38 record class succeeds. GetObjectField using that record may yield the working consumer. Otherwise optional wrapperB managerd355e0 has the same checks. The selected nonnull extracted object is eventually moved into the caller's holder; RAII cleanup is visible. Neither wrapper is named from a guess.
- Working object must pass IsInstanceOf using the class in managerd355d0 record+150 (398f1e..398f3d). A failed test returns6.
- GetObjectField record+158 obtains a format object. Null format returns6 (39945b).
- IsSameObject(format,cached objectd34380) selects1 (399083..399091). d34380 is lazily populated by GetStaticObjectField through record+148, then NewGlobalRef (399467..3994b4).
- Otherwise cached byte d34388 must equal1, and IsSameObject(format,d34390) must succeed. Byte0 is the unknown case; lazy initialization sets1 when record+170 GetStaticObjectField returns nonnull, or255 when null. Successful object is retained as globalrefd34390. The same initialization reads static boolean record+188 through399a40/GetStaticBooleanField slot490 and caches it in d34378. This is a cached snapshot; this selector does not reread that boolean on every render.
- Only after those gates, GetIntField record+160 is read at3992f8. Table57d88 uses unsigned(value−48)<=8. Exact outcomes:48→2;54→4;55→3;56→2 ifd34378==0,5 otherwise;49–53 and all values outside48–56→6. Thus48 need not equal code2's output byte stride: code2 actually reserves56 bytes. No format name is inferred from the numbers.
- Missing required metadata records take explicit error/exception-construction branches rather than ordinary fallback. Fallback claims assume required metadata is valid and JNI calls complete normally.

Metadata store/callback priorities: legacy+128→40f6e0 (40a1b8/40a1fe/40a224); format+158→40f7a0 (40a446/40a496); integer+160→40f7c0 (40a4a8/40a4f8); wrapperA+38→40f300 (40a74d/40a78e/global40a792); wrapperB+38→40f2e0 (40a7da/40a81b/global40a81f). The completed separate decoder receipts are linked in the final section below.

## Native dispatch, producer choices

The six-entry relative tables585f8 and58610 are independently read from original bytes. Both map codes2–6 to the same wrappers. Code1 varies with renderMode==0 versus nonzero, not with a guessed graphics API:

|code|wrapper|installed producer|reserved bytes/vertex|
|---|---|---|---|
|1, mode0|inline3c0127|37fae0 at3c044e|36|
|1, mode!=0|inline3c0086|381f30 at3c02ce|36|
|2|384740|38a580 at38484d|56|
|3|384430|38dbe0 at38453d|55|
|4|383e10|394890 at383f1d|54|
|5|384120|391230 at38422d|56|
|6|384a50|388a20 at384b0a|48-byte float stream plus8-byte int stream|

This dispatch is reached only after preparation succeeds and vertex countd34c30 is nonzero. A preceding GUI/model flag combination bypasses selector398e50 into385080 or385390 (3c0032..3c0046,3c0f80..3c0fe3); their complete dispatch is outside this slice. All producer installation/wait mechanisms are static evidence, not worker threads run during research.

## Code1 raw producer, concrete destination and stores

398760 takes environment,consumer,vertexCount,byteCount. It calls record+140 (reservation helper), reads/increments GetIntField/SetIntField record+150 by vertexCount and record+138 by byteCount, then GetObjectField record+130. JNI GetDirectBufferAddress(slot730 at398927) supplies base address. The returned destination is base+old byteoffset (398977..39897d), not a cast of a Java handle.

For mode0 callback37fae0, the installed context supplies that destination by pointer. 37fd5b..37fd78 computes directBase+36*(entry output index+batchbase). Concrete first-vertex stores3801fb..380245 establish:
- offsets0,4,8: transformed position floats
- offset12: packed four color bytes; the callback separately scales incoming RGBA and calls external math helperd148c0 before packing, whose exact semantics are outside this slice
- offsets16,20: source UV floats
- offsets24,26: overlay low/high16
- offsets28,30: light low/high16
- offsets32,33,34: three packed transformed-normal bytes
- offset35: no writer in this particular store block; no whole-path initialization claim

The next vertex begins at+36. Face/entry byte+20 chooses fullbright0x00f000f0 versus passed light (37fc92..37fcad). Exact normal quantization, external color-rounding semantics, clipping/sorting and all producers are not fully reconstructed here.

## Code6 legacy producer to Java writer

384a50 sets countd3432c fromd34c30, growing reusable Java float/int arrays and native buffers if necessary. 388a20 receives the same batch-state context and writes directly to native floatbufferd34338 and intbufferd34358. The demonstrated ordinary branch at388ba6..388bf1 uses48*vertexIndex and8*vertexIndex. Four vertices are written per shown face and streams advance192 and32 bytes (3890be..3890e6).

First vertex388fdc..389037 writes xyz atfloat0..2, passed RGBA at3..6,UV7..8 and transformed normal9..11; int0 is packedoverlay from context+4, int1 is packedlight. Byte+20 of entry selects fullbright0x00f000f0 instead of passed light (388b19..388b25). Position uses the affine bank and normals use its nine-float normal bank; this joins the earlier transform contract to an actual producer without claiming complete face traversal recovery.

After worker completion and any sorted-range copy,384d01..384da4 calls SetFloatArrayRegion(slot6a8) for12*count fromnativefloatbuffer and SetIntArrayRegion(slot698) for2*count fromnativeintbuffer. For nonzero count it loads record+128 and passes consumer,count,floatarray,intarray to345d50, which makes JNI CallStaticVoidMethodV(slot470 at345dcc). This is an exact call shape; the callback's textual identity is confirmed by the separate metadata receipt below.

Original JAR reparse independently confirms nested class ooOOo000OOO0ooO0oo0ooooO$Oo0Oo0o00O00Oo0OOoOOoooo method Oo0Oo0o00O00Oo0OOoOOoooo descriptor(VertexConsumer;I[F[I)V, codeSHA2568966bf971c2571df9ec6b337306b4501aa397973d721917005b19eb31f00d4c6. Its loop consumes exactly those12+2 slots and calls VertexConsumer with xyz,RGBA,UV,overlay,light,normalxyz. Pinned source identifies this as NativeRenderer.LegacyWriter.flushVertex. The separate decoder has now returned exact callback40f6e0 with this identical owner,name,descriptor and an original-JAR static-method match. Its final receipt is cross-linked below. Thus the native producer→named Java writer link is established independently of shape matching.

## Bounds

Receipt contains19 original-byte anchors,9 disassembly windows,3 jump tables and4 exact JAR methods compared with previous Java evidence. Static receipts prove conditional data movement and dispatch; they do not prove working graphics, complete shader layout, all allocation failures, runtime races, or target bit-equivalence. Names of static format singleton fields+148/+170, complete external field semantics, and all format extensions remain bounded gaps.

## Exact metadata closure

Separate guarded decoding receipts [renderer metadata](NATIVE-RENDER-BACKEND-METADATA-2026-10-18.json) (SHA25697a7b0496f16d51cb3df8110c669d00107f496ef63180c685acbd0779f8a8691) and [feature metadata](NATIVE-RENDER-BACKEND-BOOLEAN-METADATA-2026-10-18.json) (SHA2565b2342564880e31dd2620cf409186e2759793862d002e71cf3ca2890ecd9dee6) close the five requested identities and one feature flag:
- +128 is the exact original-JAR LegacyWriter method already listed. Native→Java linkage is now proved by metadata and original-JAR declaration, beyond matching call shape.
- +158 is com/mojang/blaze3d/vertex/BufferBuilder.f_85658_:Lcom/mojang/blaze3d/vertex/VertexFormat;.
- +160 is com/mojang/blaze3d/vertex/VertexFormat.f_86014_:I. No semantic rename of the SRG field without exact dependency-class evidence.
- wrapperA is net/caffeinemc/mods/sodium/client/render/vertex/buffer/DirectBufferBuilder.builder:Lnet/caffeinemc/mods/sodium/client/render/vertex/buffer/BufferBuilderExtension;.
- wrapperB is me/jellysquid/mods/sodium/client/render/vertex/buffer/SodiumBufferBuilder.builder:Lme/jellysquid/mods/sodium/client/render/vertex/buffer/ExtendedBufferBuilder;.
- +188 is original-JAR staticboolean com/elfmcys/yesstevemodel/O000O00Oooo0O00oO0oo0Oo0.o0OOooo0o0OO00OoOOOo0o0O:Z. Fresh original-JAR parse of its initializer method shows ModList.get at0, literal acceleratedrendering at3, isLoaded at5, putstatic thisexactfield at8. The source ARCompat.INSTALLED matches. Thus when all extended-format gates pass and integerfield==56, the cached Accelerated Rendering installed boolean selects5 when true and2 whenfalse. This does not claim it is currently installed, nor that the cached flag updates dynamically.

The external Minecraft/Sodium dependency classfiles are absent from supplied YSM/JDK artifacts; decoded strings establish referenced identities, not installed-version availability or external implementation semantics. The separate decoder receipts explicitly use guarded synthetic metadata callback frames and do not resume a real renderer/JVM. This static cohort itself uses no emulation.
