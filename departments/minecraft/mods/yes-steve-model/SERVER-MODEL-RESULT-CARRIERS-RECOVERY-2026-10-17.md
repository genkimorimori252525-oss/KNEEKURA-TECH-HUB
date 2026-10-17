# Server model/result carriers and one-use raw-array expansion

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twenty-two declarations across ReloadModelResult `oO0OOO0O0O0O00O0OOooOooO`, SyncModelResult `oOoOO0OO0o0Oooo00OOOOoO0`, ServerModel `oOoOOo00o00O0ooooOOO0oO0` and ServerPlayerModel `oOoo00OOoO00O0oOOOO0000o`. No target constructors, getters, native routine or external integration was executed.

## Result container construction matters to publication

ReloadModelResult stores success and casts/retains the supplied message as Component. A null models argument selects Object2ReferenceMaps.emptyMap; otherwise it calls ImmutableMap.copyOf. A null auth-name array selects ObjectSets.emptySet; otherwise ImmutableSet.copyOf. Getters return those fields. This is not a simple direct retention of the caller's mutable map/array, nor a deep clone of ServerModel/Component elements. The factory call does not promise a newly distinct instance for every already-immutable input.

SyncModelResult similarly retains its success/error Component, calls ImmutableSet.copyOf on allPlayerIds, and preserves null playerErrors versus an ImmutableMap.copyOf result. Its flag and error collections are stored independently: the constructor does not enforce success=>empty per-player errors. Therefore an overall flag alone must not be used to certify every recipient's application. Native production of these result values remains outside the evidence.

The [server manager](SERVER-MODEL-SYNC-JAVA-RECOVERY-2026-10-17.md) assigns these result map/set references during publication. Container copy factories and manager reference assignment are two different steps; neither makes all nested model state immutable.

## Server player data wrappers

ServerPlayerModel transforms animation entries to sets through ObjectOpenHashSet.of and ObjectSets.unmodifiable, collects them into a map, wraps a new Object2ObjectOpenHashMap through Object2ObjectMaps.unmodifiable, and wraps ObjectArrayList.of(textures) with ObjectLists.unmodifiable. Getters return those wrappers. These calls record requested collection restrictions; they are not proof that every external factory detaches every supplied array or recursively copies all reachable objects. No Fastutil runtime was loaded to test that broader ownership claim.

## Raw entity-match arrays are not ordinary repeatable getters

ServerModel stores its name, player model, metadata and flags, allocates two HashSets, and retains raw projectile/vehicle Object[] arguments. Each corresponding getter copies its raw field into a local, immediately takes arraylength, iterates String[] elements through the entity-ID matcher and addAll, then sets the raw field to null INSIDE the loop. It returns the retained mutable HashSet after the loop. There is no initial null check or explicit "already expanded" fast path.

Consequences of the exact body, conditional on input and no outside reinitialization:
- Empty nonnull raw array: the loop never clears the field, so repeated calls can continue returning the empty/current set.
- Nonempty array whose iteration completes (even if no entity IDs match): the local array supports the rest of that first loop even after the field is cleared; a subsequent invocation reaches arraylength on the null raw field, which would raise NullPointerException under these conditions.
- A throwing matcher/addAll can leave partial set changes; no transactional rollback is present.

These are static Java control-flow conditions, not a reproduced in-game exception or proof of the native producer's actual arrays. JNI/reflection/external writes are not excluded.

## Actual Java reference boundary

The declaration-validated [955-class inventory](SERVER-ENTITY-SET-CALLERS-EVIDENCE-2026-10-17.json) records seven method/field sites across four caller methods: constructor/getter field accesses and one direct vehicle-set getter call. It finds zero direct projectile-set getter calls and zero matching bootstrap target references. The vehicle call is in the optional TopPlugin comparison predicate owner `oooO000OOOOOOo000OOooo0o$Oo0Oo0o00O00Oo0OOoOOoooo`, taking Entity and ServerModel and checking set membership. It is not another ClientModel map getter.

The Java field writers found here are the constructor assignments and getter clears. That does not rule out native reinitialization. The optional integration's installation, active registration, repeated invocation and runtime outcome have not been verified; the predicate's existence alone is not a live failure receipt.

## Reuse

Do not equate immutable outer containers with immutable nested models, null error maps with empty ones, or getter names with idempotence. Preserve these conditions when reading the original; no automatic bug fix or native behavior reconstruction was introduced. Central669 mapping remains unchanged and independent semantic review is NOT_RUN.
