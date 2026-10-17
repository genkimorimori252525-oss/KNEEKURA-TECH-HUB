# Query-name to implementation catalog — 2026-10-17

## Lookup without reading the entire repository

[QUERY-NAME-LOOKUP-2026-10-17.jsonl](QUERY-NAME-LOOKUP-2026-10-17.jsonl) contains one
searchable row per literal query/function name. Search the exact qualified name,
then inspect that row's callback/object owner and the relevant focused dossier.
The compact lookup is derived from
[QUERY-REGISTRATION-CATALOG-2026-10-17.json](QUERY-REGISTRATION-CATALOG-2026-10-17.json),
which retains constructor offsets, bootstrap targets, registration methods,
wrapper allocations and internal callback body hashes. Neither file needs to be
loaded during unrelated repository work.

The fixed QueryBinding constructor registers 61 literal names; YSMBinding
registers 110. The total 171 is a name inventory, not 171 newly verified behaviors,
a count of implemented features or a semantic completion percentage. Aliases
between namespaces can refer to overlapping behavior; parameterized functions
and simple variables are both present.

## What the extraction proves

The scanner uses exact JAR SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
It resolves inherited registration signatures against ContextBinding, requires
one literal name and one allocation or invokedynamic target per registration,
and records the invokedynamic bootstrap method handle where applicable. Ambiguous
patterns fail instead of guessing. Callback body hashes are taken from the same
artifact when the callback owner is present. A constructor object argument can
also be an IValueEvaluator, so allocation does not automatically mean Function.

Typed wrapper selection is separate from the value target; the
[typed guard dossier](TYPED-QUERY-GUARDS-RECOVERY-2026-10-17.md) explains the guards.
An entry's semantic_review remains NOT_INFERRED_FROM_CATALOG even when a body
snapshot or source role is known. Use focused prose/verification for behavior.

## Explicit optional-extension gap

YSMBinding's constructor has a trailing nonregistration invocation at offset 1351
to `o0OOoO0oOOO00OO0ooOOoO0O`, `(ContextBinding)V`, corresponding to the pinned
source's CuriosCompat.addMolangBinding. That callback may add conditional names;
it is retained separately, not silently included in the 110-name constructor list.
No claim of a complete runtime query registry, optional-mod initialization or
absence of external registration is made. Source registration comments do not
supersede actual constructor instructions or runtime extension boundaries.

## Verification and maintenance

`tools/query_registration_catalog_ysm_265.py` accepts --jar, --evidence, --out;
--capture regenerates the catalog. The matching receipt passed two inventory
checks and rejected five corrupted fixtures, including removal of the extension
call and an invented global-coverage claim. The compact JSONL is a derived lookup,
not an additional independent evidence source.

No target execution, optional-mod probing or central mapping promotion. The map
remains 669; independent semantic review NOT_RUN. Existing fixed17/fixed10 batch
manifests remain unchanged. Next, trace the optional Curios extension explicitly
and remaining entity-specific callback bodies using these name-to-target anchors.
