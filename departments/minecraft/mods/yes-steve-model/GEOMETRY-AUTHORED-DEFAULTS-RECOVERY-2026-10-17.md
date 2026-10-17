# Authored geometry defaults and Java state construction

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. New capture:19 declarations across GeoBone and GeoModelProperties counterparts,110 integrity checks/seven negative controls. Existing GeoModel, GeoModelState and bone-state bodies are reused, not recaptured to inflate progress. No target/native execution or independent semantic promotion.

## Authored data is stored, not validated here

GeoBone counterpart `oO0OO0OooO0Oo0OoO0oOooo0` stores the supplied name and pooled name, three distinct visibility booleans, three pivot floats and three rotation floats. No parent pointer or parent index is declared in this Java carrier. The constructor performs no local coordinate conversion, finite check, bounds check or visibility normalization; StringPool is a separate dependency.

GeoModelProperties counterpart `OOoOoO0000OooOOoO0ooOOOo` stores its identifier, texture height/width, visible-bounds height/width and the supplied double[] offset reference. The four numeric getters box their stored doubles; the offset getter returns the same array. No local positive-size/finite/offset-length validation or defensive clone is present. A producer may have validated inputs elsewhere; this dossier does not establish that producer behavior.

## Exact getter-use inventory

A separate fixed955-class scan targets all17 nonconstructor getters from these two carriers. It finds15 direct calls in three method bodies and zero bootstrap references. All observed calls target GeoBone getters: the bone-state constructor, model-state constructor and processor registration method. The exact areCubesHidden getter and all six GeoModelProperties getters have no direct/bootstrap callers in this bounded inventory.

This is not proof those fields are unused in rendering: native, external, reflective and alternate symbolic-owner access are not closed. In particular, visible-bounds declarations do not by themselves establish an active Java frustum-culling implementation. Preserve the native boundary instead of inventing a Java reader to explain a name.

## Initial state and indexed storage

The already-captured GeoModelState constructor allocates fresh input arrays at12 floats per sorted bone and output arrays at4 floats per bone. Each index creates a mutable bone state and inserts it under the pooled name. Duplicate names would replace the map entry while index-based array allocation still reflects every input element; the body does not reject duplicates or sort a hierarchy. This is a conditional input constraint, not evidence of a malformed real model.

The bone-state constructor stores caller arrays/offsets, copies pivots, writes hidden and children-hidden, copies authored rotations, and writes scale1 on all axes. It does not initialize position slots, tracking or output-pivot slots. Those are initially zero on the fresh arrays allocated by GeoModelState, but callers supplying reused arrays cannot infer that from the bone-state constructor alone. It creates a Vector3f initialRotation and returns that same mutable vector from its getter. Authored rotation values are not converted in this constructor.

GeoModel initializes its public initialState by constructing a GeoModelState and taking its inputState reference. Its getter returns the retained array. This is not a deeply immutable template. The existing [bone commit dossier](BONE-COMMIT-QUEUE-RECOVERY-2026-10-17.md) separately shows snapshots subtracting and committing the initial rotation; do not mix relative snapshot rotations with absolute stored rotations.

## Locator and rendering boundary

The [locator dossier](LOCATOR-MATRIX-PREPARATION-RECOVERY-2026-10-17.md) already records that names are supplied in hierarchy order, pooled, then resolved without filtering missing bones. There is no Java parent-graph recovery or cycle validation in those constructors. Parent hierarchy and native resource validity cannot be reconstructed from the sortedBones label alone. GeoModel's native-ID cleanup registration remains a declaration/call boundary, not permission or evidence to allocate/free target-native resources.

Reuse consumers should distinguish authored values, mutable runtime state, relative snapshots and native-produced output pivots. A final field or read-only list does not make nested objects, arrays or caller-provided hierarchy valid and immutable.
