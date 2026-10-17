# Model/texture selection: local update, request validation and later synchronization

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twenty-five declarations across SetModelAndTexture `O0Oo0oooOoOOO0oOoOOoOooo`, ModelButton `o0o0oO0O0oo00o000000OOOO` and TextureButton `OoO000oOOOoO00OoOoOOo0OO`. Widget drawing/constructor support is captured, not claimed fully semantically reviewed. No GUI actions, packet transmission, model access changes, native/auth routine execution or target runtime occurred.

## Producer inventory and distinct local-update policies

The declaration-validated [constructor inventory](MODEL-SELECTION-PRODUCERS-EVIDENCE-2026-10-17.json) scans955 classes and finds four direct references across three methods: two ModelButton callback branches, one TextureButton callback, and the decoder. Zero matching bootstrap constructor handles were found. Reflection/native/external construction is not closed.

ModelButton.onPress first returns when its retained needAuth flag is true, then requires a current local player and its animatable capability. That local UI flag is separate from the server's validation. Its callback uses NetworkHandler.isRemoteChannelPresent:

- Channel present plus hasRoamingStorage(preview model short hash): update the local capability's model/texture first, then construct the request from the capability's resulting IDs.
- Channel present without that storage entry: send the preview entity's IDs without that immediate local model/texture update.
- Channel absent: update local model/texture, with no request from that branch.

The already captured PlayerAnimatableCapability.hasRoamingStorage is a storageMap.containsKey test. It is not proof that variables are populated or geometry/textures are ready. Likewise the channel predicate checks the current connection's YSM version attribute, not merely whether the world is single-player/multiplayer. The send helper separately checks channel presence again; a UI branch test is not a delivery acknowledgement.

TextureButton instead calls local updateTextureName before constructing a request from its preview model/texture IDs, then invokes the shared send helper. Its callback has no outer remote-channel branch or same-model assertion. These are ordering/local assumptions of the intended UI route, not an observed mismatch or a request to send arbitrary identifiers.

## Wire and handler boundary

The request retains two Strings and encodes model ID then selected texture with the FriendlyByteBuf UTF methods; decode reads them in that order and constructs the request. It contains no explicit target entity ID, model asset bytes or claimed client authorization result. The packet registration is the existing server-directed channel route.

The handler checks server reception side and enqueues work, discarding the returned future. The worker obtains context sender, returns if null, and proceeds only if the CAN_SWITCH_MODEL config value is true. The ordinary outer tail sets packetHandled=true whether the worker eventually applies a change or not. No acknowledgement/rollback transaction is established.

## Server validation and fallback have state effects

The worker uses the sender's model-info capability and the sender's owned-model capability. The nested callback validates model-map membership, required ownership when that model is restricted, and selected texture membership in the server model's texture list. This is a server-side check independent of the button's local flag.

A failed check calls model-info setDefault; a passed check calls setModelAndTexture with the requested IDs. After either branch returns normally, it calls stopAnimation(sender). Missing capability, disabled switching and missing sender are different paths: they do not enter this update/default/stop sequence. No payload was generated to exercise the branches, and no global authorization guarantee is inferred beyond them.

The existing [server/full evidence](SERVER-FULL-SYNC-RECOVERY-2026-10-17.md) shows setModelAndTexture comparing both strings first: equal current IDs return without marking dirty; changed IDs are assigned and mark dirty. setDefault resolves the server default pair and delegates to that setter. Thus fallback need not create a dirty transition if already at that pair, but the packet callback still reaches its ordinary animation-stop call.

Stop delegates to extra-animation staging with an empty name and sync=!dirty. The [server producer](SERVER-PROPERTY-PRODUCER-RECOVERY-2026-10-17.md) and later dirty/full tick path determine when updated state is sent. A selection request does not synchronously load the requested model or guarantee a new full packet merely because it was handled.

## Later client acceptance and rendering

The [client full-state receiver](SERVER-FULL-SYNC-RECOVERY-2026-10-17.md) applies model/texture, disabled flag and property snapshot in order through entity availability/capability handling. [Model readiness](MODEL-READINESS-SCOPE-RECOVERY-2026-10-17.md) distinguishes selected holder, loaded container, fallback, texture ID and visible drawing. These later gates can differ from the UI's earlier local update.

Do not infer successful server acceptance from an optimistic local texture/model change, or durable rollback from a void send helper. The old [preview caller inventory](GUI-PREVIEW-CALLERS-EVIDENCE-2026-10-17.json) also identifies these buttons' drawing helpers as CustomGuiPlayerEntity consumers; their preview actor is not the local capability mutated by onPress. Rendering a tile and selecting it are separate ownership paths.

## Reuse

Preserve channel-dependent local updates, key-presence versus readiness, sender-bound validation, default fallback, animation-stop ordering and eventual synchronization. No source behavior was changed; central669 mapping and independent-review status remain unchanged. Native model loading, live event scheduling and actual acceptance/output remain open evidence boundaries.
