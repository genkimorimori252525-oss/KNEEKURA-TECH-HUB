# Passenger positioning and optional head-item selection

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twelve selected declarations across three owners;79 integrity checks and8 negative controls. No target execution, independent semantic review or central-map promotion. Full owner declarations/bootstrap records are support, not a claim that all owner methods were semantically reviewed.

## Passenger selection and coordinate frame

The selected public method on `OoO00Oo00Ooo0OoOoo00o000`, descriptor `(Entity,PoseStack,float)V`, reads the entity's immediate vehicle and, if present, obtains that vehicle's capability and invokes a captured callback through LazyOptional.ifPresent. It does not recursively search a riding chain.

The callback requires initialized capability and model-present state. It finds the passenger's index in vehicle.getPassengers(), rejecting negative index, absent loaded model, empty passenger-list collection, out-of-range index and null selected hierarchy. It does not explicitly reject an empty selected hierarchy or null bone element. The [model constructor](LOCATOR-MATRIX-PREPARATION-RECOVERY-2026-10-17.md) compacts nonempty passenger arrays, so list-index selection is over that compacted outer collection; this is not evidence that original numbered locator gaps preserve passenger indices.

At bytecode offsets99..120 the callback interpolates old/current vehicle yaw using ordinary Mth.lerp and passes it through the renderer replacement yaw helper. Then it applies positive-Y rotation by180 minus that yaw, locator preparation at142 (boolean POP145), and negative-Y rotation by the same angle. These rotations surround the locator's local transform; they do not remove the locator transform. No push/pop is performed by this callback, so caller pose scope matters.

Offsets163..173 compute negative vehicle riding offset minus passenger's own riding offset. A Player with present player capability OR an entity accepted by the maid-capability helper subtracts another0.5 at221..227. Presence is not an initialized/model-present test on that passenger capability. The pinned source comment describes the offset differently; the actual subtraction instruction governs this report. Final translation is(0,yOffset,0). This changes the supplied render pose, not entity world position, physics or actual passenger placement.

The historical central-map label ModelPreviewRenderer and source counterpart util.RenderUtil remain separate naming evidence; this cohort does not overwrite that mapping or establish global source/artifact equivalence.

## SimpleHats gate and provider chain

`OOooo0o00oOoo00OOoOOo0O0` starts its installed flag false and init sets it from ModList.isLoaded("simplehats"). Its head getter delegates only when true, otherwise null. There is no separate Curios installed check in this wrapper; successful dependency linkage is not proven by static inspection.

The inner `o0OOoo000o0o0OOO00oO00oo` requests Curios inventory, maps the handler identity, selects only slot type"head", invokes the existing Curios search helper with an instanceof HatItem predicate, and returns null for absent results. It neither traverses every slot category nor accepts every head item. All four callback/bootstrap relationships are retained in the evidence.

This reuses the earlier Curios helper rather than replacing its selection policy: enabled render toggles and cosmetic-slot precedence remain relevant. A nonempty cosmetic item that fails the hat predicate can suppress the underlying functional item for that same index in that helper. External Curios/HatItem code was not executed. The [head layer](ATTACHMENT-RENDER-LAYERS-RECOVERY-2026-10-17.md) independently draws raw qualifying head equipment and this optional selected hat; the getter itself does not establish draw eligibility or visible output.

## Reuse boundary

Keep capability presence versus readiness, raw passenger ordering versus compacted locator ordering, pose mutation versus world movement, and optional provider selection versus concrete drawing distinct. Next inspect parent renderer layer registration/eligibility and pass scope, retaining native/GPU results as unverified. This cohort is later than the fixed14 optional-integration checkpoint.
