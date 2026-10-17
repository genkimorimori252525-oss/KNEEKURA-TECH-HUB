# Java audio adapters and decoder pool boundary

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.33 declarations across Vorbis/Opus stream adapters, decoder pool/holder and Java Opus wrapper;192 integrity checks/10 negative controls. Native codec methods are declarations without Code. No decoding, audio playback, target/Netty/native execution, mapping promotion or independent semantic review.

## Vorbis bridge and mono conversion

Vorbis adapter `o0OO00ooo0OooO0O00o0oOoo` wraps supplied buffer in Netty input stream and constructs external OggAudioStream. It accepts channels1 or2, advertises16-bit signed mono little-endian output at the underlying sample rate, and retains optional PCM builder. Unsupported-channel rejection follows external stream construction without local cleanup covering that failure.

read returns empty if eof or closed, otherwise requests channels*size bytes from the external stream. Empty result submits the PCM cache first, sets eof, and returns that buffer; submit failure can precede eof assignment. EOF does not itself close OggAudioStream. close calls underlying close before setting closed, with no finally assignment.

Stereo data uses a native-order duplicate for input. Writable input reuses a duplicate with limit=remaining/2; read-only input allocates a new output buffer. It takes an output slice BEFORE writing, then reads pairs of shorts and writes rounded arithmetic means as shorts. No local multiple-of-four-frame check precedes the do/while pair reads. Buffer position/alignment/order supplied by the external decoder must satisfy this algorithm; actual PCM correctness was not tested.

For stereo the returned slice starts at position0 and the cache receives its duplicate. Mono forwards the external buffer and duplicates it for cache input. This narrows the [cache buffer-position caveat](SOUND-DATA-PCM-CACHE-RECOVERY-2026-10-17.md): a zero-position slice is supplied in stereo/Opus paths, while the mono external result's position was not established here.

## Opus bridge and returned slice lifetime

Opus adapter `OOoo000Oo0ooooOoO0OOOoo0` obtains a pooled decoder, allocates a Netty buffer with capacity48000*2, explicitly retain()s it, then initializes decoder. No local exception cleanup covers allocation/init failure. It advertises a static48000Hz16-bit signed mono little-endian format.

read(size) returns empty for size0/eof/closed. Otherwise it grows capacity if needed, obtains nioBuffer(0,size), and asks the Java decoder wrapper to decode into a duplicate. len0 submits the PCM cache; negative len logs an error; either then sets eof and returns empty. Positive len returns dst.slice(0,len), and cache input is result.slice(). These slices start at0 but share the backing buffer reused by future reads; no independent audio-data copy or arbitrary retention guarantee is made.

close performs one buffer.release, returns the decoder to the manager, then marks closed. A preceding failure can skip the flag assignment. Constructor retain and this release are not, by themselves, proof of final Netty reference count zero; allocation/provider ownership was not executed. EOF does not invoke close. Joined with [looping behavior](SOUND-INSTANCE-LIFETIME-RECOVERY-2026-10-17.md), dropping an exhausted stream reference before calling clear must not be described as automatically closing these adapters.

## Decoder Java/native boundary

Wrapper `ooOo0oOo0o000O00oOOO0oo0` creates a native handle and rejects0. init requires a direct input buffer, passes a slice to native init, rejects a false result, then retains the supplied original buffer in a volatile field. decode requires direct destination and passes a slice to native decode. Neither operation advances the caller's cursor through its own slice construction.

reset invokes native reset before clearing retained input. destroy invokes native destroy but does not locally zero the final handle or add an idempotence flag. Null/buffer-range/native status semantics beyond the explicit Java checks are not proven. None of these native methods was called.

## Pool reuse and expiry are tick based

DecoderManager `o0ooOoO0o0o0O0oooOOoOOOO` synchronizes on its LinkedList. Acquire removes the newest returned decoder from the tail; if empty after removal it clears NEXT_FREE_TIME. With no pooled decoder it creates one outside the lock. Return resets the decoder BEFORE entering the lock, appends a holder with current ClientTickEvent count+200, and sets the next expiry only when the pool was empty. No duplicate-return guard or maximum size appears locally.

Tick skips when next time0 and only enters expiry processing when currentTick>nextTime (strictly greater). Within the lock it checks oldest holders, destroys those with freeTime<=currentTick, then removes them; a destroy failure can leave that holder in the list, though monitor release is protected. First unexpired holder sets the next time, or draining clears it. This is200 accepted client ticks plus the strict outer gate, not a guaranteed wall-clock10seconds. The [client tick service order](RENDER-SELECTION-RECOVERY-2026-10-17.md) supplies the upstream counter context.

## Reuse conclusion

The Java chain now separates source bytes, decoding request, PCM accumulation, cache publication, loop reopening, stream close and decoder retirement. Preserve those boundaries and input-buffer assumptions. Native codec correctness, reference-count final release, real-time playback and threading of the external engine remain unverified. Further work should target actual lifecycle callers or another unresolved Java seam, not execute native decoding to inflate coverage.
