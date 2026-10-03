# Optional native Motion overlay

`motionOverlay: true` in the registered Debug Workspace config explicitly arms the client renderer. Omitted/false forces `KNEEKURA_DEBUG_MOTION_OVERLAY=0`, including when an inherited shell environment contains `1`. The switch grants no gameplay action, camera or Cardinal capture authority. Decision hooks are independent.

The existing evidence writer publishes a selected `SERVER_ENTITY_STATE` record to a volatile display cache only after its ordinary durability flush succeeds. No separate evidence database, interpolated sample or hidden OFF trace is created. Session/run/snapshot/process/Arena/UUID/selection revision must match; selection/epoch changes and stop clear the cache. The observer records the actual Arena epoch and explicitly distinguishes `MOB_ACTUAL`, `PROJECTILE_ACTUAL` and unsupported entity types.

Bounds: 128 retained samples; coordinates within 30 million blocks; display only the current dimension, at most 100 game ticks old and within 64 blocks of the existing camera. Missing/invalid position, nonmonotonic ticks, class/dimension changes, more than 10 ticks between samples and derived distance over 16 blocks break the polyline. A distance threshold is not proof of teleportation. The pure Java cache/geometry and shared Node `SampledMotionTrace v1` contract agree on source IDs and discontinuity semantics.

Mob sample markers use a horizontal cross and solid sampled endpoint connections. Projectile markers add a vertical axis and dashed connections. These are derived display primitives, not projectiles, route candidates or continuous physical paths. The renderer uses the existing camera and balanced pose stack; it does not mutate world/AI/navigation or create gameplay objects.

Every 100 frames with submitted geometry, the existing writer may retain `MOTION_TRACE_VIEW` (`kneekura.live-motion-overlay-status/v1`, CLIENT). Its bounded source IDs identify flushed SERVER evidence, alongside retained/evicted/rejected counts and CPU build/draw-submit timings. This timing excludes GPU, framebuffer capture and writer cost. `rawPixelsVerified` is deliberately false: a render callback receipt is not pixel acceptance or a Cardinal raw capture.

Source verification: 84 Motion/Decision Node tests passed; portable Java cache/geometry/shared-contract interoperability passed; genuine Forge API writer tests passed with overlay OFF and ON; every bridge/Mixin source compiled against hash-verified actual Forge/MOD dependencies. Native render acceptance remains pending until the separate frozen-source trial is documented.
