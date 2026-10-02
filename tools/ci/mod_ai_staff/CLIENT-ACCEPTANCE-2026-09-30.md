# Celestial Staff: bounded client acceptance

**Result: partial acceptance.** One Linux X11 cloud-client session established
native input delivery, the sampled staff behavior, and visible first-person and
inventory rendering. Third-person rendering is **INCONCLUSIVE**. Full gameplay
acceptance and graceful shutdown are not established.

The [derived JSON report](CLIENT-ACCEPTANCE-2026-09-30.json) publishes only results,
versions, generated IDs and hashes. Original receipts remain unchanged and
private, together with observations, logs, game images and world data. Hashes
identify those originals; they are not downloadable public evidence.

## Observed results

- Same-run observer/native-target binding: **PASS**
- Native right-button operations `03-use-first` and `03-use-repeat`:
  **COMPLETED**, both press and release confirmed
- After first input: **PASS, scoped observation** of Glowing I and active cooldown
- Repeat during cooldown: **PASS, scoped observation** of continued countdown
  without refresh
- Sampled health, stack count and item damage: **20 / 1 / 0**, unchanged
- Later samples: **PASS** for eventual effect and cooldown absence
- First-person view: **PASS** for visible gold halo and purple star model/texture
- Inventory view: **PASS** for visible item icon and held model/texture
- Third-person view: **INCONCLUSIVE**; the player face and nearby tree obstruct
  the camera, so this frame does not validate the held model

The native receipts themselves retain `NOT_RUN` for gameplay, visual and
synchronization verdicts. Input completion alone is not gameplay acceptance.
The results above are separate derived assertions from subsequent same-run
observations and actual image inspection.

### State and tick evidence

| Capture | Server tick interval | Glowing amplifier / remaining ticks | Cooldown fraction | Health / count / damage |
| --- | --- | --- | --- | --- |
| Before first input | 2375–2378 | absent | 0.00, inactive | 20 / 1 / 0 |
| After first input | 2412–2423 | 0 / 50 | 0.90, active | 20 / 1 / 0 |
| After repeat input | 2460–2464 | 0 / 2 | 0.42, active | 20 / 1 / 0 |
| Inventory | 3679–3682 | absent | 0.00, inactive | 20 / 1 / 0 |
| Expiry sample | 6577–6583 | absent | 0.00, inactive | 20 / 1 / 0 |

These captures are **non-atomic**: integrated-server state is sampled first,
then the client image, with the full interval recorded. The two post-use state
samples are 48 server ticks apart; effect duration decreases by exactly 48 and
cooldown fraction by 0.48. This supports no refresh across the repeated input.
It does not establish exact 59/60 or 99/100 client boundaries or wall-clock
performance. First-person review uses `03-use-before`; the earlier `01-equip`
image preceded the visible hand update.

## Exact provenance and independent checks

Minecraft **1.20.1**, Forge **47.4.6**, Java **17**, Gradle **8.8**,
observer **1.0.0**.

- Fixture source revision: `892dfb8c4d10ca25dcb1874adcb22e08df1e6f42`
- Source generation: `e5be642ecc85ac83e7d9913ca48b9e351fc66f0116338c5eff5cea7a8d4cb79a`
- Distribution JAR: `e4cae193551aa4fb869b01d345cfa3558501893557eb3e3c74ebf3c2e1699d93`
- Runtime Mojmap class inventory: `312a7293032ac1dec5c7d3c8ed98cf83feee6e253d7df2033a1c3e77116f5492`
- Run: `e9583899-0186-47e2-a1a8-a33244ca143f`
- Contract: `e3419831e8b2038cfc59bf2b7c82ea5bc601cce732b272b530e4bfb04c28da6e`
- Binding: `ec1d1c81eb64243e70965c5c806ad8791ec18e7c78891356a1014b54fa14202d`
- First input receipt: `369793ffe68ee7bcfded162e9f1c0145bc1dd7c5f06819566c08f9b529ba4b52`
- Repeat input receipt: `3b1e193451f2ad3c4b608de98f62c61d9e7565dbca1b668c420e096fa26b7908`

Independent review checked **45 CAS objects**, **33 identity records** and
**12 embedded PNG payloads**, including local PNG/hash equality, input
request/binding/receipt links, before/after target consistency, compiled-class
bytes and immutable packaged model/texture hashes. Compile, export and runtime
receipts agree on the source generation. The run binds the Mojmap class inventory
because Forge userdev loads those classes rather than the reobfuscated JAR bytes.

The actual capture calls returned `AUTHENTICATED_LIVE_OBSERVER` through the
HMAC-checking bridge. Retained CAS objects contain parsed payloads, not the HTTP
signature/nonce envelopes. This review independently verified hashes and
identities; it **did not independently reverify transport HMACs**. A public
checkout cannot replay the private evidence closure.

## Preserved failure, bound and shutdown

1. The first attempt failed during `downloadMCMeta` with connection refusal,
   before game startup. Process time was **17.301 seconds**; controller time was
   **17.703 seconds**. Its unchanged receipt is
   `eabe9ce0720ccecac188a960d9d8cafd868ae23d0a6e8c793426af71ad92399a`.
2. The retry used the existing desktop proxy and a **540-second** process limit
   within the original approval. The original **15-minute** authorization was
   not extended.
3. The retry hit that bound: **timed_out=true**, **exit -9**, process time
   **540.083 seconds**, controller time **540.452 seconds**. Receipt
   `d0c46d10f4956ac5c3491c1f835feb79a3820abe094829ac6d5bea3a1e38c495`
   retains `NOT_RUN`; this is not a successful or graceful process exit.
4. A subsequent read-only desktop process probe found **zero matching game
   processes**; the native input ledger had **zero active-operation markers**.
   Desktop observation separately confirmed the game window was closed.

No new EULA file was written for the client attempt; the previously approved
server EULA acceptance is unchanged. No additional client launch was made for
this review. The remaining visual checks have been handed back to the user.

## Warning and remaining limits

The client logged missing resource-pack metadata for the separate observer pack.
A post-run `pack.mcmeta` repair specifies Minecraft 1.20.1 pack format **15**.
The focused packaging suite passes **5 tests**, including installed-resource
coverage. **No live client retest was performed after that repair**, so a
warning-free client run is not claimed.

Server state and client images are correlated within this integrated session;
no independent synchronization assertion was executed. Synchronization, remote
multiplayer, separately instrumented client-only mutation, exact client tick
boundaries, performance, Windows and broader MOD correctness remain **NOT_RUN**.
Earlier server-handler tests are documented separately in
[the server acceptance report](ACCEPTANCE-2026-09-30.md).
