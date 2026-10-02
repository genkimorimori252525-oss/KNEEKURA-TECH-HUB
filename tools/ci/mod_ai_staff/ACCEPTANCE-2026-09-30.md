# Celestial Staff pilot: exact build and server-handler acceptance

**Accepted scope:** immutable Blockbench asset import, same-source Forge build /
resolved-input capture / packaging, and one small server-side staff handler with
real effect/cooldown subsystem checks. **This is not full MOD or client acceptance.**

The companion [public summary](ACCEPTANCE-SUMMARY-2026-09-30.json) contains
derived results, versions, generated test IDs and source/JAR hashes. It is **not**
the original raw evidence. Original receipts, the signed report envelope and logs
remain local; their hashes are references, not downloadable public objects.
The original HMAC was verified locally with a private session token. A repository
checkout alone cannot independently reverify that signature or replay the complete
evidence closure. No session token, cloud machine paths or game/world data are
published in the summary.

## Fixed behavior and observed result

`kneekura:celestial_staff` invokes the existing `Item.use` hook. On the server it
applies Glowing I to the invoking player for 60 ticks, with a 100-tick cooldown.
No damage, item consumption or durability cost is implemented. During cooldown,
repeat use must not refresh duration, amplifier or cooldown. Client mutation is
blocked by the pure policy, but the actual client handler was not run.

The final authenticated same-run report is complete: **5 detected, 5 executed**.

| Test | Required | Observed |
| --- | --- | --- |
| `staff_handler` | yes | PASS |
| `staff_expiry` | yes | PASS |
| `staff_refresh_negative` | no | FAIL, effect refresh correctly detected |
| `staff_short_cooldown_negative` | no | FAIL, 99-tick cooldown correctly detected |
| `staff_damage_negative` | no | FAIL, attempted damage correctly detected |

The three negative results remain FAIL. They are deliberate controls, not failed
product behavior or assertions reclassified to manufacture a pass. Positive and
negative cases use the same assertion helpers. The expiry case verifies both
59/60 effect and 99/100 cooldown boundaries. The fake-player subclass counts
attempted `hurt` calls because Forge's normal fake player is invulnerable.

These tests call the real handler directly and explicitly advance real effect
and cooldown subsystems. They do not establish physical mouse input, elapsed
wall-clock behavior or player/client synchronization.

## Exact provenance

- Minecraft 1.20.1; Forge **47.4.6**; Eclipse Adoptium JDK **17.0.20.1+1**
- Gradle **8.8**; resolved ForgeGradle **6.0.54**
- Official MDK SHA-1: `1a1c045f235262ff617e285ea2156571ea93bfbe`
- Official Gradle ZIP SHA-256: `a4b4158601f8636cdeeab09bd76afb640030bb5b144aafe261a5e8af027dc612`
- Hosted Blockbench generation: code `c6bbe10e76be0f2806ae2e770bad3914d60b6b8e`, run `36686342010`, artifact `11083529388`
- Original asset manifest: `d2582d7e7d14e5db9a7c6f36774ed73728be1f12df30b02b9486751931877ae5`
- Capture receipt: `136e08825db23286e9b68840357333956f2dc4f48199d157ff2fb4e4f0e797ec`
- Packaged model: `bb27c19a9c3077367157acc2a0a122a8d2e7006c44a7e4a185a543115c29e116`
- Packaged PNG: `c799d9220e7e31dc7a5110b09070ce5dd92499153744414015407f76d313c483`
- Disposable fixture source revision: `24f80d2e7bcb1e8c1247f13423688677d6152dad`
- Source generation: `270bb001c9f63f77bc0b28a3a63b11ae2a08cfadd36f4db25b7a89194737d902`
- Distribution JAR: `15fd766e3249f7eb8e91ddd2767faaac5dec216fd69c4443360bdc4a272d83d6`
- Runtime Mojmap class inventory: `312a7293032ac1dec5c7d3c8ed98cf83feee6e253d7df2033a1c3e77116f5492`
- Compile receipt: `0ed6dc76b31ca6e7d6a0e518f6b18543f1bed870684de9d6392c2242e34a3936`
- Resolved export receipt: `1729bdd503c2387430ec3cc3410674c44e59ba98f5e439ca27d3c0a036ab66d7`
- GameTest receipt: `e36b6e52adb0cbad30f1601d3b39c55d7ecfc5765b70458ce9039d5d1d1cd2f9`
- Run: `81abe335-6368-4474-a2b2-b2e5d8ee3a11`; contract: `0e608e7247710bb3edd189a664fd14abdf0b0681925666543bba2983d0eb3e50`

The compile receipt contains both the distribution JAR and compiled userdev
class inventory. The run contract binds the latter because Forge userdev loads
Mojmap classes, not the JAR's reobfuscated SRG bytes. Both outputs share the same
source generation. The observer's byte-identity guard is unchanged.

The importer verifies all 15 original captured objects, then copies only model
and PNG resources. The build requires original CAS + manifest identities before
and after execution and compares JAR entries to those immutable hashes, not just
to mutable workspace files. The editable native model remains in asset evidence.

## Preserved failures and repairs

1. Initial wrapper setup could not resolve DNS, then hit its short download
   timeout. The official Gradle ZIP was downloaded with a bounded `curl` call,
   checked against the official SHA-256, and seeded into the isolated cache.
   Existing system trust was used; TLS validation was never disabled.
2. First GameTest operation: **NOT_RUN**, eight official icon downloads timed out
   before game startup. Receipt `aeb92a095ab1e3d994e93c1eaff175d6d9e15e3bdcb9b8c981c660fabce515e7`
   is retained unchanged. Exact official objects were recovered and checked
   against the verified asset-index sizes/SHA-1s.
3. Second operation: actual tests ran, but acceptance was **BLOCKED** because the
   observer correctly rejected SRG JAR class bytes against Mojmap userdev classes.
   Receipt `98501b3e7708e2c28608dd88b6e02235099977261a418164ec113fa917fbaa02`
   remains unchanged. Existing multi-output registration fixed the fixture's
   runtime artifact identity; no observer guard was weakened.
4. Third operation: new explicit request, budget, fresh world and same-source
   contract; authenticated file report **PASS**, process exit 0. There were
   three registered operations and two actual game-server starts.

New EULA files were written only in the isolated run directories under explicit
user approval of the linked Minecraft EULA and bounded staff test. There was no
login, purchase, existing-user-world access or client launch.

## Reproduction and verification

Build-only setup/import/build commands are in [README.md](README.md). In the
approved acceptance environment, the local invocation scripts were:

```
PYTHONPATH=src python ../staff-forge-acceptance/final_build.py \
  --bundle ../live-bb-c6bbe10/capture-evidence.json \
  --asset ../live-bb-c6bbe10/asset-136e08825db23286e9b68840357333956f2dc4f48199d157ff2fb4e4f0e797ec
PYTHONPATH=src python ../staff-forge-acceptance/userdev_build.py
PYTHONPATH=src python ../staff-forge-acceptance/prepare_userdev_runtime.py
PYTHONPATH=src python ../staff-forge-acceptance/launch_userdev_runtime.py
pytest -q tools/ci/mod_ai_staff/test_pilot.py
```

The local invocation scripts only assemble existing `Store`, registered
`execution.execute`, `prepare_world`, `prepare_contract` and
`runtime.read_signed_report` operations. Reproduction must use new disposable
paths and request IDs; the successful/failed operation IDs above must not be
replayed. A fresh launch requires explicit authorization, a bounded registered
budget and a newly prepared world. Never copy or publish the private session
file. The build-only CLI has no launch or EULA-acceptance operation.

Final pilot-focused suite: **25 passed**. The continuation records aggregate
verification separately. One local external-directory positive test is excluded
because the execution sandbox injects a repository marker into its parent; the
production boundary is unchanged and the genuine hosted test passes. No workflow
was modified by this pilot.

Still **NOT_RUN**: physical right-click, runtime client-handler mutation,
inventory/first-/third-person rendering, client/network synchronization,
performance, Windows acceptance and broader MOD correctness. No live HTTP
handshake was sampled during the short final tests; the accepted runtime evidence
is the verified same-run signed file report.
