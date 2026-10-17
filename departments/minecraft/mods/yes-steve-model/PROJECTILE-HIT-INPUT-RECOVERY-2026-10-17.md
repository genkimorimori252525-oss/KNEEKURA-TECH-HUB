# Projectile, fishing and client hit inputs — 2026-10-17

## Scope

Exact artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, comparison source
YesSteveModel/YesSteveModel `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
22 selected methods across seven owners include nine query callbacks, the compiler
switch-map class, arrow mixin implementation and abstract API/accessor contracts.
Primary static review only; independent semantic review NOT_RUN. No running game,
mixin transformation, projectile spawning, packet send or target execution.
Central mapping remains 669.

## Local hit queries read the global client hit result

hit_target_id and hit_target_type use LocalPlayer variable wrappers, but the
callback bodies obtain Minecraft.getInstance().hitResult rather than raycasting
from their IContext entity. Passing the wrapper guard does not make the callback
a separate per-entity hit test.

ID callback:
- BlockHitResult with MISS returns empty string. Otherwise absent client level,
  absent block registry key or unsupported result also yields empty string.
- A recognized block returns its block registry ID string.
- EntityHitResult returns the hit entity TYPE registry ID, not an entity UUID or
  numeric runtime entity ID, with empty string for an absent key.

Type callback reads the HitResult type and returns `block`, `entity`, or empty
string. It does not perform the ID callback's level/key lookup. An empty ID alone
therefore does not prove MISS; a nonnull block-type result can still have an empty
ID under the callback's other checks. The exact switch helper `YSMBinding$1` is
captured instead of guessing Java enum ordinal values.

These empty-string results describe a reached callback. A rejected typed wrapper
returns Integer 0 instead, as recorded in TYPED-QUERY-GUARDS.

## Fishing and throwable item sources

hooked_in obtains the fishing hook's injected hookedIn accessor and returns the
hooked entity TYPE registry ID or empty string for no entity/key. is_biting reads
the injected biting boolean. These callbacks directly cast to FishingHookAccessor;
they do not contain a local guard/catch for missing mixin application.

throwable_item instead checks instanceof ThrowableItemProjectileAccessor. When
present it calls getDefaultItem and converts that item's registry key to text;
otherwise or for an absent key it returns empty string. This is the projectile's
default item, not necessarily a live item-stack payload or owner inventory item.

## Arrow properties and owner-time cache

on_ground_time and in_ground call IArrowExtraInfo for the shadowed inGroundTime
integer and inGround boolean. on_ground_time performs no /20 unit conversion in
the query body. is_spectral_arrow uses Java instanceof SpectralArrow directly.
shoot_item_id reads a cached string through IArrowExtraInfo, not a fresh inventory
lookup on every query.

AbstractArrowEntityMixin initializes that string to empty. Its setOwner RETURN
injection first checks YesSteveModel availability. For a LivingEntity owner and
a nonnull item registry key it stores the owner's current MAIN-HAND item's ID.
It does not prove that item was the actual firing weapon/projectile source in all
external mods. A later invocation with unavailable YSM, nonliving/null owner or
missing key does not explicitly clear an older cached ID on this shown path.
No runtime stale-state incident is asserted and no corrective code is introduced.

## Exact annotation/refmap join

PROJECTILE-MIXIN-ANNOTATIONS-EVIDENCE captures four classes plus mixin config and
refmap entries:

| Declared target | Access/injection contract | Recorded refmap |
|---|---|---|
| AbstractArrow | setOwner(Entity) at RETURN | m_5602_(Entity)V |
| Arrow | effects field accessor | f_36852_:Set |
| FishingHook | hookedIn field accessor | f_37094_:Entity |
| FishingHook | biting field accessor | f_37099_:boolean |
| ThrowableItemProjectile | getDefaultItem invoker | m_7881_():Item |

Accessor/API methods remain abstract in the distributed class snapshots; do not
invent Code attributes or treat annotations as proof that a runtime transformer
successfully supplied implementations. Actual version/mixin conflicts and field
availability in a running installation remain unverified.

## Verification and continuation

- projectile_hit_input_ysm_265.py: --jar, --source-root, --evidence, --out;
  145 integrity checks and 12 corrupted fixtures rejected.
- projectile_mixin_annotations_ysm_265.py: --jar, --evidence, --out (or --capture);
  1 exact annotation/config/refmap check and 5 corrupted fixtures rejected.

Method and annotation checks are static; the decompiler comparison elsewhere
covers different selected classes and is not retroactively claimed for this set.
Continue remaining living-entity/environment callbacks, keeping callback return
types, guarded versus unguarded mixin access and actual state provenance explicit.
