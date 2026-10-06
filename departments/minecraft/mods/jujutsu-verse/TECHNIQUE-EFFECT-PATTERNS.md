# Technique effect patterns

This document extracts representative reusable implementation patterns rather than listing every character move.

## Hollow Purple — persistent destructive actor

Purple_tickProcedure combines:
- persistent entity motion
- Hollow Purple particles
- large spherical/AABB searches
- custom purple damage source
- block destruction helpers
- screen shake
- explicit despawn/lifetime behavior

It maintains named motion/spatial state instead of relying only on vanilla projectile physics.

Reusable pattern:
technique actor = motion state + visual emission + collision/AoE + world interaction + lifespan.

## Blue — synchronized vacuum field

Blue_entity_tickProcedure reads BlueentityEntity synchronized radius/yaw and uses:
- GetLookBlockProcedure
- VacumeBlockVectorProcedure
- SphereBlockTickProcedure
- block destruction
- repeated nearby-entity scans
- Blue particle types 1/2/3
- screen shake
- vacuum force / maximum vacuum parameters

Reusable pattern:
field actor with synced radius/orientation; tick resolves pull vectors and environmental response.

## Dismantle — sampled slash path

Dismantle_tickProcedure separates:
- DismantleDamageProcedure
- DismantleBreakProcedure

The main path advances in 0.5-unit sampling increments and uses delayed server work for cleanup/despawn state.

Reusable pattern:
analytical slash = sampled path + damage resolver + separate world-cut resolver.

## Fuga / fire-open VFX — mathematical path generation

FugaFlameParticleProcedure builds structure before randomness.

It creates:
- two moving/noisy rings with base radii around 35 and 80
- 12 and 20 points per tick
- opposite phase offsets driven by entity tick
- radial noise from sin/cos combinations
- wave-like Y displacement
- scatter particles
- six radial branches with multiple distance samples and zig-zag angle noise

The generated particle command targets jujutsu_kaisen:open_particle.

Reusable pattern:
structured VFX topology first, noise second.

## Piercing Blood — UUID-linked render relation

RenderPiercingBloodProcedure reads PiercingbloodentityEntity.DATA_UUID and interpolates spatial vectors client-side.

Reusable pattern:
a beam/projectile render actor can carry compact identity links and reconstruct the visible connection locally.

## Black Flash — marker entity + procedural renderer

A short-lived BlackflashEntityEntity provides event position/time while BlackFlashRenderer creates the high-density spectacle.

Reusable pattern:
synchronize the event, not every visible fragment.

## Projection Sorcery — intervention in rendering rules

Projection Sorcery uses dedicated mixins for:
- freeze behavior
- vanilla LivingEntity rendering
- GeckoLib rendering
- frustum/culling behavior

ProjectionflameEntity acts as a frame/reference actor.

Reusable pattern:
when a technique changes the rules of time/frame presentation, renderer/mixin intervention can be more faithful than another particle cloud.
