# Model-local language fallback and display metadata

PRIMARY_STATIC_REVIEW_ONLY. Fixed artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.15 declarations across LanguageManager `OOOOooO0O0o0OOoOOo00oo00` and ModelPackInfo `o0ooO0OOO0Oo0o0oOO00Oooo`;90 integrity checks/seven negative controls. No GUI rendering, translation resource load or independent review.

## Fallback selects a language map, not an English value per missing key

The manager first checks whether the requested locale exists in the supplied outer map. If present, it immediately returns that locale map's getOrDefault(key,defaultValue). It consults en_us only when the requested locale map is absent. Thus a present but incomplete locale map does not fall through to English for a missing key; it uses the supplied metadata default instead. Empty strings are not treated as missing, and explicit null values follow the actual supplied Map's getOrDefault behavior rather than a local nonnull normalization.

ModelPackInfo lookup normalizes a null default string to empty, and handles a null or empty outer language map. ClientModel lookup does neither null-default normalization nor an outer null-map guard before isEmpty. The three-argument ClientModel overload reads the currently selected client language and delegates to the explicit-locale overload. No lowercasing, locale alias conversion, language-entry merging or local cache appears in these paths.

ModelPackInfo directly retains hierarchy/name/description/icon/language references. The constructor does not enforce the source comment's slash-normalized hierarchy or icon dimension limit. No normalization or resizing is established by that carrier alone.

## Display content is built from live model metadata

With metadata present, buildDisplayInfo localizes metadata.name and metadata.tips, skipping blank results. Tips remove CR characters and split LF; each remaining line becomes a literal component. Authors use zero-based indexed metadata.authors.N.name/role keys in traversal order, with a mutable one-element counter captured by the mapper. An empty original author role bypasses role localization; a nonempty role is localized and prefixed to the author name. The license type is shown directly rather than looked up in model language files.

Detailed mode adds model path and hash, optional extra/random strings and a nonzero timestamp. Timestamp handling uses long multiplication by1000, Instant.ofEpochMilli, systemDefault zone and yyyy-MM-dd HH:mm:ss formatting. This is a seconds-to-milliseconds convention in the body, not checked arithmetic or a guaranteed valid timestamp range. Statistics add bones/cubes/faces and the player's texture-map size. No target metadata examples or actual rendered text were tested.

A new mutable component List is returned. The lookups read existing shared maps; constructing display components is not proof that the underlying model/language data are immutable or safe for concurrent mutation. [Model input carriers](MODEL-INPUT-CARRIERS-RECOVERY-2026-10-17.md) and [asset helpers](MODEL-ASSET-HELPERS-RECOVERY-2026-10-17.md) explain those ownership boundaries.

## Integration consequence

An adapter reproducing these semantics should not silently replace them with the common requested-key→English-key→default chain, force locale normalization or infer that every display field is translated. Keep model-local strings, vanilla translated UI labels, supplied metadata defaults and actual UI delivery separate.
