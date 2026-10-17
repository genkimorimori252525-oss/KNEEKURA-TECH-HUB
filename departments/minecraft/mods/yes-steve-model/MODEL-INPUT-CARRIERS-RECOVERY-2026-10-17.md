# Model input carriers and retained mutable data

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.31 declarations/seven owners,190 integrity checks/12 negative controls. The carriers are Java input boundaries; native producer validation and actual model loading are not executed or established.

## Builder input ownership

ClientModelData `ooOOOo00o0000o0oO000oooO` directly retains player, projectile/vehicle arrays, common assets, info, avatar map and GUI image map. Its getters return the same objects/arrays. The constructor contains stores, not cloning, null checks, shape checks or immutable wrappers. A source NotNull annotation does not add a bytecode guard.

CommonAssetData `oooOOO0o0O0oOoOO0OoOo0oo` similarly retains sound, user-function and nested-language maps. The later builder derives separate function/event maps but CommonAsset retains the sound/language references, as documented in [composition](CLIENT-MODEL-COMPOSITION-RECOVERY-2026-10-17.md). Separate outer objects do not imply separate sound buffers or language entries.

PlayerModelData `OOooOooOO00O00000oOOO0oo` passes the supplied geometry and controller-file arrays to ObjectArrayList.wrap, stores those resulting Lists, and directly retains the animation-file map and FifoHashMap textures. There is no additional unmodifiable wrapper or array-length check here. This is distinct from the read-only list wrappers used in some GeoModel/controller carriers. The builder's indices0/1 and texture index0 requirements are downstream assumptions, not guarantees supplied by this constructor.

ProjectileModelData `OO0o00OOO0oOOOo0O0Oo0O00` and VehicleModelData `O0O00OoOoo0ooOOOooOOo0OO` each retain their match String[], geometry, optional animation/controller files and texture references without copies. Match normalization, registry tag expansion and conflicting entity-ID selection belong to the later builder/helper paths. This constructor does not prove an array's contents, file compatibility or texture availability.

## Bone animation and particle event carriers

BoneAnimation `o0OOOOooooOO00oOoO0o00OO` stores bone name, pooled name and the exact three supplied List references for rotation, position and scale keyframes. It does not sort or freeze those lists. The already-captured queue activation passes nonempty lists to OrderedSegmentSearcher, which also retains them. Consequently reference sharing spans carrier and searcher; neither constructor by itself guarantees later list mutation is safe for cached cursor/bounds. No mutation or failure was reproduced.

ParticleEventKeyFrame `oOo0o0OoO0OO0oO0ooOOoooO` delegates startTick/eventData to EventKeyFrame, then directly stores effect, locator and script strings. The base narrows double tick to float; this child adds no time scaling, parsing, emission or locator resolution. Presence of a script string is not evidence it is evaluated. The existing [exact particle-list reader scan](ANIMATION-DATA-OWNERSHIP-RECOVERY-2026-10-17.md) remains narrower than a global claim of absent particle support.

## Reuse

Treat these structures as carriers, not validators or deep snapshots. A consumer that needs an immutable cache, reliable ordering or cross-thread snapshot must identify the actual producer/consumer contract rather than infer it from final fields, Native Access comments or source annotations. This work documents upstream behavior without changing protected loaders or adding validations that could alter compatibility.
