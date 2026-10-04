# YSM x Touhou Little Maid integration research — 2.6.5 release-line candidate

Research date: 2026-10-05  
Source candidate: `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`  
Status: **EVIDENCE_BACKED / STATIC**

## 1. Main conclusion

YSM's TLM integration proves an important point for KNEEKURA:

> A non-player gameplay entity can keep its own entity class, AI and game semantics while receiving
> a YSM-style per-entity presentation runtime.

The 2.6.5 candidate does **not** convert `EntityMaid` into a Player.

Instead it attaches a client capability that lazily creates:

`CustomYsmMaidEntity extends CustomHumanoidEntity<EntityMaid>`

This wrapper owns presentation/animation state around the real maid.

That is the strongest reference currently found for a future Reimu/YSM entity architecture.

## 2. Attachment path

On the client, `SyncCapability` listens for entity capability attachment.

For each client-side `EntityMaid`, it installs:

- capability ID: `yes_steve_model:ysm_maid`
- provider: `YsmMaidCapabilityProvider`

The provider lazily constructs:

`new CustomYsmMaidEntity(maid, true)`

The second argument enables the async-capable presentation path.

### Reusable topology

~~~text
EntityMaid
  |  owns AI / tasks / combat / favorability / gameplay identity
  |
  +--> YsmMaidCapabilityProvider
          |
          v
      CustomYsmMaidEntity
          | owns model/controller/Molang/presentation state
          v
      CustomYsmMaidRenderer
~~~

The gameplay entity remains authoritative.

## 3. Model asset reuse

`CustomYsmMaidEntity.onSetupAnimationController()` uses:

`getModelContainer().playerModel().maidControllerFactory()`

The integration therefore reuses the same broader player-model asset object while selecting a
maid-specific controller factory.

The wrapper also exposes the loaded YSM geometry through TLM's `IGeoEntity` interface.

### Reusable lesson

Do not fork the entire model format for every entity species.

Prefer:

- shared model/animation asset schema;
- entity-type-specific controller factory;
- adapter for the host entity's state;
- entity-type-specific semantic bindings.

## 4. TLM-specific Molang namespace

The TLM adapter registers 16 maid-specific values:

- `tlm.is_begging`
- `tlm.is_sitting`
- `tlm.has_backpack`
- `tlm.favorability_point`
- `tlm.favorability_level`
- `tlm.task_id`
- `tlm.schedule`
- `tlm.activity`
- `tlm.gomoku_win_count`
- `tlm.gomoku_rank`
- `tlm.game_statue`
- `tlm.backpack_type`
- `tlm.is_entity`
- `tlm.is_statue`
- `tlm.is_garage_kit`
- `tlm.show_item`

For a non-maid living entity the TLM evaluator returns a neutral value rather than failing.

Separately, the generic YSM namespace exposes:

- `ysm.entity_type`
- `ysm.is_player`
- `ysm.is_maid`

and `ysm.is_fishing` explicitly supports both Player fishing and TLM maid fishing.

### Reusable lesson

Use two layers:

- generic presentation semantics: entity type, locomotion, equipment, damage, pose;
- adapter namespace: maid task/favorability/backpack/game state.

This prevents the generic animation engine from importing TLM classes everywhere.

## 5. Maid controller stack

`MaidControllerCollection` builds a layered controller set from the same model assets.

### Pre-parallel

- `pre_parallel`

### Vehicle

- `vehicle`

### Main locomotion/action

- `pre_main`
- `main`
- `post_main`

### Held items

- `pre_hold`
- `hold_offhand`
- `hold_mainhand`
- `post_hold`

### Gun integration

- `fire` when the gun-fire predicate is available

### Swing

- `pre_swing`
- `swing`
- `post_swing`

### Use

- `pre_use`
- `use`
- `post_use`

### Maid-specific

- `misc`
- `cap` for roulette/extra animation
- `statue`

### Remaining layers

- `passenger`
- `parallel`
- `armor`

Most use `HybridAnimationController`; the roulette/cap layer uses
`CodedAnimationController`.

### Reusable lesson

Presentation is composed from orthogonal layers. A character does not need one monolithic
"current animation".

For KNEEKURA, likely layers are:

- locomotion/base pose;
- upper-body item/weapon;
- attack action;
- damage/reaction;
- expression;
- special character action;
- attachment/equipment;
- parallel ambient motion.

## 6. Main animation authority

`YsmMaidMainPredicate`:

1. rejects preview/null cases;
2. suppresses main locomotion when maid render state is not ENTITY;
3. suppresses it while a live vehicle is handled separately;
4. scans registered animation states by priority;
5. checks SlashBlade then TaCZ integration before falling back to normal animation playback.

### Reusable lesson

A main locomotion controller should not fight specialized controllers.

Special contexts — statue, vehicle, combat integration — should explicitly claim or suppress the base
layer.

## 7. Maid-specific actions

### Misc

`MaidMiscPredicate` provides:

- `game_win`
- `game_lost`
- `beg`

Game win/loss while seated takes priority over begging.

### Statue/display

`MaidStatuePredicate` maps:

- STATUE -> `statue`
- GARAGE_KIT -> `garage_kit`

### Vehicle/activity

`MaidVehiclePredicate` maps TLM contexts:

- Gomoku seat -> `gomoku`
- bookshelf -> `bookshelf`
- computer -> `computer`
- keyboard -> `keyboard`
- home meal -> `picnic`
- chair -> `chair`
- broom -> `broom`

### Roulette / extra animation

`MaidRoulettePredicate`:

- supports preview animation;
- plays the maid's selected roulette animation;
- uses a dirty flag to tell the coded controller to reload when the selection changes.

Server/common code resolves the selected extra animation from model properties and either a
classification map or default ordered map.

## 8. Renderer bridge

`TlmClientCompatInner` installs `CustomYsmMaidRenderer` into TLM's exposed
`YSM_ENTITY_MAID_RENDERER` hook.

This is a clean integration point because TLM explicitly owns the renderer hook while YSM supplies
the implementation when a maid is using a YSM model.

### Reusable lesson

Prefer an explicit host-mod adapter/hook over global renderer interception when one is available.

## 9. Projectile and vehicle presentation inheritance

When a YSM maid becomes a projectile owner, YSM:

1. finds the projectile model-info capability;
2. initializes it with the maid's YSM model ID;
3. broadcasts `SyncProjectileModelInfo` to visible players.

For a vehicle whose first passenger is the maid, YSM similarly:

1. updates vehicle model info with the maid's model ID;
2. broadcasts `SyncVehicleModelInfo`.

This is **presentation identity propagation**, not entity identity replacement.

### Critical limitation

Both paths contain TODOs for maid roaming-variable propagation and currently pass an empty float map.

Therefore:

- model identity propagation: **ESTABLISHED**
- full model-variable state propagation: **NOT ESTABLISHED**

## 10. Roaming variables are the biggest unfinished TLM seam

The player-side release-line code has a real local/remote roaming-variable protocol.

The TLM path is visibly unfinished in four places:

1. `CustomYsmMaidEntity.setRemoteStruct` — TODO
2. `CustomYsmMaidEntity.updateRoamingVars` — TODO
3. `CustomYsmMaidEntity.getRemoteStruct` — TODO / returns null
4. server/common `TlmCommonCompatInner.handleVariableChanges` — TODO

Additionally, `UpdateRemoteStruct` contains a commented-out "under construction" subscriber, and
`YsmMaidTickEvent.submitRoamingVariableChanges` is TODO.

### Consequence

A model whose important state depends on synchronized `v.roaming.*` variables should not be assumed
to behave identically on maid and player in this source candidate.

### KNEEKURA lesson

If Reimu or another non-player YSM-style entity needs persistent custom animation state, make that
state transport a first-class contract instead of an afterthought.

Recommended contract:

~~~text
PresentationVariableSnapshot {
  entityId
  modelGeneration
  revision
  typed/scoped values
}
~~~

Then define exactly:

- who may write;
- who owns authoritative values;
- local prediction policy;
- server validation;
- observer replication;
- model-swap invalidation.

## 11. Optional integration namespace remains stable

The generic `TLMBinding` class is created even if Touhou Little Maid is absent. Its own source
comment says the TLM Molang namespace should still exist, otherwise animations would error.

This is an excellent compatibility technique for portable models.

KNEEKURA should do the same for optional character adapters: missing integrations return neutral
values, not missing symbols.

## 12. What this means for Reimu

For a future independent Reimu mob or a TLM-backed Reimu, the strongest extracted design is:

~~~text
Reimu gameplay entity
  |-- AI / combat / navigation / damage / ownership
  |
  +--> PresentationCapability<Reimu>
        |-- immutable sampled state
        |-- YSM-style Molang namespace
        |-- controller stack
        |-- model identity + generation
        |-- custom/repl. variables
        v
      PoseState
        v
      renderer adapter
~~~

Do **not** make a visual `ServerPlayer` the architectural foundation unless a specific dependency
forces it.

If player-only behavior is required, expose a narrow compatibility adapter for that behavior rather
than changing the gameplay entity's identity.

## 13. What is transferable immediately

High-confidence reusable techniques:

1. lazy per-entity presentation capability;
2. shared asset format + entity-specific controller factory;
3. generic state namespace + adapter-specific namespace;
4. layered controller composition;
5. host-owned gameplay, renderer-owned presentation;
6. model-ID propagation to related presentation entities;
7. stable optional namespaces;
8. async-capable presentation wrapper;
9. render-state-specific suppression of base animation;
10. explicit extra-animation dirty/reload signal.

Needs redesign before reuse:

1. roaming-variable transport for non-player entities;
2. TLM conversion cache living inside generic `GeoModelState`;
3. direct optional-mod types leaking into generic paths;
4. live mutable state reads during async animation evaluation;
5. generation/revision semantics around model hot swap.

## 14. Evidence boundary

Established from official source candidate:

- capability attachment;
- maid wrapper type;
- async presentation wrapper creation;
- renderer hook;
- model/controller asset reuse;
- controller layers;
- 16 TLM Molang variables;
- maid-specific animations;
- model-ID propagation to projectile/vehicle;
- incomplete roaming implementation.

Not established:

- exact distributed JAR equivalence;
- runtime parity of every maid/player model feature;
- multiplayer roaming-variable behavior for maids;
- all combinations with TaCZ/SlashBlade/other integrations;
- performance with many YSM maids.

Those remain runtime-test targets.
