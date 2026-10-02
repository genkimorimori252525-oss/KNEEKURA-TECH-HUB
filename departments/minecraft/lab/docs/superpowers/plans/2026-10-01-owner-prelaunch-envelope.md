# Node owner prelaunch envelope and initial snapshot sidecar

Approved source-only continuation of the experimental runtime bridge. Java owns the concrete installation gate/inbox; this work unit owns Node preparation and the existing launch flow integration. No Minecraft launch, runner settings, publication or new daemon is part of this work.

## Fixed contract

The optional private operator registration is separate from ExperimentRequest. It pins the exact request hash, a strict material descriptor, canonical disposable-world registration, and the existing grant selection. A trusted root-relative locator plus SHA-256 selects that private registration; experiment text never selects its path or grants permission.

Preparation reuses the existing registered request/binding/material bytes and `buildOwnerGrantIntent`. Both preparation and sealed-input reads apply the shared full `validateVisualExperimentRequest` value contract without rewriting the original request bytes. It writes exclusive bounded run-local files under `control`: owner-envelope.json, owner-grant.json, owner-material-descriptor.json, owner-world-registration.json, owner-experiment-request.json and fixed owner-materials/build.jar/config.bin/resources.bin. The envelope pins exact dependent byte hashes and the generated session/run/snapshot/epoch/nonce. Existing/torn/conflicting files are not overwritten or healed.

Only KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE and KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256 enable the Java gate. The existing launch flow clears inherited/configured values when the private registration option is absent. When present, all registration/material/world/identity checks and immutable preparation finish before spawn. Startup rechecks the prepared files before publishing READY evidence.

The initial RunSnapshot adds only bridge.ownerControlIntent:{envelopeHash,scope:BOUNDED_DIAGNOSTIC_CONTROL,fullTargetAttestation:NOT_ESTABLISHED}. The canonical body sidecar `run-snapshot.canonical.json` is written and synced before `run-snapshot.json` becomes the immutable commit marker. Sidecar exact bytes hash to snapshotHash; it excludes snapshotHash and is never reconstructed with Java number formatting. No posthoc snapshot fields or false loaded-target attestation are introduced.

## Implementation steps

1. RED tests for private registration shape, exact request/material/world linkage, authority separation, unsupported actions/budgets, fixed output paths and exclusive/torn-state rejection; implement `bridge/owner-prelaunch.mjs`.
2. RED tests for owner environment isolation and exact snapshot body hashing/commit order; wire optional preparation/recheck into `launchDebugRun`, leaving normal launch default-disabled.
3. Run focused tests, existing source aggregate and Java/Node interoperability fixtures supplied by the Java owner worker. Report exact source verification and remaining live proof limits; hand off only this work unit's files.

## Shared interfaces

Java envelope/descriptor/world-registration schemas are the fixed schemas agreed with the owner worker. Parent owns adapter/TECH CLI actions; this slice exposes preparation/recheck helpers but adds no CLI start/execute command. Any incomplete loaded-target proof continues to block gameplay/visual PASS.

## Exact shared schemas and exports

`prepareOwnerControl({runtimeRoot,runDir,identity,operatorRegistration,bridgeContext})` prepares immutable files. `identity` has exactly debugSessionId,runId,runSnapshotId,processEpoch,handshakeNonce. `operatorRegistration` has exactly trustedRoot,relativePath,sha256; the SHA selects the exact private file bytes. `bridgeContext` is the existing validated registration result, never free caller-supplied request data.

The private operator registration file has exactly:

```json
{
  "schemaVersion": 1,
  "requestHash": "<sha256>",
  "materialDescriptor": {
    "schemaVersion": 1,
    "linkageMode": "PACKAGED_JAR_CODE_SOURCE_AND_CLASS_RESOURCE_LINKAGE",
    "targetModId": "<registered-mod-id>",
    "buildArtifactHash": "<sha256>",
    "configArtifactHash": "<sha256>",
    "resourceArtifactHash": "<sha256>",
    "classResources": [{"className": "<actual instantiated-mod class or supported Probe anchor>", "sha256": "<sha256>"}]
  },
  "worldRegistration": {
    "schemaVersion": 1,
    "registrationId": "<operator-registration-id>",
    "canonicalWorldRoot": "<absolute canonical disposable world directory>",
    "worldName": "KNEEKURA_DEBUG_WORLD",
    "dimensionId": "minecraft:overworld",
    "permissions": ["BOUNDED_DIAGNOSTIC_CONTROL"]
  },
  "selection": {
    "grantId": "<grant-id>",
    "leaseId": "<lease-id>",
    "arenaEpoch": 0,
    "expectedArenaRevision": 0,
    "allowedActions": ["wait_ticks"]
  }
}
```

The second supported linkageMode is `OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE`. classResources contains 1..8 unique Java class names and exact byte hashes. This metadata never causes arbitrary class loading. `CARDINAL_CAPTURE_PAUSE_CAMERA` is the only optional additional world permission, and must appear in the private operator registration. allowedActions must equal the request's supported operation set; unsupported use_item remains blocked.

Output `control/owner-material-descriptor.json` and `control/owner-world-registration.json` contain exactly the corresponding nested objects above. The grant is exactly the existing `buildOwnerGrantIntent`/Java `KneekuraDebugArenaOwnerGrant` schema; it is not extended. `control/owner-experiment-request.json` retains the exact original registered request bytes.

Output `control/owner-envelope.json` has exactly:

```json
{
  "schemaVersion": 1,
  "debugSessionId": "<session-id>",
  "runId": "<run-id>",
  "runSnapshotId": "<snapshot-id>",
  "processEpoch": 1,
  "handshakeNonce": "<private per-run nonce>",
  "requestHash": "<sha256 of owner-experiment-request.json>",
  "grantHash": "<sha256 of owner-grant.json>",
  "materialDescriptorHash": "<sha256 of owner-material-descriptor.json>",
  "worldRegistrationHash": "<sha256 of owner-world-registration.json>",
  "controlMode": "BOUNDED_DIAGNOSTIC_CONTROL"
}
```

Fixed copied material paths are `control/owner-materials/build.jar` (64MiB), `control/owner-materials/config.bin` (1MiB), and `control/owner-materials/resources.bin` (16MiB). No material descriptor field selects another path.

`readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot=false})` is the shared read-only verifier. It returns `{envelope,grant,request,materialDescriptor,worldRegistration,identity,ownerControlIntent}` after verifying every dependent byte hash and run/request/target/world linkage. It never creates storage. With requireSnapshot=true it additionally returns `snapshot` after verifying `run-snapshot.json`, `run-snapshot.canonical.json`, snapshotHash, exact initial ownerControlIntent and all run/request identities. The sidecar contains canonical snapshot body bytes excluding snapshotHash; exact bytes hash to the existing `sha256:<hex>` snapshotHash. No Java numeric reserialization is used.

`ownerLaunchEnvironment(env,preparedOwner)` strips both owner envelope environment keys unconditionally, then sets them only from a successfully prepared result. Preparation also returns `envelopeHash`, `envelopeFile`, and `ownerControlIntent`; private nonce/path material is not copied into public result claims.

The parent-owned action adapter's final dispatch key is bare lowercase SHA-256 of exact `stableJson({actionId,processEpoch,requestHash,runId,runSnapshotId})` bytes. This module does not define a second action key.

## Existing launch configuration opt-in

The existing private launch config may set `ownerControl` with exactly `{requestHash,operatorRegistration:{trustedRoot,relativePath,sha256}}`. No new CLI command or TECH start/execute route is introduced. `ownerLaunchSelection(config,options)` rejects conflicting config/options. Normal configs keep the owner environment pair absent. The original private operator file remains separate from the experiment input and must be selected by its exact byte hash.

## Source verification and limits

The focused owner suite covers strict authority/material/world linkage, bounded immutable preparation, disabled inherited owner environment, original canonical RunSnapshot hashing (including integer-like object keys), no partial snapshot marker, and rejection of self-consistent foreign runtime metadata. An isolated Node fake-target fixture exercises the actual existing launch flow from private configuration through pre-spawn preparation and initial snapshot publication. This is a source integration test; its synthetic READY metadata is not game-runtime or loaded-target proof.

The canonical sidecar is synced first; the complete synced snapshot is published with an exclusive hard link from a private temporary file. Filesystems that cannot support this operation fail closed. An interrupted preparation or initial snapshot publication is not healed in place.

Full source CI is the repository's existing `npm run test:ci`, with `test:bridge-owner-prelaunch` appended. Java interoperability uses a source-parser JVM's actual PID and exact Node-produced bytes. No Minecraft world is opened and full-target runtime attestation remains NOT_ESTABLISHED.
