# Owner-authorized bounded runtime connection source plan

> **For agentic workers:** Use superpowers:executing-plans and TDD. Source-only implementation; no live launch or publication.

Goal: connect the existing bounded Arena/tick/journal/evidence APIs to explicit Supervisor-issued owner input and retained typed action ingress, without creating a second runtime owner.

Baseline: genuine combined source commit ae084eb9c9ed238ec9de26907572914a384a6432. Approved parent design: scoped diagnostic control, separately named JAR and class-resource/container linkage; incomplete transformed/config/resource certainty never becomes full target or gameplay/visual PASS. Approved bridge spec: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/c7542e829cd9d6db80c7eec3c96d702d28498533/docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md

## Ownership and contracts

Node worker owns private operator registration, run-local envelope/grant/material/world/request copies, paired Env variables and immutable initial snapshot/canonical sidecar. Parent owns selected-action adapter/TECH routes. This worker owns Java inputs, native material/world gate, owner installation/inbox, Env/Bootstrap hooks and source tests. No Java class loading from caller names, network reads, shell/commands or daemon.

Env: KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE and KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256, absent by default and always paired. File must be runDir/control/owner-envelope.json. The initial snapshot binds bridge.ownerControlIntent.envelopeHash. run-snapshot.canonical.json contains exact JS canonical body excluding snapshotHash; Java hashes raw bytes and checks parsed equality rather than recanonicalizing floating numbers.

Fixed inputs: control/owner-envelope.json, owner-grant.json, owner-material-descriptor.json, owner-world-registration.json, owner-experiment-request.json; copied artifacts control/owner-materials/build.jar/config.bin/resources.bin. All regular bounded files, no symlink parents, strict JSON and expected raw hashes; envelope identity matches Config session/run/snapshot/process/nonce. Existing grant schema remains unchanged.

Envelope exact fields: schemaVersion1,debugSessionId,runId,runSnapshotId,processEpoch,handshakeNonce,requestHash,grantHash,materialDescriptorHash,worldRegistrationHash,controlMode BOUNDED_DIAGNOSTIC_CONTROL.

Material descriptor exact fields: schemaVersion1,linkageMode,targetModId,buildArtifactHash,configArtifactHash,resourceArtifactHash,classResources[{className,sha256}]1..8. Native instantiated ModContainer mod class is required; other anchors are fixed already-loaded Probe classes only. No Class.forName or request-controlled fallback paths/URLs.

World record exact fields: schemaVersion1,registrationId,canonicalWorldRoot,worldName KNEEKURA_DEBUG_WORLD,dimensionId,permissions (BOUNDED_DIAGNOSTIC_CONTROL, optionally explicit CARDINAL_CAPTURE_PAUSE_CAMERA). This operator-owned registration is outside ExperimentRequest. Java measures current server canonical world root/name/dimension; name alone is never authority.

Material modes:
- PACKAGED_JAR_CODE_SOURCE_AND_CLASS_RESOURCE_LINKAGE: already instantiated target mod, direct local native CodeSource JAR, raw digest equals registered build; selected class-resource bytes equal the corresponding expected artifact members
- OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE: explicitly selected dev/container tier; fixed native loader/module/code-source identity and bounded class-resource hashes equal owner build-member manifest. Never a silent direct-JAR fallback

Both modes report transformedClassCertainty NOT_ESTABLISHED, fullTargetAttestation NOT_ESTABLISHED, config/resource ON_DISK_NOT_LOADED unless an actual supported probe later establishes more. The concrete gate is explicitly scoped to bounded diagnostic control; UNCONFIGURED is unchanged. Installation retains exact private linkage/world observations. Action evidence retains hash references to that immutable installation, material descriptor and world registration, plus explicit certainty limitations; private paths are not copied into action rows.

Ingress uses existing control/actions/<sha256(key)> request.json/canonical-action.json/receipt chain and exclusive dispatch.json with schemaVersion1,ownerEnvelopeHash,runSnapshotId,runSnapshotHash,requestHash,handshakeNonce,leaseId,selectedActionId,idempotencyKey,payloadHash. Key is bare SHA256(stableJson({actionId,processEpoch,requestHash,runId,runSnapshotId})). Action args/type are derived from the sealed original initial_state+actions; no new caller args/key. Consume in retained order, at most one new action/tick, at most32 dispatch intents plus one separate owner cleanup reset directory. Previously accepted/applied/interrupted/uncertain actions never replay.

Installation reservation and receipt are immutable run/control metadata, not a database. Owner-installed receipt/status fields follow the shared schema sent to the parent. Mutable owner-status.json is only a bounded current-state hint backed by exact owner/run and immutable evidence; always recheck native owner on dispatch.

## Tasks

1. Pure input and envelope/snapshot/descriptor/world checks
- [x] Negative Env/input/output-path tests and retained grant validation; exact hash/canonical snapshot and sealed request/material checks
- [x] Implement inputs/files and backwards-compatible Config.OwnerSetup; pure source tests compiled/run

2. Native classloader/material/world linkage
- [x] Real directory/JAR JVM fixture tests, wrong hash/foreign anchor/layout rejection, immutable ZIP expansion bound; no Minecraft fixture proof
- [x] Implement bounded material linkage and actual Forge instantiated mod/world API adapter
- [x] Genuine selected Forge API compile; exact private installation scope/certainty and hash-only action references

3. Owner install and replay-safe typed inbox
- [x] Pure key/args/order/identity and one-shot lifetime/restoration-fence negatives; journal bounds/recovery tests remain inherited. Native tick scheduling itself is compile-verified, with live acceptance deferred
- [x] Implement fixed reservation/install/status lifecycle, bounded sequential action inbox, independent finite capture slots, explicit one-reset cleanup and material boundary proof
- [x] Wire existing Env/Bootstrap/tick owner and shutdown rendezvous; same durable EvidenceWriter and inert legacy setup

4. Source verification and handoff
- [ ] Run portable pure and genuine API tests, Node source CI on final combined bytes, existing full test and disclose browser limits
- [ ] Independent review, reconcile shared source with Node worker, exact changed-file hashes and source-only readiness documentation
- [ ] Parent owns publication/whole pinned Forge CI and deferred authorized live acceptance

## Review focus

- No caller boolean or disk hash pretends to prove resident transformed definitions or loaded config/resources
- World registration and exact native canonical root must agree before installation/mutation
- Snapshot float/hash differences, inherited Env activation and replaced/torn files fail closed
- Same original action cannot gain another key/args/order or replay after acceptance/unknown
- Revocation/lease/material/world drift blocks writes; thread-safe detach remains possible after expiry

## Source verification checkpoint

- Current Java input/output/selector/lifetime/material/world checks: 52 directory/API checks plus 8 genuine packaged-JAR fixture checks. OwnerConnection/CardinalCapture/ScopedOwnerGate compile against genuine mapped Forge dependencies
- Node→Java exact snapshot/body and actual-parser-PID handshake passed; fixture topology is synthetic and does not establish a live Minecraft owner
- Private OwnedCompletion supplies observed barrier completion only to the source owner. The durable capture manifest schema is unchanged. RESTORED exact Minecraft API presentation and released/unexpired barrier are required before further dispatch; exception/timeout/unknown closes the connection permanently with idle=false
- Owner installation cannot renew: consumed immutable reservation plus process-local one-shot state survive tick retries/close; lease begins at native installation and is rechecked before publishing an active receipt
- Shutdown aborts on the client and waits for the exact existing server-thread detach and actual client capture quiescence (including manifest acknowledgement) before the existing writer seals. Failure cannot yield renewed control
- Config/resource blobs remain ON_DISK_NOT_LOADED. Transformed resident definitions and full target attestation remain NOT_ESTABLISHED; gameplay/visual assertions cannot receive PASS from this scoped control
- Parent owns final combined Node suite, portable source runner, full pinned mod compilation and publication. No live game execution occurred

Verified one-shot cleanup terminally closes the original-grant connection after its epoch advances. The exact cleanup journal remains inspectable; previous action uncertainty is retained and no grant/lease can reinstall.
