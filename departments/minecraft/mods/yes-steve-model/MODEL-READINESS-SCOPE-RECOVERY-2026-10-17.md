# Model readiness, replacement ordering and rendering scope

Primary static review; independent semantic review NOT_RUN. Fixed artifact
SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f` and
source candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No runtime execution,
central mapping promotion, model decryption or native implementation analysis.
The 73-method snapshot covers seven owners, with seven source-track records for
six distinct files (CustomEntity and its nested holder share one source file).
Complete snapshot inclusion does not imply every unrelated render helper has
received semantic review; claims below are the reviewed scope.

## Registry and model eligibility are distinct

CustomEntity's constructor registers with AnimationParallelTicker only when its
boolean parameter is true (branch12, call16). canUpdateAsync returning true is
therefore not the registration decision. checkModelUpdate calls the container
check only if lastCheckUpdateTime<entity.tickCount; it stores tickCount after the
call (26). Equal/backwards ticks skip this ordinary path. updateModelId stores the
new name and directly invokes the check, bypassing that tick throttle.

The model lookup Optional.ifPresentOrElse uses bootstrap2 and3, linking the
present-model Consumer and fallback Runnable to exact methods. A present lookup
replaces the holder if null, fallback, or a different model object. A missing
lookup obtains the default model and replaces the holder if null, not fallback,
or a different default object. Comparisons are reference identity, not equals.

After selection, the main check loads only if the holder is nonnull, either model
identity or fallback flag changed, and holder.isLoaded returns true. It stores
currentModelContainer then modelFallback before onLoadModelContainer and
loadGeoModel. No rollback/finally restores those fields on a downstream exception.
If a new holder exists but is not ready, this method does not reset the old loaded
model in that branch; old current model state remains until the gate passes.
If holder is null while a current container exists, resetModelContainer runs.
This is conditional ordinary-path retention, not proof of a visible stale-model
bug or of asynchronous load completion.

isModelPresent separately tests holder nonnull, not fallback and holder.isLoaded.
A loaded fallback can therefore exist as current container while this predicate
is false. The scheduler's skip on isModelPresent is not equivalent to
currentModelContainer==null. Base ResourceHolder.isLoaded always returns true;
concrete humanoid/projectile/vehicle holders instead call TextureHolder.id and
Optional.isPresent. Their source labels are candidate correspondences; each exact
owner and body is retained in evidence. Presence is a readiness signal, not proof
of a completed GPU upload, valid image contents or native renderer consumption.

## Reset behavior

resetModelContainer clears container/deferred handler/holder/fallback, then calls
resetGeoModel. CustomEntity.resetGeoModel calls the superclass reset, then clears
alternate physics and lastCheckUpdateTime. CustomEntity.reset also resets modelId
to default and initialize=false before resetting the container. This distinguishes
the public reset from the base resetGeoModel that does not clear initialize.
The inspected reset methods do not themselves wait for or cancel asyncTask; the
calling schedule must establish any needed ordering. No race is claimed without
that caller evidence and runtime observation.

## Mixin and rendering-scope follow-through

Named MixinTweaker.shouldApplyMixin returns true for all arguments in the exact
artifact. onLoad/acceptTargets/preApply/postApply are empty; getRefMapperConfig
returns null. getMixins conditionally adds ParCool/Create client compatibility
entries. Thus the predicate itself does not veto WorldRendererMixin; constructor
compatibility initialization and external Mixin loading/application still remain
runtime prerequisites. This narrows, but does not erase, the hook dossier's limits.

RenderUtil has distinct predicates:

- isRenderingLevel: stored level flag OR Iris shadow result OR FirstPerson player
  rendering result, with short-circuit branches.
- isRenderingLevelExclusive: assert render thread, then stored level flag AND NOT
  FirstPerson player rendering. It does not substitute the broader predicate.
- inventory and paper-doll flags are separate static setters/getters.

CustomEntity.getPhysicsManager selects its primary physics manager for broader
isRenderingLevel OR paper-doll; otherwise lazily creates/returns alternate physics.
This need not use the same decision as immutable-render or worker-result reuse.
External Iris/FirstPerson API outcomes and actual threading of flag accesses are
not established by these Java branch bodies. A true apply predicate plus correct
refmap is still not a successful game startup/injection receipt.

## Checks and next step

400 fixed-artifact/source/body/declaration/bootstrap checks pass;15 negative
controls reject altered registration, tick equality, holder identity/readiness,
plugin acceptance, rendering-scope branches and invented finally. Mapping669 is
unchanged. No independent review has been claimed for these additions.

Next follow TextureHolder's Java readiness/lifetime and renderer model selection,
staying at public Java boundaries where native implementations would otherwise
be required. Keep load readiness, scheduled updates and visible render selection
as separate assertions until their callers are joined.
