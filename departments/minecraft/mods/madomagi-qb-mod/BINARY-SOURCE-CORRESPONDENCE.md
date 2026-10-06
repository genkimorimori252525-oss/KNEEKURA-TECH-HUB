# QB-MOD / Garnet-MOD 1.6.4.082 — Binary / source correspondence

Date: 2026-10-07

This check asks a narrow provenance question: do the Java files shipped inside the two archives correspond structurally to the compiled class tree shipped beside them?

It does **not** claim byte-for-byte reproducibility or semantic equivalence of every method.

## Inputs

- QB-MOD archive SHA-256: `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`
- Garnet-MOD archive SHA-256: `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

A derived local pair manifest was built from sorted source/class path pairs and both members' SHA-256 values.

Derived pair-manifest SHA-256:

`aebf5823d0f6113c8737b23ff80058ff26be7d7575f5cb59986c332750a6f642`

The raw pair manifest is not committed because archive hash + internal path already provides a stable source locator; the digest is retained to identify this exact derived inventory.

## Exhaustive path / SourceFile-name check

| Archive | Java files | class files | source→class path matches | missing class | class missing corresponding Java SourceFile name |
| --- | ---: | ---: | ---: | ---: | ---: |
| QB-MOD | 156 | 156 | 156 | 0 | 0 |
| Garnet-MOD | 37 | 37 | 37 | 0 | 0 |
| Total | 193 | 193 | 193 | 0 | 0 |

Method:

1. for every Java file under `MCP/puellamagi/mods/**` or `MCP/garnet/mods/**`;
2. derive the corresponding compiled path outside `MCP/`;
3. require the `.class` to exist;
4. require the class constant pool to contain the corresponding Java basename (the SourceFile-name evidence);
5. hash both source and class into the derived pair manifest.

This is exhaustive for the top-level Java/class inventory in the supplied archives.

## Sampled javap correspondence

A second check used `javap -p` against the supplied QB + Garnet classpath.

### EntityMadoka

Binary reports:

`Compiled from "EntityMadoka.java"`

Custom method surface includes:
- `shortRangeAttack(EntityLivingBase,int)`
- `middleRangeAttack(EntityLivingBase,int)`
- `longRangeAttack(EntityLivingBase,int)`
- private `madokaShooting(...)`

This corresponds to the source structure used by the combat catalog.

### EntityHomura

Binary reports `Compiled from "EntityHomura.java"` and exposes:
- `teleportRandomly()`
- `teleportTo(double,double,double)`
- the three range attacks
- `homuraShot(...)`

### EntityWalpurgisnacht

Binary reports `Compiled from "EntityWalpurgisnacht.java"` and exposes:
- `attackFlameLance(...)`
- `attackPrickle(...)`
- damage/living/spawn/death hooks corresponding to the encounter analysis.

### EntityGriefSeed

Binary reports `Compiled from "EntityGriefSeed.java"` and exposes:
- `spawnMajoFromGrief()`
- `randomSpawnMajo(...)`
- `forcedSpawnMajo(...)`
- `chooseMajo(...)`
- Soul Gem damage/countdown accessors
- `setHomulilly()`

This is especially relevant to the hidden incubation-ritual analysis.

### EntityGarnetTameable

Binary reports `Compiled from "EntityGarnetTameable.java"` and exposes:
- Standby / Free / Follow / Satellite checks and setters
- `changeMode()`
- owner-name access
- auto-healing

### ItemGarnetGun

Binary reports `Compiled from "ItemGarnetGun.java"` and exposes the private/public state-machine surface expected from source:
- reload state
- magazine release/reload
- bullet firing
- full-auto flag
- bolt cycling
- NBT tag checking

## Interpretation

The supplied distributions show **strong source↔binary structural correspondence**:

- complete 1:1 top-level path coverage;
- matching SourceFile names across all 193 class files;
- representative class interfaces agree with source-derived subsystem findings.

This materially raises confidence that the shipped MCP Java tree is the appropriate primary static-analysis source for this exact distribution.

It still does **not** establish:

- reproducible compilation from the supplied Java tree;
- equality of every method body with the compiled bytecode;
- absence of compiler/post-processing differences;
- behavior after Forge/Minecraft runtime transformation;
- successful execution on the original 1.6.4 stack.

Facet status should therefore be described as **MAPPED / strong structural correspondence**, not full semantic equivalence.

A future higher-assurance pass could compare decompiled bytecode or normalized instruction graphs for every class and record mismatches explicitly.