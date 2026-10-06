# QB-MOD / Garnet-MOD 1.6.4.082 — Networking, persistence and synchronized-state boundaries

Primary evidence: supplied QB/Garnet Java source and structurally corresponding class trees.

## 1. Network surface

The explicit custom packet surface discovered in this snapshot is small.

### Garnet full-auto channel

Garnet registers a legacy custom payload channel and `PacketHandler` receives `Packet250CustomPayload`.

Server path:
1. require `player instanceof EntityPlayerMP`;
2. read current equipped ItemStack;
3. require its item to be `ItemGarnetGun`;
4. apply `packet.data[0]` to that stack's FullAuto state.

Positive boundary:
- an arbitrary non-gun equipped stack is rejected.

Static risks:
- no payload-length validation before indexing `data[0]`;
- payload is not a typed/versioned message;
- client input state becomes a weapon-control flag directly;
- no sequence/rate information is carried.

ANCHOR:
- use a typed Forge channel/message;
- validate side, length/schema and current held weapon;
- make ammo/reload/cadence server-authoritative;
- optionally treat input as “trigger held” only, not “fire accepted”.

## 2. GUI opening is not packet-state injection

Madomagi uses Forge's legacy GUI handler.

Client side:
- entity ID is passed in the GUI open coordinates field `x`;
- client looks up entity by ID and creates a new `GuiMadomagi`.

Server side:
- `MadomagiGuiHandler` does **not** reconstruct the menu from entity ID;
- instead it returns a mutable shared field `container`;
- entity code creates `ContainerMadomagi`, calls `injectContainerAndID`, then `openGui`.

This creates a cross-request shared-state hazard:
- one global handler instance owns the last injected container;
- concurrent/reentrant players can theoretically overwrite that state before server retrieval.

ANCHOR:
- send entity ID/UUID/menu data through the supported menu-opening buffer;
- server independently resolves the target entity;
- construct one menu instance per player/open request;
- never store request-specific container state in a singleton handler.

## 3. Five-slot tactical inventory

`InventoryMadomagi`:
- fixed size 5;
- each occupied slot saved as normal ItemStack NBT + `Slot` byte;
- common entity NBT stores this list under `Inventory`;
- AI queries/consumes this inventory;
- inventory is dropped on entity death and on Ultimate Form entry.

The GUI interaction temporarily forces Standby:
- mode byte is copied to an unsynchronized `memoryMode`;
- server enters Standby while menu is open;
- menu close restores Free/Follow/Satellite/Standby from the remembered byte.

This makes GUI state affect tactical AI behavior.

Persistence caveat:
- `memoryMode` and `openInventory` are runtime fields, not persisted/synchronized as durable state. That is reasonable for transient UI state but should be explicitly modeled in a modern rewrite.

## 4. Garnet synchronized companion state

`EntityGarnetTameable.entityInit` allocates DataWatcher indices:

| Index | Type | Meaning |
| ---: | --- | --- |
| 15 | byte | enabled/contracted flag |
| 16 | byte | tactical mode |
| 17 | string | owner username |

NBT:
- `Owner` string;
- `Mode` byte.

On load:
- non-empty Owner causes owner restore;
- entity is re-enabled;
- Mode restored.

The enable bit itself is not persisted separately; ownership implies enable on load.

ANCHOR:
- UUID owner;
- explicit saved command state enum;
- modern SynchedEntityData accessor IDs;
- schema migration if old save import is ever supported.

## 5. Magical-girl synchronized state

`EntityMahoShojo` adds:

| Index | Type | Meaning |
| ---: | --- | --- |
| 20 | byte | form: normal/transformed/Rebellion/Ultimate |
| 21 | byte | posture/aim pose |
| 22 | int | Soul Gem corruption |

NBT:
- `Trans` byte;
- `SoulJem` integer;
- `Inventory` list.

Important details:

### Posture is transient
DataWatcher 21 is not written to NBT. After reload it naturally returns to neutral posture.

### Soul Gem setter is additive
Load calls:

`setSoulGemDamage(savedSoulJem)`

and that method does:

`current + value`.

Because a newly created entity starts at zero, ordinary load reconstructs the saved value. The method name is still dangerously misleading and cannot safely be reused as an absolute setter after nonzero initialization.

### Misspelled persisted key
The schema key is `SoulJem`, not `SoulGem`.

If old-world compatibility is desired, an ANCHOR migration must support the exact legacy misspelling.

## 6. Soul Gem ItemStack state

Soul Gem uses ordinary item damage for corruption.

Additional transient/local detector state lives in ItemStack NBT:
- `nearGriefSeed` boolean.

Holding the item updates the detector flag based on nearby witch/GriefSeed entities.

This is a case where:
- durable gameplay resource = item damage;
- presentation/proximity cache = NBT boolean.

Modern rewrite should avoid writing persistent stack data every tick when a client-visible computed predicate or component can serve the same purpose.

## 7. Grief Seed entity synchronized/persisted state

DataWatcher:
- 20 int: Soul Gem damage/corruption;
- 21 int: incubation countdown, default -1.

Custom NBT writes:
- embedded block coordinates/data;
- shake/in-ground state;
- `countDown`;
- `SoulJem`.

### Critical persistence gap: Homulilly ritual identity

Special ritual seed uses a plain Java field:

`private boolean isHomulilly = false;`

`setHomulilly()` sets it true.

`chooseMajo()` checks it first and returns Homulilly Nutcracker.

But neither `writeEntityToNBT` nor `readEntityFromNBT` stores/restores this flag.

Therefore after save/load or unload/recreation through NBT, the seed has no source path that restores `isHomulilly=true`. Its next witch selection falls back to the ordinary random table.

This is a **strong static persistence-bug candidate**. A bounded 1.6.4 runtime save/reload test would be the ideal final proof.

### Superclass NBT caveat

EntityGriefSeed overrides read/write methods without calling `super.writeEntityToNBT` / `super.readEntityFromNBT`.

Because Minecraft's outer Entity serialization writes base position/identity separately, not every inherited field is necessarily lost; however EntityLiving/Creature-specific NBT behavior may be bypassed. Exact impact should be tested or compared against 1.6.4 superclass implementations before making a stronger claim.

## 8. Charlotte phase persistence gap

Charlotte DataWatcher:
- 18 byte: revivable count;
- 19 byte: second-form flag.

NBT saves only:
- `Revivable`.

Read restores only revivable count.

There is no NBT save/restore of DataWatcher 19.

Loaded entities use the default constructor/DataWatcher initialization, so the second-form flag initializes false unless another runtime path sets it after load.

Result: **second-form identity is not durably persisted in this class**.

Likely consequences include reverting:
- second-form model/scale selection;
- movement/fall behavior;
- collision terrain destruction;
- summoning suppression.

This is a high-confidence source-level persistence defect candidate.

## 9. Witch ecology age is intentionally or accidentally session-local

`EntityMajo` fields:
- `private int age`;
- `private int summonServant`.

They drive:
- maturation/evolution;
- summon timing;
- kill acceleration.

The class has no custom NBT read/write for these fields.

Therefore chunk unload/save-load creates a new runtime object whose constructor resets both values to zero, unless another subclass manually seeds age.

This means ecological growth progress is **not durable across entity serialization**.

Whether this is a bug or an intentional anti-runaway property cannot be determined from current author/history evidence.

ANCHOR needs an explicit design decision:
- durable ecology: persist age/summon state;
- local-session ecology: intentionally reset and document it.

## 10. Parent/master references are mostly runtime-only

Several encounter relations are plain object references rather than stable IDs.

Examples:
- Ophelia phantom → master Ophelia;
- Shadow Puella Magi → Walpurgisnacht;
- Homulilly servants → Nutcracker;
- Garnet servant → master entity.

These are used for:
- lifetime checks;
- kill credit/age feedback;
- parent population bookkeeping.

The inspected subclasses do not persist those parent references as UUID/entity identifiers.

Consequences after unload/reload can include:
- child loses parent kill callback;
- phantom loses parent linkage;
- encounter population accounting diverges;
- form-bound child may survive/behave differently if its lifetime test depends on a missing reference.

ANCHOR:
- use encounter ID/master UUID where relation must survive serialization;
- keep raw object references only as cached resolved handles.

## 11. Correctly persisted polymorphic state

Not all special state is lost.

Examples:

### Shadow Puella Magi
- DataWatcher 18 type;
- NBT `PuellaMagiType`;
- restored on load.

### Court Lady
- DataWatcher 18 guide/type;
- NBT `Type`;
- restored.

### Ophelia
- `Phantom` boolean itself is persisted;
- master pointer is not.

### Charlotte
- revivable count is persisted;
- second-form bit is not.

This mixed quality is useful for reconstruction: the author clearly used NBT selectively, so missing fields should not be assumed to be automatically handled elsewhere.

## 12. Walpurgis render-state synchronization

Walpurgis DataWatcher 18 stores a float derived from health and is used for shaft rotation/presentation.

This demonstrates another pattern:
- server simulation health;
- synchronized derived presentation state;
- renderer reads the watcher.

Modern rewrite can often eliminate duplicated derived state and compute visual interpolation from synchronized health/boss phase, unless historical timing requires a separate value.

## 13. State taxonomy for ANCHOR

A modern reconstruction should explicitly classify each field:

### Durable authoritative
- owner UUID;
- tactical mode;
- form;
- corruption;
- 5-slot inventory;
- GriefSeed special incubation type;
- Charlotte phase/revival state;
- ecology age, if designed durable;
- encounter/master UUID, if designed durable.

### Synchronized presentation
- form;
- posture;
- phase/model selector;
- boss animation values.

### Transient server runtime
- action cooldown;
- path penalty;
- current target;
- open-menu flag;
- cached resolved parent entity.

### Client input
- trigger held;
- GUI interaction intent.

Do not merge these categories into one NBT/DataWatcher bag.

## Key migration lesson

This MOD is a strong example of why **“it has a DataWatcher value” does not mean “it survives save/load.”**

For every modern entity state:
1. decide authority;
2. decide synchronization;
3. decide durability;
4. decide reconstruction after unload;
5. test the save/reload boundary explicitly.