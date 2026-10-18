# Exact native manager → Java member lookup

[member index](NATIVE-JAVA-MEMBER-INDEX-2026-10-18.json) is an authored lookup keyed by `manager-global+offset`, for example `0xd355b0+0x128`. It contains **46 unique slots from 11 specified continuation receipts**, with zero duplicate slots and zero contradictions:

- 42 original-YSM declarations
- 1 declared Minecraft dependency declaration: commons-lang3 Pair.of
- 3 declared JDK java.base declarations read from existing modeled checkpoint metadata

This is a deliberately bounded index of the selected receipts, not complete manager coverage, the central semantic-name map, or the original17 native-entry registration table. Readable semantic aliases are intentionally absent.

Each entry retains exact owner/name/descriptor, member kind, staticity, declaration access when recorded, class hash, declaring class and artifact identity. Evidence points to the source receipt and its SHA256, member index and checkpoint SHA256. Guarded callback records additionally preserve callback/payload digests ; full instruction evidence stays in source receipts. Top-level sources retain the original image/JAR/JDK/checkpoint provenance and synthetic-state description where supplied.

The java-collection-checkpoint-proof schema does not record access flags, original image hash or JAR hash. Its three entries therefore have `access:null` and explicit `not recorded by source receipt` status; missing provenance is not silently borrowed from a different experiment. Their source artifact is the declared java.base JMOD. Their zero-instruction checkpoint SHA256 differs from the next6 callback checkpoint and is retained separately.

## Evidence boundaries

The 43 callback-derived identities came from bounded, isolated metadata decoding in cloned state, with fresh callback frames; the index does not replay them. The other3 entries are a read-only existing modeled metadata/pointer proof with zero guest instructions. Neither category establishes runtime invocation, full JNI initialization, successful object construction, live installed dependencies, enum initialization or asset processing. Existing declaration/source confidence is not promoted.

## Validation

The external builder validated source hashes, recorded payload identities/digests, static/access agreement and duplicate rejection. Repository integration rechecks all11 source receipt hashes and46 unique slot entries. Source instruction records remain in the linked receipts; no automatic whole-repository audit or callback replay is needed for a lookup.
