# Full-property application versus model reset — 2026-10-17

## Status and bounds

Primary static review of the fixed official JAR, SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
Comparison source is YesSteveModel/YesSteveModel at
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`; whole-source equivalence remains
NOT_ESTABLISHED. The lifecycle snapshot selects 16 methods across eight owners.
Full owner declarations/bootstrap records support inherited call resolution;
they do not make every declared method a reviewed semantic mapping.

No independent semantic review, game execution, packet delivery test or native
implementation analysis. Central map remains unchanged at 669. The result is a
conditional ordering concern to test, not a demonstrated in-game defect.

## Joined inherited path

1. SyncModelInfo capability consumer updates model/texture before properties.
2. Its player-capability receiver inherits updateModelAndTexture from
   `o0O0oOooOo0OoOo0oOo00O00` (CustomHumanoidEntity). That body sets initialized,
   stores texture, calls inherited updateModelId at offset 11, then texture update.
3. CustomEntity `oOo00OoOO00O000ooO0Oo00o` updateModelId stores the ID and checks
   model/container state immediately. A holder/model/fallback identity change
   loads geometry only when the holder is loaded. Unready holders can defer
   the replacement; same-model/same-fallback state need not reload geometry.
4. AnimatableEntity `o0000OoOooO0oo0o0oooo0Oo` geometry load calls virtual
   `oOOOo0OOO0ooooo0O00OO0o0()V` (resetGeoModel) before rebuilding geometry,
   controllers and animation processor. The selected declaration hierarchy is
   PlayerAnimatableCapability → CustomPlayerEntity → CustomHumanoidEntity →
   CustomEntity → AnimatableEntity.
5. Each overriding reset delegates to the next parent. Player capability clears
   roamingStruct first. The base reset invokes the tracker's virtual reset at
   offset 42. PlayerStateTracker `ooOO000o0O0OOOoO0Oo0o0Oo` clears effects and sets
   remote flight, exp/health/maxHealth/food, axes and shield cooldown to zero/false.
   Its localPlayer identity and static yaw history are not reset by this method.
6. Player capability onLoadGeoModel can reconstruct its roamingStruct from the
   cached per-model variable map. This is not replay of the scalar property packet.

## Three different normal sequences

- Ready replacement: model update → geometry load/reset → property application.
  The snapshot can repopulate the tracker after this reset on the ordinary path.
- Same model without reload: no implied tracker reset. Only fields whose presence
  bits are set are overwritten by the property handler. A full flag alone does
  not clear omitted scalar fields, as documented in the producer/query cohorts.
- Delayed replacement: model update defers geometry → property application → a
  later readiness-triggered geometry load/reset. If this sequence occurs and no
  later property application intervenes, the earlier scalar values are cleared.
  This implication follows from the ordering, but actual occurrence/duration,
  later full resends, native/external callbacks and visible effect are untested.

Do not turn the third case into a claim that every delayed model loses state or
that every full snapshot is incorrect. It supplies a precise runtime test case:
record readiness and model identity, applied packet masks, tracker reset, query
reads, subsequent messages, and both local/remote player roles on one timeline.

## Local roaming reload and extra animation ordering

DispatchServerDrivenProperty's capability callback applies extra-animation
commands first, roaming changes second, scalar tracker fields last. A first local
full roaming initialization for the current hash may call reloadGeoModel; remote
full roaming replacement does not take that same reload branch. The local reload
therefore resets tracker state before the callback's final property application,
which repopulates present scalar fields on normal completion.

CustomPlayerEntity reset also clears extra-animation playback/dirty flags and
sets its stored name to `idle`. An extra-animation command applied earlier in the
same callback is not automatically replayed by the shown tail. Whether a valid
animation command and this first-local-roaming reload coincide in a running game
is a separate test question; no patch or runtime bug claim is made here.

## Closed direct-write inventory

`PROPERTY-STATE-WRITERS-EVIDENCE-2026-10-17.json` scans all 955 class files for
PUTFIELD references to PlayerStateTracker Z/I/F fields. It finds 19 sites in three
methods: constructor (localPlayer), reset, and updateServerDrivenProperty.
One direct invoke reference to the property-update descriptor is found, in the
Dispatch callback. This is a fixed-JAR direct-reference inventory only: reflection,
native code, external mods and effects-map mutation are outside this scalar scan.
It does not assert a closed runtime universe or prohibit later ordinary packets.

## Verification

- Lifecycle tool: `tools/property_reset_lifecycle_ysm_265.py`, with --jar,
  --source-root, --evidence and --out. 119 checks, 14 corrupted fixtures rejected.
- Write inventory: `tools/property_state_writers_ysm_265.py`, with --jar,
  --evidence and --out; --capture regenerates evidence. 2 checks, 6 corrupted
  fixtures rejected. All 955 classes visited; 19 writes/3 methods/1 apply call.
- These are byte/source/operand integrity checks, not runtime reproductions.

Next: inventory ordinary full-resend/dirty-mark triggers and their Java callers
before estimating whether delayed-reset state can persist. Preserve the native
boundary and distinguish absence of a direct call from absence of all behavior.
