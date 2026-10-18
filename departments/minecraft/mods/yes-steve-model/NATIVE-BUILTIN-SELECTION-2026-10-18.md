# Blacklist filtering and builtin destination selection

## Conclusions

Blacklist rules apply to the full archive record name before the 31-byte builtin prefix is removed. Native control flow filters comments and blank lines but does not trim surviving patterns. Suffix path normalization is present; final containment beneath builtin is not proved. These are static constraints, not observed configuration, archive contents or safe extraction.

## Blacklist producer and line semantics

The path is config root d35348 joined with blacklist.txt (3d8e53..3d8e67). Status helper 311210 is called at 3d8eed. Tag 1 enters reader 4e0060 at 3d8f03. Otherwise 3d8f4c passes native literal d2ecd0, length 0xc49 (3145), to writer 4dfb30 and jumps to cleanup at 3d9778. This is not evidence of file existence or write success. The fallback branch does not compile the new default contents during this pass.

The default literal is configuration/help text embedded in the native image, not extracted archive content. It explains regex matching of complete archive names and includes four example patterns, all commented out. It also says the default model has a separate loading mechanism; that explanatory claim is not independently verified by this bounded seam. Literal bytes and hash are included separately.

For the read branch:
- Vector comparison against original constant 3aaa0 (sixteen CR bytes) and scalar paths replace CR with LF, e.g. 3d8fcd..3d8fe4. CRLF therefore becomes two delimiters, with empty segments skipped.
- Lines are delimited on LF, e.g. 3d9620..3d9636 and 3d96d0..3d96ff.
- Empty lines are skipped (3d9685). Lines whose FIRST byte is # are skipped (3d9690). No inline-comment stripping is shown.
- It scans each remaining line using imported isblank at 3d96a4; all-blank lines are skipped. The actual locale is not established. This is isblank, not isspace.
- The scan pointer advances, but surviving lines are compiled from the original start/end: 3d9716 restores original start; 3d9b1c..3d9b2b passes it and line end to compiler 32c1e0. Thus leading/trailing blanks remain regex characters. A line starting with blanks then # is not recognized as a comment.
- Compiler option word is exactly 0x15 (3d9b25); resulting regex objects occupy 0x20-byte vector records. Local GCC 14 headers identify this bit pattern as ECMAScript|icase|optimize, but these headers are auxiliary reference, not pinned build provenance. Preserve numeric flags as the authoritative fact; full locale/regex dialect compatibility needs pinned implementation evidence.
- No invalid-pattern recovery or skip-on-compile-error guarantee is proved here.

## Matching and selection

The loop first requires archive name length at least 31 and exact case-sensitive bytes assets/yes_steve_model/builtin/ (3d97fd..3d982c, preceding report's original-byte literals). Every compiled rule receives the ORIGINAL full archive name [begin,end), before prefix stripping or normalization. At 3d9872 → 3d1930, R8=0 and R9=1. The latter selects match mode: 3d1d64..3d1d75 invokes executor 3d24c0 once; the alternative branch 3d1d92..3d1df5 advances starting positions for searching. This matches whole-range regex_match rather than substring search semantics; local regex.tcc supplies corroborating structural correspondence, not pinned implementation identity.

A true result causes 3d989a → 3d97f0, skipping the record. Otherwise advance to the next 0x20-byte regex object (3d98a0). If none matches, read the record (3d98d9). Prefix match alone therefore does not imply extraction; blacklist compilation, matching and archive read all remain required conditions. Actual blacklist rules are unavailable.

## Destination normalization and containment

3d98de..3d98f6 requires length greater than 30, then subtracts exactly 31 and advances pointer by 31. 3d9905 → 3d1390 copies that remaining byte range into a native path object and parses components via 3196a0. 3d9915 → 31df40 processes the suffix path, then 3d9927 joins its output to builtin d352f8 through 35caa0/31cc30.

31df40 is lexical-normalization-like component processing: it explicitly recognizes single dot (31dfd5) and dotdot (31e019..31e022), removes some preceding components, and conditionally preserves dotdot by appending it at 31e54a..31e552. This is not blanket rejection of parent components. Generic append 31cc30 also has a replace-left branch at 31cc47..31cc6b when predicate 318eb0 is true or the left path is empty; complete root/platform semantics of that predicate are not audited here.

No explicit suffix rejection for absolute/rooted paths or parent components, no canonical descendant check after join, and no symlink-resolution/containment check are present in the audited extraction callsite. The suffix is normalized before joining, not validated as contained afterward. Therefore containment is UNPROVED. This is not a claim of a demonstrated exploitable traversal: actual archive entry names, earlier parser constraints, fixed integrity comparison, writer behavior and filesystem state have not been supplied or tested. A trusted archive and successful earlier integrity gate cannot be silently substituted for a code-enforced path-containment contract.

## Boundaries and provenance

No archive payload or user configuration was read. No target/JVM/guest execution, host test, extractor, output write simulation, comparison bypass or successful fixture was introduced. Original native image SHA256 remains 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. Copied windows and the full default configuration literal remain outside Git; the compact contract and hashes are published. Original inputs remain immutable. Path parser, complete regex semantics, invalid-pattern behavior, actual rules, file contents and destination containment remain explicit future evidence boundaries.

## Subsequent regex closure

[Native flags and full-range executor evidence](NATIVE-BLACKLIST-REGEX-2026-10-18.md) strengthens the earlier auxiliary-header comparison using pinned upstream sources and exact native scanner/matcher/acceptance paths. Original runtime locale, compiler release and complete dialect conformance remain unproved.
