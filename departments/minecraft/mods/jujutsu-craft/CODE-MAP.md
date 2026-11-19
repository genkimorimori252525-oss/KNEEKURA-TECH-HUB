# Code map

## Bootstrap / registry

- `net.mcreator.jujutsucraft.JujutsucraftMod`
- `init/JujutsucraftModEntities`
- `init/JujutsucraftModItems`
- `init/JujutsucraftModMobEffects`
- `init/JujutsucraftModParticleTypes`
- `init/JujutsucraftModSounds`

## Combat core

- `procedure/RangeAttackProcedure`
- `procedure/DamageFixProcedure`
- `procedure/BlockDestroyAllDirectionProcedure`
- `procedure/LogicAttackDomainProcedure`
- `procedure/LogicSimpleDomainProcedure`
- `procedure/WhenEntityAttacked1Procedure`
- `procedure/WhenEntityAttacked2Procedure`

## Gojo

- `procedure/CursedTechniqueGojoProcedure`
- `procedure/InfinityProcedure`
- `procedure/InfinityActiveTickProcedure`
- `procedure/AntiInfinityProcedure`
- `procedure/TechniqueBlueProcedure`
- `procedure/AIBlueProcedure`
- `entity/BlueEntity`
- `procedure/TechniqueRedProcedure`
- `procedure/AIRedProcedure`
- `entity/RedEntity`
- `procedure/HollowPurpleProcedure`
- `procedure/AIPurpleProcedure`
- `entity/PurpleEntity`

## Sukuna

- `procedure/CursedTechniqueSukunaProcedure`
- `procedure/DismantleProcedure`
- `entity/ProjectileSlashEntity`
- `procedure/CleaveProcedure`
- `procedure/MalevolentShrineProcedure`
- `procedure/MalevolentShrineActiveProcedure`

## Domains

- `entity/DomainExpansionEntity`
- `procedure/DomainExpansionCreateBarrierProcedure`
- `procedure/DomainExpansionOnEffectActiveTickProcedure`
- `procedure/DomainExpansionBattleProcedure`
- `procedure/SimpleDomainOnEffectActiveTickProcedure`
- `procedure/DomainAmplificationOnEffectActiveTickProcedure`

## Mahoraga / Ten Shadows

- `procedure/TenShadowsTechniqueProcedure`
- `procedure/CursedTechniqueMahoragaProcedure`
- `procedure/AIEightHandledSwrodDivergentSilaDivineGeneralMahoragaProcedure`
- `procedure/MahoragaCutTheWorldProcedure`
- `procedure/SelectMahoragaProcedure`
- `procedure/SummonMahoragaProcedure`
- adaptation logic also appears in `WhenEntityAttacked1Procedure`, `EntityActiveProcedure`, `AntiInfinityProcedure`

## Animation / sync

- `procedure/SetupAnimationsProcedure`
- `procedure/PlayAnimationProcedure`
- `procedure/PlayAnimationEntityProcedure`
- `procedure/PlayAnimationEntity2Procedure`
- `network/*`
- `PacketHandler`
- `PlayerVelocityPacket`

## Persistent state

- `JujutsucraftModVariables.PlayerVariables`
- `JujutsucraftModVariables.WorldVariables`

The dominant architectural fact is that behavior is spread across many generated Procedure classes. Class names are discovery hints; call paths and shared helper usage control claims.
