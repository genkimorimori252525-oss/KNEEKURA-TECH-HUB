# Twilight Forest — Networking Map

## ANCHOR

1.20.1 uses Forge `SimpleChannel` in `TFPacketHandler`.

- protocol string: `"2"`;
- packet IDs are sequential integers;
- codecs/handlers are registered in one central `init()` method;
- 18 messages are explicitly registered there.

The entrypoint calls `TFPacketHandler.init()` during common setup.

## FRONTIER

Networking moves to NeoForge payload registration via `RegisterPayloadHandlersEvent`.

`RegistrationEvents.setupPackets` creates an optional versioned payload registrar (`1.0.0`) and explicitly declares direction:

- play-to-client;
- play-to-server;
- bidirectional.

The network package contains 30 Java files in the pinned FRONTIER tree.

Notable newer payload surfaces include:

- movement/double-jump/sidestep;
- map-slot cycling and goggles zoom;
- gradual glide;
- charm spawning;
- lifedrain particles;
- boss-bar synchronization;
- quest synchronization;
- traveller-wing state;
- mason-jar item state;
- ore-meter reset.

## Portability lesson

The reusable part is **not** the NeoForge payload API itself. It is:

- explicit packet ownership;
- explicit direction;
- typed payload/codec pairs;
- small handler-per-message classes;
- versioned protocol boundary.

A 1.20.1 Forge backport can preserve those semantics on top of `SimpleChannel`, even if the registration API stays old.
