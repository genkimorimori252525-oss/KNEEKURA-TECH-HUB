# Struct copy contracts and roaming-change bookkeeping

Primary static review; independent review NOT_RUN. Exact artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Thirty-three declarations
across Struct, HashMapStruct, Vec3fStruct, LocalRoamingStruct and RemoteRoamingStruct.
No networking, target execution or map promotion. Five source files are pinned.

## copy does not promise the same ownership for every Struct

Struct declares get/put/copy without an implementation-level isolation guarantee.
HashMapStruct's ordinary constructors allocate a property map and record a boolean
right-value flag. copy with that flag true constructs a new Struct wrapper around
the SAME property map; the returned wrapper's flag is false. With flag false it
first constructs a new PooledStringHashMap from the existing map. There is no
explicit recursive value-copy loop in this Struct method. Do not promise deep
copy solely from the interface name; delegated map-constructor behavior is a
separate boundary. The original right-value flag is not consumed/reset by copy,
so repeated copies of that original wrapper can share the same map.

Vec3fStruct dispatches pooled x/y/z names to abstract float getters, returns null
for unknown names, ignores putProperty and returns this from copy. It is a
read-only property interface, not necessarily a frozen vector snapshot: subclasses
supply the getters and can observe changing backing state.

Both roaming copies build a new HashMapStruct(true) and iterate their current
float entries into it. This snapshots the scalar entries on that path, then the
right-value sharing rule can apply on a subsequent assignment copy. No concurrent
snapshot consistency or foreign-storage thread safety is established.

## Local value mutation precedes dirty/change tracking

LocalRoamingStruct.putProperty converts through ValueConversions.asFloat, writes
the value map, then compares the returned old float to the new float. Equality
returns immediately before names or dirty tracking. Therefore map mutation and
change notification are distinct operations; an insertion with an equal returned
old value does not necessarily add a name/notification on this path. Do not assume
an arbitrary supplied map's default-return value without checking its construction.

For unequal values it adds the name, checks names.size<=64, then writes the changes
map and sets dirty=true. Over-limit return occurs AFTER the value-map write and
name addition. MAX_SIZE64 is therefore not a hard cap on all stored values in this
method, nor a universal rejection of an assignment. MAX_NAME_LENGTH32 is declared
but is not checked by this integer-key setter. Other producers/serialization may
have their own validation; no network safety claim follows from these constants.

popChanges returns the existing changes object, replaces it with a new accumulator
using the same model hash and the prior change-count capacity, then clears dirty.
It does not clear the main values or names set. Its result is not a live view of
the replacement accumulator. Constructor retains the supplied values map and
initializes names from its key set; aliasing/caller mutation remain relevant.

## Remote struct behavior

RemoteRoamingStruct retains its supplied float map, converts writes via asFloat,
and updates batches with putAll. It has no LocalRoamingStruct-style dirty or size
gate in these bodies. This describes the Java storage wrapper, not authentication,
packet validation, delivery or synchronization. Those consumers are unverified.

## Verification and continuation

192 static checks pass;12 missing/corrupt-evidence controls reject copy branch,
local equality/64-boundary and invented update handlers. This is a post17-cohort
checkpoint addition and should not be silently folded into that fixed receipt.
Mapping669 remains unchanged; whole-source equivalence and independent semantic
review remain unproven. Next inspect pooled-name/map wrappers and actual roaming
change consumers, preserving the distinction between local storage mutation and
what is selected for synchronization.
