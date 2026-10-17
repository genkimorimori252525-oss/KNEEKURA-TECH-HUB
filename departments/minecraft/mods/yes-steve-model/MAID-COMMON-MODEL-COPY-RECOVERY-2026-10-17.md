# Common-side maid bridges and model-copy mutation

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.27 declarations/three owners,155 integrity checks/nine negative controls, with exact method/event annotations. No network transmission, model mutation in a running game, native execution or independent semantic review.

Owners: common facade `OOOo0ooOO0000oOOOoOoOOo0`; common inner `OooOO0oOoOo0o0OoOOOOo00O`; copy listener `OoOo0OOoOOOOO0ooo0O000oo`.

## Common installation checks differ from client initialization

The common facade calls ModList.isLoaded("touhou_little_maid") on its installation query. It does not apply the client facade's version-range/development-mode gate or read that facade's cached installed flag. Each shown delegate checks this common installation predicate. registerEvent creates/registers the copy listener when present, with no local duplicate-registration guard. Actual mod/event availability remains external.

The Molang-execution outer/inner methods carry CLIENT-only annotations. The inner requires EntityMaid, isYsmModel and a present maid capability, parses via parseSingleExpressionUnsafe, then invokes executeMolangExp(value,true,false,null). The existing base method enqueues work: allowEmitting=true, pre=false, no result consumer; the call is not immediate evaluation proof. Its local catch covers ParseException only. Runtime parsing exceptions, queue execution and later callback failures are not all converted by that catch. [Parser pool](PARSER-POOL-LIFETIME-RECOVERY-2026-10-17.md) and [numeric/error entry](PARSER-ENTRY-OWNERSHIP-RECOVERY-2026-10-17.md) preserve the separate lifetime/error paths.

## Projectile and vehicle model transfer

The projectile-owner bridge requires EntityMaid with isYsmModel. For a present projectile model-info capability it calls init with the maid model ID and a NEW empty Object2FloatOpenHashMap, creates a sync-info message and calls broadcastToVisiblePlayers. It does not copy maid roaming variables. The earlier projectile mixin's server-side routing is a separate caller gate; this helper itself does not establish packet delivery or recipient acceptance.

The common inner also declares a vehicle-model helper requiring a YSM maid to be the vehicle's exact first passenger. Its callback updates vehicle model-info with the maid model ID and a new empty roaming map, then requests a visibility broadcast. A fixed955-class [exact-symbol caller inventory](MAID-VEHICLE-CALLERS-EVIDENCE-2026-10-17.json) found zero direct invokes and zero bootstrap references to this helper. The public common facade has no corresponding vehicle delegate. This bounds the observed Java route; it is not global closure over native, reflection or external callers, and the helper's presence must not be advertised as a proven active vehicle feature.

handleVariableChanges checks maid type/isYsmModel and then returns without applying the supplied changes. This agrees with the client-side no-op/absent-handler findings; it does not imply that unrelated external maid synchronization is absent.

## Roulette selection is an internal helper contract

The inner roulette method checks maid type and isYsmModel. Index -1 calls stop immediately. Otherwise it obtains the server model, selects a named classification only if nonblank and present, or falls back to the root ordered map. It locally tests size>index before reading getKeyAt(index) and passing that key to playRouletteAnim. This is an upper-bound test, not a complete nonnegative-index validator for every other input.

This helper does not validate sender identity or ownership. Those concerns belong to the invoking boundary and must be checked before reusing it for untrusted input; no global authorization or exploitability claim is made from this helper alone. No packet or malformed request was generated or sent.

## Creative model copy into a statue/garage kit

The instance RightClickBlock subscriber first checks YSM availability, creative player and a Hakurei Gohei in the player's MAIN hand. It reads the hit block position and the block entity, dispatching garage kit first, then statue. It has no local event-hand comparison, side-only test or event cancellation in this body. External event semantics are not inferred from that absence.

Statues require core-block status and nonnull extra-maid NBT. Garage kits read extra NBT without a corresponding local null guard. Both parse the NBT id and proceed only when the resolved type equals the registered maid type.

For a present player model-info capability, the copy callback mutates the supplied NBT in this order:
1. IsYsmModel=true
2. YsmModelId=player model ID
3. YsmModelTexture=player selected texture
4. YsmRoamingUpdateFlag=its existing int value plus1
5. YsmRoamingVars=a NEW EMPTY CompoundTag

The last operation replaces the stored roaming tag; it is not a copy of the player's roaming values, despite the general model-copy operation. The method preserves other NBT fields by mutating the supplied object rather than replacing the entire entity tag. No resource bytes or protected model asset are copied by these Java instructions.

After the void applyPlayerInfo helper returns, the statue branch calls refresh and the kit branch calls setData(currentFacing,data). These calls are not conditioned on whether the player capability was present and actually changed the NBT. A void helper completion does not establish successful model transfer. Exceptional exits and external persistence/render updates remain untested.

## Reuse consequence

Separate model/texture identifiers, empty variable-map initialization, real roaming updates, internal helper validation, event gates and external persistence/broadcast completion. These are bounded existing behaviors to understand, not missing features silently implemented by this research.
