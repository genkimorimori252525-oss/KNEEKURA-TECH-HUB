# Retained Decision presentation — 2026-10-03

The canonical LAB consumer adds a bounded overview and a standalone derived HTML view. It reads the already retained canonical stream; it does not initialize, ingest, finalize, query a world, invoke AI, or alter owner control.

## Contract

- Exact UUID, debug session, run, snapshot, process, Arena and selected revision are mandatory. Only complete observed SERVER records in a window of at most 10,000 ticks are selected; input is capped at 50,000 retained observations. Duplicate IDs/ticks and mixed known dimensions are refused.
- The seven Decision stages remain optional. Missing stages show `NOT_CAPTURED`. Overview retains the latest distinct fact keys, original epistemic/causal labels, total counts and up to four source IDs with explicit truncation. Defaults: four keys/stage, 32 timeline events; maximum eight/64. Fact values exceeding 512 UTF-8 JSON bytes are omitted, not summarized into invented facts. Overview is capped at 64 KiB.
- Motion uses the existing SampledMotionTrace engine and at most 128 actual retained positions. Missing positions and gaps break lines; a configurable distance threshold breaks a line as a derived display rule, never as proof of teleportation. No forward-fill or interpolation creates samples.
- Observer-only ground cells, actual returned PathFinder cache and declared navigation nodes stay distinct from actual Mob movement. Cache is not a complete neighbor trace. Ground is not evaluator admission/effective Malus. Missing path result does not prove unreachable.
- All four spatial layers are OFF until explicitly checked. PLAN_XZ and fixed isometric preserve spatial roles with squares, triangles/crosses, actual sample circles and thick dashed declared routes. ELEVATION uses tick/height and excludes spatial ground/cache/navigation overlays.
- The timeline cursor filters spatial samples and hides layers acquired after the cursor. A layer's acquisition tick remains visible. The overview is explicitly labelled as the end-of-window aggregate, not cursor-current AI state. Only the latest retained cache/ground/navigation capture in the requested window is presented; historical intermediate layer snapshots remain available through typed drill-down.
- Presentation JSON is capped at 256 KiB. HTML embeds escaped JSON, uses `textContent`, a per-document script nonce and CSP denying network access. Export creates a new file (`wx`) outside the resolved retained run directory and refuses existing destinations.

## CLI

```text
node debug-workspace/cli.mjs evidence-decision-view <exact-uuid> --config <private-config> --revision <n> --arena-epoch <n> --start-tick <n> --end-tick <n>
```

This prints the bounded structured packet. Add `--output <new-file.html>` to create the standalone view outside the retained run. The existing `evidence-decision --channel ...` remains the detailed typed query.

## Verification

Eight added tests cover bounded repeated facts/large values, retained samples, unavailable stages, source/identity/window fences, missing-position/distance breaks, unsafe JSON embedding, separated path/cache roles, dimension/duplicate refusal, and export protection. The Motion/Decision suite passes **82 tests, zero skipped**.

Actual CLI JSON reads and HTML exports were run against finalized native-r8's `zombie-ground-3` and native-r12's Hydra/Knight return windows. Ground retains 49 cells; Hydra retains eight original-return timeline events in the selected 16-tick view; Knight retains one original-return event and three actual position samples. Hydra has zero position samples in that chosen narrow window, which remains explicit.

Canonical/finalization SHA256 before and after all reads/exports:

| Trial | canonical observations | finalization |
| --- | --- | --- |
| native-r8 | `922c4a66721a53ff99754cab86fb6a6c8da9dc1261bf0edbd7f46d54f80d81ae` | `be145baa5f681000e6c8e4e3ccb8f1428b1c3767370775a9436a07088cb1d07e` |
| native-r12 | `d167bd4efa0934fc035128f5555d3e5e5e56c234a8a9650274f330ec142e1010` | `0bf2345cd81612ac8516ef70ef3a9c45220ab8dfe5aa09524466e92f280fe7b9` |

Private artifacts/receipt: `K:/kneekura-decision-native-data-20261003/retained-decision-presentation/`. Browser inspection verified initial OFF controls, actual 49-cell squares and retained sample marker, ELEVATION switching, Knight's original method-return source ID and timeline-to-tick cursor synchronization. No browser warning/error logs were observed on the Knight view. The temporary localhost server and browser tab were closed after verification.

These checks validate the consumer and selected retained windows. They do not add missing gameplay observations, prove all eight Mob behaviors, Snow Queen/Ur-Ghast original callbacks, complete Boss battles, or measure total native observer effect.
