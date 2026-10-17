# Client model composition and asset inheritance

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. This dossier REUSES all14 builder declarations already captured in [conditional-animation evidence](CONDITIONAL-ANIMATION-NAMES-EVIDENCE-2026-10-17.json), owner `OOOOOO00o0Oo000O0OO0OOO0`; it does not inflate counts by recapturing them. The new helper cohort supplies IDs/container ownership. No target/native execution, independent review or confidence promotion.

## Construction order and fallback

The builder constructs common assets, player, projectiles, vehicles, client info and finally ClientModel in that order. A default build assigns the static DEFAULT_MODEL and then marks only the player main-animation map's values copied-from-default. The shown loop does not separately mark first-person, projectile or vehicle maps.

Player geometry takes indices0 and1 with no local size guard. Animation-file key exactly fp_arm selects the first-person map; all other file keys merge into the main map. putAll follows source iteration order, so collisions follow later writes without establishing a stable order for an arbitrary producer map.

A nondefault build fills absent main and first-person animation keys from DEFAULT_MODEL via computeIfAbsent. Returned values are the same Animation references, not clones. The shown body assumes the default exists. Main and first-person condition managers then inspect their respective final key sets. Controller files are merged separately; there is no corresponding default-controller inheritance in this body. See [animation-data ownership](ANIMATION-DATA-OWNERSHIP-RECOVERY-2026-10-17.md) for mutable elements despite read-only containers.

## Texture and entity-model selection

Player textures and their PBR values are appended to allTextures without identity deduplication. A nonempty configured default name is selected if present, otherwise getKeyAt(0) is used. This is not blank-string trimming, and no empty-list fallback is shown. Ordered lookup and hash lookup are the distinct representations documented by [asset helpers](MODEL-ASSET-HELPERS-RECOVERY-2026-10-17.md).

Each projectile/vehicle entry constructs its own animation/controller maps from optional files or empty maps. The isDefault parameter is unused in these two method bodies; no default-player animation fallback occurs there. Textures/PBR are appended and each matched entity ID receives map.put(id,model), so a later entry can replace an earlier match. #tag expansion belongs to ModelIdUtil and depends on the external registry, not a regex/glob matching engine.

GUI-image construction skips the entire loop when properties are null, skips null textures, appends accepted textures and returns an unmodifiable new map. This one null check is not global proof that player-building tolerates missing properties. Client-info construction passes the authorization boolean through; authentication and protected parsing are not investigated or changed here.

## Function/event naming is a two-channel transformation

For the user-function map, the first @ at index0 skips the entry; a later @ retains only the prefix; no @ retains the whole name. The map stores the same IValue references, and colliding prefixes follow iteration's later put. For events, a first @ with a nonempty suffix adds the same IValue to the suffix's handler list after no-argument String.toLowerCase. Additional @ characters remain in that suffix. This is default-locale conversion, not explicit Locale.ROOT normalization.

Thus @event is event-only; name@event contributes a named function and an event handler; name@ contributes the named function without an event; a name without @ is function-only. Handler insertion order follows the input map traversal, with no explicit sort. CommonAsset retains the resulting maps and lists directly. [Molang event wrappers](MOLANG-EVENT-WRAPPER-RECOVERY-2026-10-17.md) consume these handler lists later; assembly alone does not establish when or whether an event fires.

## Practical reuse

Preserve the distinction between player-only fallback and vehicle/projectile-local data, map-container copying and shared Animation/IValue objects, event registration and execution, syntactically valid IDs and registered entities. This is an observed Java composition contract, not a replacement parser specification or a claim of actual malformed model inputs.
