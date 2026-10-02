# Staff continuation controller audit — 2026-09-30

**Derived summary, not raw evidence. Dedicated staff gameplay acceptance remains NOT_RUN.**

This review covers the disposable server, control client and invoking client on
the existing loopback fixture. It preserves the original v3/v4 results and does
not turn successful preparation or fixture tests into a live acceptance claim.

## Verified failures and corrections

- **v3 runtime preparation:** The registered runtime environment omitted the
  previously working `GRADLE_OPTS`. `downloadMCMeta` failed with connection
  refusal before game startup; the process completed with exit 1 and no timeout.
  The continuation restored the exact existing per-role environment values.
  All three desktop metadata/assets/natives prerequisite runs then completed
  successfully without launching a game or changing network/trust settings.
- **v4 server readiness:** The server started, but the private controller sent
  `/v1/observe` with an empty query. The actual dedicated-server observer requires
  one approved player UUID and an explicit dimension. The authenticated rejection
  therefore blocked dependent client launches. The corrected controller sends
  the fixed UUID, `minecraft:overworld` and integer limit 1; a valid empty result
  is permitted before that player joins. Original error evidence is retained.
- **Normal cleanup:** The observer executes registered commands at permission 2;
  Minecraft's `stop` command requires permission 4. The new controller rejects
  that command and uses the existing exact owned-process cleanup path. Server
  authority was not widened.
- **Separate product-adapter defect:** The dedicated native-input route requested
  `staff_state` without a dimension, which the real Java `StaffStateQuery`
  rejects. The adapter now explicitly requests the existing fixed Overworld
  fixture. A player in another dimension is rejected; legacy, integrated-client
  and log query shapes remain unchanged. No game or observer Java source change
  was needed.

v4 was closed without a staff gesture. Controller cleanup recorded closed
execution threads and no owned game processes; a subsequent actual-desktop
probe independently found none. These are separate checks.

## Audit matrix

| Check | Verified result and boundary |
| --- | --- |
| Full controller request loop | **8 tests passed.** Both grouped and separate first-use/repeat/expiry flows exercised the real session, pairing, input-route, command-receipt and retained-evidence validators, plus cleanup |
| Negative full-loop paths | Partial/error readiness, unknown command completion, malformed binding, unknown native completion and partial post-use observation blocked the relevant dependent action |
| Readiness contract | **4 tests passed** using signed local HTTP, the real Python observation validator and the Java dedicated-query guard, including the zero-player server case |
| Setup commands | Actual cached Minecraft/Brigadier parsing accepted all **13 fixed setup commands at permission 2**, covering the 10-command normal staging sequence; permission-4 `stop` was rejected |
| Native query and route regression | **82 focused tests passed**, reported separately: [query contract regression](../../../tests/test_minecraft_input_query_contract.py), [dedicated runtime](../../../tests/test_minecraft_dedicated_runtime.py) and [input route](../../../tests/test_minecraft_input_route.py). This is not an aggregate count or a full repository-suite claim |

The full-loop harness uses strict recorded transport responses and isolated
JVM/native/PID boundaries; it starts no game and sends no real native input.
The command parser uses a strict isolated lookup for the exact staff item ID
because the plain-JVM fixture lacks Forge's networking transform. It proves
grammar and permission compatibility, not live item registration or command
execution. Test counts above overlap and must not be added together.

## Reviewed bytes and remaining limits

- Private controller SHA-256: `95ea209d17734e0f185983ff70015020e0c66b6f82fddf8278ec35ee5be2ebb2`
- Product input-route SHA-256: `5284e5dca9cdb1be39fa2959e5fba88a2a312754c93204b36723995cfa0fb177`
- Independent audit-record SHA-256: `8ea41fa005ef95bf40ffe3508379ba84545adea1004fe186b79b206c69eadbb5`

No unresolved caller/validator mismatch was found in this reviewed scope.
Live command execution, client rendering, memory sufficiency, native delivery
and capture within the short effect/cooldown window remain to be established
by fresh same-run evidence. The 20-minute ceiling, including two minutes for
cleanup, remains unchanged. Only the prepared attempt is available; an unbound
retry is denied, and uncertain input is never replayed.
