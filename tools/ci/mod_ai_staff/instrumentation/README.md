# Opt-in staff client-use trace

`pilot.py --configure --client-trace` creates a separately identified disposable
fixture. Without `--client-trace`, configure remains byte-identical to the
original fixture and does not include the helper or metadata.

This is a narrow exact-source transformation, not a Java transpiler, ASM hook,
coremod, game launcher or acceptance oracle. The generator refuses any change to
the pinned `CelestialStaffItem.java`. It retains the original stack lookup and
method statements, wrapping the latter in `try/finally` with
`ClientUseTrace.begin(level, player, stack)` and `Scope.close()`. Defensive probe
guards preserve the original method's return value and thrown exception.

The helper only reads client-side state. Server calls are no-op. The first client
caller thread becomes the scope owner; subsequent foreign-thread calls or closes
are UNKNOWN. The hook executes synchronously inside that original Item.use call.
It does not change effects, cooldowns, health, inventory or item durability.

## Read-only interface

The exact public helper is `org.kneekura.staff.ClientUseTrace`:

- `begin(Level, Player, ItemStack)` returns a `Scope`
- `Scope.close()` is no-throw and idempotent
- `snapshot()` returns a deeply immutable `Map<String, Object>`

Snapshot schema version 1 contains `limit: 16`, monotonically increasing
`started`, `completed`, `unknown`, `dropped` counters and at most 16 `records`.
Each record contains `sequence`, `player_uuid`, `completed`, `unchanged`,
`before`, `after`, `effect_mutation_attempts`, and `cooldown_mutation_attempts`. Unknown identity is null. Probe failures retain
`completed: false`, `unchanged: null` and null mutation counters; missing/in-flight completion is not
successful evidence. `dropped` counts older records evicted from the bounded
window, without erasing the cumulative counters. A malformed mutation hook after
close invalidates that retained record and increments `unknown`; `completed`
remains the cumulative number of completed observation pairs, so completed and
unknown counts need not sum to started. Such an invalidation cannot pass.

Each successfully read state has:

- `health`
- `main_hand`: `item`, `count`, `damage`
- `glowing`: null, or `amplifier`, `duration_ticks`
- `staff_cooldown`: `active`, `fraction`, for the item used by this call

`completed` describes completion of both observations, including when the
original method throws; it does not mean the original use returned successfully.
`unchanged` is exact before/after map equality. Neither field is a gameplay PASS.
A live consumer must match the actual run, player and newly completed invocation,
reject UNKNOWN/incomplete evidence, and combine it with the relevant operation.
Immediately before each of the pinned fixture's two original mutator statements,
the generated hook calls `Scope.mutationAttempt("effect")` or
`Scope.mutationAttempt("cooldown")`. The original mutator is unchanged. These
counters expose even an attempt whose state is subsequently restored. Acceptance
must require zero attempts as well as unchanged boundaries and no UNKNOWN.
Unrecognized sites, foreign-thread attempts and attempts after close are UNKNOWN.
This establishes only whether those known verified source sites executed. It is
not general instrumentation of arbitrary game effects or post-transform code.

The observer must not load this helper for an ordinary build. It may expose
`staff_client_trace` only when this helper is among the verified target class
probes. Missing helper, failed reflection, zero started calls or mismatched
identity cannot establish the client no-mutation assertion.

## Separate source and artifact identity

Configure returns `client_trace` metadata and embeds the same canonical metadata
at `META-INF/kneekura-client-trace.json`. It records original source SHA-256,
instrumented source SHA-256 and helper source SHA-256. Build-only validation
checks the exact source bytes before and after execution, requires the packaged
helper and matching metadata, and includes the identities in its summary.
Normal source-generation and compiled-class/JAR receipt identities still apply.
The already delivered uninstrumented distribution is not modified or relabeled.

Tests compile and execute the helper and actual generated hook against bounded
Java API fixtures. Known-bad effect, cooldown, health, stack, damage and item
changes must be observed as changes. A test-only bad client policy runs both
original mutation sites and then restores state: unchanged boundaries stay true
but both mutation-attempt counters are nonzero. Other tests cover read failures,
foreign-thread calls, deep immutability, bounded retention, server no-op,
return/exception preservation and exact-source/provenance rejection. These tests
are instrumentation checks and do not themselves claim live game acceptance.
