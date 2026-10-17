# Sound-instance lifetime and looping-stream ownership

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.19 declarations across MinecraftSoundInstance, CustomSoundInstance and LoopingAudioStream;114 integrity checks/10 negative controls. No sound playback, target/provider/native decoder execution, mapping promotion or independent semantic review. This follows [Molang sound dispatch](PARTICLE-SOUND-DISPATCH-RECOVERY-2026-10-17.md), not a replacement for its emission/ID gates.

## Actor and volume lifetime

MinecraftSoundInstance `Oo0OoO0O00o00oOOooo00OOO` retains the supplied Entity strongly and initializes position from its coordinates. It uses SoundSource.PLAYERS and an unseeded random source. Each tick updates volume=configuredVolume*current configured percent/100, then stops on entity.isRemoved; otherwise updates position. Setting configuredVolume does not directly update the active volume field until this tick path. There is no explicit current-level/session comparison or liveness check beyond removed in this body.

Pitch and looping setters store fields without local clamp. UI mode sets attenuation NONE and relative true but does not zero coordinates or disable later actor-position updates. Audible behavior depends on the external engine.

setStopped first invokes inherited stop, then submits a Minecraft.execute callback asking SoundManager.stop(this). Entity-removed tick calls inherited stop directly, not this two-stage wrapper. Neither path locally closes a custom stream; engine cleanup must be established separately before asserting resources freed or immediate silence.

## Deferred custom-stream creation

CustomSoundInstance `o0000oo0oOO00O00O0o0o0O0` retains provider and a volatile latest stream reference. getStream creates a new CompletableFuture and submits a client-executor Runnable; its SoundBufferLibrary and Sound arguments are unused. The Runnable chooses a LoopingAudioStream when its boolean argument is true, otherwise provider.openStream. It assigns the stream field before future.complete. Throwable in that Runnable completes the future exceptionally; a failure of the outer execute call itself is not inside that handler.

There is no future-cancellation or stopped-state check before opening, no close when complete returns false, and no local close of a previously retained stream before replacing the field on another getStream call. These are conditional ownership limits, not proof that the sound engine issues duplicate/cancelled requests. Volatile publication of one reference does not make provider/resource lifetime transactional.

isStopped with no stream delegates to the superclass. With a closed stream, it requests superclass setStopped if needed and returns true; with an open stream it returns superclass status. Closed-stream detection is a read-side side effect, not just a pure boolean accessor.

## Loop EOF clears the reference before cleanup

LoopingAudioStream `OOO000o0OO0O0Oo0oo00ooOO` opens one provider stream and saves its format during construction. It catches/rethrows IOException and UnsupportedAudioFileException from the open operation; the subsequent getFormat is outside that catch.

read(size) reads the retained stream when nonnull. On an empty result it writes the stream field null at27, then calls clear at31, then opens a replacement. Because clear only closes a nonnull field, that particular clear cannot close the just-dropped previous reference. The earlier stream might independently close at EOF, but that is a provider-specific question; do not silently call this guaranteed release or an observed leak.

The reopen/clear block catches Throwable and returns a shared zero-length buffer on failure. The initial read and the second read after reopening are outside that catch. If the replacement also returns empty, clear is called and the empty buffer returned; there is no unbounded retry loop in one read call. Format remains the first stream's retained AudioFormat, with no equality check on replacement format.

close sets volatile closed=true BEFORE clear. clear calls stream.close then sets field null; a close exception can leave a nonnull stream with closed=true. clear alone does not set closed, and read does not test closed directly. EOF/reopen failure can thus leave stream null while isClosed remains false; whether the external engine then stops is not determined here. No concurrent-close safety guarantee follows from only the closed field being volatile.

## Reuse and next boundary

Keep future completion, engine stop, stream EOF, stream close, provider reopening and actor removal as separate lifecycle events. Before reusing a loop wrapper, specify ownership when replacing references and what cancellation does. Continue provider/resource-holder lifetime only within Java-visible contracts; native decoder contents and actual audio output remain outside scope. This cohort is later than the client-session checkpoint.
