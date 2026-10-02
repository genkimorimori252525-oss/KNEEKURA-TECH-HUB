# Registered native client input

Implementation: `minecraft/input_route.py`, `minecraft/native_input.py`, and the
existing `input_contract.py`. This is a selected native implementation with
fixture coverage, **not live Minecraft input acceptance**.

## Platform and input semantics

The disposable Forge 1.20.1 / Java 17 workspace is Linux. The selected backend is
`linux-x11-send-event-v1`, using installed `libX11.so.6` through ctypes. It sends
synthetic, window-addressed native events. It never injects global device events,
moves the desktop pointer, uses XTEST, installs packages, launches the game, or
executes registry-supplied commands. Windows, Wayland and keyboard input remain
unsupported; original Windows acceptance remains outstanding.

The only gesture is `mouse:right`, held 1–250 ms, with no open screen and the
GLFW cursor disabled. `position` must equal the integer viewport center returned
by `input bind`. It denotes the gameplay crosshair, not an arbitrary UI click.
GLFW's button handler does not move its cursor from event coordinates; inventory
and UI clicking are therefore rejected by this driver.

For the fixed dedicated staff fixture, authenticated input snapshots explicitly
select the bound player in `minecraft:overworld`, with `limit=1` and
`staff_state=true`. A changed dimension fails closed. This scope does not add
generic dimension discovery; legacy, integrated and log queries are unchanged.

The authenticated ClientProbe response binds the existing complete run identity
to Java PID, exact Linux `/proc` process-start ticks, native X11 handle,
foreground state, local dimensions, screen and cursor mode. The driver checks
PID/start ticks locally, exact handle/window PID, foreground/local dimensions and
pre-existing held controls. Window titles never serve as identity.

Each `XSendEvent` uses the explicit native window, `propagate=False` and
`NoEventMask`: Xorg specifies delivery only to the client that created that
window. Both events address the same target, regardless of physical pointer
motion. GLFW X11 handlers route synthetic Button3 press/release through normal
mouse callbacks. This is source/API compatibility evidence, not proof that
Minecraft handled a use action. Actual game acceptance is still required.

Short server grabs protect identity checks and each send. They are not pointer
locks and are released before the hold interval. Deadlines are checked after
blocking preflight/coordinate calls, before mutation. The helper owns one scoped
release. On parent timeout/cancellation, SIGTERM requests that cleanup; after
750 ms (250 ms for read-only helpers) a stuck helper is killed and reaped.
Closing its connection releases any server grab. No physical button was held;
the parent never injects a global or second cleanup event. An unconfirmed
application-side release is UNKNOWN and quarantined. OS/X-server failure is
never converted into a guaranteed release or gameplay PASS.

## Explicit invocation

Copy `input-registry.example.json` to an operator-controlled local file. Enable
it only for an already approved disposable client session and select its private
session file and explicit display. Never publish real session files, secrets,
machine paths or local receipts.

1. `kneekura-minecraft --store <existing-cas> input bind --registry <input-registry>`
2. Copy returned `identity`, `target_id` and `position` into this request shape:

   ```json
   {"schema_version":1,"operation_id":"staff-use-001","identity":{},"target_id":"COPY_FROM_BIND","control":"mouse:right","position":[320,240],"hold_ms":50}
   ```

   Replace the empty identity, placeholder target and sample position with exact
   bind values. The example position assumes a 640×480 viewport.
3. `kneekura-minecraft --store <existing-cas> input dispatch --registry <input-registry> --binding <binding_hash> --request <request-json>`

Binding is read-only and starts no game. Dispatch is explicit mutation. Unknown
fields, duplicate JSON keys, disabled registries, changed authority/run/native
scope, unsupported controls, UI mode and non-crosshair coordinates fail closed.
The session must be its canonical `directory/session.json`, with its endpoint
in the same directory; relocated copies are rejected. The replay ledger lives
there with a run-identity owner marker. Changing CAS, copying session files or
changing IDs cannot safely retry an uncertain attempt.

UNKNOWN/cancellation retains the active marker. Preserve it and the receipt;
establish that the helper exited, inspect the game's input state and current
window/epoch, and review screenshots/logs. Elapsed time is not confirmation. If
release remains uncertain, stop and resolve it on the desktop; never blindly
delete the lock. After confirmed neutral state, use a newly approved disposable
session/epoch rather than clearing or replaying the uncertain operation.

Receipts link the immutable request/binding, existing authenticated client
captures, screenshot byte hashes and logs in the existing CAS. Failure captures
remain evidence. `COMPLETED` means the helper confirmed target-addressed event
and release delivery to X11, not game consumption. Actual right-click gameplay,
server behavior, visuals and synchronization remain separately `NOT_RUN` until
the declared observations establish them.

## Checks and sources

With project dependencies and JDK tools in PATH, run:
`python -m pytest tests/test_minecraft_input_contract.py tests/test_minecraft_native_input.py tests/test_minecraft_input_route.py tests/test_minecraft_input_query_contract.py tests/test_minecraft_runtime.py tests/test_minecraft_connected_cli.py`

Fixtures cover Java `/proc` matching, missing-display failure, exact
window/NoEventMask structs, asynchronous pointer motion, slow-preflight expiry,
scoped release, bounded stuck-helper cleanup, cancellation, relocated-session and
cross-CAS replay, and retained failure evidence. They are not game acceptance.

The separate [native API summary](verification/native-api-2026-09-30.json)
records an actual owned-hidden-window GLFW fixture: only its target received
right-button PRESS then RELEASE; its decoy received none. It did not exercise
foreground/session binding or Minecraft, and leaves those verdicts NOT_RUN.

Primary API/source references:
- https://xorg.freedesktop.org/archive/X11R7.5/doc/man/man3/XSendEvent.3.html
- https://raw.githubusercontent.com/glfw/glfw/3.3.1/src/x11_window.c
- https://raw.githubusercontent.com/glfw/glfw/3.4/src/x11_window.c
