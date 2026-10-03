# Related projectile native display — source checkpoint

Date:2026-10-04 (Asia/Tokyo). Work in progress under the active remaining goal. This implementation extends the earlier single-selected-entity native age display; runtime pixels and broad usability require separate acceptance.

The explicit default-OFF native overlay can now draw independent related-projectile groups when the existing selected-shooter projectile/control burst actually produced accepted-spawn and completed-tick observations. No additional AI, entity lookup, owner getter, physics tick, forward-fill or projectile discovery occurs. Only rows already flushed by the canonical writer feed the derived cache. Original records and public projectile observation contracts are unchanged.

Exact session/run/snapshot/process/Arena/selection revision and selected-shooter UUID guard each input. An accepted `ServerLevel.addFreshEntity` true return registers the actual projectile UUID/class/burst/spawn event index. A missing/false/late/foreign spawn does not authorize a trajectory. The spawn position is not a completed-tick sample. Subsequent original completed-tick returns must match that accepted identity; removed references do not resume. Only finite bounded positions from those tick returns become display points, retaining their exact observation IDs. Malformed positions, source gaps, dimension/type boundaries and large observed distances prevent fabricated connections.

The display retains at most16 accepted UUID groups and128 related completed-tick positions **globally**, independently of the existing selected-entity128-position cache. Both are cleared on context change/selection clear/disable. Immutable snapshots are combined only when their selected-shooter contexts match, guarding races between the separate snapshot reads. Geometry stays bounded to2048 lines,64-block camera distance and100 actual game ticks of age. The per-projectile UUID supplies its fixed initial hue; it warms toward yellow/red and expires. Native projectiles use dashed connections and three-axis point markers. A finite palette does not guarantee unique colors; retained/SimLab ID labels remain the stronger identity aid.

The renderer forwards actual raw-Cardinal quiescence to the **combined** geometry before acquiring a drawing buffer; related lines remain suppressed through raw capture/restoration. Native status reports retained group UUIDs and accepted-spawn source IDs separately from submitted point/segment source IDs. Retained group count is not a currently-visible group count, and draw submission is not framebuffer/GPU proof.

## Source validation

- RED→GREEN pure Java/Gson cache and geometry contracts cover late arm, tick-only positions, duplicate suppression, simultaneous independent UUIDs/hues/source references, capture suppression, expiry, mismatched source/revision/owner/burst/class/spawn index, removal, source gaps, selection clear,16-group/global128-position bounds and malformed-position breaks.
- Genuine writer/API tests in overlay OFF/ON modes verify that related groups use the actual flushed accepted-spawn/tick observation IDs and Arena. OFF retains no hidden groups. No game process is launched by these contracts.
- Motion/Decision113 tests /0 skipped and genuine owner/Arena/camera/world/API regressions pass. Hash-checked all-bridge/Mixin compilation passes without new dependencies. Portable source selftests include the new cache/geometry contract for CI.

Native simultaneous drawing, projectile age pixels, exact pixel/source geometry correspondence, all-camera/overlap usability, GPU draw attribution and paired observer-effect acceptance remain unverified at this source checkpoint.
