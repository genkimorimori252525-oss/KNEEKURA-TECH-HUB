# Living-entity and environment query inputs — 2026-10-17

## Selected batch

The exact catalog anchors 57 YSM callback names, followed through same-owner helper
and bootstrap references; LadderFacingVariable is additionally captured. Total:
70 selected methods across two owners, including helpers. This is not a new
semantic mapping count. Query roots are listed explicitly in the evidence.

Fixed JAR SHA-256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
Comparison source: YesSteveModel/YesSteveModel
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`, YSMBinding.java and LadderFacingVariable.java.
Primary static review; independent semantic review NOT_RUN. No target/game,
optional mod or live-world execution. Central mapping remains 669.

## Environment and movement sources

weather reads the context ClientLevel: thunder wins with 2, rain gives 1,
otherwise 0. dimension_name is that level's dimension registry-location string;
fps reads Minecraft's FPS getter. block_light and sky_light combine the context
level with the context entity's blockPosition. No null-level fallback is added
by these reached callbacks; the ordinary variable guard is a separate boundary.

is_open_air instead uses the entity's own level: canSeeSky must be true and the
MOTION_BLOCKING heightmap Y must not exceed the entity block-position Y. It is not
just a light-level or weather query. biome_category's deprecated helper is an
unconditional ACONST_NULL/ARETURN body; name registration does not make it a
working biome classifier.

is_sleep compares Pose.SLEEPING; is_sneak requires onGround plus Pose.CROUCHING.
These are not raw keyboard-key tests. is_passenger and eye_in_water call the
corresponding entity state methods. frozen_ticks and air_supply return the
entity's counters. delta_movement_length is the full Vec3 delta-movement length,
without the *20 scaling used by other speed queries; do not equate their units.

## Equipment, combat and entity role

has_helmet/chest_plate/leggings/boots/mainhand/offhand test nonemptiness of the
EquipmentUtil-selected stack, retaining its cosmetic precedence. has_elytra uses
the distinct elytra helper. mainhand/offhand_charged_crossbow read the actual
entity item-in-hand and require the CROSSBOW item plus its charged test; they do
not automatically reuse cosmetic selection.

is_riptide, armor_value, hurt_time, on_ladder, arrow_count, stinger_count, swinging
and swing_time read the corresponding living-entity fields/methods. swinging_arm
returns 0 only for MAIN_HAND, otherwise 1, including a null/non-main value on the
shown comparison. attack_time invokes getAttackAnim with effective animation
partial tick. These are observations, not commands to attack or animate.

entity_type returns `player` for Java Player, special `maid` for exactly the
`touhou_little_maid:maid` registry key, otherwise the registry key string or empty
string if absent. is_player/is_maid compare those returned strings. is_fishing
checks Player.fishing != null for Player, otherwise delegates to TlmClientCompat;
that external compatibility implementation is not established by this cohort.

## Blink and shoulder names are narrower than they sound

is_close_eyes returns sleeping OR a computed blink window. The window uses
`(renderTicks + Math.abs(UUID least-significant-long) % 10) % 90`, with the long
remainder converted to float before addition, and strict 85 < remainder < 90.
It is driven by the animation event's render clock, not a new wall-clock timer.
The exact constants, conversions and comparisons are captured; no actual blink
frequency or all-input numerical behavior was benchmarked.

has_left/right_shoulder_parrot only tests whether the selected shoulder CompoundTag
is nonempty. It does NOT validate the tag's entity ID as PARROT. In contrast,
left/right_shoulder_parrot_variant resolves the tag's `id`, filters to PARROT,
converts its `Variant` to an enum name lowercased with Locale.ENGLISH, and uses
`empty` when the Optional path has no matching parrot. Therefore a nonempty
nonparrot shoulder tag can make the first query true while the variant query
normally returns `empty`. Do not silently harmonize these different predicates.

## Ladder, attributes and angle units

LadderFacingVariable asks for lastClimbablePos, reads that block state and its
optional HorizontalDirectionalBlock.FACING, and returns get2DDataValue or 0.
The zero fallback is not a distinct "unknown" sentinel; its normal direction
encoding can also contain zero. It does not require the block to be a LadderBlock
or independently confirm the entity is currently climbing.

Player attribute callbacks read the entity's getAttributeValue for the selected
vanilla or Forge attribute: attack damage/speed/knockback, movement speed,
knockback resistance, luck, block/entity reach, swim speed, gravity, step-height
addition and nametag distance. They do not read the server-property tracker cache.
Attribute/provider availability and behavior remain external API boundaries.

elytra_rot_x/y/z require the AbstractClientPlayer wrapper and convert the raw
client player's elytra angle field using Math.toDegrees. These reached callbacks
return boxed Double; no radians are returned under the same callback names.

## Verification and continuation

`tools/living_environment_inputs_ysm_265.py` takes --jar, --source-root,
--evidence, --out. 366 integrity checks passed and 17 mutated fixtures were
rejected, including missing named roots and critical helper/callback bodies.
The selected same-owner closure does not include arbitrary external callees.

Continue view/render-context/texture callback provenance and remaining specialized
Molang functions. Preserve actual predicate differences, null/zero/string
sentinels, live versus cached fields and optional dependency boundaries.
