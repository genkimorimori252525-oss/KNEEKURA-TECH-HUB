# Official debug verification world

User designation: 2026-10-04 (Asia/Tokyo). TECH HUB is canonical; LAB is its feature subtree.

The official debug verification world (the "Tank") is `KNEEKURA_DEBUG_WORLD` in:

```text
C:\Users\genki\.codex\worktrees\g3-real-machine-acceptance\reimu-mod\run\client_a\saves\KNEEKURA_DEBUG_WORLD
```

The existing `.codex` path above was verified. The spelling `C:\Users\genki.codex\...` from the later message does not exist on this host. Workspace root is `C:\Users\genki\.codex\worktrees\g3-real-machine-acceptance\reimu-mod`; game directory is `run/client_a`. The earlier `.minecraft-simlab-golden` world is historical evidence, not this designated connection target. Current private acceptance copies are derived trials, not replacement official worlds.

[Connection example](lab/debug-workspace/config.official-tank.example.json) records this host's target using the existing configuration format, with decision hooks/overlay OFF. Copy it to a local configuration and verify the current workspace/build/world identities before launching. This designation/example does not itself establish a live connection, owner registration, lease or mutation permission. Current automated acceptance continues on isolated copies, preserving the original85-file SHA256 baseline. Changes to the shared original require a separately prepared operation with existing authority checks.

## Reusable geometry template

Read-only saved state `kneekura-tank-owner.json` reports `GEOMETRY_VERIFIED`, `OBSERVATION_BRIGHT`, width19 /depth19 /height11, origin `[0,224,0]` in `minecraft:overworld`, recipe hash `sha256:e9ed87f3b512cf59dac3ce6eb0c08654d047657be1e383dc6df580a5582bcac3`.

[Sanitized presentation/recipe example](lab/debug-workspace/tank-presentation.official.example.json) contains only `status`, `displayMode`, `recipeHash` and `recipe`. No save binaries, player inventories, owner credentials, action authorizations or live lease are included. It is the original saved recipe, not a fixture generator or proof that another world has matching geometry. Package it as `kneekura/tank-presentation.json` in the existing registered resource ZIP only when its saved-world recipe matches; follow [registered presentation](lab/docs/KNEEKURA_REGISTERED_TANK_PRESENTATION.md).

## Size changes and integration boundary

Read-only inspection confirms the g3 `KneekuraDebugTankCoordinator` accepts a plan recipe's `origin` and `dimensions`; `KneekuraTankGeometry` bounds each dimension to1..64 and volume to65,536, with world-coordinate limits. Rotation checks the existing world authorization, prior recipe hash and verified owner state. The source reference is g3 LAB `8e36ea8b1c8634bb1422c965b0e5f179d54f1cdf`, also recorded in the [prior acceptance](lab/docs/KNEEKURA_LIVE_ACCEPTANCE_REMAINDER_20261002.md).

The canonical TECH subtree imports the registered grid/lightmap presentation. [Registered pre-experiment Tank rotation](lab/docs/KNEEKURA_REGISTERED_TANK_ROTATION.md) now adds a separate sealed, bounded source-owner operation that allocates a new disjoint empty region and closes the old owner. It preserves prior regions and does not import the legacy reset/coordinator protocol. Source-contract checks pass; genuine Minecraft rotation/reconnect is still pending for this producer. A world directory alone does not install its supporting bridge. Reset/dynamic fidelity and full configurable Tank acceptance remain untested here. Do not replace the official world with a generated room or claim an altered trial's geometry is its baseline.
