# Sound-data ownership and Java PCM cache

PRIMARY_STATIC_REVIEW_ONLY. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.35 declarations across data, holder/cache record, builder, PCM stream and enum/switch support;214 integrity checks/13 negative controls. No original sound files, audio playback, target/provider/Netty/native decoder execution, central mapping promotion or independent semantic review. Separate JDK-only checks are bounded API models.

## Copy once, expose retained data later

SoundData `ooOooOoo00oo0ooOOoOOo0oo` copies the supplied buffer's remaining region using duplicate views. Format code2 allocates direct storage, other codes heap storage; null remains null. The duplicate put leaves the original source position and stored destination position unchanged. It maps1→VORBIS,2→OPUS,otherwiseUNDEFINED and retains supplied sample rate/count without local range validation. The getter returns the stored mutable ByteBuffer, not a new duplicate/read-only view.

## Model holder has identity keys and weak values

SoundDataManager `o0OOOoOoO0oO000Oo0OOoO00` asserts render-thread access on register. Its IdentityHashMap strongly keys model identities and weakly references holders. A live holder is reused; otherwise a new holder is created and a cleaner callback eventually submits model-key removal through Minecraft.execute. That callback removes by model key without comparing the current holder generation. If a replacement entry exists before an older callback runs, removal is not locally guarded against that replacement. Actual GC/executor ordering is not demonstrated.

The holder's PCM cache hit returns PcmAudioStream with a duplicate of the cached buffer and the same segment-list/format references. Duplicate buffer cursors are independent but bytes are shared. Cache submission constructs16-bit signed mono little-endian AudioFormat at the data's sample rate, puts the cache entry, then removes the build marker.

## Build eligibility uses integer duration and contains(value)

On a cache miss, eligibility computes samples/sampleRate with long integer division and compares<=4. This is not a floating duration<=4.0 test; positive durations below5seconds can truncate to4. No sample-rate-zero guard exists in this local calculation.

The marker test at61 invokes ConcurrentHashMap.contains(soundData), NOT containsKey. The map stores SoundData keys and a separate Object placeholder value. The [JDK-only contract](tools/PcmCacheJdkContract.java) confirms contains checks values, so a present key with a distinct placeholder does not satisfy that test. There is also no atomic putIfAbsent operation in this sequence. Do not claim duplicate-build exclusion based on the map's name or concurrency-safe container alone. Actual duplicate requests/resource impact are not measured.

An eligible path constructs BuildingPcmCache then writes a marker before selecting VORBIS/OPUS stream construction; unsupported format throws after that point. Decoder construction and failure cleanup are outside the reviewed Java holder contract. No decoding was performed.

## PCM accumulation mutates the supplied buffer

Builder `oOO0oOO0o0O0o0000oO0o0o0` allocates pooled direct capacity from `(int)samples * 2` (cast before multiply), retains a mutable segment list and starts uninvalidate. putPcm only acts while not invalidated and writable bytes>0. It chooses len=min(writable,source.remaining), calls source.limit(len) on the ORIGINAL supplied buffer, writes that buffer to Netty and records len.

limit(len) is an absolute limit, not position+len. The JDK-only example position4/limit10 with len6 leaves only2remaining after limit6. Thus arbitrary nonzero-position input is not guaranteed to copy the recorded segment length. Actual decoder-supplied positions and Netty behavior were not exercised here, and no corruption outcome is asserted. The call also mutates the input limit rather than using a duplicate.

submit marks invalidated BEFORE allocating/copying the completed buffer, releases the pooled buffer, then hands the new buffer/segments to the holder. No finally protects release/marker removal across all exceptions, and no separate abort/close method is declared in this builder. These are ownership boundaries for reuse, not observed leaks.

## Cached PCM read ignores requested size

PcmAudioStream `O0oo00O0OOOo000oOo0ooOOo` requires channels==1, but does not locally validate all format/segment/buffer invariants. It retains inputs. read(size) ignores size and returns the next recorded segment via buffer.slice(offset,segmentLength), then increments index/offset. No local negative-length/bounds check precedes the JDK slice; its own exceptions remain possible. EOF or closed returns a shared zero-length buffer. EOF does not itself set closed. close only marks closed; it does not free the shared cached storage.

## Verification and continuation

[PCM-CACHE-JDK-VERIFICATION-2026-10-17.json](PCM-CACHE-JDK-VERIFICATION-2026-10-17.json) records9 checks of standard JDK contains, limit, duplicate-copy and integer-division behavior. It does not load YSM, Netty or audio libraries. The exact artifact auditor separately checks the captured calls/operands. Continue only enough Java decoder-adapter reading to establish buffer-position/EOF/close contracts; do not run native codec or protected-model paths. The [looping-stream dossier](SOUND-INSTANCE-LIFETIME-RECOVERY-2026-10-17.md) retains its separate dropped-reference cleanup caveat.
