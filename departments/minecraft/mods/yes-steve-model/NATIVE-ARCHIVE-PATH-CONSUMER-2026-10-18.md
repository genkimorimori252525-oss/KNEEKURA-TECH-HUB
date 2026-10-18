# Owned YSM archive path: bounded static consumers

## Result and hard boundary

The owned path d35258 is consumed by filesystem status, archive opening/record reading, and a fixed aggregate integrity comparison. Later code reads selected builtin resources and writes them beneath the configured builtin path. It is not a path-only or native-registration-only consumer. All observations below are original-byte/static metadata facts, not observed archive contents or passing execution.

The installed ModList/ModFileInfo/ModFile/SecureJar graph and actual absolute YSM archive path remain unavailable as described in NATIVE-MODLIST-MAP-CONTRACT-2026-10-18.json. No original archive payload was opened, extracted, decoded, or hashed. No target/JVM/guest execution, comparison bypass, passing fixture, or original-artifact mutation was performed.

## Status and opening

3d8857 passes d35258 to status helper 311210 at 3d8866. AL must equal 1 (regular-file tag in the earlier status contract); otherwise 3d886d branches to 3da953, which constructs failure information including the supplied path. This is a new status requirement, independent of config/temp-directory success.

3d8897 constructs reader 4dab30 with path d35258 and third argument zero. The reader copies the path (4dab98 → 4e0a00) and calls 4d8cb0 at 4daba4. At 4d8ced it calls fopen with the retained path and original literal 42799 = "rb". Null FILE enters error construction. Static two-stage ELF import resolution is in NATIVE-ARCHIVE-READER-IMPORTS-2026-10-18.json; actual loader binding and open success are unverified.

Reader stream vtable d2fed0 is resolved by the immutable checkpoint, not assumed from zero-filled original slots. +10 is 4e7bf0, calling fread at 4e7c0d and checking ferror at 4e7c1e; +20 is 4e7c90/ftello; +28 is 4e7bb0/fseeko; +30 is 4e7cc0/fclose. The table also contains a fwrite callback, but its mere presence does not mean the archive is opened for writing. The observed archive open mode is rb. Reader parsing and per-record read helper 4dad30 have many independent seek/read/format/error branches; their success is not supplied by this report.

## Filter, record hash, order and aggregate comparison

- Reader-produced record vector is loaded at 3d891c..3d892b. Iteration advances by 0x48 at 3d895a. The current record has name pointer +10, name length +18 and requested output length +40. These are structural observations; actual records remain absent.
- 3d896c loads a prefix list from d35c98..d35ca0. Its immutable-checkpoint entries are META-INF/native/ (16 bytes, original literal 404f6) and META-INF/jars/ (14 bytes, 43290). If a name is at least prefix length and bcmp(name,prefix,length) equals zero at 3d89ad, that record is skipped. Thus the aggregate deliberately excludes these prefixes and cannot justify an "all archive bytes authenticated" claim.
- For a retained record, 3d89d4 sizes a buffer, 3d89ea invokes reader 4dad30 with that record and output buffer, and 3d8a0c calls 573dd0(buffer,length,0x94d2ba004e0ef9dd). Helper 573dd0 is a 64-bit hash/mixing routine; this bounded review does not assign it a public algorithm name or cryptographic guarantee.
- The computed value is stored in a tree node at +30 (3d8a3e), alongside name length +20 and pointer +28. Name comparisons use memcmp over the minimum length (3d8ab7 and later comparison) followed by length ordering. Tree insertion uses 2ba6d0 at 3d8bf2. This is name-based ordered collection, not source archive iteration order. Exact duplicate-name resolution is not established here.
- The loop from 3d8c71 appends node name through 2f8f80, a newline, the stored 64-bit value through numeric stream helper 2f9640, and another newline. 2ba620 advances the tree iterator. Exact numeric/locale formatting is not independently proven; do not synthesize a byte-exact hash manifest from this report alone.
- 3d8d09 obtains the resulting stream string. 3d8d25 hashes it with the same seed 0x94d2ba004e0ef9dd. 3d8de5 compares against 0x048417704ddff4de; 3d8de8 branches on inequality to 3daa88. That failure path constructs error record code 0x33 (3daa9f), passes through 4db980, and reaches throw-like exception helper 2abe00 at 3daaf4. It is not a normal-success continuation.

The actual hash, expected manifest content, selected-entry bytes, decompression behavior, error handling and successful equality remain unobserved. The fixed comparison must remain intact; there is no authorization or implementation here to bypass it.

## Later resource writes and registration boundary

Equality falls through at 3d8dee to construct literal blacklist.txt. Subsequent code includes independent status/read-or-write behavior for that configuration file. The blacklist content/pattern semantics are not resolved here.

Later 0x48-byte record iteration at 3d97f0 tests the first 31 name bytes against constants at 3aad0 and 369c0. Overlapping 16-byte comparisons establish prefix assets/yes_steve_model/builtin/. The loop consults a further pattern predicate (3d9872 → 3d1930); matching records can be skipped. For remaining records, 3d98d9 invokes the archive reader again. The prefix is removed by adding 31 to the name pointer and subtracting 31 from length (3d98ed..3d98f6); path conversion and join with builtin global d352f8 occur at 3d9905..3d9927. 3d99ce passes destination and buffer data/length into write helper 4dfb30. This identifies a conditional builtin-resource materialization path, not proof that files exist, are safe to write, or were written. Path normalization/traversal protection and full writer behavior remain separate unresolved contracts.

3d9a7d destroys the reader; normal return is 3d9aa8. The parent init function called this routine at 413bd3. Returning still does not imply 17 native bindings were registered: an intervening mode/guard path can return early at 413c79. Otherwise 413c82 calls 406b00 to construct/resolve further managers, and only after its return does 413c97 begin the known 17-descriptor construction. Existing native-registration-static-map.md establishes later dispatcher 416175 → 327000 and RegisterNatives at 327e73. No registration completion is established by this static review.

## Evidence

NATIVE-ARCHIVE-PATH-CONSUMER-2026-10-18.json summarizes the exact PCs, literals, unresolved boundaries and provenance. NATIVE-ARCHIVE-PATH-CONSUMER-EVIDENCE-2026-10-18.json hashes copied native windows. NATIVE-ARCHIVE-READER-IMPORTS-2026-10-18.json records PLT → relative slot → trampoline → dynamic relocation/import; NATIVE-ARCHIVE-INTEGRITY-PREFIXES-2026-10-18.json and NATIVE-ARCHIVE-READER-VTABLE-2026-10-18.json record immutable metadata source hash. Disassembly endpoints or initial fragments can split instructions; claims use complete instructions and explicit target boundaries. Underlying raw byte windows and extraction receipts remain outside Git; pinned input bytes and checkpoints are unchanged.
