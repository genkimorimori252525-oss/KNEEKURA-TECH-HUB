# YSM Molang surface research — 2.6.5 release-line candidate

Research date: 2026-10-05  
Source candidate: `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`  
Status: **EVIDENCE_BACKED / STATIC**

## 1. Why Molang matters

In YSM 2.6.5, Molang is not merely a cosmetic arithmetic language. It is the presentation-side
control plane between Minecraft entity state, model/controller state and bounded effects.

The parser creates separate namespaces:

- `ysm` — YSM/environment/entity/model helpers
- `ctrl` — controller conditions and controller mutation
- `tlm` — Touhou Little Maid state
- `args` — user-function arguments
- `fn` — scoped user functions

Command completion additionally exposes standard `math` and `q` bindings.

Source locator:

- `client/animation/molang/CustomMolangParser.java`

## 2. Parser/runtime topology

The source candidate contains three related layers:

1. `client/animation/molang/` — 47 Java files
2. `geckolib3/core/molang/` — 102 Java files
3. `molang/` — 37 Java files containing lexer, parser, AST and evaluator/runtime types

The parser itself is pooled with `ConcurrentLinkedQueue<MolangParser>`; a rented parser is reset
before return.

The custom parser also recognizes a restricted "roaming assignment only" expression form for
`v.roaming.*`.

### Reusable lesson

Separate:

- parsing/AST;
- pure state query bindings;
- controller commands;
- effect emission;
- persistent/synchronized model variables.

That separation makes it possible to restrict or sandbox side effects without removing expressive
queries.

## 3. Direct `ysm` namespace surface

The following **110 registrations** are directly visible in `YSMBinding`. Optional integrations such
as Curios can add further bindings, so 110 is a lower bound for this source revision.

### 3.1 Functions — 23

- `dump_equipped_item`
- `dump_relative_block`
- `mod_version`
- `equipped_enchantment_level`
- `effect_level`
- `relative_block_name`
- `relative_block_name_any`
- `bone_rot`
- `bone_pos`
- `bone_scale`
- `bone_pivot_abs`
- `first_order`
- `second_order`
- `particle`
- `abs_particle`
- `perlin_noise`
- `play_sound`
- `stop_sound`
- `stop_all_sounds`
- `keyboard`
- `mouse`
- `sync`
- `defer`

### 3.2 Context/global variables — 7

- `dump_mods`
- `head_yaw`
- `head_pitch`
- `weather`
- `dimension_name`
- `fps`
- `time_delta`

### 3.3 Entity variables — 19

- `dump_effects`
- `dump_biome`
- `ground_speed2`
- `input_vertical`
- `input_horizontal`
- `person_view`
- `rendering_in_paperdoll`
- `rendering_in_inventory`
- `block_light`
- `sky_light`
- `is_passenger`
- `is_sleep`
- `is_sneak`
- `biome_category`
- `is_open_air`
- `eye_in_water`
- `frozen_ticks`
- `air_supply`
- `delta_movement_length`

### 3.4 Living-entity variables — 29

- `has_helmet`
- `has_chest_plate`
- `has_leggings`
- `has_boots`
- `has_mainhand`
- `has_offhand`
- `has_elytra`
- `is_riptide`
- `armor_value`
- `hurt_time`
- `is_close_eyes`
- `on_ladder`
- `ladder_facing`
- `arrow_count`
- `stinger_count`
- `entity_type`
- `is_player`
- `is_maid`
- `food_level`
- `xxa`
- `yya`
- `zza`
- `mainhand_charged_crossbow`
- `offhand_charged_crossbow`
- `is_fishing`
- `swinging`
- `swing_time`
- `swinging_arm`
- `attack_time`

Important generalization:

`entity_type` returns `player` for players, `maid` for the TLM maid type, otherwise the
registered Minecraft entity type ID. The model expression surface is therefore not fundamentally
limited to `Player`.

`food_level` deliberately returns 20 for non-player living entities as a compatibility fallback.

### 3.5 Player variables — 19

- `texture_name`
- `first_person_mod_hide`
- `has_left_shoulder_parrot`
- `has_right_shoulder_parrot`
- `left_shoulder_parrot_variant`
- `right_shoulder_parrot_variant`
- `attack_damage`
- `attack_speed`
- `attack_knockback`
- `movement_speed`
- `knockback_resistance`
- `luck`
- `block_reach`
- `entity_reach`
- `swim_speed`
- `entity_gravity`
- `step_height_addition`
- `nametag_distance`
- `in_shield_block_cooldown`

### 3.6 Client-player variables — 3

- `elytra_rot_x`
- `elytra_rot_y`
- `elytra_rot_z`

### 3.7 Local-player variables — 2

- `hit_target_id`
- `hit_target_type`

### 3.8 Projectile variables

Projectile:

- `projectile_owner`

Throwable item projectile:

- `throwable_item`

Fishing hook:

- `hooked_in`
- `is_biting`

Abstract arrow:

- `on_ground_time`
- `in_ground`
- `is_spectral_arrow`
- `shoot_item_id`

## 4. `ctrl` namespace

The `ctrl` namespace combines state classification with commands for the active coded controller.

### 4.1 Main-state conditions

Priority order in the source:

**HIGHEST**

- death
- riptide
- sleep
- swim
- climb
- climbing
- ladder_up
- ladder_stillness
- ladder_down

**HIGH**

- fly
- elytra_fly

**NORMAL**

- swim_stand
- attacked
- jump
- sneak
- sneaking

**LOW**

- run
- walk

**LOWEST**

- idle

The chosen main state is cached in the entity state tracker so repeated queries within the same
update do not rescan every condition.

For `walk`/`sneak`, this source's CtrlBinding uses the absolute interpolated
`walkAnimation.speed` and a minimum threshold of 0.05.

### 4.2 Condition helpers

- `hold`
- `swing`
- `use`
- `armor`
- `ride`

Optional mods add additional controller bindings.

### 4.3 Controller commands

- `set_animation`
- `set_beginning_transition_length`
- `reset`
- `indicate_reload`

Constants:

- `state_continue`
- `state_stop`
- `state_pause`
- `state_bypass`
- `loop`
- `play_once`
- `hold_on_last_frame`

Variable:

- `playing_extra_animation`

### Reusable lesson

Queries and commands belong to different semantic classes even if they share one expression
language.

KNEEKURA should mark every binding as one of:

- PURE_QUERY
- CONTROLLER_MUTATION
- LOCAL_VISUAL_EFFECT
- NETWORK_EFFECT
- DEBUG_ONLY

This is safer than treating all Molang functions as equivalent.

## 5. Effect emission is explicitly gated

Several YSM functions check `context.entity().allowEmitting()`.

Examples:

- particle / abs_particle
- play/stop sound
- sync
- defer

This matters because the same controller/expression can be evaluated more than once for different
render contexts.

### Particle

Particle emission refuses to run when emitting is disabled or when the animatable is a fake GUI
player.

### Sound

Sound play/stop functions also require emitting permission. Sound state is managed through a
per-context sound manager, with a UI-specific path for fake-player previews.

### Sync

`ysm.sync`:

- accepts at most 16 float arguments;
- for a local player with a remote YSM channel, sends `EmitMolangSync` to the server;
- a remote player does not independently emit the same sync;
- local/fake contexts can trigger the local model sync event path.

### Defer

`ysm.defer` only schedules a named deferred animation event when emitting is allowed and an
animation context exists.

### Reusable lesson

Evaluation and emission must be separate capabilities.

A future KNEEKURA expression engine should be able to evaluate a pose in:

- shadow pass;
- inventory preview;
- replay;
- correction pass;
- speculative/parallel pass

without repeating particles, sounds or network messages.

## 6. User functions

The `fn` binding resolves arbitrary named model user functions lazily from the current model
context and caches the resolved expression for the parser scope.

This provides a model-local composition mechanism without hard-coding every animation helper into
Java.

### Reusable lesson

User-defined functions are valuable, but cache identity must include the model generation. A model
hot swap must not allow a cached function from the old model to survive into the new one.

## 7. Roaming variables

The release-line player path contains explicit local/remote roaming-state machinery.

### LocalRoamingStruct

- maximum tracked names: 64
- maximum name length constant: 32
- values are floats
- changes are accumulated into a delta object
- `popChanges()` swaps the pending delta buffer and clears dirty state
- the delta includes `modelHashShort`

### RemoteRoamingStruct

- receives and applies integer-pooled-name -> float changes
- exposes a copy as a generic Struct

### Network message

`RoamingVarsChanges` carries:

- `modelHashShort`
- `entityId`
- server-bound name -> float values
- client-bound pooled-name -> float values

`SubmitRoamingVarsChanges` routes changes to a ServerPlayer capability or to the TLM compatibility
hook when the target is a maid.

### Critical TLM gap

The TLM server-side `handleVariableChanges` method is still TODO in this 2.6.5 candidate, and the
maid-side local/remote roaming methods are also unfinished.

This means **TLM model/animation support is real, but full roaming-variable parity with player
models is not established**.

## 8. Stable optional namespace pattern

`TLMBinding` exists even when Touhou Little Maid is not installed. The source comment explicitly
says this avoids animation errors.

The installed TLM adapter populates the namespace with real evaluators; otherwise the namespace
itself remains structurally present.

### Reusable lesson

Optional integrations should keep script schema stable:

~~~text
namespace exists
  |
integration available?
  | yes -> real values
  | no  -> neutral/default values
~~~

That is much safer for portable model packs than making the namespace disappear.

## 9. Security / determinism boundary for KNEEKURA

YSM 2.6.5 demonstrates why model scripting needs a capability model.

A KNEEKURA derivative should define:

| Capability | Examples | Worker-safe? | Repeat-safe? |
|---|---|---:|---:|
| pure state query | speed, pose, hurt, light | after snapshot | yes |
| bone query | current bone rotation/position | after pose snapshot | yes |
| controller mutation | set animation/reset | controller owner only | no |
| local effect | particle/sound | commit phase only | no |
| network effect | sync | owner/commit phase only | no |
| debug | dump state | explicit debug mode | context-dependent |

Do not let off-thread evaluation freely touch live Minecraft state or emit external effects.

## 10. KNEEKURA extraction

The useful reusable design is:

~~~text
ImmutablePresentationInput
        |
        +--> q / ysm-like pure query namespace
        |
        v
Molang AST + model-local functions
        |
        +--> controller decision
        |
        v
staged PoseState
        |
        +--> committed controller mutations
        +--> committed particles/sounds
        +--> committed network events
~~~

Attach a model-generation token to:

- cached user functions;
- deferred events;
- roaming deltas;
- queued Molang tasks.

That prevents old-model work from mutating a newly loaded model.

## 11. Evidence boundary

Established:

- parser/binding namespaces;
- 110 direct YSMBinding registrations;
- controller state/command surface;
- emission gating for key effects;
- roaming player-side structure;
- unfinished TLM roaming path.

Not established:

- exact distributed 2.6.5 binary/source equivalence;
- behavior of every optional-mod-added binding;
- runtime once-only guarantees under every render pass;
- performance budget of complex Molang;
- hostile/untrusted-expression robustness.

Those require separate runtime or focused security/performance work.


## Exact-artifact evaluation continuation

The bounded 2026-10-05 continuation maps ExecutionContext, Expression and ValueConversions and
14 methods. It resolves two integer ArgumentCollection overloads through their terminal converter
calls, records Exception-to-null wrapper behavior and primitive/string branch semantics, and retains
community creator scripts as future fixture leads only. See
[MOLANG-EVALUATION-RECOVERY-2026-10-05.md](MOLANG-EVALUATION-RECOVERY-2026-10-05.md).
