# Opt-in mob POV camera

Approved intent: 2026-10-07 user instructed a light feedback audit followed by implementation, before returning to NaturalGhast. Repeated intermediate approval prompts are not required by that instruction.

## Scope

Tech Hub LAB for Minecraft1.20.1/Java17, on the current TANK_CORE branch base `6b7456278b25e1f8ac3fbeb416ee7ee9a525c542`. One exact, registered, loaded Mob UUID; integrated private server and spectator observer only. Live eye camera follows Minecraft's render entity without writing mob position/rotation/AI or stopping server ticks. Return explicitly or on expiry, target/world/owner loss or external camera change.

No new dependency, fake-player MOD, default activation, per-frame telemetry, video, image ring buffer or background frame export. Viewing creates only bounded operation/restoration receipts. Snapshot creates exactly one requested PNG plus metadata; retain UNKNOWN for missing/unpaired observations. Camera RGB does not prove AI sensing or gameplay correctness.

## Contracts and ownership

Add `visual_rig.mode = mob-eye-live-v1` with existing `fov`30..100 and integer `viewport`64..2048. Permit max_captures0..16 (zero means view-only). Cardinal keeps its existing minimum4 and visual assertion contract; mob POV accepts structured assertions only. Python and Node validators agree. New explicit world permission `MOB_POV_CAMERA` never implies cardinal pause permission.

Existing local owner-control transport publishes bounded numbered mob_pov commands: attach(subject UUID, durationMs1..120000), snapshot, return. At most32 operations/run; sequential immutable slots, exact envelope/snapshot/request/lease/arena binding; no arbitrary executable/action payload. Runtime revalidates the actual owner, registered subject/type/dimension, loaded Mob and relevant camera ownership before mutation. Snapshot reserves one actual capture from the existing Arena budget, never four; duplicate slots cannot repeat effects. Attach duration is capped by actual remaining lease. Return/abort must remain possible without renewed mutation authority.

Use one shared client camera claim for cardinal and mob POV. Restore the previous camera only in its still-current world and while the operation still owns the presentation; otherwise fall back to the local player where safe, or leave an externally replaced camera untouched and report uncertainty. Do not restore entity transforms or stale worlds. Cardinal behavior remains unchanged except cooperative conflict exclusion.

## Live image evidence

Reuse the existing bounded image worker/PNG path. Mob POV has a distinct raw image kind/rig and no fabricated cardinal manifest. Capture at AFTER_LEVEL before hand/HUD/post effects, with actual render-camera pose/quaternion, FOV, projection/view matrices, viewport, client tick/render frame/partial tick, subject UUID/type and exact run identity. Record independently observed server tick/gameTime as an asynchronous reference, explicitly not a synchronized same-tick sample. Species camera effects are presentation facts, not AI perception.

View-only does not write frame files. One requested snapshot has a short render deadline and4MiB PNG limit; failed/uncertain requests are never automatically retried. Writer completion, not queue admission, proves durable delivery. Shutdown waits for actual camera detach and pending delivery before evidence finalization.

## Verification

Group tests for valid/invalid rig/budgets, independent permission, exact target/runtime identities, immutable replay/order, camera conflict, stale world/owner, expiry/death/unload/disconnect and zero unsolicited images. Compile actual Forge adapters; bounded private native pilot checks attach/render/snapshot/return, live server ticks and cleanup. Record native NOT_RUN if prerequisites fail; no pure test proves Minecraft rendering. Preserve original-world hashes and finalized evidence.

## Trade-offs

Ruling: use a separate mob POV rig, not frozen cardinal — live behavior needs a different time contract — cost if wrong: revise the new artifact/validator seam.
Ruling: implement view plus single PNG first, defer clips — meets selective retrieval without extra data/dependencies — cost if wrong: later bounded sequence/encoder work.
Ruling: retain local branch without push/merge — user requested implementation, not publication — cost if wrong: a later integration step.
