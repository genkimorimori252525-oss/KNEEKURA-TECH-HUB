# Selected texture and pre-registered texture lifetimes differ

PRIMARY_STATIC_REVIEW_ONLY. Fixed YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. This is a focused join of existing readiness, texture-holder, GUI, maid and player evidence, corroborated with javap for the already captured humanoid holder. No new owner snapshot, mapping promotion, GPU operation or target execution.

## Selected holder first, optional all-texture retention second

HumanoidResourceHolder's constructor first looks up the outer entity's textureName in the player texture map. A nonnull result is selected; otherwise it uses PlayerModel.defaultTexture. It registers that selected texture with the supplied immediately flag and releaseDelay at bytecode offset52, then stores releaseDelay.

When registerAllTexture is true it creates a list and iterates player textures, projectile textures and vehicle textures in that order. Each call uses the two-argument register(texture,false) overload (offsets126,186,246), then retains the returned holder in that list. This overload uses delay200 in the [texture-manager contract](TEXTURE-HOLDER-LIFETIME-RECOVERY-2026-10-17.md). It does not pass the outer selected-texture delay. False leaves the list null. The constructor does not require all these other holders to be ready before returning.

isLoaded checks only the currently selected textureHolder.id().isPresent. It does not iterate the retained all-texture list. This fits the [readiness contract](MODEL-READINESS-SCOPE-RECOVERY-2026-10-17.md): selected-resource availability is not a guarantee that all model-related textures have finished registration or upload.

## Recorded callers and units

The captured PlayerAnimatableCapability and CustomYsmMaidEntity factories pass registerAllTexture=true, immediately=true and delay600. The captured CustomGuiPlayerEntity factory instead passes false,true,300. These values count accepted texture-manager tick visits during delayed cleanup, not a wall-clock promise of exactly30/15seconds. Actual tick availability and work-budget processing remain separate.

The private setTexture helper requests immediate registration with its stored releaseDelay and replaces the selected holder reference. The manager's identity cache returns an already-live holder without changing that holder's delay. Consequently a texture first pre-registered through the200 overload can retain that delay when later selected through a600/300 request, if the same texture object's holder is still live. Likewise, a previously selected holder need not adopt200 when encountered in the all-texture pass. This is a conditional composition of existing bodies, not an observed cleanup-timing failure.

The list strongly retains the holders it collected while that resource holder/list remains reachable. The manager's weak values and cleaner scheduling are different layers. No exact garbage-collection or native-free timing is established.

## Name and index updates remain a different operation

The initial constructor fallback chooses PlayerModel.defaultTexture but does not itself rewrite the outer textureName/index. Later CustomHumanoidEntity.updateTexture runs only when isModelPresent. A found name selects that texture and its value-list index; a missing name switches to the first key/value and index0. This differs from blindly reselecting the configured default name on every update. [View/texture inputs](VIEW-TEXTURE-INPUT-RECOVERY-2026-10-17.md) already captures those bodies.

For reuse, define separately the selected texture, pre-registration set, retained references, cache identity, registration readiness and release-delay ownership. Neither one ready holder nor a configured delay proves global texture completion or disposal.
