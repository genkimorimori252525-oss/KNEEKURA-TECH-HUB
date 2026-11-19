# Cardinal capture and trigger source contracts

This source slice implements X3 and bounded X5 orchestration. It has not run in a Minecraft client. Source checks and compilation establish API compatibility/control logic only. Default runtime state is NOT_CONFIGURED; no environment variable or file automatically enables camera control.

## Explicit owner installation

The existing Arena owner must first be installed with its actual disposable-world authorization and loaded-JVM attestation gate. A trusted Supervisor then installs `KneekuraDebugCardinalCapture` on the client thread with a `KneekuraDebugCaptureOwner` and `KneekuraDebugCaptureEvidenceSink`. `uninstall()` aborts/cleans up an active attempt. Request JSON cannot supply implementations of these owner interfaces.

The concrete capture owner receives the same Arena grant and an immutable `KneekuraDebugCapturePolicy` derived by the Supervisor from the exact registered visual request. Policy pins request hash/generation, FOV, viewport, duration, fixed behavior-assertion IDs and separate owner authorization for pause/camera takeover. Request booleans never replace owner authorization. Four image slots are reserved once through the existing Arena owner; lease/revision/attestation are rechecked on the server thread, including at least barrier budget +100ms of remaining lease.

No raw command, script, launch transport or second scheduler is added. Capture IDs are bounded filesystem-safe IDs and cannot be replayed in the installed run. A callback handling trigger slots must use the supplied deterministic capture ID, enforce its deadline and call the same authorized capture path.

## Barrier and camera behavior

Supported fallback: unpublished integrated server, exact registered world, no existing screen/postprocessing effect, no pressed input, exact requested current framebuffer dimensions. Unsupported conditions reject before presentation mutation. The detached client camera entity is never added to a Level and the player is never teleported.

After actual `Minecraft.isPaused()` becomes true, a bounded existing server task records subject/world state and holds its owner thread for at most two seconds. The client takes NORTH/EAST/SOUTH/WEST on strictly increasing render frames. Every frame verifies retained client subject state, barrier ownership, actual position/angles/FOV and unchanged viewport. Entity eye-height interpolation is calibrated on uncaptured frames, then checked. No same-frame claim is made.

Pixels come from AFTER_LEVEL before hand/HUD. Actual projection matrix is retained. In pinned Forge 1.20.1, AFTER_LEVEL receives the projection PoseStack, so the view matrix is observed at AFTER_ENTITIES in that same render frame. Its convention is `JOML_COLUMN_MAJOR_CAMERA_RELATIVE`: subtract the recorded camera position from a world point, multiply by view matrix, then projection matrix. This retains roll/camera transformations and avoids treating a projection stack as a view matrix.

Exact restoration compares Minecraft API readback against saved camera entity/position/angles, camera type, FOV, bobbing, GUI, screen, mouse-grab and pause state. `setScreen(null)` does not synchronously unpause; completion waits for observed unpause and server hold release. World loss/interference/timeout yields UNKNOWN or PARTIAL; the implementation does not rewind player/world state to manufacture restoration.

Pause, server hold, camera takeover and render-eligibility changes are explicit perturbations. Affected behavior assertions are INCONCLUSIVE; visual review remains NOT_RUN. A BrokerEvidenceCut is never interpreted as the pause barrier.

## Evidence interfaces for X4/X6

The existing raw evidence writer retains frame PNGs under `evidence/raw/visual/<sha256>.png` and emits EXPERIMENT-scope VISUAL_CAPTURE observations. The observation payload is the direct `cardinal4_raw_frame` or `cardinal4_capture_manifest` object. Images are immutable, limited to4MiB each and16MiB total pending writer work; the same worker persists/fsyncs each image before acknowledging its raw row. Existing-file conflicts/symlinks/FIFO replacement fail closed. No separate writer/store is created.

`validateVisualManifest` and `readRawVisualImage` are the strict Node entrypoints. The manifest binds run/session/snapshot/process, experiment generation/request hash, Arena epoch/revision/baseline, exact subject UUIDs, controlled-state hash, per-view image/observation hashes, camera matrices/viewport, frame/tick intervals and observed restoration proof. Missing and uncertain frames have explicit MISSING/WRITE_UNKNOWN statuses. The structured state contains dimension/gameTime/arenaBounds and selected subject UUID, position, velocity, yaw/pitch and AABB bounds. It contains no vision-inferred facts.

The controlled-state hash is produced over exact Gson bytes; consumers must not assume a cross-language JSON reserialization recreates those bytes. Canonical source Observation IDs and EvidenceCut are supplied by the existing Node store. `retainVisualManifest` requires matching canonical source payload and verifies present image bytes. X4/X6 must preserve these source references and raw/derived separation.

## Bounded triggers

`EvidenceRuntime.armTriggerCapture(config, registeredCaptureCallback)` is explicit opt-in. `triggerCapture(kind, sourceObservationId, captureId)` accepts canonical source observations only. Ordinary `refresh()` polls the same controller/ring, recognizing new canonical rows with a declared `payload.triggerKind` and exact experiment identity. Arming does not replay historical trigger rows. Native anomaly detection beyond existing tagged observations belongs to its Probe owner; this module does not infer damage or exceptions from arbitrary log text.

Configuration fixes trigger kinds, sorted sample offsets, tolerance, cooldown, maximum windows, deadline and a budget of at most four four-frame capture sets. Pre-roll uses already retained images; missing past frames remain missing. Future capture callbacks run once per due slot and must enforce the supplied runtime deadline/identity. Unresolved or rejected callbacks become OUTCOME_UNKNOWN; an acknowledgement alone is never an image. Only a matching canonical capture within the declared time tolerance can fill a slot. No continuous full-resolution recording is enabled.

Trigger manifests reuse `evidence/captures`, the canonical prefix proof and ObservationRingBuffer coverage. Retention rechecks source identity, actual source time eligibility, image hashes, proof/coverage and honest verdicts. Finalization rejects further writes.

## Source verification

- `npm run test:visual-capture`: strict manifest, structured-state, PNG, trigger and retention tests
- `npm run test:ci`: existing full source aggregate plus the visual/trigger suite
- `node debug-workspace/forge-bridge/check-capture-source.mjs --java-home REGISTERED_JDK`: pure Java protocol/barrier/restoration/policy/immutable-image tests
- Add `--forge-classpath-file REGISTERED_JAR_LIST_JSON` for actual dependency compilation plus the real writer queue/durability test. The JSON is an array of absolute cached dependency JAR paths. `--arena-source-dir REGISTERED_MAIN_JAVA_DIR` is needed only while the X2 prerequisite source lives in a separate integration copy

Actual compilation was checked against mapped Forge1.20.1-47.4.6 and genuine dependencies with JDK17; no Minecraft-shaped stubs were used. Minecraft launch, pause/camera behavior in a real client, visual correctness, performance and repair acceptance remain NOT_RUN. No workflow/runner settings or publication are changed by this slice.
