# Animation/variable/expression packet routing boundaries

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.46 declarations/four owners,254 integrity checks/10 negative controls, including client-only annotations. Full NetworkHandler support is retained, but this dossier reviews the three connected packet routes and transport helper boundaries, not every registered protocol message.

No packet was generated/sent, no server/game or expression executed, and no global security or exploitability conclusion is established.

## Registration and transport-helper guard

NetworkHandler `OO00OoOOOOooO0ooOoOoOooO` registers ExecuteMolang at3 with PLAY_TO_CLIENT, SetPlayAnimation at7 with PLAY_TO_SERVER and SubmitRoamingVarsChanges at15 with PLAY_TO_SERVER. Exact bootstrap links retain their encode/decode/handle callbacks. These registration constraints and each handler's own reception-side test are distinct observations.

The protocol-version constant is2.6.0 although the researched artifact release is2.6.5. The custom presence check requires a nonnull connection/channel and equality of its channel-version attribute to that constant. setChannelVersion uses compareAndSet(null,suppliedString), not unconditional replacement. The SimpleChannel creation's two acceptance predicates return true; that mechanism is separate from the custom presence attribute and is not an identity/ownership proof.

sendToServer checks isRemoteChannelPresent BEFORE delegating to the external channel. This closes the earlier [shortcut-routing](EXTRA-ANIMATION-KEY-ROUTING-RECOVERY-2026-10-17.md) boundary: an absent local check in the shortcut callback does not mean this shared helper sends unconditionally. The all/player/tracking helper methods use their corresponding external PacketDistributor routes; the visible-players helper uses TRACKING_ENTITY with the supplied center, while its self variant uses TRACKING_ENTITY_AND_SELF. Actual recipient lists, transport delivery and external API behavior are not executed here.

## Handling is queued, not acknowledged completion

All three handlers obtain the supplied NetworkEvent.Context, conditionally enqueue work, discard the returned future, and call setPacketHandled(true) on their ordinary tail. A wrong reception side still reaches that handled flag. A successfully marked packet is not proof its queued task ran, succeeded, changed a capability or completed later animation work. There is no local finally guaranteeing the flag after an exception in earlier calls.

## SetPlayAnimation

Owner `OO00OOoo0ooO0o000O0oO0oO` retains index, classification string and entity ID. The short constructor uses entityId=-1 for self; stop factories use animationIndex=-1 and empty classification. Codec order is index VarInt, classification UTF, entityId VarInt; decoder/constructors add no local semantic bounds checks.

For a server reception, the queued lambda obtains the sender inside the task and returns if absent. A non-self target ID is looked up in that sender's current server level, routed only if TlmCommonCompat recognizes a maid, then returns. The self route obtains the sender's model-info capability. Stop invokes stopAnimation; play obtains the server model, chooses a nonblank existing classification or the root map, checks size>index and calls playAnimation with getKeyAt(index).

This repeats the common helper's incomplete lower-bound contract; the local size comparison is not a universal valid-index check. The inspected routing body has no comparison of a targeted maid's owner to the sender and no local CAN_SWITCH_MODEL check. These are specific omitted checks in these bodies, not proof that every broader transport/server policy permits an action. For reuse, UI gating and a nonnull sender must not be substituted for target authorization.

## SubmitRoamingVarsChanges

Owner `oOOoOo0o0OOOooo00OOo0O0o` retains the supplied changes object; codec delegates to RoamingVarsChanges with decode flag false. The handler checks server reception and sender presence before enqueuing, captures the sender, and reads sender.serverLevel when the task runs. It does not freeze the level at the earlier check.

The target is level.getEntity(changes.entityId), not implicitly the sender. A maid routes to the already-documented common no-op variable-change helper. A ServerPlayer target routes to that target's model-info capability and updateRoamingVars(target,changes). If that player is the exact first passenger of a nonnull vehicle, a present vehicle capability and present Molang vars trigger vehicle update with the target's model ID and vars. The source calls transfer an existing vars object; deeper copy/merge policy belongs to [roaming-state merge](ROAMING-STATE-MERGE-RECOVERY-2026-10-17.md).

No target==sender or owner comparison is performed in this inspected dispatch chain. Entity type, shared-level lookup, capability availability and data validation are different from authorization; an integration accepting untrusted target IDs must establish its own bounded policy instead of inferring one from method names. No malformed request or remote test was performed.

## ExecuteMolang

Owner `o0oo0O0o0oO0O0o0OoOOOoOO` has a single-ID constructor creating a one-element array and an array constructor retaining the supplied int[] directly. Codec writes/reads the ID array then the UTF expression. Library size/string limits are external; no new limits or deduplication are added in these bodies.

On client reception it enqueues the CLIENT-only handler. That handler returns without a client level, otherwise traverses entityIds in order. Player targets use their animatable capability; other recognized maids route to the common bridge. The player callback parses inside each selected capability callback and enqueues executeMolangExp(value,true,false,null), not one globally compiled expression shared across every ID. Duplicate IDs are not locally eliminated.

The callback catches ParseException only. Other runtime parsing failures are not covered by that catch and can interrupt the current traversal; actual failures were not reproduced. The existing [parser-entry](PARSER-ENTRY-OWNERSHIP-RECOVERY-2026-10-17.md) and [common maid](MAID-COMMON-MODEL-COPY-RECOVERY-2026-10-17.md) dossiers distinguish parsing, pooled cleanup, post-phase queueing and later expression effects. Command-side permission checks, external sender authentication and actual expression execution are separate boundaries, not claims made from this client receiver.

## Reuse checklist for this seam only

Keep protocol registration direction, channel-presence hints, sender existence, target lookup/authorization, capability readiness, value/index validation, queued work, handled status and eventual effects distinct. This records existing Java behavior and validation limits without changing upstream networking or testing another server.

## Producer follow-through

The later [command/relay dossier](MOLANG-COMMAND-PRODUCER-RECOVERY-2026-10-17.md) follows the known constructor sites. It distinguishes the command's permission predicate from SubmitRouletteConfig's separate server-to-tracking-client relay. Neither route's guards should be presumed to cover the other.
