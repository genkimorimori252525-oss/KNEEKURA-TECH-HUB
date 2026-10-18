# Common native lifecycle: bounded static contract

## Result

The native common-init wrapper sets an attempted-init latch before the initializer. A later call with the latch already set returns null without rerunning initialization. The first native shutdown request sets a separate shutdown gate, installs a detached self-termination fallback, then invokes registered callbacks in forward registration order. Repeated shutdown requests return without waiting for the first caller's cleanup. These are original-byte control-flow findings, not observed runtime behavior.

The fallback attempts `kill(getpid(), 9)` after a requested ten-second `nanosleep` if the process remains alive. Normal JVM/process exit can make it irrelevant. The inspected timer and normal callback-completion path contain no cancellation handshake. No signal, native thread, JVM, target instruction, or emulated shutdown was executed for this research.

## Evidence and reproducibility

`reproduce.py` hashes original SO/JAR, extracts 14 exact source-backed code windows, checks two native bindings against original classfiles, verifies ten ELF import chains and the timer vtable relocation, and writes [evidence receipt](NATIVE-COMMON-LIFECYCLE-EVIDENCE-2026-10-18.json). The named `.bin`/`.asm` files indexed there are authoritative; hexadecimal-named exploratory excerpts may overlap or end mid-instruction and are not independent function-boundary claims. Ranges are half-open. Original SO SHA256: `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`; original JAR SHA256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.

## Java boundary and native init

Exact owner for both bindings: `com/elfmcys/yesstevemodel/OoOo0ooo0o00O0oooO0oooOo`.
- `o0OOooo0o0OO00OoOOOo0o0O()Ljava/lang/Object;` → `0x3c21a0`.
- `O00OOOooOoooOoo0o0o0oO0O()V` → `0x3c2310`.

The existing `COMMON-NATIVE-LIFECYCLE-EVIDENCE-2026-10-17.json` establishes Java interpretation: null means success; a nonnull Component becomes an initialization exception; the shutdown hook is installed only after the null result. The original class declarations were rechecked here; that prior evidence's hash is included.

At `3c21d2`/`3c2242`, native init reads `d34c59`. Nonzero branches to a null return. On the initial path `3c224f` exchanges 1 into it before `3c225d` calls `3c6f90`. This is not a compare-and-swap winner test: the previous exchanged value is not inspected. Therefore this bounded code does not prove a thread-safe once-only initialization contract. No latch reset is visible in this entry, including its cleanup branches. An already-set latch's null return is not proof of fresh resource initialization or successful earlier initialization.

The helper returns a temporary ownership record; its reference at stack+0x28 is converted with JNI `NewLocalRef` (+0xc8, call `3c2272`) when nonnull, and its owner is cleaned up. The normal helper tail `3c9dc1..3c9ded` zeros the returned record.

Concrete setup anchors, without claiming all resources initialized:
- `3c9753..3c97e7` installs task invoker `3e27d0` and manager `35e210` in 32-byte executor records. Deferred installation does not establish execution.
- `3c9ce3` captures worker `3f5f40`; `3c9d22` calls thread wrapper `41acf0` with flag 1. That wrapper reaches create at `41aec3` and detach at `41af75`.
- `3c9d39` moves the resulting wrapper into `d35460` through `39d470`. Move offsets +0x10/+0x18 become completion pair `d35470/d35478`; +0x20 becomes flag `d35480`.
- `3c9d77..3c9d9d` registers server cleanup callback `3cb010` via `3dbaf0`, before the normal null result.

## Shutdown dispatch and self-termination fallback

`3c2310..3c231a` passes argument 1 to `3dbd20`. That dispatcher uses mutex `d35000` when the threading marker is present, reads gate `d35570`, sets it to 1 if previously zero, and unlocks before callback execution. A previously nonzero gate returns at `3dbeb8`. Thus shutdown-requested and shutdown-completed are different states; another caller does not wait here.

Only the first-call path with a nonzero argument enters `3dbd85..3dbe4a`:
1. `3dbdbf` installs vtable `d1baf0`; `3dbddd` calls `2fcdb0`.
2. `2fcdb0` invokes imported `pthread_create` at `2fcdd4` with start thunk `2fccb0`. The thunk invokes virtual +0x10. ELF RELATIVE relocation at `d1bb00` resolves that slot to `3dc180`.
3. `3dbdf5` calls `2fcd20`, which calls imported `pthread_detach` at `2fcd30` and clears the thread handle on success. The later conditional join at `3dbe13` is skipped with that cleared handle.
4. `3dc185..3dc196` builds `{tv_sec=10,tv_nsec=0}`. `3dc1a6` calls imported `nanosleep` with the same structure as request and remainder. A -1 result retries only if `__errno_location()` reports 4 (EINTR). Other sleep results proceed; this is not a guarantee that ten seconds elapsed.
5. `3dc1ba` calls imported `getpid`; `3dc1c1` supplies signal 9; `3dc1c6` calls imported `kill`. No success check or retry follows.

The timer body never reads the allocated local state, shutdown gate, callback list, or completion word. Normal callback completion has no visible cancellation call. `pthread_create` nonzero branches to `2fcd89` → error helper `2fcb5d`; detach nonzero branches through `2fcce1` to the same error helper. These failure paths do not follow the demonstrated normal dispatch path. Creation failure does not establish a running timer; detach failure can occur after creation, but its complete exception/unwind outcome remains outside this contract. Neither actual scheduling nor successful self-termination is established.

## Callback ordering and ownership

Registry `3dbaf0` appends 32-byte callable records to `d35028/d35030/d35038` under `d35000`, moving capture ownership. When the shutdown gate is already set, it invokes the incoming callback immediately rather than appending it (visible call `3dbb35`, with lock still held). The dispatcher snapshots begin/end, invokes each +0x18 function in forward order at `3dbe6a`, then performs a second pass invoking each +0x10 manager with operation 3 at `3dbead`, and resets end to begin at `3dbeb1`. Capacity is retained. Exceptions can prevent subsequent callbacks or the second pass; this is not a finally-guaranteed complete cleanup.

Two concrete registered callbacks:

### Collector and executor cleanup, `4181c0`

Registration is at `413702..41372d` (JNI setup path already anchored by the global-reference collector receipt). When that setup precedes common initialization, this callback precedes the server callback in the forward list; the complete registry inventory is not reconstructed.

1. Submit an empty string through `3cb820`/`3cbb90` and wake `d34ed0` if accepted (`4181de..41821d`). This queue is distinct from collector and server work.
2. Invoke completion object's virtual +0x10 using `d34ef0`, inspect/wait on its +0x10 state, inspect its stored exception pointer, then clear/release pair `d34ef0/d34ef8` (`418233..41830e`). An exception can interrupt later cleanup.
3. Set byte `d35988` at `418310`; submit a zero pair through `41ba10`/`41bd80`, then wake `d35958` on accepted insertion (`418316..41835d`). This connects to the prior global-reference collector queue and the buffer-control destructor's guard. It does not identify the server pending list as that queue.
4. If `d35980==1`, use completion object `d35970`, its virtual +0x10 and state-word wait loop; clear `d35980` at `4183e1`.
5. Clear/release generic executor ownership pair `d35cf0/d35cf8` at `4183eb..41847f`. This is the executor used by server receive, not the server pending-request list. Releasing this owner does not by itself prove every queued task ran or every other owner was released.

### Server worker cleanup, `3cb010`

Wake `d353f0` while holding `d35520` where threading is enabled, then unlock (`3cb01b..3cb042`). These identities match server enqueue's pending-list synchronization; pending list `d35420` itself is not cleared in this callback. If `d35480!=1`, return. Otherwise use completion object `d35470`, invoke virtual +0x10 at `3cb079`, inspect low 31 bits of state +0x10, and wait through `2e3ec0` while needed (`3cb07c..3cb0bf`), then clear flag at `3cb0c1`.

Both wait patterns also branch onward when the wait helper returns false, so flag clearing alone must not be elevated to an independently proven completed-state assertion. This is a completion-state synchronization pattern, not a direct `pthread_join` call. The virtual method identities, all helper return semantics, worker stop observation, pending-request disposition, and actual drain/completion remain unresolved.

## Limits

Names such as “completion object,” “collector,” and “self-termination fallback” describe the bounded structural role; only exact binding/import identities are symbol-proven. No complete initializer resource inventory, failure rollback, shutdown race analysis, or whole-program cancellation absence is claimed. Client model-receive queue, global-reference collector, logging/secondary queue, generic executor, and server pending-request list remain separate objects. All findings are static semantics; none demonstrate runtime shutdown or cleanup completion.
