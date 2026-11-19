# Animation and networking

## Player animation

`SetupAnimationsProcedure` registers a PlayerAnimator `ModifierLayer` under the Jujutsu Craft animation key.

A custom animation message contains:

- animation name
- target entity ID
- override boolean

The client resolves the entity and applies the named `jujutsucraft:<animation>` keyframe to the PlayerAnimator layer.

## GeoEntity animation

GeckoLib-backed combat entities use a separate path. Animation helper procedures ultimately invoke `setAnimation(String)` on GeoEntity-style actors.

Player animations and Gecko entity animations therefore have separate transport/execution surfaces.

## General networking

The main mod owns a Forge `SimpleChannel` plus queued server work. Network classes cover key presses/menu choices and explicit state actions.

`PacketHandler` + `PlayerVelocityPacket` form an additional velocity-sync helper.

## Persistent state

`JujutsucraftModVariables.PlayerVariables` serializes/synchronizes combat state through NBT. It includes curse energy/current/max values, selected technique, primary/secondary technique, costs, level/experience/fame/profession, charge, technique use count, Six Eyes/Sukuna/passive flags and overlays.

`WorldVariables` extends SavedData for world-level persistence.

## Historical repair signal

ver45 changelog explicitly says a multiplayer animation bug was fixed. Current dual-path animation structure is evidence of the current architecture only; it is not claimed to be the exact repair without old bytes.
