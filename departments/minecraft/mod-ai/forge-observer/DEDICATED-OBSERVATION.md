# Dedicated receiving-client observation

This opt-in development path extends the existing Store, observer and registered
runner. It does not start another service or automatically connect a client.
The original schema-1 integrated-client and GameTest contracts keep their meaning.
A successful launch or paired capture is `NOT_RUN` for gameplay assertions.

## Independent authorities

A schema-2 `dedicated_server` contract owns a fresh server world. Each
`dedicated_client` contract owns a separate fresh client game directory and
references the immutable server contract. A receiving client has no local server
world, server tick, or shared epoch. Server and client workspaces have independent
locks, profiles, configuration hashes, source generations and launch budgets.
Their target runtime class inventory, source revision, exact runtime versions and
explicit loopback policy must match. The policy selects literal `127.0.0.1`, one
port and bounded player UUIDs; each client selects exactly one UUID.

Use `world prepare --layout server` for the server and `client-directory prepare`
for receivers. `contract prepare` accepts exactly one of `--world` and
`--run-directory`. Registered `validate run --kind server` launches `runServer`;
`--kind client` launches `runClient`. The Gradle guard checks the final argument-provider boundary after Forge has
expanded its RunConfig and configured JVM/environment/classpath state. It binds
the actual server `--world` argument and game directory to the owned marker;
relative `.` is accepted only in the exact owned working directory. Alternate
universe/save roots, duplicates and option terminators are rejected. A rejected Gradle attempt can consume its explicit budget;
it is never silently retried.

The Java receiver starts from its client login lifecycle. It independently checks
its game directory, selected player, connection and native process/window. Logout,
reconnect, player replacement or changed channel invalidates that epoch. It does
not inherit server-side state as a substitute for client observations.

## Target code and dependency bytes

Dedicated contracts require `runtime_scope=TARGET_CODE_AND_DEPENDENCY_BYTES` and
an immutable `dependency_inventory_hash`. The Python preparation API
`prepare_dependency_inventory` retains every original ordered resolved archive,
including required mappings ZIPs, with its coordinate, scope, namespace, stage,
size and SHA256. It binds the exact successful registered export receipt and
current source/configuration generation. Missing, changed, reordered, omitted or
stale mandatory inputs prevent contract/session creation.

`prepare_target_profile` creates a distinct `PINNED_TARGET_CODE` profile. Its
`coverage.complete` remains false; target completeness and dependency-byte
completeness are separate fields. The original broad `UNKNOWN` profile is
preserved. This does not claim analysis of all dependencies or loaded/transformed
class completeness. The observer verifies all distinct archive bytes at startup;
later requests invalidate on changed file metadata. This is not continuous
attestation of instructions already loaded in memory.

Private session files contain the dependency file mapping and authentication
secret. Do not publish them. A derived public summary may cite original hashes,
but is not a hash-identical raw receipt.

## Pairing and native input

`observe-pair --server-session ... --client-session ... --player-uuid ...` takes
server-before, independent client, and server-after captures within one bounded
deadline. It checks each authenticated handshake and identity, selected player,
dimension and reciprocal loopback socket tuple. Separate tick/frame/log intervals
remain visible. The resulting pair is explicitly non-atomic and does not by
itself prove packet processing, gameplay causality or synchronization.

The existing `input bind` and `input dispatch` routes bind a Linux X11 native
window to the authenticated receiving-client connection. They retain before/after
screenshots and release status. A completed native event is not hardware-device
attestation or proof that the game accepted a use action. Uncertain input is not
replayed. Windows native input remains unsupported.

This fixed staff native-input route requests one explicitly bound player in
`minecraft:overworld` and sets `staff_state=true`. The actual `StaffStateQuery`
guard requires that dimension; missing or changed dimensions are rejected.
The route does not infer the player's dimension or follow a dimension change.

## Fixed staff fixture

`tools/ci/mod_ai_staff/pilot.py` has an explicit `client_trace=True` preparation
option for the exact staff fixture source. The default source and delivered MOD
remain unchanged. The instrumented build has a separate recorded identity and
read-only hooks around the known use branch and its two known mutation sites.
The bounded trace detects those sites even when a mutation is restored before
return. It does not cover arbitrary later bytecode transformations or all possible
mutator APIs.

The development observer can retain selected vanilla Glowing/cooldown packet
receipts for this exact fixture. Its Netty hook forwards every packet unchanged
and counts receipt, not completion of packet processing. Missing or malformed
instrumentation remains unsupported/unknown rather than fabricated zeroes.

`tools/ci/mod_ai_staff/verify_client.py` checks fixed before/use/after records,
including exact versions/assertions, native target and chronology, immutable trace
history, selected packet values and independently observed state. Its result is
`RETAINED_RECORD_CONSISTENCY_NOT_LIVE_ATTESTATION`; whole product acceptance is
not established by synthetic fixtures or imported records. Actual live runs,
visual review and their bounded evidence must be reported separately.

The companion `verify_controls.py` checks the declared non-invoking player,
within-cooldown repeat and tick-delayed expiry records. Control observations must
bracket the invoking window on a distinct socket/player. Repeat checks bind a
separate native receipt and intersect server expiry bounds with a one-tick update
phase allowance. Expiry captures must pass conservative server-tick deadlines.
All three preserve full trace history and reject missing or contradictory records.
Their PASS is still a scoped retained-record result, with any unrecorded OS input
and general gameplay/network correctness outside its claim.

## Integrated U04 target selection

The fixed Hydra route uses a separate schema-3 `integrated_client` contract. It
retains the existing world-bound physical-client/logical-server identity, with no
dedicated socket or server-reference fields. The fixture marker's compile receipt
and class inventory remain distinct from the selected Twilight dependency.

An explicit `u04_hydra_derived_dependency` selection identifies one exact resolved
runtime archive, retained remap receipt and bounded required Hydra/setup/renderer/
model class resources. Preparation revalidates the provider's original input,
tool, mapping, classpath, raw output and normalized entry bytes. The selected
archive's original resources must remain unchanged. Its exported namespace is
preserved; a separate derivation record describes SRG-to-Mojmap processing without
claiming source equivalence or ForgeGradle equivalence. Every other resolved
archive remains in the complete byte inventory.

The observer checks selected archive/probe bytes independently of marker probes
before readiness. The fixed `U04HydraProbe` then observes one explicitly requested
client-side Hydra UUID, its actual dispatcher-selected renderer, default/no-JAPPA
marker state, texture resource/hash and pose. It binds these fields to the existing
screenshot's hash, camera and frame interval. It does not assert that a draw call
occurred or that the entity is visible. Those require inspection of the captured
frame; mismatched or absent state remains UNKNOWN/UNAVAILABLE.

Mutable Minecraft-owned options and server settings must not be registered as
immutable files. Bind a separate immutable setup record with their initial hashes,
and report which live values were actually observed. Normal game normalization
or camera changes must not be disguised as immutable dynamic configuration.
