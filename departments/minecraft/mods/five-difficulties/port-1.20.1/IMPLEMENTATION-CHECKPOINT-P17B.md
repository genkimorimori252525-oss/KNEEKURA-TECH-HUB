# Implementation checkpoint — P17b phantom

Date: 2026-11-20
Oracle: X1 `EntityTHPhantom`, `RenderTHPhantom`, its `addSpawn` list.

| X1 | Port |
|---|---|
| `EntityTHPhantom` (幽霊) | `th_phantom` (`PhantomEntity`), spawn egg, biome modifier `th_phantom_spawns` (weight 20, 1–3) |
| `RenderTHPhantom` | `P17Renderers.Phantom` (Musou Fuuin texture, additive) |

## X1 behaviour kept on purpose

- A fairy-pattern ghost, 1 × 1, form 0..7 as its colour, speed 0.18, attack 6, detection 30, flying 3, silent;
  it does not call fairies. In bright sky light (brightness above 0.5) it may die at random; it leaves no corpse.
- Drops: the fairy loot, then its own (small red shots, power, point, 1 in 10 a soul torch).
- Spawns like a monster in the dark: sky light at most a random 0..31, light at most a random 0..7 (thunder
  darkens the sky to 10), not on peaceful, behind the config switches.
- Renderer: three drifting, shrinking camera-facing wisps, red while hurt.

## Receipts

Dedicated server (local; P5–P17 together, 11 scenarios PASS, 0 FAIL): `FIVE_DIFFICULTIES_P17_PHANTOM_PASS`.
