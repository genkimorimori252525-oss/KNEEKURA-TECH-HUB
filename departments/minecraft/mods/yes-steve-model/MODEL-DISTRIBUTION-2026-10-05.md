# YSM model distribution / network research — 2.6.5 release-line candidate

Research date: 2026-10-05  
Source candidate: `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`  
Status: **EVIDENCE_BACKED AT JAVA/JNI BOUNDARY / NATIVE PROTOCOL OPAQUE**

## 1. Scope

This report maps the public Java side of YSM 2.6.5 model distribution.

It does **not** attempt to defeat or unpack the protected native implementation.

The historical public tree contains no C/C++/Rust/Zig/Go source. The transfer protocol implementation
behind the JNI methods is therefore treated as opaque.

## 2. Forge channel

`NetworkHandler` creates one Forge `SimpleChannel`.

- protocol version string: `2.6.0`
- channel name derives from that version
- remote/local acceptance predicates are permissive at Forge registration time
- YSM separately stores the peer channel version as a Netty channel attribute

The channel registers presentation/model messages and two handshake messages.

Notable IDs:

| ID | Direction | Message |
|---:|---|---|
| 1 | server -> client | SyncDataToClient |
| 2 | client -> server | SyncDataToServer |
| 3 | server -> client | ExecuteMolang |
| 4 | server -> client | SyncModelInfo |
| 5 | client -> server | SetModelAndTexture |
| 6 | server -> client | SyncAuthModels |
| 7 | client -> server | SetPlayAnimation |
| 8 | server -> client | SyncStarModels |
| 9 | client -> server | SetStarModel |
| 15 | client -> server | SubmitRoamingVarsChanges |
| 16 | server -> client | SyncProjectileModelInfo |
| 17 | client -> server | SubmitRouletteConfig |
| 18 | client -> server | EmitMolangSync |
| 19 | server -> client | MolangSync |
| 21 | server -> client | DispatchServerDrivenProperty |
| 22 | server -> client | SyncVehicleModelInfo |
| 23 | client -> server | EmitSwingHand |
| 51 | server -> client | ServerInfo |
| 52 | client -> server | ClientInfo |

IDs 10–14 are present only as commented/deprecated registrations in this source.

## 3. Login handshake

The public source exposes the handshake completely.

### Server

`LoginEvent.onLoggedInServer`:

1. checks that YSM native/runtime availability is healthy;
2. when the joining entity is a ServerPlayer;
3. sends `new ServerInfo()`.

### Client

`ServerInfo.handleOnClient`:

1. stores the received channel version on the exact Netty connection;
2. schedules `ClientModelManager.receiveServerInfo()`;
3. replies with `new ClientInfo()`.

### Server acknowledgement

`ClientInfo.handleOnServer`:

1. stores the client's channel version;
2. validates/corrects the player's model capability;
3. resets mandatory/animation state;
4. sends authorized-model state;
5. sends starred-model state;
6. calls `ServerModelManager.syncModelsToPlayer(player, null)`.

Therefore the model transfer is **server-initiated after a bidirectional version handshake**.

## 4. Server-side synchronization scheduling

`syncModelsToPlayer` schedules work on the Minecraft server thread.

It:

1. gathers online players in the same dimension type;
2. sorts them by distance from the joining player;
3. derives currently selected model IDs from channel-capable players;
4. calls native `syncTaskEnqueue` with:
   - target player UUID array;
   - target player name array;
   - selected model ID array;
   - completion callback state.

The distance sort implies the server-side native sync task is given presentation-demand information,
not just a blind archive of every player's current model.

Exact prioritization inside the native task is **UNKNOWN**.

## 5. Server JNI boundary

Public Java declares:

- `reloadBegin(state)`
- `syncTaskEnqueue(playerIds, playerNames, selectedModels, state)`
- `syncReceiveData(playerId, ByteBuffer)`
- `exportModel(...)`

Native code calls back into Java helpers including:

- `syncSendData(playerId, ByteBuffer, TrafficContext)`
- packet pre-encoding helper
- encoded-packet send helper
- sync completion callback

The server therefore exposes a narrow topology:

~~~text
native sync worker
   |             ^
   | ByteBuffer  | ByteBuffer
   v             |
Forge/Netty connection
~~~

## 6. Backpressure-aware server send loop

The Java send helper does not blindly flood the connection.

On first use it records:

`current totalPendingWriteBytes + 64 KiB`

as a high-water mark.

Before each send it checks the Netty outbound-buffer size. If above the mark it sleeps and retries.

After `Connection.send`, it waits for a `PacketSendListener` result:

- success -> return true
- failure -> sleep then retry
- disconnected/interrupted -> return false

### Reusable lesson

Large model/resource delivery needs transport backpressure.

However KNEEKURA should not copy this exact worker-blocking loop without measurement. Prefer an
explicit asynchronous send state machine if the same behavior can be obtained without sleeping a
worker while waiting for callbacks.

## 7. Client transport boundary

`SyncDataToClient` and `SyncDataToServer` both say explicitly:

> the model-sync protocol is defined and implemented by the native layer; Java only provides data
> send/receive interfaces.

Both packet classes:

1. copy the entire packet payload into a direct ByteBuffer on decode;
2. hand that direct buffer to the appropriate model manager.

Client public JNI boundary:

- Java -> native: `ClientModelManager.syncReceiveData(ByteBuffer)`
- native -> Java: `ClientModelManager.syncSendData(ByteBuffer)`

The client remembers `LAST_CONNECTION` so the native worker can answer even before a normal
Minecraft player object is available.

## 8. Client synchronization state machine visible from Java

`ClientModelManager.SyncStateType` contains:

- WAITING
- LOADING
- IDLE
- PREPARING
- SYNCING

### Initial server-info behavior

`receiveServerInfo()` sets:

- LOADING for an integrated/local server;
- IDLE for a remote server.

### Native preparation callback

`syncPreparation(-1)` -> PREPARING

`syncPreparation(total > 0)` -> SYNCING, received = 0

`syncPreparation(0)` -> IDLE

### Abort/failure

`syncAborted()` -> IDLE + listener callback

`syncFailed(msg)` -> IDLE + failure callback + optional player/system/log message

Logout calls `syncAbort()`, which sends a null buffer into native and returns the client to WAITING.

Server logout calls `ServerModelManager.syncTaskAbort(UUID)`, which also enters native through a
null receive buffer.

### Reusable lesson

Using an explicit terminal abort/failure path is good.

A future KNEEKURA transfer state should go further and distinguish:

- handshake
- catalog/index
- requested/admitted
- transfer
- decode/build
- publish/activate
- ready
- failed
- aborted

instead of overloading one broad SYNCING state.

## 9. Model-pack metadata and model payloads are separate callbacks

Native can call `updateModelPackInfo(ModelPackInfo[])`.

That callback updates pack metadata and schedules texture registration/release on Minecraft's owner
thread.

After the pack phase, native can call `alterModel(...)` to:

- remove obsolete client models;
- remap/rename existing model IDs;
- update authorization flags.

Actual model payload activation enters through:

`addModel(@Nullable ClientModelData modelData, modelPath, isDefault, isNeedAuth)`.

This means Java already exposes distinct phases for:

1. pack/catalog metadata;
2. existing-model alteration/removal;
3. new model data build;
4. publication into the live model map.

## 10. Model build / publication path

For a non-default payload:

~~~text
native addModel(ClientModelData)
       |
       v
ClientModelBuilder.build(...)
       |
       v
NEW_MODEL_QUEUE.add(model, modelPath)
       |
       v
ClientModelManager.tick()
       |
       v
copy + publish MODELS
       |
       v
onNewModelLoaded listeners
~~~

This separates worker-side receipt/build from owner-thread publication.

That is a valuable design pattern.

## 11. Static progress-wedge hazard

A notable control-flow hazard exists in `addModelInternal`.

For non-default model data:

1. it calls `ClientModelBuilder.build(modelData,...)`;
2. if the builder throws, it logs `Failed to process <modelPath>`;
3. then immediately `return`s.

The normal progress accounting occurs later:

- increment `SYNC_STATE.received`;
- if received == total, set IDLE;
- notify progression listeners.

Because the build-exception branch returns **before** this accounting, a failing model build can
leave Java's visible sync progress below `total`.

### Confidence

**DIRECT_SOURCE STATIC HAZARD**

### What it does NOT prove

It does not prove that official issue #444 is caused by this path.

Issue #444 reports an apparently earlier symptom — index/session state appears present while model
content does not populate the client cache. The opaque native protocol could be blocked before
`addModel` is ever invoked.

### KNEEKURA lesson

Every admitted transfer item needs exactly one terminal accounting result:

- ACTIVATED
- SKIPPED
- FAILED
- ABORTED

A decode/build error must not bypass the completion counter.

## 12. Why issue #444 can be localized without breaking native protection

Even though the protocol body is native, the Java/JNI boundary gives enough observation points to
identify the blocked phase.

A bounded diagnostic build/test harness can record:

### Handshake

- ServerInfo sent
- ClientInfo received
- connection channel version set

### Server scheduling

- `syncModelsToPlayer` entered
- `syncTaskEnqueue` invoked
- target UUID / model-count metadata only

### Byte transport

- count/size/timestamp of each `SyncDataToClient`
- count/size/timestamp of each `SyncDataToServer`

Do not log private payload bytes.

### Client native callbacks

- `syncPreparation(total)`
- `updateModelPackInfo(count)`
- `alterModel(counts)`
- `addModel(modelPath, modelData != null)`
- `syncAborted`
- `syncFailed`

### Build/publication

- ClientModelBuilder success/failure
- NEW_MODEL_QUEUE size
- MODELS publication
- listener notifications

This creates a safe phase trace:

~~~text
HANDSHAKE
 -> SERVER_ENQUEUED
 -> FIRST_SERVER_BYTES
 -> FIRST_CLIENT_REPLY
 -> PREPARING
 -> PACK_METADATA
 -> MODEL_ADMITTED
 -> MODEL_BUILT
 -> MODEL_PUBLISHED
 -> IDLE
~~~

Whichever transition is missing identifies the next layer to inspect.

## 13. Issue #444 hypotheses after static mapping

These are ranked **test hypotheses**, not conclusions.

### H1 — native/session transfer never enters model payload phase

Fits the report that index/session artifacts appear but client payload cache remains empty.

Probe:

- packet byte counts after handshake;
- does `syncPreparation(total>0)` fire?
- does `addModel` ever fire?

### H2 — one model build fails and Java progress wedges

Supported by the direct source hazard above.

Probe:

- instrument every `addModel` entry and every builder outcome;
- compare admitted total with terminal item outcomes.

### H3 — session/catalog identity differs from content activation identity

The 3.0-dev FRONTIER redesign now explicitly separates exact connection/session, catalog
publication and content activation. That architectural change makes this class of lifecycle problem
plausible historically, but it is not proof of a 2.6.5 bug.

Probe:

- log connection identity + session-generation metadata at Java callbacks where available;
- never reuse state across reconnect in the diagnostic harness.

### H4 — Molang/model content parse failure blocks readiness

Issue #444 reports Molang parse errors in a bundled model.

Static source shows model build can fail terminal accounting, but it has **not** been established that
those reported Molang errors throw out of ClientModelBuilder or that they prevent native content
transfer.

Probe:

- first test the same server with a minimal known-good opaque model;
- separately test the problematic bundled model;
- compare phase traces.

## 14. FRONTIER comparison

Current 3.0-dev documentation formalizes several boundaries that are implicit/opaque in 2.6.5:

- exact connection ownership;
- session ownership;
- catalog publication;
- content activation;
- one server-global physical resource dispatch worker;
- owner-thread publication.

This is a cleaner reference architecture for future KNEEKURA resource distribution than copying the
2.6.5 native protocol.

## 15. Reusable KNEEKURA resource-distribution design

~~~text
Connection
  |
  v
SessionGeneration
  |
  +--> CatalogSnapshot
  |      |
  |      v
  |    ContentRequests
  |      |
  |      v
  |    bounded transfer queue
  |
  v
Decode/Build staging
  |
  +--> success -> owner-thread publication
  |
  +--> failure -> terminal FAILED accounting
  |
  v
ReadySnapshot
~~~

Required properties:

1. exact-connection/session identity;
2. content-address or model-generation identity;
3. bounded backpressure;
4. no private payload logging;
5. one terminal result per admitted item;
6. decode/build separated from transfer;
7. owner-thread publication;
8. reconnect invalidates old session work;
9. phase-level observability;
10. no requirement to understand protected payload internals to debug lifecycle flow.

## 16. Evidence boundary

Established:

- handshake order;
- server sync trigger;
- Forge packet registry;
- Java/JNI ByteBuffer transport boundary;
- server backpressure helper;
- client sync-state transitions;
- pack metadata vs model build/publication phases;
- build-exception progress-wedge hazard;
- absence of native source in the historical public tree.

Not established:

- native wire format;
- exact cache-file format semantics;
- request/response opcodes inside native payloads;
- cause of issue #444;
- distributed binary/source equivalence.

Those remain explicitly unresolved.
