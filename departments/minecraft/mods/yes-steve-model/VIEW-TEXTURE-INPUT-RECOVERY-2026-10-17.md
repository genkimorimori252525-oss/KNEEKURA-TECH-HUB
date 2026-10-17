# View, render-context and texture query inputs — 2026-10-17

## Scope

Exact JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`;
comparison source YesSteveModel/YesSteveModel
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
33 selected methods across nine owners cover PersonView, texture/head-hide
variables, FirstPerson Java adapter, selected RenderUtil/Iris predicates and
registration callbacks. Primary static review only; independent semantic review
NOT_RUN. No game, shader, optional-mod API or target runtime executed; map 669
unchanged. Support declarations are not additional confirmed semantic mappings.

## Three different view predicates

PersonView.getPersonView returns the client's camera-type ordinal only if the
context entity is identical to Minecraft's current player AND the broad
RenderUtil.isRenderingLevel predicate is true. Otherwise it returns the
THIRD_PERSON_FRONT ordinal. It is not a direction calculated from entity position.

query.is_first_person compares that result to FIRST_PERSON. In contrast,
PersonView.isFirstPersonView(animatable) additionally excludes Iris shadow passes.
Do not treat these two methods as universal aliases: their explicit shadow test
differs. The identity input also differs (context.entity versus animatable.entity),
which matters for selectively copied child contexts.

RenderUtil's broad predicate is renderingLevel OR Iris shadow OR FirstPerson's
rendering-player predicate, with short-circuit evaluation. Its exclusive predicate
first asserts render-thread access, then evaluates renderingLevel AND NOT
FirstPerson rendering-player. The assertion exists in this exclusive helper,
not in every other context getter. Inventory/paperdoll flags have their own
getters/setters; these are not one universal render-mode enum.

## Inventory, paperdoll and head hiding

rendering_in_inventory uses PersonView and is true for IPreviewEntity animatables
OR the global inventory render flag. It is not solely a screen-open test.
rendering_in_paperdoll directly reads the separate paperdoll flag.

FirstPersonModHideVariable requires all of: animation event reports NOT rendering
in level exclusively, FirstPerson compatibility is installed, PersonView reports
FIRST_PERSON. Only then it returns shouldHideHead; otherwise false. The event's
recorded flag is distinct from directly calling the current global predicate.
shouldHideHead delegates to the adapter's isRenderingPlayer, whose API call is
gated by its installation flag. Successful optional-mod runtime linkage is not
established by recording these guards.

## FirstPerson offset adapter

The adapter recognizes `firstperson` or legacy `firstpersonmod` during init.
When installed it registers a player-offset handler and sets head position 24.
setHeadPos divides by 16f into a volatile float; default 24 therefore stores 1.5.
The registered callback keeps current x/z and replaces y with `1.5f - HEAD_POS`.
It does not add this value to current y, nor use original/entity/delta arguments
in that shown body. Volatility of this one value is not a general thread-safety
claim. The separately exposed isEnabled method directly calls the external API
without its own installation check; only actual caller guards can bound it.

## Texture name is animatable-model data

TextureNameVariable checks whether context.animatableEntity is CustomPlayerEntity,
then calls its inherited texture-name getter; otherwise returns null. A Player
entity guard alone does not retarget the retained parent animatable to that player.

CustomHumanoidEntity.getTextureName returns its selected textureName if
isModelPresent, otherwise the first texture key from the current model container.
The latter path does not add a null-container/empty-texture fallback. Do not
promise an empty string or always successful access for an uninitialized model.

updateTexture, when isModelPresent, selects the named texture when found and
records its value-list index. Otherwise it replaces textureName with first key,
sets the first texture and sets index zero. It does nothing under the false
isModelPresent branch. These are model/resource selection rules, not a proof of
texture upload, visible pixels or an actual render call.

## Verification and continuation

`tools/view_texture_input_ysm_265.py` takes --jar, --source-root, --evidence, --out.
208 integrity checks passed and 14 corrupted fixtures were rejected. This joins
existing frame/readiness evidence; it does not rerun graphics or optional mods.
The fixed ten-cohort checkpoint remains unchanged.

Continue specialized bone-coordinate and Molang side-effect functions, preserving
units, allowEmitting gates and native/render output boundaries. Use decompiler
comparisons only where complex structure makes the extra view useful.
