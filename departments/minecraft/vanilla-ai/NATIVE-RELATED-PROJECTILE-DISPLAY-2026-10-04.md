# Related projectile native display — bounded acceptance

Date:2026-10-04 (Asia/Tokyo). Work in progress under the active remaining goal. This implementation extends the earlier single-selected-entity native age display. The source contracts and limited native pixels below remain separate from broad usability acceptance.

The explicit default-OFF native overlay can now draw independent related-projectile groups when the existing selected-shooter projectile/control burst actually produced accepted-spawn and completed-tick observations. No additional AI, entity lookup, owner getter, physics tick, forward-fill or projectile discovery occurs. Only rows already flushed by the canonical writer feed the derived cache. Original records and public projectile observation contracts are unchanged.

Exact session/run/snapshot/process/Arena/selection revision and selected-shooter UUID guard each input. An accepted `ServerLevel.addFreshEntity` true return registers the actual projectile UUID/class/burst/spawn event index. A missing/false/late/foreign spawn does not authorize a trajectory. The spawn position is not a completed-tick sample. Subsequent original completed-tick returns must match that accepted identity; removed references do not resume. Only finite bounded positions from those tick returns become display points, retaining their exact observation IDs. Malformed positions, source gaps, dimension/type boundaries and large observed distances prevent fabricated connections.

The display retains at most16 accepted UUID groups and128 related completed-tick positions **globally**, independently of the existing selected-entity128-position cache. Both are cleared on context change/selection clear/disable. Immutable snapshots are combined only when their selected-shooter contexts match, guarding races between the separate snapshot reads. Geometry stays bounded to2048 lines,64-block camera distance and100 actual game ticks of age. The per-projectile UUID supplies its fixed initial hue; it warms toward yellow/red and expires. Native projectiles use dashed connections and three-axis point markers. A finite palette does not guarantee unique colors; retained/SimLab ID labels remain the stronger identity aid.

The renderer forwards actual raw-Cardinal quiescence to the **combined** geometry before acquiring a drawing buffer; related lines remain suppressed through raw capture/restoration. Native status reports retained group UUIDs and accepted-spawn source IDs separately from submitted point/segment source IDs. Retained group count is not a currently-visible group count, and draw submission is not framebuffer/GPU proof.

## Source validation

- RED→GREEN pure Java/Gson cache and geometry contracts cover late arm, tick-only positions, duplicate suppression, simultaneous independent UUIDs/hues/source references, capture suppression, expiry, mismatched source/revision/owner/burst/class/spawn index, removal, source gaps, selection clear,16-group/global128-position bounds and malformed-position breaks.
- Genuine writer/API tests in overlay OFF/ON modes verify that related groups use the actual flushed accepted-spawn/tick observation IDs and Arena. OFF retains no hidden groups. No game process is launched by these contracts.
- Motion/Decision113 tests /0 skipped and genuine owner/Arena/camera/world/API regressions pass. Hash-checked all-bridge/Mixin compilation passes without new dependencies. Portable source selftests include the new cache/geometry contract for CI.

## Native-r33 at frozen source

Producer `adb0fe504c3ab60b66b31368c824d2dbf562ed80`, Java Edition1.20.1 /Forge47.2.0. One actual-AI Skeleton with a bow and a survival player use a labeled private prelaunch support-room/high-health fixture copied from the original85-file Tank. Player yaw90/pitch0 is explicitly preconfigured to view west; no diagnostic changes the live camera, world or AI. The prior R32 world85 files and separate post-setup/prelaunch baseline85 are preserved and SHA-verified. Original/control85 hashes remain unchanged.

The projectile-only200-tick burst retains45 callbacks /37,716 payload bytes and ends **WINDOW_ENDED**: five accepted Arrow spawns,32 completed-tick returns (28 retained positions and four removed returns), four original hurt-call returns and four base hit returns. This window does not reconstruct later shots/missing positions or prove complete combat. Production retained presentation/validators pass without changing canonical data.

Canonical evidence:428 unique observations /SHA256 `0ef40736c09a4ada4150c524db0f4235ba09ee9d9d1249e958fa0d91acdc553d`, `EVIDENCE_COMPLETE`, clean ACK/drop0/queue0 and `VERIFIED_EXIT`. Native PID14968 is stopped. Actual JFR start/stop and FLR header are verified:2,255,319 bytes /SHA256 `30f426a87e52dbefff18a28ba069fcf95cf114e5ec853006ba88d598fdc5de83`.

One explicitly private read-only **own Minecraft framebuffer** diagnostic reads640×480 pixels at gameTime40580,131 client ticks after selection. PNG SHA256 `b45fa917a2718a40954d3b1b79678819f383361919247bbebbfa5623ff4682f6`. Direct visual inspection shows the Skeleton/support room, faint older red projectile-shaped traces, a warmer intermediate arc and a new violet arc/three-axis markers, with the separate Mob floor trace. This is derived native display, **not raw registered Cardinal capture** or a fabricated image. Its synchronous readback/PNG IO costs100.5855ms; that perturbation is excluded from performance acceptance.

The closest of21 native submission receipts is `obs:forge-runtime:14968:174` at40586, **six ticks after the image**, retaining three groups/21 actual positions/rejected0. Its submitted source references include seven completed-tick positions for each of these accepted UUIDs:

| Actual projectile UUID | Accepted source /tick | Completed-position source ticks |
| --- | --- | --- |
| `779a104b-0415-47fc-93db-00cdfc46d42b` | `obs:forge-runtime:14968:54` /40487 |40488..40494 |
| `a5a8e5c5-902b-4937-b011-d8bc416a7daa` | `obs:forge-runtime:14968:98` /40527 |40528..40534 |
| `d3296437-37d2-4b65-8d06-1fcf3cdd065f` | `obs:forge-runtime:14968:147` /40567 |40568..40574 |

At the image tick these retained positions lie in old/middle/new age bands respectively. The screenshot and source receipt establish limited multi-group native display; their temporal companionship does **not** establish exact per-pixel/UUID/geometry correspondence. Subsequent source receipts retain five groups/28 points even after old points expire visually: retained count is not visible count. The native cache does not fabricate post-window positions.

The source's three exact-HEAD GitHub checks are SUCCESS: source push `37162641275`, source PR `37162643134`, pytest `37162643171`. Later documentation HEADs require their own checks. All-camera/high-overlap readability, native UUID labels, palette collisions, exact pixel/source geometry correspondence, GPU draw attribution, raw-capture suppression in a combined live shooting scenario and paired observer-effect acceptance remain open.

Subsequent [R37](NATIVE-RAW-OVERLAY-SEPARATION-2026-10-04.md) verifies bounded raw/derived suppression through a normal fixed-owner capture while four synthetic related groups/128 positions remain cached. Same actual snapshots yield eligible432..462 lines and suppressed0; all four raw views and a separate restored derived frame were inspected. This closes only the synthetic fixed-owner QA case. Natural shooting/dynamic owner registration, exact pixels/GPU, native IDs and broad readability/performance remain open.
