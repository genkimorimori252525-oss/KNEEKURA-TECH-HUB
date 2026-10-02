# Fixed staff acceptance scenarios

All files here are inputs. Their `execution_status` and client verdicts stay
`NOT_RUN` until separately recorded actual evidence supports a result. Historical
server evidence remains separate in the existing pilot report. Do not rewrite
these inputs into receipt-shaped JSON or infer a live PASS from a fixture test.

## Before running

1. Check the exact target and fixed assertion SHA-256. Rebuild/import/index after
   every code, asset or config edit. Keep the userdev class artifact distinct
   from the reobfuscated distribution JAR.
2. Use only the explicit registered workspace, approved disposable template,
   existing EULA/launch permission and remaining budget. The client save must be
   prepared with the existing `world prepare --layout client` route; a server
   world layout cannot stand in for a managed client save.
3. Resolve all braced values locally. Register the exact player-scoped
   `equip_staff` command before creating a session. It is setup only. Never use
   `/effect`, data mutation or `Item.use` directly as physical-use evidence.
4. Prepare a fresh run contract with the matching physical side and scenario.
   The existing execution route creates its own private session; do not create
   another session manually or reuse an epoch after restart.

For example, after preparing the client world and actual current index:

```sh
python -m kneekura_tech_hub.minecraft --store <store> contract prepare \
  --registry <registered-client.json> --index <actual-index-hash> \
  --world <prepared-client-save> --scenario tools/ci/mod_ai_staff/scenarios/client-observation.json \
  --output <local-client-contract.json>
```

This only prepares identity. A separately authorized `validate run --kind client`
is required for a live run. These example commands do not grant authorization.

## Observe, bind and interact

`client-observation.json` includes the exact native input route and a local
registry template. `input bind` establishes a fresh run-bound native target;
`input dispatch` accepts the existing v1 input request fields only. Copy identity
and target ID from the actual binding, derive an in-bounds client-local viewport
point from the current capture, and use the specified 50 ms `mouse:right` press.
The selected driver is Linux X11 only. View changes are operator checkpoints;
keyboard automation, Windows and Wayland are not silently substituted.

Use the existing read-only route for each named before/after/view capture:

```sh
python -m kneekura_tech_hub.minecraft --store <store> observe \
  --session <private-session-file> --operation client \
  --query-json '{"entity_uuids":["<actual-player-uuid>"],"dimension":"minecraft:overworld","limit":1,"staff_state":true,"screenshot":true}'
```

The query is strict when `staff_state` is enabled: one canonical UUID, one
explicit dimension, integer limit 1. The Forge observer samples only the selected
entity on the server thread. For a player, the additional `staff_state` object is:

- `schema_version: 1`, `observation_side: "logical_server"`, `applicable: true`
- `main_hand`: registry item ID, stack count, damage value
- `glowing`: null or duration in ticks and amplifier
- `staff_cooldown`: fixed item ID, registration presence, active flag and fraction

A non-player selection reports `applicable: false`. An absent registered staff
reports unavailable cooldown fields as null. No arbitrary NBT, full inventory,
reflection or success-state writes are exposed. Generic observations without
this opt-in retain their existing behavior.

## Fixed evaluation and controls

Keep physical input, behavior, visual and synchronization verdicts separate:

- Binding/dispatch and key release are input evidence; completion alone is not
  proof that Minecraft handled the use
- Before/after exact-player samples can establish observed effect presence,
  unchanged health/item count/damage and non-increasing cooldown/effect values
- Compare tick/frame/log intervals. A late sample or one crossing expiry is
  inconclusive; do not add a wall-clock sleep assumption to manufacture a pass
- Exact 60-tick Glowing and 100-tick cooldown assertions use the existing fixed
  `staff_expiry` GameTest. Sampled client screenshots cannot replace those tests
- Inventory, first-person and third-person each need their own screenshot/hash
  and explicit host review against the captured asset
- Dedicated network synchronization needs a separate server and receiving
  physical client. Runtime client-branch non-mutation needs branch-specific
  evidence; eventual server-synchronized state alone cannot prove that property

`server-behavior.json` selects only the two actual required test IDs. The three
optional negative controls must each remain visible as FAIL; never omit them
because the selected target result is PASS. `client-controls.json` fixes report,
input and client-evidence counterexamples. Offline tests execute report and
injected-input controls; the live visual/behavior controls remain NOT_RUN.

On a failure, use existing `history.capture_history` with immutable before/after
locators and the fixed scenario/assertion identities. Capture symptom, trigger,
cause, repair and lesson; an unproven cause remains UNKNOWN. Repair the actual
source/asset, create new build and contract identities, and repeat the same
assertions only within the approved remaining launch budget. Never retry an
UNKNOWN physical operation blindly, weaken expectations, or consume an extra
launch merely because a fixture says to continue.
