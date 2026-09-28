# Forge 1.20.1 development observer

Opt-in development source set; never ship it as part of a release MOD. The constructor registers only when the environment is non-production and an explicit `kneekura.session` property is supplied. The Python execution adapter's `kneekura-run.init.gradle` provides the separate source set and managed run directory. Do not manually combine `session create` with a normal validate-run that already creates its session.

Components: BridgeTransport (JDK17 loopback HTTP, authentication and HMAC); RunLedger (GameTest event identity/counts); ForgeObserver (game-thread state and report binding); ClientProbe (client-thread camera/frame/screenshot capture). Dedicated-server classloading must not eagerly load client classes.

The actual source compiled and reobfuscated against the official Minecraft1.20.1/Forge47.4.6 MDK in [run36377840477](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36377840477). This removes the earlier uncompiled-source limitation. It does **not** establish that the live integration works: no game process has yet been launched for that checkpoint.

The session verifies build resource probes and registered config files, not every in-memory transformed instruction or every dynamic configuration value. A returned snapshot carries intervals and is not atomic. Imported or live observation is not itself a passing behavior/rendering assertion. Expected GameTest IDs and same-run completion must be established separately.

Outstanding live integration includes fresh-world startup, exact report registration/completion, client-thread screenshot scheduling, command final-result protocol and authentication across a complete run. Preserve UNKNOWN rather than automatically retrying a possibly accepted mutation. See [implementation status](../IMPLEMENTATION-STATUS.md).
