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

## Critical method-body bytecode spot checks

A later bounded pass used `javap -c -p` against selected distributed class files. This does not make the comparison exhaustive, but it verifies that several important source findings are present in the shipped executable bytecode rather than existing only in stale Java text.

Selected class SHA-256 values:

| Class | SHA-256 |
| --- | --- |
| `EntityMahoShojo.class` | `cfbf9ade7e616645d0f56377bff5881673562cadf357ec610b1b2a02c259754d` |
| `EntityWalpurgisnacht.class` | `6a0ac3dd2f86b5788de73045f80bdeb4c430fc00c6c9587dffcc692357c25bb6` |
| `EntityGriefSeed.class` | `c7a7f4bb045d2314825128f5da7a35dbb1214add5331ebbed57260acef85b866` |
| `EntityMajo.class` | `48e46ca125b0eb066dfa3df7ebfba31e03d40f3638ba40d95e3c9c794ef9e4bb` |
| `EntityHomulillyAIAttack.class` | `3319c205d91e30059442232bf5891f06469ee2011a55b88fda3c6f5fe1a9a85c` |
| `EntityJB.class` | `58c03c20eb92106baa845b7e90d1f831802214064c8e093abdd93a7f034b878a` |
| `PacketHandler.class` | `dbad89c3d0c9cc328a6082b3e98437a4e461f9d494c10d5c287a7cb41272c293` |

The inspected legacy classes report class-file major version 50 (Java 6-era bytecode) and the expected `SourceFile` names.

### Grief Seed species selector

Distributed `EntityGriefSeed.chooseMajo` bytecode:
- tests `isHomulilly` first and returns Nutcracker when true;
- otherwise loads constant 5 and calls `Random.nextInt(5)`;
- executes a `tableswitch 0..4`;
- switch default constructs `EntityWalpurgisnacht`.

Therefore the source-level observation is executable-binary-backed: the default Walpurgis constructor exists, but that specific random selector only yields 0..4.

### Grief Seed incubation formula

Distributed `setNewCountDown` bytecode computes:

`500 + Random.nextInt(1000) - getSoulGemDamage() * 5`

and writes it to DataWatcher 21.

This confirms the source-derived relationship between Grief Seed state and incubation latency.

### Homulilly attack selector and teleport loops

Distributed `EntityHomulillyAIAttack.attackTNT` loads constant 1 and calls `Random.nextInt(1)`, then branches on whether the result is non-zero. Since Java `nextInt(1)` always returns 0, only the zero branch is reachable.

The same class bytecode also contains two loops bounded at 64 attempts:
- random teleport search;
- line-of-sight recovery teleport-to-target search.

### Walpurgis anti-air potion target

Both distributed classes:
- `EntityMajoAIWalpurgisnachtAttack`;
- `EntityMajoAIWalpurgisnachtPlay`;

load `theHost`, construct the potion effect and invoke `EntityWalpurgisnacht.addPotionEffect` on the host after the anti-air explosion path.

Thus the suspicious self-poison behavior is present in shipped bytecode in both AI variants, not merely in the Java source.

### Soul Gem setter semantics

Distributed `EntityMahoShojo.setSoulGemDamage(int)`:
1. calls `getSoulGemDamage()`;
2. adds the incoming argument;
3. writes the sum to DataWatcher 22.

So the source method named like a setter is executable as an additive mutation.

### GUI handler shared container

Distributed `MadomagiGuiHandler` contains one private instance field `container`.
- `injectContainerAndID` assigns it;
- server `getServerGuiElement` returns the same stored field;
- client GUI resolution independently looks up the entity by id.

This verifies the shared mutable server-container design in bytecode.

### Garnet gun packet boundary

Distributed `garnet.mods.PacketHandler.onPacketData`:
- validates Player is `EntityPlayerMP`;
- validates held item is `ItemGarnetGun`;
- loads `Packet250CustomPayload.data`;
- immediately executes byte-array index 0 (`baload`);
- passes that byte into `setDoFullAuto`.

No payload-length branch appears before the index operation in this method.

### JB inverse economy

Distributed `EntityJB.chooseItem` computes `Random.nextInt(64 - itemDamage)` and tests the final reward threshold at 63.

Therefore:
- damage 0 → `nextInt(64)`, 63 is reachable and Diamond has 1/64 probability;
- damage >=1 → the random upper bound is <=62, so the Diamond branch cannot be reached.

This corrects any broader statement that the branch is wholly unreachable.

These checks remain **selected semantic correspondence**, not full method-body equivalence across all 193 classes.

## Additional projectile method-body correspondence

A second selected bytecode pass checked the projectile substrate that makes QB-MOD's dense volleys mechanically meaningful.

Selected distributed class hashes:

| Class | SHA-256 |
| --- | --- |
| `EntityGarnetArrow.class` | `9fca45578309ca3fc00b138fec13083c34dee1c221cad3feb8bc4edc2b3ae5c1` |
| `EntityGarnetThrowable.class` | `6fe031d9b2c5a019b9ad2ebdb40462aea5deb49914c4ae39c22cec469c51ab63` |
| `EntityMami.class` | `0f1920adf86b1bb43dad4cb8680772eddefa0b69e0c582bef644b48eea1d8435` |
| `EntityHomulillyNutcracker.class` | `88aadde2533d42a0aa727b6e429bf505aa54b98e41e9f81d2f6a1bbe5eb02c19` |
| `EntityMajoAICharlotteWander.class` | `5bcceb22cbf6a3a2967bc20b517fcd4bbadb225c913dacba0b09317a9b458404` |

### Garnet Arrow hurt-resistance reset

Distributed `EntityGarnetArrow` bytecode, immediately before its `Entity.attackEntityFrom` call:
- loads the hit entity;
- pushes integer 0;
- writes `Entity.field_70172_ad`.

In the MCP source that field is `hurtResistantTime`.

### Garnet Throwable hurt-resistance reset

Distributed `EntityGarnetThrowable` performs the same write:
- entity hit;
- integer 0;
- `putfield Entity.field_70172_ad`;
- then computes the damage source and calls `attackEntityFrom`.

This verifies that the source-level multi-hit policy is present in both shipped projectile bases.

### Throwable critical explosion

In the same distributed `EntityGarnetThrowable` method:
- critical entity impact loads float **6.0** and invokes world explosion creation with terrain damage enabled;
- source shows critical block impact uses strength **4.0**.

`EntityGarnetBullet` is compiled as a direct subclass of `EntityGarnetThrowable`.

`EntityMami` source marks only the `Tiro Finale!` shot's bullet critical in the inspected Mami firing path, connecting that character finisher to the shared explosive-critical implementation.

### Nutcracker death cleanup and Charlotte debug path

The corresponding distributed classes exist with matching SourceFile identity; source inspection additionally records:
- Nutcracker death selecting all `EntityMob` in a ±200 expanded AABB and calling `setDead()` on every other result;
- Charlotte wander printing the candidate counter from the active position-search loop.

These two are retained as static/runtime-risk leads; this subsection does not claim runtime reproduction.

### Nutcracker anti-air host-poison bytecode

`EntityHomulillyAIMoveForTarget.class` SHA-256:
`5537224d0d68874698e08e95892208b58b075dcdfde51aae8b61d1b4fdab1608`.

In the distributed bytecode, after the strength-6 anti-air explosion:
- the method loads field `theHost`;
- constructs Poison effect duration300, amplifier4;
- invokes the potion-effect method on the host object.

This matches the Java source and the two Walpurgis AI copies. The self-poison target choice is therefore present in the shipped executable path of the Nutcracker movement controller as well.

## Damage-gate bytecode spot checks

The same bounded `javap -c -p` pass was extended to the damage pipeline.

Additional selected class hashes:

| Class | SHA-256 |
| --- | --- |
| `EntityKriemhildGretchen.class` | `d79d04365e272bb1595fe1f2a50c3f803c7a5f711d30ded75857872d6b26a5b4` |
| `EntityHomulillyNutcracker.class` | `88aadde2533d42a0aa727b6e429bf505aa54b98e41e9f81d2f6a1bbe5eb02c19` |
| `EntityMami.class` | `0f1920adf86b1bb43dad4cb8680772eddefa0b69e0c582bef644b48eea1d8435` |

### Throwable DamageSource fallback ladder

Distributed `EntityGarnetThrowable` bytecode contains, in order after the hit entity's obfuscated `field_70172_ad` (MCP `hurtResistantTime`) is written to zero:

1. `DamageSource.func_76356_a(projectile, thrower)` → thrown damage;
2. if rejected and target is not `EntityGarnetBase`, `DamageSource.func_76358_a(thrower)` → mob damage;
3. if rejected again and thrower is enabled `EntityGarnetTameable`, `DamageSource.func_76365_a(owner)` → player damage.

Each path invokes the distributed `Entity.func_70097_a(DamageSource,float)` attack method.

This confirms that the source's source-type fallback ladder is present in the shipped binary.

### Critical Throwable ordering

Distributed `EntityGarnetThrowable`:
- tests its critical bit;
- invokes world explosion creation with **6.0F** before the direct hit path;
- then writes hit entity `field_70172_ad = 0`;
- then calls the direct damage method.

Therefore a critical entity impact has the same source-derived ordering:

`explosion → clear ordinary hurt resistance → direct projectile damage`.

### Mami critical flag

Distributed `EntityMami.mamiShot(..., boolean)`:
- checks the final boolean argument;
- when true, calls `EntityGarnetBullet.setIsCritical(true)`.

The long-range source path that announces `Tiro Finale!` supplies that boolean as true. Combined with the previous bytecode check, the explosive-critical implementation used by the finisher is present in the shipped classes.

### Kriemhild rolling damage budget

Distributed `EntityKriemhildGretchen.func_70097_a` contains:
- per-hit cap constant **10.0F**;
- reads `armorValue`;
- if `armorValue + incoming >10`, replaces accepted amount with `10 - armorValue`;
- adds accepted amount back into `armorValue`.

Distributed living-update bytecode:
- decrements `superArmor` while positive;
- otherwise writes `superArmor=20` and `armorValue=0`.

This confirms the source-derived **rolling ~10-damage budget per ~20-tick custom window** rather than ordinary vanilla i-frame behavior.

### Walpurgis / Nutcracker local super-armor

The distributed Walpurgis and Nutcracker classes both contain their own `superArmor` integer fields and write constant **20** after accepted damage.

Because this target-local field is separate from Minecraft's ordinary `hurtResistantTime`, the Garnet projectile reset does not erase this boss-specific gate.

These remain selected semantic checks, not a full 193-class normalized instruction comparison.

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