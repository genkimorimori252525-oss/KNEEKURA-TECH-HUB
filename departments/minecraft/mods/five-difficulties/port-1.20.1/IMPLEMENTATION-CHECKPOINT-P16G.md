# Implementation checkpoint — P16g icicle sword and Hakurouken

Date: 2026-11-20
Oracle: X1 `ItemIcicleSword`, `EntityCirnoIceBox`, `RenderCirnoIceBox`, `ItemHakurouken`,
`EntityHakurouReflecter`, `RenderHakurouReflecter`.

## Ported

| X1 | Port |
|---|---|
| `ItemIcicleSword` (icicle 0/30/0/2) | `icicle_sword` (`X1Weapons.IcicleSword`) |
| `EntityCirnoIceBox` + renderer | `CirnoIceBoxEntity`, `P16Renderers.CirnoIceBox` (vanilla ice texture, as X1) |
| `ItemHakurouken` (hakurou 0/100/0/0) | `hakurouken` (`X1Weapons.Hakurouken`) |
| `EntityHakurouReflecter` + renderer | `HakurouReflecterEntity`, `P16Renderers.HakurouReflecter` |
| 1.7.10 `ItemSword` guard on right-click | `X1Weapons.GuardSword` (BLOCK use animation, 72000 ticks) |

## X1 behaviour kept on purpose

- Icicle sword: each hit freezes the target in a solid ice box unless it is already frozen or over 3 wide or
  tall; repaired with ice. The box puts the target back to its previous position each tick, scales its motion
  by 1e-9, holds its look, head and age, winds a creeper's fuse back, teleports a frozen player back; a dying
  (not yet removed) target stays frozen. After 50 ticks it melts 0.08 a tick and is gone at height −0.7.
- Hakurouken: releasing the guard while sneaking throws a wall along the look (0.18 a tick, 20 ticks); on the
  ground while moving it steps back 1.5 instead. Either costs 1 durability. The wall removes every non-laser
  shot within 1 (the user's own too); another's shot is answered with an aqua scale shot (damage 3) from the
  user along the user's look. Its block check traces the mirrored path, as X1. X1's knock-back branch for
  non-shots cannot be reached and is not ported.

## Not ported (no 1.20 counterpart)

- Ice box: 1.7.10 `attackTime` bump, ghast attack-counter rewind (private in 1.20); Cirno melting the box
  twice as fast comes with Cirno in P17.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_ICICLE_SWORD_PASS height=1.95
FIVE_DIFFICULTIES_P16_HAKUROUKEN_PASS
```
