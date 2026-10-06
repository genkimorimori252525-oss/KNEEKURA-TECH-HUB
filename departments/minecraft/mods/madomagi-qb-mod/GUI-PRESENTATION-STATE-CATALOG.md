# QB-MOD 1.6.4.082 — GUI / presentation / synchronized-state catalog

Primary evidence: supplied QB-MOD source snapshot and alternate texture-pack inventory.

## 1. Magical-girl internal inventory

`InventoryMadomagi` is a five-slot inventory bound directly to one EntityMahoShojo.

It supports:
- NBT serialization with explicit slot indices;
- drop-all;
- lookup by item id;
- lookup by item class;
- lookup by item id + durability threshold;
- consume one stack item;
- damage an internal item;
- GUI open/close callbacks into the owning entity.

Those callbacks matter because the inventory is not merely storage: it participates in NPC behavior such as:
- Grief Seed cleansing;
- Rebellion trigger item detection;
- torch placement;
- UF inventory ejection.

Technique: **NPC inventory as both player-visible container and AI resource pool**.

---

## 2. GUI-open tactical state

EntityMahoShojo's GUI callbacks:
- remember current companion mode;
- force Standby while inventory is open;
- restore the remembered mode when closed.

Ultimate Form refuses normal inventory access.

Technique: **UI session temporarily acquires exclusive control over NPC tactical state**.

ANCHOR should make this server-authoritative and per-menu/session.

---

## 3. Legacy GUI handler risk

`MadomagiGuiHandler` stores one mutable `ContainerMadomagi container` field.

The entity injects a Container before opening the GUI; server `getServerGuiElement` later returns that shared field.

Client side instead resolves the target entity by entity id carried in the GUI x argument and creates a fresh Gui/Container.

This creates a potential cross-player/reentrancy race in the server handler:
- handler instance is shared;
- container is mutable shared state;
- concurrent/interleaved openings could overwrite the field before retrieval.

ANCHOR must resolve the target entity/menu state from the server-side open payload per player, not from a shared handler field.

---

## 4. Container policy

`ContainerMadomagi`:
- exposes five NPC slots in one row;
- adds normal 27-slot player inventory + 9 hotbar;
- shift-click merges between NPC and player inventories;
- allows interaction only while NPC is alive and player is within 8 blocks;
- invokes close callback on container close.

Positive invariant:
- menu validity is tied to **entity liveness + spatial proximity**.

Keep that contract on ANCHOR.

---

## 5. GUI presentation

`GuiMadomagi` reuses the vanilla hopper texture and changes the title to the magical girl's entity name.

This is a simple low-cost strategy: custom behavior without a custom GUI asset.

Technique: **reuse vanilla container presentation while binding labels/state to an NPC**.

---

## 6. Form → model → texture

`RenderMahoShojo` holds separate model instances:
- normal;
- magical-girl transformed;
- Rebellion;
- Ultimate.

Every render:
- synchronized form selects the actual `mainModel`;
- posture state independently drives `modelBipedMain.aimedBow`.

EntityMahoShojo separately chooses texture suffix by form.

This gives two orthogonal visual axes:

`form state → model + texture`

`combat posture → pose flag`

That separation is more valuable than the legacy renderer calls themselves.

---

## 7. Per-character model mappings

Client proxy registers character-specific model sets:

- Madoka: normal / MS / UF model set.
- Homura: normal / MS / UF.
- Sayaka: normal Biped / Sayaka MS reused for special forms.
- Mami: normal / Mami MS.
- Kyouko: normal / Kyouko MS.
- Kirika: normal / Kirika MS.
- Yuri: ambidextrous renderer with normal / Yuri MS.

The renderer therefore supports **shared state semantics with heterogeneous asset depth**: a character can have a unique model for every form or reuse a model where no unique geometry exists.

---

## 8. Boss scale as presentation metadata

The client registrations encode intentionally extreme scale values:
- Kriemhild Gretchen renderer scale 15;
- Walpurgis 5;
- Gertrud 4;
- Oktavia / Homulilly / Servant Oktavia around 3;
- Nutcracker 4;
- smaller familiars below 1.

This is distinct from server-side hitbox size. A modern renderer should keep visual scale, collision dimensions and navigation footprint as explicit separate values.

---

## 9. HeightCorrection

`RenderMahoShojo.preRenderCallback` only applies the special pre-render scale path when config `HeightCorrection` is true.

This is **client rendering correction**, not pathfinding/entity-height logic.

The name can be misleading if read without the renderer context.

---

## 10. Alternate TexturePack-01

The supplied alternate pack contains character/form PNG replacements under the Puella Magi texture namespace.

It is useful as presentation evidence:
- confirms form-specific asset naming/slots;
- demonstrates the renderer/texture contract is externally skin-able.

It does not prove gameplay behavior and remains separate from source-backed implementation findings.

---

## 11. Presentation/state techniques

1. synchronized gameplay form separated from posture;
2. form selects model and texture;
3. character can reuse or specialize form models;
4. NPC inventory doubles as AI resource state;
5. opening UI temporarily freezes tactical mode;
6. menu validity tied to entity + distance;
7. vanilla GUI texture reused for custom NPC storage;
8. visual scale separated conceptually from hitbox;
9. config-gated renderer correction;
10. external texture pack slots aligned with state-driven texture names.

ANCHOR implementation should use modern Forge menu/open-screen APIs and per-entity synchronized data, but can preserve these contracts.