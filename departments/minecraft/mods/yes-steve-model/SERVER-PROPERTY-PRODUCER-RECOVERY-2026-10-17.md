# Server property producer and rate gate — 2026-10-17

## Scope and evidence

Primary static review only. Exact official 2.6.5 Forge 1.20.1 JAR:
SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, 63,269,843 bytes.
Comparison source: YesSteveModel/YesSteveModel revision
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
The evidence records complete declarations, instructions, supplemental operands,
handlers and bootstrap/constants for 39 methods across the three owners below.
This count includes supporting codec methods; it is not 39 new semantic mappings.
Central mapping stays 669. Independent semantic review NOT_RUN; no target JVM,
network packets, game, GPU or native implementation was executed.

| Source role | Exact owner suffix |
|---|---|
| capability/ServerDrivenPlayerPropertiesTracker | Ooo0O0000OO0OOO0o0Oo0oOO |
| util/TokenBucket | O00O00O0OoO0O0Oo0Oooo0o0 |
| network/message/DispatchServerDrivenProperty | O00OO0Oo0O0Oo0O0Ooo0o00O |

## Producer order

- `setupPacket(player,sync)` clears the pending packet when sync is false or its
  entity ID differs. In its exact `(ServerPlayer;Z)Dispatch...` body, the first
  branch at offset 1 reaches clear at 18; same-ID branch at 15 bypasses clear.
- `tick(player,sync,lowBandwidthUsage)` selects bandwidth mode before packet setup.
  Experience, flight, integer-cast health/maxHealth, food, raw float axes and
  shield-cooldown caches are updated when changed even with sync false. Staging
  is separately gated by sync. Float-axis comparison precedes byte quantization.
  Health compare/copy includes F2I; sub-integer health changes need not produce a
  different cached integer. This is a representation observation, not a bug.
- Normal sync tail attempts broadcast. `broadcastPacket` first rejects empty
  packets (branch 7), then requests rate permission (call 14, branch 17).
  NetworkHandler call is at 25; a new pending packet is assigned at 40 only after
  normal return. Denial leaves the coalesced packet available. No exception
  handler/finally or successful-delivery guarantee is established here.
- Effect add/remove stage into pending packet without an immediate broadcast in
  those methods. Extra animation stages if either new or old name is nonempty;
  this is not equality-based deduplication. Molang changes require both normal
  bandwidth and sync before stage/broadcast.

## Rate algorithm, not a measured throughput

Mode changes/null limiter create TokenBucket(3,3) for low bandwidth, otherwise
TokenBucket(4,7). Constructor computes Math.round(1000 / outputPerSecond):
333 or 143 milliseconds for those constants. It initializes capacity slots to 0.
Request reads System.currentTimeMillis (offset 0), rejects only now < nextTime
(the comparison branches at 10), removes oldest history, inserts now at index 0,
and sets nextTime to the minimum of history[i] + interval*(i+1), using Math.min
at 78. Equality is accepted. Wall-clock jumps and actual server scheduling were
not tested; do not turn parameter 7 into a measured seven delivered packets/sec.

## Full builder differs from delta send

`full(player,broadcast)` clears pending state only if broadcast is true, allocates
a new message, sets the full flag, and snapshots scalar/effect/axis state. Empty
active effects still produce an explicit empty effects field. Amplifier encoding
adds one and narrows to byte. Shield false is not explicitly staged: conditional
branch 296 skips its setter at 301. Extra animation is included even if empty.
This method neither sends nor invokes the rate limiter; it returns the builder.
The full flag is not itself a reset of every client property. Resolve receiver
and model-reset order before drawing stale-state conclusions.

## Reproduction and recovery provenance

`tools/server_property_producer_ysm_265.py` accepts --jar, --source-root,
--evidence and --out. The evidence and verification share this document prefix.
Fresh re-extraction after an environment rollback passed 214 integrity checks
and rejected 13 intentionally corrupted fixtures. This supersedes an unpublished
local attempt; no unavailable old receipt or old local commit is represented as
published. Integrity checks compare artifact/source bytes and operands, not
executable behavior or independent semantic review.

Next join: [server full synchronization](SERVER-FULL-SYNC-RECOVERY-2026-10-17.md).
