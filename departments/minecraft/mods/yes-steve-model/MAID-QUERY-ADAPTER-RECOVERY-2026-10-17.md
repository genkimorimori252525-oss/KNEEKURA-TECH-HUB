# Optional maid query adapter

PRIMARY_STATIC_REVIEW_ONLY; artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Captures 53 declarations across TLMBinding (`oOO0O0o0ooO0O0o0oo0oOooO`), TlmClientCompat (`OoOo0Oo0O0oOooOoOoOooOO0`), and TLMBindingInner (`oo0ooO0Oo00oo0oOOooOooOO`). Extra compat methods are supporting snapshots, not proof of external renderer/controller implementation. Central map unchanged; independent semantic review and target runtime NOT_RUN.

## Availability is a cached initialization decision

INSTALLED starts false. init looks up locally loaded `touhou_little_maid`, then checks Maven version range literal `[1.1.15,)`. In-range sets true; out-of-range uses `!FMLEnvironment.production`. Missing mod leaves the initial false. When enabled, initialization calls event, renderer and animation-state registration adapters. No external provider or supported-version behavior was executed.

TLMBinding uses LazyValue construction. Its constructor asks TlmClientCompat.addBinding to choose real versus empty registrations based on INSTALLED at construction. These captured classes do not themselves rebuild an existing binding when INSTALLED changes. Actual first-access/init ordering is not proved here, so an early-construction concern is conditional, not a reproduced defect.

## Sixteen names in both branches

Both branches register the same livingEntityVar names. With no enabled provider, callbacks return:

- false: is_begging, is_sitting, has_backpack, is_statue, is_garage_kit
- Integer 0: favorability_point, favorability_level, gomoku_win_count
- Integer 1: gomoku_rank
- true: is_entity
- empty String: task_id, schedule, activity, game_statue, backpack_type, show_item

These are not universal provider-status indicators. `is_entity` true is a fallback on any valid LivingEntity context, not evidence that the provider is installed.

With provider enabled, each callback is wrapped by checkMaid. A LivingEntity that is not EntityMaid returns boxed Integer 0 for every name, including normally string-valued names. An invalid nonliving context is separately handled by ContextVariable's typed guard. A valid EntityMaid passes raw callback result through; do not assume normalization to String/Float.

Real callback routes:

- is_begging/is_sitting/has_backpack use external EntityMaid/IMaid methods.
- favorability_point uses getFavorability; favorability_level follows getFavorabilityManager().getLevel().
- task_id returns getTask().getUid() directly, without a local toString. Preserve external return type rather than inventing a string conversion.
- schedule lowercases the external schedule enum name with Locale.ENGLISH; activity returns scheduleDetail.getName().
- gomoku_win_count reads record manager; gomoku_rank calls MaidGomokuAI.getRank.
- game_statue (literal spelling retained): only when vehicle is EntitySit, return `win` before testing `lost`; otherwise empty string.
- backpack_type converts the backpack type ID toString.
- is_entity/is_statue/is_garage_kit compare public renderState to the three external MaidRenderState enum fields.
- show_item returns empty for empty shown backpack item or missing registry key, otherwise item key string.

## Reuse boundary

Choose absent-provider, wrong-entity and active-maid cases separately: they have different defaults/types. This adapter connects external state to Molang but does not explain provider AI, inventory mutation or actual rendering. The fixed base171 query/YSM lookup excludes this separate namespace; do not add its counts to semantic completion. The scoped integrity auditor verifies bytecode/bootstrap/source snapshots, not optional-mod compatibility. See [typed guards](TYPED-QUERY-GUARDS-RECOVERY-2026-10-17.md) and [parser binding lifetime](PARSER-POOL-LIFETIME-RECOVERY-2026-10-17.md).
