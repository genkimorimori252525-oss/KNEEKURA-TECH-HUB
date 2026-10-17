# Touhou Little Maid location adapters are live views

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Owner `oOoOOOo0o0oO0OOOo0ooOOo0` plus anonymous $1/$2 implementations. 31 declarations,174 integrity checks and eight negative controls. The dependency's runtime, class loading and rendered attachment behavior are not executed or established.

## Bone conversion

The helper allocates an anonymous ILocationBone retaining the supplied GeoBoneState. All12 rotation/position/scale/pivot getters delegate to that retained state at access time, with no unit/sign conversion, copied pose vector or captured numeric snapshot. Pivot getters use the bone's authored pivot getters, not native output absolute-pivot getters. This distinction matters for any external attachment matrix consumer.

The existing bone-state getTlmBone method caches the helper's result lazily in an Object field. No local synchronization or optional-mod availability test appears in that getter. This describes the local boundary, not a claim that an unavailable dependency is reached in normal gameplay. Different surrounding callers may apply availability gates.

## Model conversion and collection ownership

The model wrapper retains GeoModelState. Each location-list getter converts the current corresponding list using stream.map(...).toList(). The mapper casts every IBone to the concrete GeoBoneState, obtains its cached TLM wrapper and casts to ILocationBone. It does not accept arbitrary IBone implementations merely because they implement the interface, filter null entries, or handle exceptions per bone.

The resulting list is a newly produced unmodifiable Stream.toList container, but its elements are live wrappers. Extra left/right hand getters create a new mutable outer ReferenceArrayList and append each converted inner list in input order. Container creation is not deep pose isolation and is not a synchronized snapshot of concurrently changing bones.

backpackBones checks whether the backpack list is empty; only then it converts the elytra list. A nonempty list containing an unresolved/null bone does not trigger this fallback and can fail in the mapper. There is no coordinate fallback or concatenation of both groups. Other declared model routes cover left/right hand, extra hands, left/right waist, pistol/rifle and head; do not invent additional routes from other model-state fields.

The existing GeoModelState getter lazily caches the model wrapper itself. Wrapper caching and per-call list creation are separate: repeated calls can reuse individual live bone adapters while rebuilding list containers.

## Relation to existing evidence

[Locator matrix preparation](LOCATOR-MATRIX-PREPARATION-RECOVERY-2026-10-17.md) documents the already-captured GeoModelState lazy getter and unresolved-name behavior. [Bone state](BONE-STATE-RECOVERY-2026-10-17.md) retains the historical AnimatedGeoBone mapping/source distinction. This new cohort fills the concrete bridge bodies without changing those mappings or proving third-party availability, loader behavior or actual visuals.
