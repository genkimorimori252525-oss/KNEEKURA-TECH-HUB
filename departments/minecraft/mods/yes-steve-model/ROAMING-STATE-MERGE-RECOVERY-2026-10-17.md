# Player/vehicle roaming state selection and pending merge

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Thirty-two complete methods
across PlayerAnimatableCapability, RemoteStorage and VehicleAnimatableCapability.
Three source records cover two files. No network operation, target execution or
server-authorization claim. Broader captured methods support selected claims below.

## Cached model state versus active roaming struct

The player capability owns a map keyed by model hash. Loading a model container
sets currentHashShort from its info; container reset sets it to0. Geo-model load
selects that hash's storage only when storage.vars is nonnull, constructing a
LocalRoamingStruct for a local player or RemoteRoamingStruct otherwise. Without
ready cached values it sets roamingStruct=null. Geo-model reset also clears that
active struct, not the entire per-model storage map in this override.

hasRoamingStorage checks map membership, not vars readiness. A pending-only entry
can therefore exist without a fully initialized map. Presence/ready/active-model
match must not be treated as the same state.

## Full initialization and incremental updates differ by local-player status

resetRoamingVars creates/fetches the hash's RemoteStorage. For a local player it
accepts a full map only when storage.vars is null. It installs the supplied map,
merges pending changes, and when the hash is current creates local roaming and
reloads the geo model. The reload resets then reconstructs the active struct from
that cached map through the previously inspected load hook; the intermediate null
is not alone proof that initialization was lost. Later full maps for that already
initialized local storage are ignored on this method's branch.

For a remote player, full initialization replaces storage.vars unconditionally,
merges pending changes and updates active roaming only when the hash is current.
The method retains incoming map references rather than copying them.

updateRemoteRoamingVars ignores local-player or empty updates. For remote state
it creates/fetches storage, applies putAll if ready, or enqueues the supplied map
reference otherwise, then attempts vehicle propagation. Pending merge dequeues
FIFO and applies putAll in that order; later updates win ordinary duplicate-key
writes. The vars field is volatile, but that declaration alone does not establish
whole-map/queue thread safety or a lock protecting compound transitions.

## Vehicle propagation and state handoff

Player-to-vehicle updates require current model-hash match, a vehicle and this
player being its first passenger. This is a local propagation predicate, not
proof of server-side message authorization. Vehicle initRoamingVars replaces the
remote wrapper; incremental update lazily creates an empty map if needed then
merges changes. Its preAnimationSetup forwards the struct to the processor even
though the hook receives shouldTick; it contains no separate shouldTick guard.
Processor.putRemoteStruct ignores null and stores nonnull reference in scoped
roaming state, as grounded in the processor dossier.

Player copyFrom uses storageMap.putAll, changes model/texture/disabled state,
then clears the source map and source active roaming reference. It is not a deep
copy of nested RemoteStorage/maps. Exception rollback and lifetime of other
retained references are not guaranteed by this body.

## Checks and next seam

179 static checks pass;12 malformed-evidence controls reject local/remote gates,
vehicle hash test, queue call and invented full-reset finally. Mapping669 and
global source-equivalence cautions remain. This is outside the frozen17-cohort
receipt. Next inspect ordinary client entity-load deferral and server-driven
property application sequencing to connect message arrival to these state APIs,
without treating static declared handlers as evidence of actual delivery.
