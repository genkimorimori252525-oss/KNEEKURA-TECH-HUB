# Legacy 1.7.10 Mob AI Role Catalog

Scope: major normal invasion actors plus relevant latent/defender actors in the uploaded 1.1.2 distribution.

## Shared strategic arbitration

`EntityIMLiving.updateAITick` applies:

```text
if attackTarget != null -> TARGET_ENTITY
else if targetNexus != null -> BREAK_NEXUS
else -> CHILL
```

Target selection runs before movement/action tasks. Local combat can therefore interrupt the strategic Nexus objective, while each mob's task stack decides how it fights or breaches.

`EntityAIAttackNexus` validates adjacency to the exact bound Nexus and normally deals 2 Nexus damage. `EntityAIGoToNexus` owns route requests, stuck detection, retry backoff and direct-motion fallback.

## Role matrix

| Actor | Primary role | Distinguishing behavior |
|---|---|---|
| Zombie T1/T2 | baseline melee breacher | destructive flavours dig; can wait/help Engineer |
| Zombie T3 Brute | shock melee | sprint/charge, high attack |
| Zombie Pigman | fast fire-immune breacher | digging + Engineer cooperation; T3 charge |
| Pigman Engineer | route specialist | dig + bridge + ladder/tower + scaffold + counterfactual infrastructure |
| Creeper | demolition escalation | strongly avoids walls in route cost, but commits to directional explosion when blocked |
| Thrower T1 | artillery + heavy breacher | boulders + custom obstruction clear |
| Thrower T2 | heavy artillery | TNT ranged attack, stronger destructiveness, knockback immune |
| Skeleton | ranged suppression | arrows; can halt advance while target is in LOS/range |
| Spider/Baby | climbing pressure | wall climb; baby pounce |
| Jumping Spider | leap assault | ballistic pounce |
| Mother Spider | force multiplier | timed egg laying; offspring contract yields six baby spiders |
| Imp | climbing fire pressure | melee hit ignites target |
| Burrower | 3D tunneling technology | custom 3D/parametric navigation + digging; latent in legacy waves |
| IM Wolf | Nexus defender | attacks IMob, doubled damage, heals on hit, can respawn near active Nexus |
| Bird/GiantBird/Vulture | aerial research | swoop/tackle/pickup test stack; debug-only legacy research |

## Engineer cooperation — clever but brittle

`EntityAITargetOnNoNexusPath` can select Pigman Engineer when the current route still ends too far from the Nexus. That Engineer is stored in the ordinary `attackTarget` slot.

A higher-priority `EntityAIWaitForEngy` interprets that target as an ally/follow target before lower-priority generic `EntityAIKillEntity(EntityLiving)` can treat it as prey.

Helpers can call `supportForTick`; the Engineer sets build rate to roughly `1.0 + supportThisTick * 0.33`.

This is economical, but it relies on task priority and target overloading. A modern design should separate strategic objective, hostile combat target and cooperation target.

## Creeper: avoid first, demolish second

Creeper makes collidable non-Nexus cells extremely expensive in path cost. Only when `onPathBlocked` fires does it derive a cardinal obstruction direction, set `commitToExplode`, hold the chosen side and detonate after the fuse.

Demolition is therefore an escalation after route failure, not the default movement rule.

## Thrower: bypass-world-edit warning

Thrower's `clearPoint` directly removes a small oriented block region; the source itself calls part of it a “cheat.” This bypass is less disciplined than `TerrainModifier` and illustrates why protected-object rules must be shared by **all** world-edit entry points.

## Capability composition

Spider roles are composed from tier/flavour plus task injection rather than one class per role: baby pounce, jumping pounce, mother egg-laying, etc. This is a useful capability-composition pattern.

## Unproven rally path

Spider installs `EntityAIRallyBehindEntity(... EntityIMCreeper ...)`, but the pinned target setup does not visibly install the complementary Creeper-selection path needed to prove that rally behavior is active. The helper exists; reliable runtime use is not asserted.
