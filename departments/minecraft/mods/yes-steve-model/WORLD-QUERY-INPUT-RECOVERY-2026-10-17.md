# World, position and camera query inputs — 2026-10-17

## Evidence

Primary static review of exact official JAR SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, compared with
YesSteveModel/YesSteveModel `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
23 selected methods across nine owners include QueryBinding's constructor,
EntityFunction and the two relative-block helper overloads. No new central maps;
669 unchanged. Independent semantic review NOT_RUN. No world/registry/game/native
execution or runtime query results are claimed.

| Registered function | Exact owner suffix | Arity contract |
|---|---|---|
| biome_has_all_tags | OOO0o0o0o0oOOoOOo00OOOOO | >=1 |
| biome_has_any_tag | o0OO000O0OoOOoOO00ooo00O | >=1 |
| relative_block_has_all_tags | OOoOOO0o0OoooOO00oO0ooOO | >=4 |
| relative_block_has_any_tag | O000O00o0OO0o0O0OoOo000O | >=4 |
| position | o0o000OOo0000OOOOOOoOOO0 | ==1 |
| rotation_to_camera | O0oo000oo0oOOOooOOo0ooOO | ==1 |

The first five derive from EntityFunction, which validates an Entity context.
Camera rotation uses the broader ContextFunction. Arity is validated by callers;
a raw direct eval does not acquire an additional argument-count guard here.

## Relative block: evaluation before range rejection

MolangUtils owner `oOO0OO0OOO0ooOo000o0O0OO` delegates the two-argument helper to
the overload with argsOffset=0. The overload evaluates all three offset arguments
via getAsDouble, in x/y/z order (calls at 3,12,22), BEFORE checking their ranges.
Thus a rejected x offset does not prevent y/z argument evaluation on a normally
returning getter path. Do not confuse the later short-circuit range expression
with lazy evaluation of the earlier argument assignments.

It returns null if any absolute offset exceeds 5; equality at +/-5 passes.
The three 5.0 constants and comparison branches are captured. Offset axes use
world coordinates without a yaw-relative rotation in this helper. Coordinates
are built as `(int)Math.round(entityCoordinate + offset - 0.5d)` per axis, with
explicit double arithmetic, long round result, then L2I narrowing. The helper
then obtains entity.level().getBlockState(pos); it does not interpolate the
entity coordinate using the animation partial tick.

The preceding typed conversion matters: asDouble maps null and numeric NaN to
zero, booleans to 0/1, other nonnumeric objects to one, and retains infinity.
Consequently this is not strict numeric-string parsing. Infinite converted offsets
fail the >5 gate. These are composed static semantics from the already captured
conversion helper, not executed hostile-input/world tests.

## Tags and biome source

Relative tag functions use arguments 0–2 for offset and start tags at index 3.
A null block terminates with null before tag arguments are evaluated. Biome
functions first query the entity's current blockPosition in its current level
and start tags at index 0. Neither uses an arbitrary caller-supplied biome object.

All/any variants convert reached IDs in order. Invalid reached ID returns null.
All returns false at first missing tag; any returns true at first matching tag.
Remaining arguments are unevaluated after the decisive result. A tag registry
lookup builds a TagKey and checks the retrieved state/holder. Registry contents,
chunk behavior and tag matches were not executed or certified.

## Position and camera are different observation surfaces

Position converts argument 0 with asInt, then obtains AnimationEvent.getPartialTick
(not getRequestedPartialTick), widens the float to double and calls Mth.lerp on
old/current entity coordinates. Axes 0/1/2 return boxed Double; default returns
null. It is an interpolated coordinate query, unlike relative-block lookup's
current entity coordinate. Existing conversion semantics mean nonnumeric objects
can become axis 1 rather than being rejected by this function itself.

RotationToCamera also converts the axis to int, rejects values outside 0..1,
then reads Minecraft's main camera. Axis 0 returns negative camera X rotation;
axis 1 returns 180f plus camera Y rotation. Results are boxed Float. No entity-to-
camera position subtraction, atan2, angle wrapping or degree-to-radian conversion
appears in this function. Do not implement a look-at vector just because of its
registered name; follow the actual orientation convention and downstream units.

## Verification and next seam

`tools/world_query_input_ysm_265.py` takes --jar, --source-root, --evidence and
--out. 158 integrity checks passed and 15 mutated evidence controls were rejected,
including modification of the range constant. This is static integrity evidence,
not independent review, a running world test or Bedrock behavior equivalence.

Next: query registration/context guards and time/controller state inputs, with
attention to actual boxing/units and lazy evaluation boundaries. Preserve this
cohort's world-axis and partial-tick distinctions in reusable analysis.
