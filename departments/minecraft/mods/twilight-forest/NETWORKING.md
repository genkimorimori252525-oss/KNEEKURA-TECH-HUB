# Twilight Forest — Networking Map

Status: **FRONTIER registration/direction mapped; ANCHOR comparison mapped**

## ANCHOR — Forge 1.20.1

The 1.20.1 line uses Forge `SimpleChannel` through `TFPacketHandler`.

Characteristics:

- central channel;
- protocol string;
- sequential numeric message IDs;
- centralized registration;
- packet handling wired during common setup.

This works, but message direction/ownership is less visible at the type-registration boundary.

## FRONTIER — NeoForge payload model

Evidence:

- `src/main/java/twilightforest/events/RegistrationEvents.java`
- blob `40c87d293513059666fd71ae077cb169c44be52c`

`setupPackets` creates:

```text
PayloadRegistrar
namespace: twilightforest
version: 1.0.0
optional: true
```

Each payload explicitly declares direction:

- `playToClient`
- `playToServer`
- `playBidirectional`

Each registration couples:

```text
TYPE
STREAM_CODEC
handler
direction
```

## Mapped FRONTIER directions

### Server → Client

Examples include:

- area/structure protection;
- progression state;
- magic/maze maps;
- advancement toast;
- forced player movement;
- particles;
- charm/fallen-leaf visuals;
- uncrafting config sync;
- multipart entity updates;
- thrown-entity state;
- lifedrain effects;
- boss-bar state;
- mason-jar state;
- quests;
- traveller wings.

### Client → Server

Examples include:

- double jump;
- sidestep;
- hotbar swap;
- map-slot cycling;
- uncrafting GUI actions;
- ore-meter reset.

### Bidirectional

Observed:

- goggles zoom;
- gradual glide.

## Design lesson

The important upgrade is not “NeoForge payload API” itself.

The transferable contract is:

```text
message type
+ codec
+ explicit direction
+ narrow handler
+ protocol version
```

A 1.20.1 Forge implementation can preserve this on top of `SimpleChannel` by wrapping registration in typed helpers and testing direction explicitly.

## Multipart networking dependency

FRONTIER also patches vanilla server entity synchronization with ASM:

- `SendDirtyEntityDataTransformer`
- blob `7ec8bfd1d124ec6745747091332d9b9e53b6845e`

It injects a Twilight Forest multipart hook into `ServerEntity.sendDirtyEntityData`.

This confirms multipart boss synchronization is not just an ordinary custom packet concern; part of it depends on a vanilla synchronization interception point.

## Exact FRONTIER payload inventory

At snapshot `793c4d4c…`, `RegistrationEvents.setupPackets` registers **29 payloads**:

- **21 server → client**
- **6 client → server**
- **2 bidirectional**

### Server → client (21)

`AreaProtectionPacket`, `CreateMovingCicadaSoundPacket`, `EnforceProgressionStatusPacket`, `MagicMapPacket`, `MazeMapPacket`, `MissingAdvancementToastPacket`, `MovePlayerPacket`, `ParticlePacket`, `SpawnCharmPacket`, `SpawnFallenLeafFromPacket`, `StructureProtectionPacket`, `SyncUncraftingTableConfigPacket`, `UpdateTFMultipartPacket`, `UpdateThrownPacket`, `LifedrainParticlePacket`, `UpdateDeathTimePacket`, `TFBossBarPacket.AddTFBossBarPacket`, `TFBossBarPacket.UpdateTFBossBarStylePacket`, `SetMasonJarItemPacket`, `SyncQuestsPacket`, `TravellersWingsStatePacket`.

### Client → server (6)

`PerformDoubleJumpPacket`, `SwapHotbarPacket`, `PerformSidestepPacket`, `CycleMapSlotPacket`, `UncraftingGuiPacket`, `WipeOreMeterPacket`.

### Bidirectional (2)

`GogglesZoomPacket`, `GradualGlidePacket`.

Machine-readable copy: `PACKET-MAP.json`.

The direction split makes the authority boundary visible: most world/progression/boss/presentation state originates server-side, while the client sends narrow action/UI intent.
