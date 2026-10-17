# Sound dispatch to resource lifetime

Task-scoped navigation only. No ordinary startup audit, tool installation or audio execution is required. Exact artifact2.6.5 Forge1.20.1; central map669 unchanged, recent findings PRIMARY_STATIC_REVIEW_ONLY.

1. [Molang emission, ID replacement and manager scopes](PARTICLE-SOUND-DISPATCH-RECOVERY-2026-10-17.md)
2. [Actor instance, future and loop lifetime](SOUND-INSTANCE-LIFETIME-RECOVERY-2026-10-17.md)
3. [Sound data, weak holder and PCM cache](SOUND-DATA-PCM-CACHE-RECOVERY-2026-10-17.md)
4. [Vorbis/Opus Java bridge and decoder retirement](AUDIO-DECODER-JAVA-BOUNDARY-RECOVERY-2026-10-17.md)

## Resource-holder bridge reuses existing evidence

[MODEL-READINESS-SCOPE-EVIDENCE-2026-10-17.json](MODEL-READINESS-SCOPE-EVIDENCE-2026-10-17.json) already captures CustomEntity `oOo00OoOO00O000ooO0Oo00o`. Its onLoadModelContainer counterpart registers a ModelSoundHolder for the newly selected model and stores it on the resource holder before reading the model's defer handler.

Its custom sound getter first dereferences resourceHolder.soundHolder (without a separate resourceHolder-null guard). It looks up the supplied name in current model assets and requires nonnull SoundData, nonnull buffer and format!=UNDEFINED. It captures the holder and SoundData into the provider lambda, returning Optional.empty otherwise. This provider later opens using those captured references; it does not re-query the animatable's newest model at stream-open time. Replacing/resetting the animatable holder therefore is not, by itself, proof of closing an already captured provider or an active engine stream.

The base AnimatableEntity default returns Optional.empty. The sound manager's custom-name branch requests the provider and creates a CustomSoundInstance before its asynchronous engine play request. Holders/readiness, provider capture, stream opening and audible output are distinct stages. Successful lookup does not prove decoder input validity or native loading.

These bridge claims add no new captured-method count; they refine semantic reading of the existing snapshot. The fixed sound batch below explicitly includes that older anchor.

## Bounded verification and limits

[SOUND-LIFECYCLE-CHECKPOINT-2026-10-17.json](SOUND-LIFECYCLE-CHECKPOINT-2026-10-17.json): five cohorts (three new lifetime/cache/adapter groups plus prior dispatch and model-readiness anchors), all PASS in0.921seconds.0 overlapping snapshots is not independent corroboration. Existing frozen checkpoints remain unchanged.

Run tools/sound_lifecycle_checkpoint_ysm_265.py explicitly with --jar, --source-root and --out when this seam changes. The separate9-case JDK cache/buffer contract checks only language/library behavior, not target audio. Native codec methods remain declarations; no sound files, decoding or playback were invoked.

Do not collapse stopped/closed/eof, future success, PCM cache publication or pooled decoder expiry into one completion boolean. Preserve buffer cursor and ownership constraints, signed/zero input assumptions and exception order when reusing these ideas. Next connected Java work should follow actual effect cleanup/reset callers rather than repeating the underlying decoder boundary.

Later cleanup extension: [sound keyframes and exact callers](SOUND-KEYFRAME-CLEANUP-RECOVERY-2026-10-17.md), with10 direct stop/trim/reset calls and no claimed external closure. This postdates the fixed5 checkpoint above.
