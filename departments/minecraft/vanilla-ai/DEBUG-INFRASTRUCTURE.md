# Vanilla debug infrastructure — exact 1.20.1 correction

Evidence: the original [ANCHOR ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json), the scoped Foundation Map and additive [debug transport/renderer/callsite ledger](DEBUG-INFRASTRUCTURE-BYTECODE-LEDGER-2026-10-05.json). [R65 research validation](DEBUG-INFRASTRUCTURE-RESEARCH-2026-10-05.md) records34 exact explanation classes,142 selected methods,161 fields and73 inspected disassemblies. Bytecode invocation sites are static source facts, not observed runtime execution or loaded-transformation equivalence.

## Exact owners and version boundary

The actual owner is `net/minecraft/network/protocol/game/DebugPackets`.

This 1.20.1 class map contains **no** `PathfindingDebugPayload`, `GoalDebugPayload` or `BrainDebugPayload` owners. Earlier signature-based notes referring to those typed payload classes were cross-version vocabulary and must not be used as 1.20.1 hook evidence.

The actual 1.20.1 data owners include:

- `GoalSelectorDebugRenderer$DebugGoal`;
- `BrainDebugRenderer$BrainDump`;
- `ClientboundCustomPayloadPacket` with the older channel/buffer transport;
- Path's optional debug node arrays.

Use exact bytecode/API locators for this generation. A modern typed custom-payload record is not a backport-compatible class merely because its concept is useful.

## Dormant senders

The inspected bodies show:

- `sendPathFindingPacket(Level, Mob, Path, float)`: immediate return;
- `sendEntityBrain(LivingEntity)`: immediate return;
- `sendGoalSelector(Level, Mob, GoalSelector)`: side check followed by return, with no goal payload emission.

The existence of names, serializers, synthetic helper methods and renderers does not prove production transport is active. PathFinder's inspected body also does not populate Path debug arrays with `setDebug()`.

## Actual caller sites

The all7,108-owner class-reference inventory supplies structural candidates; the actual invocation instructions below are then verified in their whole disassemblies. A constant-pool reference alone is not a call. These findings cover this artifact, not arbitrary MOD/reflective/dynamic dispatch.

| Sender | Actual bytecode callers |
|---|---|
| Path | `PathNavigation.tick`, `FlyingPathNavigation.tick`, `DebugPathCommand.fillBlocks` (3 sites) |
| Goal | `Mob.sendDebugPackets` (1 site), passing its `goalSelector`, not `targetSelector` |
| Brain | `sendDebugPackets` overrides in Allay, Axolotl, Camel, Frog, Tadpole, Goat, Sniffer, Zoglin, Hoglin, AbstractPiglin, Warden and Villager (12 sites) |

Mob's server AI step invokes virtual `sendDebugPackets` after its relevant AI/control work. Subclass calls and inheritance remain separate from whether the final sender emits anything. The DebugPathCommand class is a source caller, not proof that a command is registered/available or executed in an acceptance trial.

Thirty-three Path-reference candidates were inspected within the73-class scan. There are no `Path.setDebug` member-reference lines or invocation sites in those inspected outputs. The two internal static Path-render calls in BeeDebugRenderer/BrainDebugRenderer likewise do not prove that their parent renderers are dispatched by the normal client. Path stream deserialization assigns its debug fields directly; this is distinct from populating a server search frontier.

## Older channel/buffer transport and receiver

`ClientboundCustomPayloadPacket` implements the Forge custom-packet interface and carries a ResourceLocation plus a FriendlyByteBuf. Its constructors enforce a1,048,576-byte payload limit. This is a transport limit, not a selected-subject/scene/search budget. Packet serialization writes the identifier followed by buffer bytes. Received packets retain release ownership; `getData` creates a copy. The packet handler dispatches to `ClientPacketListener.handleCustomPayload` and normally releases its owned data afterward.

The actual Forge receiver first offers `NetworkHooks.onCustomPayload(packet, connection)`. When Forge does not consume it, the fallback enforces the client thread, copies/decodes the buffer, handles the identifier, and releases that copy in `finally`. Unknown identifiers are logged. Do not remove or bypass these loader/thread/buffer boundaries when adapting the concept.

| Channel (`minecraft:` namespace) | Actual receiver data order and population |
|---|---|
| `debug/path` | entity int ID, waypoint tolerance float, `Path.createFromStream`; then `pathfindingRenderer.addPath(id, path, tolerance)` |
| `debug/goal_selector` | BlockPos, entity int ID, goal count int; each goal: priority int, running boolean, name UTF (read limit255); then `DebugGoal` objects and `addGoalSelector` |
| `debug/brain` | XYZ doubles, UUID, entity int ID, name/profession strings, XP int, health/max-health floats, inventory string, nullable Path, wants-golem boolean, anger int; then VarInt-counted activity/behavior/memory string lists, POI/potential-POI BlockPos sets and gossip strings; then `addOrUpdateBrainDump` |

The inspected dormant senders do not write these full packet headers. The private `DebugPackets.writeBrain` describes the tail starting at inventory/optional memory PATH and the lists/POIs/gossip, not an active complete Brain sender. A surviving `lambda$sendGoalSelector` writes priority/running/simple class name but is not proof the dormant parent invokes it.

`writeBrain` performs live Brain/memory/behavior/entity-specific getter work. Activity/behavior strings and memory descriptions lose type/reference identity and direct invocation causes; memory text is sorted, truncated to255 characters, and can include TTL or “ticks ago.” Description helpers can resolve entities, traverse collections and call custom `toString`/tracker getters. These serializers are not a bounded immutable evidence reader and must not be replayed to fill KNEEKURA's missing Decision fields.

## Path debug data and capture switches

Path stores optional open/closed node arrays (initially empty) and a nullable target-node Set. `setDebug` assigns them; `createFromStream` restores them on the client. The normal Finder does not call `setDebug`. Its private static final `DEBUG` constant is0 in this artifact, and the inspected compiled search bodies have no debug population branch. It is not an exposed runtime capture switch; changing a field value alone cannot restore absent compiled instructions.

`Path.writeToStream` writes **nothing** unless targetNodes is non-null and nonempty. When populated, the order is reached boolean, next index, target-node count/Target streams, target XYZ, path-node count/Node streams, open-node count/streams and closed-node count/streams. The reader expects those fields. Merely enabling a sender for an ordinary Path can therefore fail to provide the expected Path bytes; a true optional-present marker does not repair an empty serialization body.

Node debug streams contain XYZ, walkedDistance, costMalus, closed, type and f. They do not retain full g/h/cameFrom/reference graph or all evaluated/rejected candidates. Target streams also are not the complete closest-target/reached internal state. Empty arrays, a reconstructed returned route, and an original captured frontier must keep separate provenance. KNEEKURA's original invocation hooks and finite search IDs supply their own evidence rather than relabel this debug stream as a complete search.

Render constants are separate from capture and transport. PathfindingRenderer's private final SHOW_OPEN_CLOSED/SHOW_GROUND_LABELS/box-type defaults and BrainDebugRenderer's SHOW_* constants are compiled presentation choices; they are not a public switch that enables server search recording. F3 chunk-border toggling changes `DebugRenderer.renderChunkborder` only. Neither F3 nor a renderer field makes the dormant AI senders active.

## Renderer and authority boundaries

PathfindingRenderer, GoalSelectorDebugRenderer and BrainDebugRenderer are client presentation. Open/closed/cost/type display is useful vocabulary but does not supply server evidence by itself.

The actual host call is `LevelRenderer.renderLevel → DebugRenderer.render`. That dispatcher calls chunk-border rendering only when enabled and reduced-info allows it, then GameTest rendering. It does **not** call PathfindingRenderer, GoalSelectorDebugRenderer or BrainDebugRenderer. KeyboardHandler's debug key handler calls the chunk-border toggle. Thus server data production, client decoding/cache population and renderer dispatch are three independent requirements.

| Renderer | Actual cache, display and lifetime |
|---|---|
| PathfindingRenderer | Maps by transient entity int ID, records arrival `Util.getMillis`, and stores waypoint tolerance. Render draws first, then removes Path/creation entries older than5,000ms; pathMaxDist is not removed there. It has no clear override, so the interface's default no-op clear does not reset these maps. Without render dispatch its expiry loop does not run. Render range uses Manhattan camera distance<=80. Route color is node-index order, not sampled observation age. Target/next-route boxes and optional open/closed boxes are presentation of supplied data. |
| GoalSelectorDebugRenderer | Map by entity int ID; add replaces the list, remove/clear are explicit; no timestamp TTL. `DebugGoal` retains priority/running/name/position, but render uses list order for vertical labels and running state for color, without showing priority or Goal flags/reasons. Its camera reference uses Y=0 and `closerThan(...,160)` against the goal's full BlockPos: at Y224 the vertical distance alone exceeds that limit. This is a static display condition, not evidence that no Goal ran. |
| BrainDebugRenderer | Maps by UUID plus int entity ID, removes entries whose client entity is absent/removed, and explicitly clears dumps/POIs/selected UUID. Nearby Mob names use a30-block horizontal-distance check; selected details show profession/XP/health/inventory/behaviors/activities/memories/gossip/Path and supported anger. POIs use their own range/presentation. No captured server search IDs or typed causal operands are created. |

Brain selection uses an8-block targeted-entity ray to update `lastLookedAtUuid` **after** drawing; an empty target does not clear that UUID, and spectator rendering skips the update. This sticky client look selection is not the same authority as an explicit server-side selected UUID/revision/Arena/run. Login calls `DebugRenderer.clear`, and removal handles Goal/Brain entries; per-renderer overrides determine what actually clears. Transient entity IDs and arrival milliseconds do not satisfy KNEEKURA's immutable run/process/Arena/search/time identity.

LAB must retain exact server source observations and immutable identity before deriving a local client overlay or packet. Overlay OFF adds no hidden drawing loop; raw Cardinal evidence must not silently include a derived overlay. No particles, entities or blocks are spawned to draw diagnostic lines.

## Commit-pinned MOD precedent

[Moonlight1.20 snapshot `a083393`](https://github.com/MehVahdJukaar/Moonlight/tree/a08339340ef4e39ce4d204728737c872c0329e4e) declares Minecraft1.20.1/Forge47.4.10 and Fabric in its properties. Its complete, non-truncated tree does not contain the named DebugPacketsMixin/DebugRendererMixin/DebugRenderersCommand feature files. Do not describe that snapshot as the inspected re-enabling implementation.

The actual feature example is [Moonlight snapshot `72afa38`](https://github.com/MehVahdJukaar/Moonlight/tree/72afa38c8b7f5c05639644fdabc92d5254924732), declaring Minecraft1.21.1 / Moonlight1.21.1-3.7.0 and NeoForge/Fabric dependencies. Exact tree/blob IDs, independently recomputed Git blob hashes and source SHA256s are recorded in the ledger. This is source precedent, not a verified installed binary or ANCHOR compatibility test.

- [DebugPacketsMixin](https://github.com/MehVahdJukaar/Moonlight/blob/72afa38c8b7f5c05639644fdabc92d5254924732/common/src/main/java/net/mehvahdjukaar/moonlight/core/mixins/DebugPacketsMixin.java) adds HEAD injections gated by ServerLevel and entity-type configuration. It sends modern typed Pathfinding/Goal payloads through a different `sendPacketToAllPlayers(ServerLevel, CustomPacketPayload)` signature. Goal data includes priority/running/`toString`; the inspected file does not re-enable Brain sending.
- Its Path fallback partitions **returned Path nodes** using their closed flag and obtains an evaluator Target before calling `path.setDebug`. Those reconstructed arrays omit other open/closed/evaluated/rejected candidates and are not a captured original frontier. The extra evaluator call and mutation also differ from KNEEKURA's original-invocation-only evidence contract. Do not copy that reconstruction or present it as exact candidate observation.
- [DebugRendererMixin](https://github.com/MehVahdJukaar/Moonlight/blob/72afa38c8b7f5c05639644fdabc92d5254924732/common/src/main/java/net/mehvahdjukaar/moonlight/core/mixins/DebugRendererMixin.java) adds TAIL render dispatch behind `ClientConfigs.DEBUG_RENDERS`, including Goal/Path and additional diagnostics. The inspected dispatch does not include BrainDebugRenderer. Client dispatch and server data configuration are distinct gates.
- [DebugRenderersCommand](https://github.com/MehVahdJukaar/Moonlight/blob/72afa38c8b7f5c05639644fdabc92d5254924732/common/src/main/java/net/mehvahdjukaar/moonlight/core/commands/DebugRenderersCommand.java) requires permission2 and provides navigation/Goal entity-type filters, initially inactive. Its `frustum capture` command calls the client LevelRenderer frustum capture; it is not a server AI search-capture switch. Source command registration alone does not verify dedicated-server configuration synchronization.

The useful precedent is explicit source-side opt-in plus actual client render dispatch. Typed1.21.1 payloads, Path debug-data APIs, evaluator target APIs and loader hooks require a version-specific adapter if backported. KNEEKURA keeps its existing scoped transport, immutable source IDs and bounded original callbacks; R65 adds no upstream code, dependency, compatibility claim or new instrumentation. Re-enabling a debug flow remains subject to separate observer-effect and native acceptance.

## Proven hook surface

Read-only selected-subject snapshots can use the verified Goal/Brain/Path/control APIs. A deep path recorder must observe the original search before evaluator cleanup. Exact Goal/Behavior lifecycle calls and Sensor/candidate population require separately armed original-invocation hooks; never rerun them for the debugger.

Existing selected-subject native hooks/overlays keep their dated acceptance scopes. R65 adds detailed static B8 explanation only, not a fresh loaded-hook/render/transport/native PASS or completion of the original goal. [Original requirement reconciliation](ORIGINAL-REQUIREMENT-RECONCILIATION-2026-10-05.md) retains community/FRONTIER/catalog/Boss/integrated-case/cost and final-review work.
