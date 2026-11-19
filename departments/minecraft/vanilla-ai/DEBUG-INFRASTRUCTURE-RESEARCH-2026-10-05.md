# Vanilla debug infrastructure research — R65

This fulfills the detailed static explanation in original B8 of [the authorized handoff](../LOCAL-EXECUTION-HANDOFF-2026-10-02.md). [Debug infrastructure](DEBUG-INFRASTRUCTURE.md) maps actual sender/caller/receiver/serializer/debug-array/renderer/switch/authority semantics and commit-pinned MOD precedent. The additive [ledger](DEBUG-INFRASTRUCTURE-BYTECODE-LEDGER-2026-10-05.json) records34 exact explanation classes,142 selected methods,161 fields and20 static bytecode invocation sites. It is not runtime acceptance or original-goal completion.

## Input and provenance

The Minecraft1.20.1 / Forge47.2.0 / Mojmap `resolved_userdev` artifact SHA256 remains `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`. Foundation Map ID is `522cbb565d187f8e1e7b97140206f5ac11e8ca90719528bd661f875f184e34fd`; index snapshot is `55a63559b62697c11e8ece0cd2fcb97d2db4730684789a31240b2c515f08ba06`. JDK17.0.12 executable/release/modules hashes and all73 inspected class/disassembly hashes are reverified.

All7,108 Minecraft class references supplied structural candidates. Actual `invoke` instructions were inspected in every DebugPackets-reference candidate, all33 Path-reference candidates and relevant render hosts. The resulting sites are3 Path senders,1 Goal sender,12 Brain senders,1 LevelRenderer dispatcher,1 Keyboard chunk toggle and2 internal Bee/Brain static Path-render calls. No setDebug member-reference lines or invocation sites appear in those outputs. No direct Goal/Brain renderer call appears in the inspected candidates. This is scoped static invocation evidence; dynamic/reflection/MOD calls and actual loaded execution remain separate.

The original exact disassemblies were reused by hash; missing bodies use the same hashed `javap -private -s -c -l -verbose` provider. One existing ChunkMap disassembly uses CP932. A private UTF-8-only parser failed, preserving its output/log; the corrected parser decodes with the recorded per-file encoding and resumes without rerunning the retained provider output. Raw SHA256s remain authoritative. Public slice hashes use UTF-8 of joined decoded lines, retaining CR, and are not canonical bytecode-body hashes.

Existing Vineflower1.11.2 is a private reading aid:49 initial class inputs yielded45 derived Java files /764,724 bytes, provider exit0 and79 retained log lines. Actual bytecode/descriptors/flags control the findings; derived Java is not original or loaded-source equivalence. Minecraft/whole javap/derived Java remain local. No product dependency, executable behavior, native process or world change is added.

Two Moonlight commit-pinned non-truncated trees distinguish an actual1.20.1 snapshot from the modern1.21.1 feature. Source files are reverified against Git blob SHA1 framing and SHA256, including version properties/license source. The source trees/whole upstream Java stay private; public links/hashes/explanation establish precedent only. No third-party code is installed or copied into product implementation.

## Requirement correspondence

| Original B8 item | Verified static explanation |
|---|---|
| DebugPackets / Pathfinding / Goal / Brain payload | Exact old channel/buffer/data owners, missing typed modern payload classes, dormant sender bodies, private serializer tails and client receiver field order |
| Call sites / server-client authority | Exact sender invocation sites, virtual Mob debug caller, Forge interception/main-thread/buffer ownership and separate source/cache/render gates |
| Open/closed/target population | Optional arrays, DEBUG constant false, no setDebug reference in scanned candidates, actual zero-write Path gate and direct client deserialization |
| Three renderers / capture switches | Actual dispatcher omissions, constants versus runtime chunk-border toggle, labels/ranges/cache lifetime/selection and frustum versus AI capture distinction |
| Existing MOD precedent | Exact1.20 feature-file absence versus actual modern injections/type filters/client render gate/commands; reconstructed returned-node arrays retain derived provenance |

## Verification and continuation

Artifact/provider/class/disassembly/member locators, critical send/receive/populate/render boundaries, field constants and upstream hashes are verified before publication. Relative links, UTF-8 JSON and the focused diff are checked. Prose/source correspondence is the relevant check; no mirrored test or new Minecraft run is needed for documentation-only work.

Existing original callback/Viewer/native records keep their own bounded scopes. R65 does not relabel reconstructed arrays, client strings/look selection or an upstream implementation as KNEEKURA's exact server evidence. Required B9 community cases, general Mob catalog, B10 FRONTIER reconciliation, true Boss fields, same-case integrated diagnosis, nine cost measurements and exactly one final independent whole-diff review remain in the [original reconciliation](ORIGINAL-REQUIREMENT-RECONCILIATION-2026-10-05.md). Final HEAD CI/Draft readback are separate publication evidence; main remains unmerged.
