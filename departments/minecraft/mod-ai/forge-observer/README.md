# Forge 1.20.1 development observer

Opt-in development source set; never ship it as part of a release MOD. The constructor registers only when the environment is non-production and an explicit `kneekura.session` property is supplied. The Python execution adapter's `kneekura-run.init.gradle` provides the separate source set and managed run directory. Do not manually combine `session create` with a normal validate-run that already creates its session.

Components: BridgeTransport (JDK17 loopback HTTP, authentication and HMAC); RunLedger (GameTest event identity/counts); ForgeObserver (game-thread state and report binding); ClientProbe (client-thread camera/frame/screenshot capture). Dedicated-server classloading must not eagerly load client classes.

The source compiled/reobfuscated against the official Minecraft1.20.1/Forge47.4.6 MDK. It subsequently completed a **real live server integration** at code commit `3fa14453327e7992231e3d479ac1d1eebbd96b3c`, [run36381518610](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36381518610): fresh-world startup, authenticated handshake, exact target-entity observation, successful zero-valued command, duplicate-request handling, and completed GameTest report. The required bridge test passed; the optional known-bad test deliberately failed and remained visible.

The session verifies build resource probes and explicitly registered config files, not every in-memory transformed instruction or every dynamic configuration value. The live probe registered no immutable runtime config files. A returned snapshot carries intervals and is not atomic. Imported or live observation is not itself a passing behavior/rendering assertion. Expected GameTest IDs and same-run completion remain separate checks.

Command outcomes use Brigadier success callbacks, not numerical result positivity; unobserved callbacks remain UNKNOWN. The Python consumer correlates operation/command IDs and labels the result `command_execution`. Preserve UNKNOWN instead of automatically retrying a possibly accepted mutation.

An empty Forge test world needs explicit server.properties seed/name settings compatible with its contract; Main normalizes that file at startup. PrefixGameTestTemplate(false) in Forge1.20.1 affects exact test IDs as well as templates. A capped all-entity sample is not a complete world inventory: use exact entity UUID/dimension when asserting about one fixture entity.

The [2026-09-30 recovery review](../RECOVERY-ACCEPTANCE-2026-09-30.md) establishes scoped default Hydra rendering from inspected, same-run camera/frame/PNG evidence. General rendering/network correctness, Windows process behavior and MOD performance remain unverified. The historical [live verification](../LIVE-VERIFICATION-2026-09-28.md) retains its original scope; use [current acceptance](../CURRENT-ACCEPTANCE-2026-09-30.md) for the remaining work.

The schema-2 dedicated receiver and scoped dependency-byte contract are described in [dedicated observation](DEDICATED-OBSERVATION.md). That document distinguishes implementation/fixture checks from live acceptance; it does not replace the historical run above.

## Bounded error diagnostics

Authenticated HTTP409 responses retain UNKNOWN and no-retry semantics. A fixed
envelope identifies only an allowlisted exception family: timeout, rejected
request, rejected state/identity, or internal error. It never exposes exception
messages, stack traces, machine paths or session secrets, and is not a root-cause
assertion. The Python client verifies the request-bound HMAC and exact bounded
schema before retaining the error payload and correlation metadata in the
existing Store. Unsigned, malformed, oversized, legacy or incorrectly successful
error envelopes cannot create a diagnostic artifact.

A prior handshake's validated summary has its own identity. Its decoded-content
hash and original response-payload hash are distinct; no raw free-form handshake
is retained by this error path. Successful v1 observation handling is preserved.
