# Minecraft MOD-AI continuation — 2026-09-30

Status: **PARTIAL PRODUCT ACCEPTANCE.** M2 is exercised on actual Blockbench.
M3 includes actual staff-MOD provider/Core inputs, the Forge build and signed
server GameTests. M4 has a concrete Linux/X11 input path and client save-layout
support; live client acceptance is still pending. M5 fixtures/scenarios are
implemented and original U01–U05 have real-input static results; their wider
real-MOD/client acceptance remains open.

| Milestone | Implementation | Verified acceptance / remaining gap |
|---|---|---|
| M2 | Complete for the one static Java-item slice | Actual Blockbench capture, structure/export and three-view editor review pass |
| M3 | Provider/Core caller and staff import/build/handler paths implemented | Real staff bytecode/classpath/mapping derivation and Core staging pass; signed server tests pass; deployed Core/human canonical approval and upstream research remain distinct |
| M4 | Client saves layout, authenticated PID/start/window binding, registered Linux/X11 right-button route and retained input evidence implemented | Python fixtures and actual Forge Java compilation pass; physical input/client rendering/sync and Windows remain unrun |
| M5 | Real-MOD task catalog, A-case fault recipes, fixed client/server scenarios and existing history implemented | Direct-handler server cycle passes; client-inclusive cycle remains unrun; U01–U05 static checks are partial; U06 is undergoing separate Connector/candidate static checks |

Linux/X11 is the concrete available platform for this slice, not a Windows
compatibility claim. No native Windows backend or acceptance is claimed.

This checkpoint supersedes the executable-head and environment assumptions in
`LOCAL-AI-HANDOFF-2026-09-28.md`, without deleting its historical RED evidence.
Working branch and draft PR remain unchanged; no merge/deployment was performed.

## Verified implementation

### M2: actual editor, repaired assets, bounded export

- Restored a complete checkout. The old native-capture RED was already fixed on
  the incoming branch. The actual current RED was missing read-only post-failure
  editor diagnostics.
- Diagnosed the actual desktop failure against pinned Blockbench 5.2.1 source:
  plugin APIs existed before successful WebGL setup, and the GPU-error window
  could be selected as the editor. The loader now requires complete setup and a
  live render context, selects one exact file-based editor page, and the existing
  hosted job uses explicit Mesa software GL.
- Real desktop session first passed at `f5651fe5ebbaf4df9526f4644054705d74f0215f`.
  Artifact inspection found legacy-target drift (editor default `26.3`), missing
  purple accents, and an almost-solid halo. Transport success was not accepted as
  model correctness.
- At `a14f4ed7940236fc6c5493a0cb67835c878191a0`, the owned project is pinned to
  legacy Java format `1.9.0` (Blockbench's format covering Minecraft 1.20.1), with
  seven explicit bounded display transforms. A palette-only rectangle operation
  and separated halo/star geometry repair the observed visual failures. Raw
  script/plugin/filesystem routes stay closed; texture decoding is awaited.
- Native bitmap embedding is forced per capture, independent of global editor
  preferences. Version/display/project/sequence changes remain fail-closed.
- `asset_export.py` checks captured request/receipt identity, model/native format,
  native/runtime geometry and face equivalence, flat outliner, exact display
  settings, PNG framing/CRC/decompression bounds, embedded texture equivalence,
  and finite numeric UVs. It derives resource IDs and creates only a fresh export
  directory. It never installs into a project or overwrites existing resources.
- `python -m kneekura_tech_hub.minecraft.assets --store CAS export --receipt HASH
  --parent EXISTING_DIRECTORY` is the explicit local export entry point.
- `c6bbe10e76be0f2806ae2e770bad3914d60b6b8e` adds bounded retention of only the
  exact non-secret capture/export CAS closure for verified downstream import.

Live runs:
- [First capture](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36683367656)
- [Repaired legacy assets and export](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36685697463)
- [Same pipeline with exact capture records](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36686342010)

All captured and exported byte hashes were checked after download. The second
run's three PNGs were directly reviewed by the host AI: open gold halo, distinct
purple star, and readable staff silhouette. See
`verification/editor-review-2026-09-30.json`. This editor-only review does not
establish inventory, first-/third-person, or in-game legibility. Loaded provider
revision remains `UNATTESTED`; source pinning is not runtime attestation.

Latest imported evidence at this checkpoint:
- artifact ID `11083529388`
- ZIP SHA-256 `7d501b5651d82ef25eedf59d8ad3624b1e7c86dc1ea3f08b7fa987640f7a9d69`
- capture receipt `136e08825db23286e9b68840357333956f2dc4f48199d157ff2fb4e4f0e797ec`
- export manifest `d2582d7e7d14e5db9a7c6f36774ed73728be1f12df30b02b9486751931877ae5`
- 15 exact CAS objects rehashed and revalidated locally; no secret package bytes

### M3: existing Core and real provider execution

The existing Core staging caller returned an apparently valid bundle that its
actual Core schema/policy rejected: selected-file acquisition with an UNKNOWN
license. It now requires explicit caller-reviewed per-root license metadata and
runs the real Core preflight before CAS publication. The CLI uses
`--source-licenses reviewed-licenses.json`; it never infers an upstream license.
Actual Core schema/ingestion/guidance tests preserve provenance and human gates.
Schemas/policy are included in built wheels and loaded from package resources;
a real wheel was built and its isolated installed staging path was verified.

The unchanged provider adapters executed official pinned Vineflower 1.11.1 and
tiny-remapper 0.11.2 with Temurin Java 17.0.20.1+1 on an actually compiled Java17
fixture. Decompiled output recompiled; remapped class/field/methods and a smoke
caller passed; identical requests hit immutable caches. See
`verification/provider-2026-09-30/README.md` and its derived public summary. The
exact raw receipts remain local, and referenced hashes do not imply that public
receipt objects are available. This is
real-tool fixture interoperability, not a real MOD's transformed-code acceptance.

The same adapters subsequently ran on the **actual staff MOD** with all 101 exact
ordered Forge compile artifacts. Vineflower output recompiled. Tiny-remapper used
Tiny v2 converted by its bundled mapping-io from verified official Mojang + exact
ForgeGradle mappings: 7,436 classes and 96,612 members checked. All seven remapped
class instruction/signature listings and six resource files match the prior
same-source ForgeGradle package. Original/recompiled/remapped policy smokes pass.
Core staged two actual source documents into five schema-valid review-only
records; the AI ingestion gate rejected writes. This is static interoperability,
not runtime equivalence or deployed Core approval. Reproduction and minimized
summaries are in `verification/real-mod-2026-09-30/`.

The static comparison JAR `2cc36031…` and signed-run package `15fd766e…` are
separate same-source builds: class/resource bytes match, but their manifest
Implementation-Timestamp/ZIP metadata differs. Their raw package hashes remain
distinct; no exact signed-run/package-generation equivalence is claimed.

A separate fresh Forge 1.20.1/47.4.6 pilot implements the staff's bounded
server-only glow/cooldown handler and verified resource import. The final
corrected-source build/export passed, and the JAR's model/PNG hashes exactly
match the verified editor export. Source and packaged bytes were independently
reviewed. The reusable build helper also binds builds explicitly to original capture
hashes before/after execution, rather than just mutable workspace bytes.

First final-asset build evidence (before strengthened handler assertions):
- JAR SHA-256 `2f6fd565a2ddde9a6be8c4cb7c30ade0553852a4e01346732ac3f19e3af312dd`
- compile receipt `259c175cf2e8e6380d12e57e5e4d671642ce8b30808c8bae92f19f1e2f4b3837`
- export receipt `fed693027a14cf506a7204fac1b865e27d7371c79a786cf54347a1ef73bf1849`

Under explicit user approval, the Minecraft EULA was accepted in only the fresh
isolated staff test directory. First registered launch attempt ended `NOT_RUN`
during official asset downloads, before tests started: zero tests, no signed
completion and no gameplay PASS. Receipt
`aeb92a095ab1e3d994e93c1eaff175d6d9e15e3bdcb9b8c981c660fabce515e7`
is retained. The cache was repaired before a new same-scope run; this failed
prerequisite is not relabelled as a runtime success.

A second real GameTest run executed the desired and known-bad tests but the
observer correctly rejected a reobfuscated-JAR/Mojmap-userdev namespace mismatch.
Its outcome remains BLOCKED, receipt
`98501b3e7708e2c28608dd88b6e02235099977261a418164ec113fa917fbaa02`.
The fixture registration was repaired using the existing dual-output path: retain
the distribution JAR for packaging proof, and bind the run to the actual userdev
class-directory inventory. No observer hash check was weakened.

Final authenticated same-run signed file-report acceptance is **PASS**:
- run `81abe335-6368-4474-a2b2-b2e5d8ee3a11`
- receipt `e36b6e52adb0cbad30f1601d3b39c55d7ecfc5765b70458ce9039d5d1d1cd2f9`
- report completed=true, detected=5, executed=5, process exit=0
- `staff_handler` and `staff_expiry`: required PASS
- refresh, 99-tick cooldown and attempted-damage controls: optional FAIL as intended
- packaged JAR `15fd766e3249f7eb8e91ddd2767faaac5dec216fd69c4443360bdc4a272d83d6`
- actual userdev class inventory `312a7293032ac1dec5c7d3c8ed98cf83feee6e253d7df2033a1c3e77116f5492`

See `tools/ci/mod_ai_staff/ACCEPTANCE-2026-09-30.md` and its derived public JSON
summary. Raw receipt bytes and the signed envelope remain local; public hashes
reference originals and cannot independently reproduce their signature checks.
The tests directly invoke the handler and tick real server subsystems; they do
not establish physical input or wall-clock timing. No live HTTP handshake was
sampled. An old generic top-level `tests_executed` field remained the unit-test
counter (0); the authenticated GameTest report's executed_count=5 is authoritative.
A final regression fixes future generic counts to use the validated GameTest
count, including a tampered-signature negative. Historical receipts are unchanged.


### M4: registered native input and client-world integration

- `world prepare --layout client` creates `runDir/saves/<world>`; server layout
  remains the default. Ownership marker and session bind the layout. A wrong
  launch kind, stale world, changed template or symlink is rejected before budget
  consumption. This corrects the actual Forge client storage layout.
- `ClientProbe` retains its existing capture path and adds authenticated Linux
  process ID, exact process-start ticks, native X11 handle, foreground state and
  local viewport size. Unsupported platforms cannot bind the native route.
- `input_route.py` connects existing `dispatch_input` to `native_input.py` and
  explicit CLI registration. Only a local Linux/X11 right-button gesture is
  implemented. No executable command/path can be supplied by a registry.
- The selected driver is now `linux-x11-send-event-v1`: synthetic button events
  are addressed only to the exact creating client of the authenticated window,
  without propagation or global pointer/device injection. It is restricted to
  gameplay with disabled cursor and the bound viewport's crosshair center; it is
  not a menu-coordinate driver or hardware-input attestation.
- Review reproduced a physical-pointer race in the initial XTEST design; that
  path was removed. Short per-send server grabs protect window identity, not
  physical pointer motion. Deadlines are rechecked after blocking preflight and
  before mutation. Timeout/cancellation permits bounded scoped cleanup, then
  terminates a stuck helper; unconfirmed application release stays UNKNOWN.
- A real cloud-desktop owned-window GLFW test received exactly the target's
  press/release callbacks and none at a decoy. No game, foreground authentication,
  pointer or focus mutation occurred. This proves the native event API, not the
  Minecraft gameplay result. See `verification/native-api-2026-09-30.json`.
- The replay ledger belongs to the private session rather than a selected CAS,
  so changing stores cannot repeat input. Relocated/copied session paths are
  rejected before input; changing an operation ID does not clear quarantine. Existing CAS retains before/after
  screenshots and log/handshake/input hashes. Input completion never produces a
  gameplay, visual or synchronization PASS.
- Observer requests now have a total wall-clock socket deadline; real slow-header
  and slow-body fixtures prove byte drips cannot evade an idle timeout.
- Opt-in `staff_state` observation requires one exact entity UUID, dimension and
  limit=1. It returns only main-hand identity/count/damage, Glowing state and staff
  cooldown. It does not dump arbitrary NBT or mutate state. Exact tick boundaries
  remain the server GameTest's responsibility.

The current observer extension compiled against actual cached Forge1.20.1/47.4.6
with Java17. Native/API fixtures are not proof of actual desktop behavior.

## Review and verification discipline

Independent scoped and whole-change reviews drove RED→GREEN fixes for installed-wheel
resources, native/export parity, boolean UVs, preference-independent embedding,
cancellation propagation, exact protocol integer types, and retaining validated
GameTest counts independently of target acceptance. The final two review findings
were reproduced and fixed with a fresh 85-test focused run. No schema/policy weakening or raw editor route
was used to obtain GREEN.

- `f5651fe`: complete hosted suite **821 passed**, real Blockbench passed
- `a14f4ed`: live Blockbench/export passed; hosted suite **940 passed, 1 failed**
  because a new test fixture inherited hosted `RUNNER_TEMP` while using pytest's
  `/tmp` root. This is retained as a real CI failure, not called GREEN
- `9224c8709dc2f174ceb55f61866cd7a0b5f07166`: fixes that test's explicit runner
  root and adds confinement negatives; 17 harness tests passed with simulated
  hosted environment. Both exact-head hosted test jobs passed, **943 passed**,
  and real Blockbench also passed
- Local focused asset/input suite: **210 passed, 1 deselected**; the deselected
  pre-existing positive private-directory fixture is incompatible with this
  sandbox's injected parent repository marker. Production guard was not weakened
- Local full runs without PostgreSQL skip database integration tests; hosted CI
  provides its own PostgreSQL16 service. Missing local DB is not a reason to
  claim the full local suite passed

Final source aggregate (Java17 plus cached official Gson): **1006 passed,
103 skipped, 1 deselected**. Skips require the local PostgreSQL test environment;
the single deselection is the sandbox directory fixture explained above.
`verification/local-final-2026-09-30.json` records code hashes and the exact
normalized command. Independent final review reports no unresolved critical or
important code finding. Refreshed observer-only Forge compilation passed in13s,
with no game tasks. The final actual-provider verifier again confirms all7 class
and6 resource comparisons, all3 reflective policy smokes and review-only Core
staging. These are local source checks; final published-head CI is still pending.

## Original U01–U05 real-input static slice

`verification/twilight-static-2026-09-30/` records actual existing-adapter
execution on pinned Twilight Forest1.20.1/4.3.2508: 49 verified source blobs,
91 prepared MOD/dependency classes, 45 query groups over78 pages, 170 complete
documents over320 pages, ten exact JVM selectors, and6156 exact packaged-resource
matches with zero mismatches/missing paths. Focused regressions:105 passed.
The literal authored Mojmap MOD-owner queries remain PARTIAL with zero binary
hits; explicit SRG follow-ups reach the shipped classes. No namespace is silently
relabeled. AI/inheritance, Forge damage hooks, coremod/network producer/consumer,
renderer/model/texture and generated-item/data paths are traceable. Full target
dependency/config closure, source/binary class equivalence and behavior/render/
network experiments remain open. These results do not close U01–U05 as a whole.

## Open acceptance

- Actual client acceptance of the implemented native input/window binding,
  physical right-click, inventory/first-/third-person observation, synchronization
  and dedicated performance evidence
- Completion of original U01–U06 acceptance beyond the executed static slices; `verification/acceptance-map-2026-09-30.json`
  maps all 24 A-cases to actual test nodes and explicitly marks partial cases.
  Adapter tests are not substituted for missing MOD/client observations
- Twilight Forest research remains before Sinytra Connector. Player-facing
  reconnaissance is discovery/navigation only; implementation evidence and
  exact version boundaries continue to govern conclusions

Do not mark M4/M5 or the whole product complete from these partial results.

## Next concrete client steps

1. Use an explicitly authorized disposable graphical client environment with the
   exact Minecraft1.20.1 / Forge47.4.6 / Java17 inputs and a bounded registered
   launch budget. Prepare a fresh `--layout client` world; never use a user save.
2. Capture the existing ClientProbe on that run and bind the implemented local
   Linux/X11 input route to its authenticated process/window identity.
3. Follow `tools/ci/mod_ai_staff/scenarios/client-observation.json`: one bounded
   physical use, cooldown repeat, fixed before/after state and inventory/first-/
   third-person views. Keep dispatch, behavior, visuals and synchronization as
   separate verdicts. Unknown input is quarantined rather than automatically retried.
4. Record any demonstrated failure/repair through existing history. Windows and
   dedicated performance acceptance still need their own environments/scenarios.

A supported cloud Linux desktop has been verified to share the test workspace
and an active X display. Client launch is pending its explicit scoped approval;
no client success is inferred from desktop availability. The existing server
approval/receipts remain bounded to their completed server tests.
