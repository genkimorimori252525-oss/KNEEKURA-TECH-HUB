# Player render entry, event and attachment registration

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twenty-one declarations across player renderer, switch helper and special event.125 integrity checks/9 negative controls; no independent semantic review, mapping promotion or target/GPU/event-bus execution. Constructor/bridge/support declarations are included, not newly confirmed mapping counts.

## Entry and registration order

`o0ooO0o0ooo000OOO0o0oo0o` registers hand-item, elytra, shoulder-parrot and head layers in that order in its constructor. This constructor does not register the backpack layer; optional additions require their separate registration path. The inherited renderer's list and spectator/body-pass policy remain documented in [render selection](RENDER-SELECTION-RECOVERY-2026-10-17.md). The [concrete layer rules](ATTACHMENT-RENDER-LAYERS-RECOVERY-2026-10-17.md) apply only when invoked.

Player rendering first asks SWarfare whether to hide the player; true returns before capability lookup. Missing player capability also returns. Otherwise checkModelUpdate executes before constructing the special event with player, retained custom-player capability and current model ID. The event bus post result true returns before entering the inherited render path. External listeners can alter/cancel the event; their behavior is not inferred.

## Two texture reads straddle the event

At offsets52..58 the renderer copies the event's texture override into its own field BEFORE posting the event at66. On the non-cancelled path it reads the event's override again at80 and passes that value explicitly to renderAnimatableEntity. The event constructor does not assign an override, so it starts null under ordinary Java initialization. Its setter simply stores the supplied reference.

Consequently a listener's later override can reach the explicit inherited render argument without updating the renderer's earlier field copy. The renderer's getTextureLocation method separately reads that field; when null it resolves the player's capability texture, or missing-texture location if absent. Do not equate the two values or claim the listener override is lost from the main explicit-argument path. This is an ordering distinction, not an observed texture bug. No guessed fix was applied.

The event owner `oo0o0oOo0O0o00o0oO0O0OO0` carries the exact Forge Cancelable class annotation, captured alongside method annotations. It retains final player/custom-player/model-ID references; its no-argument constructor sets those three to null. This event does not itself implement listener behavior, texture upload or model replacement.

## Names and riding adjustment

Name visibility uses squared distance with discrete32/otherwise64 range, rejects absent local player, and then follows team visibility rules for other players. Team-specific branches can return before the final generic renderNames/camera-entity/invisibility/vehicle tests; those tests are not universal extra gates on every team branch. The generated enum switch helper is retained with the class evidence.

Name rendering skips GUI fake players. Within squared distance100, an objective in display slot2 adds a score line and translates y0.25875 before the ordinary display name. Pose push/pop are ordinary-path operations without a local finally.

setupRotations delegates to the parent first, then adds y0.5 when the current vehicle is recognized as a maid chair or sitting entity. This is distinct from the [passenger locator adjustment](PASSENGER-HAT-ATTACHMENT-RECOVERY-2026-10-17.md); neither by itself proves net visible offset when composed with all callers.

## Next seam

Follow optional layer registration and first-person renderer entry only where not already covered; do not repeat the inherited renderer body audit or infer native drawing from Java call order. This cohort was added after the fixed14 optional-integration checkpoint.
