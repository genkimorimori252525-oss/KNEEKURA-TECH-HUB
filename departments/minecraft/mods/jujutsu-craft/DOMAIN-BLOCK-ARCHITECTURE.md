# Domain block architecture — Jujutsu Craft ver50.1

Status: **ORIGINAL_BINARY static analysis / runtime NOT_RUN**

This document treats Domain Expansion as temporary world geometry, not only as a combat effect.

## 1. Shared radius and center

Global `MapVariables.DomainExpansionRadius` defaults to **22.0 blocks**.

The common builder works around persistent domain centers such as:

- `x_pos_doma2`
- `y_pos_doma2`
- `z_pos_doma2`

At the default radius the enclosing scan cube is 45×45×45, but the code does **not** replace every block in that cube.

Placement is constrained by spherical/radial bands and construction counters, so the domain grows in staged layers.

## 2. Three palette roles

`GetDomainBlockProcedure` writes three block-state strings:

- `domain_outside`
- `domain_inside`
- `domain_floor`

Default palette:

- outside: `jujutsucraft:jujutsu_barrier`
- inside: `jujutsucraft:block_universe`
- floor: `jujutsucraft:block_universe`

Character domains override those roles.

## 3. Basic closed-domain geometry

For normal closed domains, `DomainExpansionBattleProcedure` constructs a spherical shell.

Broad structure:

```text
outermost radial band
  -> domain_outside

inner shell bands
  -> domain_inside
     or in_barrier for patterned / invisible cells

lower/interior surface
  -> domain_floor
     plus domain-specific terrain rules
```

The outer shell is therefore independent from the visual interior/floor palette.

## 4. Shell thickness

Shell thickness is a semantic parameter.

- normal: **1 block**
- caster with `ZONE` effect: **3 blocks**
- Idle Death Gamble / domain ID29: **10 blocks**

ID29 therefore encodes arena robustness/appearance directly in the common geometry algorithm.

## 5. Closed vs open-type builder mode

Domain state stores a numeric mode in `cnt2`.

Observed modes:

- `0` — normal closed-domain route
- `>0` — open-type route used by mastered Malevolent Shrine / Womb Profusion paths
- `-1` — Megumi special route

A critical bytecode detail is that `DomainExpansionBattleProcedure` converts `cnt2>0` into an open-mode boolean.

When open mode is active, the normal shell-construction branch is skipped. The builder only performs barrier material work in a **Cover/clash-repair** case and only where an existing barrier-tag block is present.

So in current ver50.1 the open-type mode is not merely “same sphere with another texture”; it suppresses ordinary enclosing-barrier construction while retaining clash/cover interoperability.

## 6. Open-barrier eligibility

Malevolent Shrine (ID1) and Womb Profusion (ID18) can enter the open-type mode when the relevant mastery/Sukuna-or-Kenjaku state is present.

For players, the open route is suppressed while sneaking.

The code also contains a very rare progression path that can grant the `jujutsucraft:mastery_open_barrier_type_domain` advancement.

The exact player-facing progression experience remains runtime NOT_RUN.

## 7. Reversible world overlay

Domain construction is designed to be reversible.

When a barrier-tag block replaces a world block:

1. current block state is serialized to text;
2. the barrier BlockEntity stores it in persistent NBT as `old_block`;
3. nested/barrier-replacement paths preserve underlying barrier information;
4. domain teardown calls `JujutsuBarrierUpdateTickProcedure`;
5. `old_block` is parsed and restored.

`AIDomainExpansionEntityProcedure` drives the break/cleanup scan.

The important invariant is:

```text
original world
  + temporary domain overlay
  -> combat
  -> restore original block state
```

This is safer and more composable than treating a domain as permanent world generation.

## 8. Barrier block physics

`JujutsuBarrierBlock` uses effectively indestructible/high-resistance properties and delegates collision to `CanPassThroughBarriersProcedure`.

Pass-through condition includes:

- player `PlayerCursePowerMAX == 0`; or
- entity type tagged `forge:no_curse_power`.

For those entities, collision can be empty from side/below while the top remains standable.

Cursed-energy actors receive normal solid barrier collision.

This encodes “who can interact with the supernatural barrier” into collision policy rather than only visual effects.

## 9. InBarrier filler

`InBarrierBlock` has empty collision/outline shape and WALKABLE path type.

It is used as logical/invisible filler in patterned shell areas.

This lets the builder distinguish:

- solid visible domain interior material;
- logical barrier volume that should not be a normal solid block.

## 10. Malevolent Shrine inner pattern — ID1

Palette:

- inside: `domain_bone`
- floor: `block_red`

For closed/cover shell construction, the inner shell is patterned.

Bone cells are selected on specific horizontal/modulo bands; other cells use `in_barrier`.

This produces a perforated/grid-like interior instead of a uniformly solid sphere.

In mastered open mode the ordinary enclosing sphere branch is suppressed, as described above.

## 11. Unlimited Void — ID2

Palette:

- inside: `block_universe`
- floor: `block_universe`

It uses the common spherical construction without a special terrain algorithm in `DomainExpansionBattleProcedure`.

Its uniqueness is primarily the domain attack/effect payload rather than custom floor topology.

## 12. Inumaki domain — ID3

Palette:

- inside: `domain_blue_sky`
- floor: default universe unless changed elsewhere

Uses common spherical construction.

## 13. Coffin of the Iron Mountain — ID4

Uses dedicated volcanic interior/floor block materials from the Coffin-of-Iron-Mountain block set.

The geometry remains common; the palette carries most of the arena identity.

## 14. Authentic Mutual Love — ID5

Palette:

- inside: universe
- floor: gravel

Shared closed-domain geometry.

## 15. Chimera Shadow Garden — ID6

Palette:

- universe-style inside/floor

Megumi paths can place `cnt2=-1`, giving the domain a special lifecycle/builder mode distinct from both normal closed `0` and mastered open `+1`.

Do not equate that numeric state to every lore detail without runtime evidence; the distinct implementation mode is directly established.

## 16. Kashimo domain — ID7

Palette:

- cloud
- cloud

Shared domain geometry.

## 17. Horizon of Captivating Skandha — ID8

This domain has one of the strongest custom terrain algorithms.

The lower/interior area uses radial thresholds to select:

- central `domain_grass`
- outer `domain_sand`
- intermediate/lower `domain_water`

Resulting topology is effectively:

```text
central island / grass
  -> beach / sand
     -> surrounding water
        -> enclosing domain shell
```

This is true block-level arena generation, not merely a texture swap.

## 18. Tsukumo domain — ID9

Uses a sand-oriented floor with common shell logic.

## 19. Choso domain — ID10

Palette:

- blood
- blood

Shared geometry.

## 20. Meimei domain — ID11

Palette:

- cloud
- podzol

Shared geometry.

## 21. Ishigori domain — ID12

Palette:

- universe
- black sand

Shared geometry.

## 22. Nanami domain — ID13

Palette:

- universe
- stone bricks

Shared geometry.

## 23. Ceremonial Sea of Light / Hanami — ID14

Palette:

- blue sky
- flower floor

Shared shell plus themed floor.

## 24. Self-Embodiment of Perfection — ID15

Palette:

- bone inside
- universe floor

ID15 has a special **three-axis modulo-5** rule.

Depending on x/y/z modulo conditions, a cell becomes:

- visible bone interior material; or
- `in_barrier`.

This creates a web/lattice-like inner shell rather than a plain surface.

## 25. Womb Profusion — ID18

Palette:

- blood inside
- red floor

Like Malevolent Shrine, ID18 can enter the open-type `cnt2>0` route for the appropriate mastered/Kenjaku state.

Normal shell generation is suppressed in that open mode except for cover/clash repair.

## 26. Time Cell Moon Palace — ID19

Direct named domain procedure exists.

No unique palette branch was identified in `GetDomainBlockProcedure`, so it falls back to the default palette unless another runtime path modifies it.

This distinction is intentionally recorded rather than inventing themed blocks from the domain name.

## 27. Itadori domain — ID21

This domain has custom lower/interior geometry.

The builder uses combinations of:

- `domain_water`
- its selected `domain_floor`
- `domain_fence`
- `in_barrier`

to create layered water/floor/fence structure in the lower arena.

The exact visual arrangement should be runtime-captured before making a screenshot-level claim, but the custom block topology is static-code established.

## 28. Deadly Sentencing — ID27

The floor has a radial split.

- inner radial area -> domain floor / plank-like material
- outer floor -> `domain_stone_bricks`

This creates an explicitly authored courtroom-like arena partition under the common sphere.

Judgeman/trial semantics remain separate from the physical shell.

## 29. Angel domain — ID28

Palette:

- blue sky inside
- cloud floor

Dedicated domain/temple actor supplies additional presentation.

## 30. Idle Death Gamble — ID29

Palette:

- white inside
- white floor

Special construction rule:

**shell thickness = 10 blocks**

instead of the normal one-block shell.

Domain lifetime also uses a special longer duration path (3600 ticks vs the common 1200 in the observed creation flow).

This is the clearest example of domain gameplay modifying the common builder itself.

## 31. Uraume generic family domain — ID24 route

The generic family-domain route maps the Uraume family to:

- ice inside
- ice floor

It is a generic-family domain path rather than a separately named dedicated Procedure in the same sense as the directly named domains above.

## 32. Kugisaki domain — ID34

Direct named domain route.

Palette uses a podzol-like floor with common outer shell.

## 33. Uro domain — ID38

Palette:

- universe
- universe

Uses common geometry.

## 34. Threefold Affliction — ID39

Palette:

- white
- white

Yorozu's technique payload/True Sphere semantics are separate from the common physical barrier.

## 35. Rozetsu domain — ID43

Palette:

- dark stone
- dark stone

Direct named domain route.

## 36. Other observed palette families

`GetDomainBlockProcedure` also contains family-indexed palette branches used by the generic `OtherDomainExpansionProcedure`.

Examples include:

- Kurourushi ID23: bone / red
- Graveyard ID25: default / gravel
- Ogi-family ID26: default / gravel
- Chojuro ID32: sand / sand
- Yaga ID33: red / planks
- Nishimiya-family ID36: default / cloud
- Ino-family ID40: default / dark stone
- Crystal Curse ID47: cloud / Coffin-of-Iron-Mountain material

These are described as family/generic routes unless a separately named domain Procedure was directly confirmed.

## 37. Domain overlap / clash

Domain creation scans nearby domain users and existing domain state.

Shared persistent state includes concepts such as:

- `Failed`
- `Cover`
- cover count
- domain centers
- select / skill_domain
- mode `cnt2`

When domains overlap, the engine can enter failure/cover/rebuild states rather than simply placing a second independent sphere.

Existing barrier `old_block` information lets a clash rebuild/replace barrier material without permanently losing the pre-domain world.

## 38. Common sure-hit / DomainAttack policy

Domain payloads mark attacks with persistent `DomainAttack`.

`LogicAttackProcedure` sees the flag and delegates target acceptance to `LogicAttackDomainProcedure`.

That policy considers:

- domain ownership/state;
- selected domain;
- Simple Domain-related state;
- Neutralization;
- failure/cover/clash state;
- target/caster relations.

The exact payload remains character-specific, but “this attack is a domain attack and should use domain target policy” is shared infrastructure.

## 39. Anti-domain systems

The mod keeps counter techniques semantically separate:

- Simple Domain
- Domain Amplification
- Hollow Wicker Basket
- Falling Blossom Emotion
- Neutralization

They are effects/capabilities interpreted by common combat/domain gates rather than one generic “domain immunity” boolean.

Domain Amplification is additionally part of Infinity bypass policy.

## 40. Engineering extraction

The reusable architecture is:

```text
DomainDefinition
  radius / mode / palette / thickness / custom terrain

DomainBuilder
  staged reversible block overlay

DomainState
  owner / center / cover / failed / clash / mode

DomainPayload
  character-specific sure-hit/effects

CounterPolicy
  simple domain / amplification / basket / neutralization

DomainTeardown
  restore old_block
```

That separation is the strongest part of the current domain implementation.
