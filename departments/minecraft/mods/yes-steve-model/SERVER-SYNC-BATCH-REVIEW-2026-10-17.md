# Handshake, server publication and Java synchronization boundary review

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No target/native routine, network send or model data was executed. The fixed10 [receipt](SERVER-SYNC-BATCH-CHECKPOINT-2026-10-17.json) passes1917 integrity checks/122 corrupt-evidence controls in2.564seconds. Three repeated method snapshots agree with zero conflicts. Counts are not semantic completion;669 central mappings remain byte-identical.

## Connected reading order

1. [Handshake](CHANNEL-HANDSHAKE-RECOVERY-2026-10-17.md): first-write version registration differs from equality-based channel presence. The client reply is not conditional on a newly registered value; repeated server initialization is.
2. [Server Java synchronization](SERVER-MODEL-SYNC-JAVA-RECOVERY-2026-10-17.md): server-task scheduling, dimension-type/distance selection, INIT before publication, different callback paths and local packet-send completion. Four native declarations remain no-Code boundaries.
3. [Result/model carriers](SERVER-MODEL-RESULT-CARRIERS-RECOVERY-2026-10-17.md): immutable-container copy requests versus mutable elements; conditional one-use raw-array getters and the exact optional-integration caller.
4. Existing [client sync state](CLIENT-MODEL-SYNC-STATE-RECOVERY-2026-10-17.md) and [server state propagation](SERVER-FULL-SYNC-RECOVERY-2026-10-17.md) retain their distinct readiness/application gates.

## Comparisons outside the artifact batch

The [Netty source-unit receipt](NETTY-OUTBOUND-UNIT-COMPARISON-2026-10-17.json) pins official4.1.82.Final source, where message count and pending-byte accounting are different units. This narrows the meaning of the Java traffic threshold but does not verify the loaded library version, run Netty or reproduce a throughput problem. The ten-cohort artifact/source batch does not re-fetch that external source. Its original file remains outside Git.

No parsed native input, encryption/protection behavior, JNI callback scheduling, active optional plugin, successful injection or in-game failure is inferred from these Java contracts. Native-access comments establish neither runtime caller identity nor thread safety. Recent findings still await independent semantic review; no source fix is part of this research.
