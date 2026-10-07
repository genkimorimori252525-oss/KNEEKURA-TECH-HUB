# Opt-in mob POV

Implemented on `codex/mob-pov-camera-20261007`; use this branch's LAB and Python source together. No additional MOD or dependency. It requires a private integrated debug server, spectator observer, loaded registered `Mob`, sealed owner material/world/request identity and a live nonrenewable lease. Public/multiplayer servers are unsupported.

Declare `visual_rig: {mode: "mob-eye-live-v1", fov: 60, viewport: [640,360]}` and explicit world permission `MOB_POV_CAMERA` alongside `BOUNDED_DIAGNOSTIC_CONTROL`. FOV30..100; viewport integer64..2048 must equal the actual framebuffer. `max_captures: 0` is view-only; 1..16 permits that many explicitly requested PNGs. Visual/cardinal assertions and trigger captures are unsupported. Cardinal retains its own permission and minimum4 budget.

Prepare/register the ordinary immutable ExperimentRequest and scoped-control registry first. Repin the complete module set for this source, including `bridge/mob-pov.mjs`. Never copy hashes/UUIDs/nonces from documentation into authority inputs. Source-bound native setup is demonstrated by [finite pilot](native/run-mob-pov-tank.mjs); it needs an existing registered host/template and exact cached compile classpath.

The Tech Hub command prefix is `kneekura-minecraft experiment` (or `python -m kneekura_tech_hub.minecraft experiment`). With `--registry REGISTRY --request-hash HASH`:

```text
mob-pov --command-index 0 --camera-operation attach --subject-uuid UUID --duration-ms 10000
inspect-mob-pov --command-index 0
mob-pov --command-index 1 --camera-operation snapshot
inspect-mob-pov --command-index 1
mob-pov --command-index 2 --camera-operation return
inspect-mob-pov --command-index 2
```

Wait for each immutable receipt before publishing the next index. Maximum32 operations/run, indices0..31. Attach1..120000ms is capped by remaining lease. Same index/content returns `ALREADY_REQUESTED`; changed/reordered/foreign requests are rejected. A transport submission is `NOT_CONFIRMED`; inspection reports the owner and does not establish target attestation or experiment success. After unknown dispatch, inspect the original index; do not retry at another index.

Default live view allocates no PNG/frame history or recording buffer. A snapshot reserves one declared capture and saves one <=4MiB PNG through the existing bounded evidence worker. Call LAB `readMobPovImage({runDir, envelopeHash, commandIndex})` from `bridge/mob-pov.mjs` to retrieve bytes only after a `CAPTURED` receipt. It checks exact subject/type/dimension/run identity, metadata, full PNG/hash/dimensions and canonical image binding. Finalization also binds the frame to retained canonical observations and seals its PNG/finite command records. Return metadata is finite evidence, not a frame recording.

Frames are `RAW_SCENE_RGB` at `AFTER_LEVEL_BEFORE_POST_EFFECT_HAND_HUD`. Species camera post effects, hand and HUD are omitted from this raw stage; live presentation may differ. Actual pose/quaternion/FOV/viewport and matrices accompany client tick/frame/interpolation. `serverReference` is an independent asynchronous sample, explicitly **not same-tick**. Rendered RGB never proves mob AI perception. Viewing changes observer presentation/camera; no zero-observer-effect claim is made. The camera does not write mob transforms/AI or hold server ticks.

Return/expiry/owner loss/death/unload/world change/camera replacement terminate viewing. Restore only the still-owned camera in the same world; a valid original camera is preferred, otherwise a valid player fallback. External camera replacement is preserved and restoration is `UNKNOWN`. Cardinal and POV share one camera claim. Image-write completion may follow view termination; shutdown waits for camera evidence quiescence. Do not seal or export a running owner.

## Verification

See the dated acceptance entry in [AI feedback](../../../../../docs/AI-FEEDBACK.md). Source/contract checks are separate from native coverage. The pilot preserves original-world hashes and exercises zero default PNG, advancing server ticks, one requested image, explicit return and expiry on a frozen saved Reimu. Moving/dead/unloaded target and external-camera native cases require further bounded acceptance; pure lifecycle tests alone do not establish these client behaviors.
