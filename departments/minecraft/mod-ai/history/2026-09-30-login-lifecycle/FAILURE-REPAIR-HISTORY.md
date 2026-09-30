# Staff login lifecycle failure and offline repair

This is a minimized derived summary of the closed V5 batch and its offline repair. It is not hash-identical raw evidence. Original hashes identify separately retained artifacts; they do not provide public downloads. No raw logs, receipts, sessions, private paths, tokens or images are published.

## Observed failure

Minecraft 1.20.1, Forge 47.4.6 and Java 17. Server phase 002 and control phase 004 returned authenticated readiness with status OK; their observation outcome remained NOT_RUN. The invoker joined with server entity ID 2, then phases 006 and 007 returned authenticated HTTP 409 REQUEST_REJECTED for GET /v1/handshake. Both retained UNKNOWN and retry_allowed=false. No setup command or native gesture ran. First use, repeat, control and expiry acceptance remain NOT_RUN.

## Proven implementation defect and limits

The exact patched ClientPacketListener.handleLogin calls ForgeHooksClient.firePlayerLogin at bytecode offset 383, reads the packet playerId at 387, assigns it at 401 and adds the player at 417. The hook posts LoggingIn synchronously at offset 13. The former observer froze boundEntityId and installed StaffPacketTrace inside that event, before the final server-assigned ID existed. A changed ID then violated its later identity check.

The exact live provisional IDs were not captured. Control joined with server ID 1; its success is consistent with a coincidental provisional/final ID match, but that coincidence is not proven. The signed REQUEST_REJECTED category does not identify the underlying exception. This implementation proof does not claim an exact reconstruction of the live exception.

## Offline repair

LoggingIn consumes the epoch and retains the original player, connection lifetime and channel object without freezing the provisional entity ID or exposing a receiver. A one-shot END client tick revalidates those identities and the selected UUID, then binds the final entity ID. Receiver startup verifies and initializes its session and owned directory before a checked callback installs the packet trace; only a successful callback permits receiver activation. Logout, clone, duplicate login, identity loss and startup failure permanently invalidate the pending lifetime, and later entity-ID changes remain rejected.

Lifecycle baseline recorded 16 failures and cold-session initialization baseline recorded 8 failures. Final affected observer verification passed 184 cases with no skips, including the 28 lifecycle cases. Independent source/lifecycle review passed 106 overlapping cases with no blocking findings. These counts are not added together. The broad project suite was interrupted after scope was narrowed; no aggregate project pass is claimed. Actual Forge compile and dependency export passed for server, client and control against the frozen repaired observer source and compiled-class inventories. Target-code coverage and ordered dependency-byte identities are complete for the declared staff scope; coverage.complete remains false and broad profiles remain UNKNOWN. These builds launched no games and created no worlds or sessions.

Repair status: OFFLINE_REPAIR_VERIFIED_LIVE_NOT_RUN. Post-fix live staff acceptance is NOT_RUN. The history adapter supplies no new runtime attestation or Core promotion.

## Original outcomes and preservation

The batch clock began at 2026-09-30T18:06:34.946911+00:00. Intentional exact-owned SIGTERM closed all execution threads at 2026-09-30T18:16:20.245894+00:00; the actual desktop process probe at 2026-09-30T18:17:17.371428+00:00 was empty. All three original process receipts remain FAIL with completed=true, exit_code=1 and timed_out=false. Closure is not a timeout or successful staff acceptance.

All three earlier history directories and all 23 captured original artifact identities were rechecked unchanged. The initial pending-repair history remains immutable. One exact case query resolved every retained evidence document, and repeated import retained the same hash. The adapter made zero canonical writes.

## Evidence identities

- Final history: 66d7d6111849f64fc29bfd9a37274f71c64657d71892227b9982e69f187a8270
- Previous offline-repair history: 2c60bcd0491c75ee4af93e5a06d8b591f2554f64b9ccaa85cfffc37b21387449
- Initial pending-repair history: c4a1ad9b9c3542de98692aef5602ce6bae8ea57be9508cdaf93c6eddcf177992
- Repair evidence index: 81599a9fa3e6f2e1b00884c5fb50c9424d871da39fcbdb6aab9703ba49f62089
- Patched Forge archive: e4a657dab7bcbb97f8dd653e181ba9c5b44a90b2b6ce13aa2b2dd246957a8324
- ClientPacketListener.class: 80568d89e78331d7e7b186da60c22014e3782bd95c9a8d15eb6b11ef199c4969
- ForgeHooksClient.class: 021f8622e1b8fe67b04e9122662dabc87a782d2907a30a722c0608440ad8cd71

Exact repaired source and verification hashes are in the companion JSON. Coverage remains PARTIAL because post-fix live acceptance is pending and the original live provisional IDs and exception message are unavailable.
