# Model asset helpers: IDs, ordered lookup and shared ownership

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. 32 declarations, three owners, 179 integrity checks and eight negative controls. No target execution, independent semantic review or central-map promotion.

## ModelIdUtil counterpart

Owner `o0OooOOOoO0Oo0ooO0OOo00o`. The hash-short helper takes exactly the first eight characters and calls Integer.parseUnsignedInt with radix16. It supplies no local null/length/hex validation and returns an int representation, not a full-hash identity proof.

Path split uses the last forward slash: filename plus prefix including that slash. Backslashes are not separators here. Filename extraction strips only a recognized .zip/.7z/.ysm suffix at a dot index at least1; suffix comparison uses no-argument toLowerCase, hence default locale. Last-folder extraction maps null/empty to empty and removes one trailing slash, not arbitrary repeated trailing separators. Model-pack icon resource paths incorporate String.hashCode; uniqueness is not established.

Entity matching builds a HashSet. Strings starting with # are parsed without that prefix, invalid ResourceLocations are skipped, and matching Forge entity-type tag members contribute their holder resource IDs. Other strings are parsed and added directly if valid; this branch has no registry existence test or wildcard expansion. Result ordering is not promised. Registry contents, null tag services and actual matching at runtime are outside this static check.

## FifoHashMap counterpart

Owner `O0OO0oooo0oO0oOOo0OOooO0`. The array constructor passes the supplied arrays to ObjectArrayList.wrap and Object2ObjectArrayMap, wraps the two lists unmodifiable, then constructs a separate Object2ObjectOpenHashMap from the ordered map. The map-taking constructor first obtains fresh key/value arrays through toArray and follows the same construction.

Index access/list getters use the two wrapped lists; size, empty, contains and get delegate to the hash map. put, remove, putAll and clear throw UnsupportedOperationException. keySet, values and entrySet directly return the ordered map's views, without another local unmodifiable wrapper. These are distinct representations and boundaries; do not advertise this class as a deeply immutable map or assume every inherited default operation is covered by four rejected mutators. Exact external Fastutil view mutation/backing-array behavior was not executed here. No runtime inconsistency is asserted.

## CommonAsset counterpart

Owner `OoO00O0oOo0000oo0OOO0oO0`. Its constructor directly stores all four supplied references: sounds, user functions, event-handler lists and nested language maps. Getters return those same references. final fields provide neither deep copying nor an immutable snapshot of entries, handler lists, expressions or sound buffers.

## Reuse boundary

[Client-model composition](CLIENT-MODEL-COMPOSITION-RECOVERY-2026-10-17.md) connects these helpers to existing builder evidence. Keep input normalization, aliasing, duplicate resolution and external registry validation separate. The auditor checks artifact/source integrity and deliberate snapshot corruption, not the truth of every interpretation or upstream native validation.
