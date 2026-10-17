# Foreign/public variable binding reachability — 2026-10-17

## Bounded result

The fixed JAR contains ForeignVariableBinding and its variable wrapper, but a
955-class CONSTANT_Class reference inventory finds only those two classes
referring to the pair. No outside-pair constant-class referencer is found. This
is a Java constant-pool observation, not proof that native code, reflection,
external mods or dynamically supplied bindings can never activate it.

Exact JAR SHA-256:
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
Pinned comparison source YesSteveModel/YesSteveModel
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`,
geckolib3/core/molang/binding/variable/ForeignVariableBinding.java.
Outer owner `oO0o00o0o0oOo000OoO000oO`; nested variable suffix
`$Oo0Oo0o00O00Oo0OOoOOoooo`.

## Stored name, live storage lookup

getProperty interns the requested name and uses computeIfAbsent to cache a
ForeignVariable carrying that integer name. resetScoped clears this wrapper map;
it does not mutate previously retained wrapper instances or underlying storage.
The variable evaluates by directly casting the evaluator entity to IContext,
reading foreignStorage and then getPublic(name), or returns null for absent
storage. It is read-only Variable, not an AssignableVariable implementation.
There is no local type guard/catch equivalent to ContextFunction's validation.

The [child-context](CHILD-CONTEXT-ARROW-RECOVERY-2026-10-17.md) path may attach a
child capability's public storage while keeping parent scoped/temp storage. This
separate binding's existence does not demonstrate that ordinary expressions can
resolve its namespace in the default parser. The captured PrimaryBinding and
CustomMolangParser registration paths do not instantiate it; the constant-pool
inventory gives a stronger bounded check than inferring use from source presence.

Do not add a namespace or initialize public names to make this research look
functional. That would change upstream behavior. Also retain the earlier direct
storage-init result: only null public-name initialization was found on that
scanned Java path. Neither negative observation covers native initialization.

## Verification and decompiler comparison

- FOREIGN-BINDING-EVIDENCE: 5 methods/two owners; matching auditor passed 40
  integrity checks and rejected 7 corrupted fixtures.
- FOREIGN-BINDING-REFERENCES-EVIDENCE: all 955 classes, two pair referencers,
  zero outside-pair referencers; 2 checks and 4 corrupted fixtures rejected.
- Vineflower 1.11.1 independently generated a readable candidate from the same
  unchanged class bytes, showing the same pooled name/cache/null-storage path.
  See [comparison receipt](VINEFLOWER-COMPARISON-2026-10-17.md).

Primary static review only; independent semantic review NOT_RUN; no target game
execution, native-provider work or mapping promotion. Central map remains 669.
Continue other reachable typed query inputs instead of assuming this isolated
binding is an active normal feature.
