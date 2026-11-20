# Implementation checkpoint — P17k shot-item dispenser; P17 closed

Date: 2026-11-20
Oracle: X1 `CommonProxy.registerDispenser` (shot_item), `ItemTHShot.shootDanmaku`.

## X1 behaviour kept on purpose

- A dispenser holding any of the 19 shot items makes a fresh `EntityFamiliar` that is never spawned and fires
  `shootDanmaku` as it: from the dispenser's centre, along the facing × 0.7 (X1 calls `getVectorNomalize` and
  throws the result away), starting SIZE[shotTypeTrans] + 1 ahead, slow mode off. The item's NBT (number,
  form, speed, special, gravity, colour) applies as for a player; one item is used unless it carries
  "Infinity".

## P17 status

All X1 `entity/living` mobs are ported (P17A–P17J), plus the cursed decoy doll, Miracle Mallet, Hanabeeper
egg / spawns and this dispenser. The Miko sword moves to P18 with the Divine Spirit it needs.

## Receipts

- Server: `FIVE_DIFFICULTIES_P17_DISPENSER_PASS shots=1` (fired east, owner a familiar, 3 → 2 items) plus every
  P17 check, and P6/P8–P17 all `RUNTIME_SCENARIO_PASS` (1 local run). The test reaches the protected
  `DispenserBlock.dispenseFrom` by reflection with its official name (dev runtime only).
