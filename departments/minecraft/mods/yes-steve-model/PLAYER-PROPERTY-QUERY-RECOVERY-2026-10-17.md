# Player property masks and local/remote query provenance

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twenty-eight selected
complete methods across PlayerStateTracker, three property setters and selected
QueryBinding/YSMBinding consumers. Binding names join the constructor/bootstrap
records already retained in MOVEMENT-QUERY; not every query is newly analyzed.
No game/network execution or central mapping promotion.

## Presence masks update only their selected fields

PlayerStateTracker.updateServerDrivenProperty handles bits1..10: flying, effects,
experience level, food level, health, max health, xxa, yya, zza, shield cooldown.
An absent bit leaves that field unchanged. Effects clear first only when the
effects bit is present AND isFull is true, then putAll. The full flag alone is not
a universal reset of every cached field. Reset explicitly clears these instance
fields/effects and calls the inherited tracker reset.

Axis byte fields are converted to float by dividing by127, without an additional
receiver clamp in this method. Sender setters OR the corresponding128/256/512
mask, call org.joml.Math.clamp with arguments (input,-1,1), multiply by127, call
org.joml.Math.round and narrow to byte. Preserve the actual external owner and
argument order; do not silently substitute a different Math API.

### External dependency comparison, not a loaded-runtime claim

[JOML1.10.5's official Math source](https://raw.githubusercontent.com/JOML-CI/JOML/1.10.5/src/org/joml/Math.java)
defines clamp with lower/upper/value order. Under that implementation, the captured
(input,-1,1) call is equivalent for finite inputs to max(input,-1), not a symmetric
upper/lower clamp. Normal inputs already within[-1,1] are unaffected by this
difference. The exact JOML version loaded in a running game has NOT been verified;
this is a dependency-sensitive comparison, not a reproduced defect or a patch.
The static YSM auditor below does not validate an external JOML binary.

## Queries choose live fields or server-backed caches

For a nonlocal PlayerAnimatableCapability, health/max_health/player_level and
food_level use tracker caches. Otherwise health/max use the live entity methods,
player_level the player field; food uses Player food data or20 for a nonplayer.
Health/max raw Object results can be boxed integers on the remote path versus
boxed floats on the live path. Subsequent numeric conversion is a separate step.

YSM xxa/yya/zza likewise choose tracker values only for a nonlocal player capability;
other cases read the entity fields. These are not the displacement-derived
input_vertical/input_horizontal functions from MOVEMENT-QUERY. Shield cooldown
uses the capability's tracker for any player capability, otherwise false, so it
does not share the same local/remote condition as the axis queries.

PlayerStateTracker.isFlying reads local abilities when its local flag is true,
else cached remoteFlying. Effect level reads the local entity's active effect
(amplifier+1 narrowed to byte) for local state, otherwise the cached effect map
with zero fallback. These distinctions prevent treating all query fields as one
uniform server snapshot.

## Yaw speed uses an entity-tick sampling path

Local yaw-speed update runs from updateEntityTickData, not every render pass, and
uses yaw difference times20 divided by the positive entity-tick gap on the normal
strict-forward tracker path. It updates LAST_YAW on the first accepted tick but
only recomputes YAW_SPEED when the prior tick count>0. Those two fields are static
and not cleared by this instance reset body. query.yaw_speed selects that static
value for LocalPlayer; otherwise it uses20*(currentYaw-previousYaw). Neither
subtraction in these inspected helpers wraps angles. No sampled game measurement
or visible rotation bug is asserted.

## Verification and continuation

163 static checks pass;11 missing/corrupt-evidence controls reject scale, axis
mask, external Math owner, byte narrowing and invented receiver cleanup. Mapping669
and source-divergence cautions remain. This post-checkpoint cohort is not part of
the frozen17-cohort receipt. Next follow server-side change producers/full-versus-
delta selection and relevant query consumers, keeping arithmetic/dependency
comparisons separate from actual packet delivery and runtime effects.
