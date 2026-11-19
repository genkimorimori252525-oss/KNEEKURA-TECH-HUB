# Wither: Reincarnated — Code Map

Scope: exact ANCHOR JAR SHA-256
`00589726de7d82628d92761394a8a3e6b153c28942f50c9ae6ba7860b0fab80a`.

This is a class-level map derived from the distribution JAR. It is not a source
tree and does not reproduce method bodies.

## Architecture

```text
minecraft:wither / WitherBoss
        |
        +-- WitherBossMixin -------------------- phase, damage, server AI, death,
        |                                        head positions, navigation hooks
        |
        +-- HandleWitherEvent ------------------ installs controllers/goals,
        |                                        possession selection, lifesteal
        |
        +-- WitherMoveControl
        +-- WitherNavigation
        |
        +-- goalSelector
        |    1  WitherBarrageGoal
        |    2  WitherLaserGoal
        |    3  WitherChargeGoal
        |    4  WitherBackUpGoal
        |    5  WitherRangedAttackGoal
        |    6  WitherRandomTravelGoal
        |    7  look-at-player
        |    8  random-look
        |
        +-- targetSelector
             hurt-by / player / generic living target
```

The priorities above were recovered from the v1.0.5 static installation path.
They describe this exact binary only.

## Core package groups

| Area | Main classes | Role |
|---|---|---|
| entry/config | `WitherReincarnated`, `WRCommonConfig`, `WRClientConfig` | registration and tunables |
| Wither flight | `WitherMoveControl`, `WitherNavigation` | smooth free-flight steering/path following |
| Wither attacks | `WitherChargeGoal`, `WitherLaserGoal`, `WitherBarrageGoal`, `WitherRangedAttackGoal`, `WitherBackUpGoal` | discrete attack/movement states |
| roaming | `WitherRandomTravelGoal` | long-range travel/reposition |
| targeting | `WitherTargetNearestPlayerGoal`, `AdvancedNearestAttackableTargetGoal` | health/state-gated target choice |
| possession | `PossessedCapability`, possessed goals, `HandlePossessedMobsEvent` | temporary undead ownership/alliance state |
| world/combat events | `HandleWitherEvent`, `ModifyAIEvent` | goal injection, fear behavior, lifesteal and environmental interaction |
| projectiles | `WitherSkullMixin`, `ProjectileMixin`, `ExplosionMixin` | skull damage/explosion/deflection/lifetime |
| network | `Messages` + six clientbound packet classes | compact server-to-client state/event sync |
| client state | `HandleAnimationsEvent`, `HandleWitherMusicEvent`, `ParticleSpawnersEvent` | derived animation/audio/FX state |
| render | `BetterWitherRenderer`, `BetterWitherSkullRenderer`, model/layer classes | custom boss/skull appearance and beam |
| audio | `WitherSoundInstance`, `WitherMusicSoundInstance`, laser/weak loop classes | entity-following loops and music |
| compatibility/data | `TagInit`, entity/biome tags | data-driven opt-outs |

## Mixin surface

Common Mixins:

- `WitherBossMixin`
- `LivingEntityMixin`
- `WitherSkullMixin`
- `ExplosionMixin`
- `MobMixin`
- `ItemMixin`
- `EntityMixin`
- `RandomStrollGoalMixin`
- `PlayerMixin`
- `ProjectileMixin`
- `DefaultAttributesMixin`

Client Mixins:

- `MinecraftMixin`
- `SimpleSoundInstanceMixin`
- `LevelRendererMixin`
- `LivingEntityRendererMixin`
- `ClientPacketListenerMixin`
- `AbstractSoundInstanceMixin`
- `BossEventMixin`

Engineering implication: the MOD combines ordinary Forge events/Goals with
fairly broad vanilla patching. That is effective for a global Wither overhaul,
but it increases compatibility surface and is not automatically appropriate for
standalone custom bosses.

## Data-driven compatibility boundaries

The JAR contains entity-type tags for:

- entities that do not flee from the Wither;
- entities the Wither cannot possess;
- entities the Wither will not attack.

It also contains a biome tag used by Wither travel logic to avoid unsuitable
water-biome destinations.

This pattern is worth retaining: cross-MOD exceptions should be exposed as data
where possible rather than hard-coded class lists.

## Packet surface

Exactly six dedicated clientbound packet classes were found:

1. camera shake;
2. laser start;
3. laser update;
4. possession update;
5. skull blast;
6. Wither animation start.

The network design is intentionally much smaller than the client presentation
state. Client systems reconstruct animation, beam, sound and particles from these
small state/event messages.
