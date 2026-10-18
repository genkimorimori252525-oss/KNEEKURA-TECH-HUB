# Server export and reload: bounded static contract

## Result

Export `3c2920` is a void executor submission retaining up to three Java global references. Reload `3c5190` is separately gated worker admission: its normal boolean return is the old busy byte XOR 1. Neither entry returns a completed export/load result. Reload calls Java commit before clearing its native busy flag; Java commit itself may schedule later publication. Export's later Consumer receives a constructed result through the collector/JNI task facility, after the worker's output or handled-error path.

Original SO/JAR only; no target instruction, JVM, worker, user callback, network operation, or export was executed. All created files are research receipts outside the repository. `reproduce.py` verifies original hashes, exact bindings/class declarations, code backing, ELF relocations/imports, JNI slots and the binary open-mode table. Named ranges in `NATIVE-SERVER-EXPORT-RELOAD-EVIDENCE-2026-10-18.json` are authoritative half-open byte windows; hexadecimal-named exploratory windows are not independent function-boundary claims.

## Exact Java boundary

Both native overloads belong to `com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00` and have name `Oo0Oo0o00O00Oo0OOoOOoooo`:
- Public static native `(Ljava/lang/String;Ljava/lang/String;Ljava/util/function/Consumer;)V` → `3c2920`.
- Private static native `(Ljava/lang/Object;)Z` → `3c5190`.

The exact `SERVER-MODEL-SYNC-JAVA-EVIDENCE-2026-10-17.json` caller is the `(Consumer;Consumer;)Z` overload, invoking native reload at bytecode offset 7 and returning its boolean. Its captured callback first calls the supplied reload callback, then obtains the server and schedules synchronization where applicable. Existing Java evidence proves `reloadCommit` sets INIT before testing success and can schedule map publication; it does not make native worker return synonymous with completed publication. The reviewed Java cohort contains the export declaration, but no export caller body; no fabricated export-caller ordering is added here.

## Export argument and task ownership

`3c2966..3c296f` returns immediately for a null first string, without submission or Consumer invocation. Otherwise JNI +0xa8 `NewGlobalRef` is used for the first string (`3c29a0`), optional second string (`3c2a4d`), and optional Consumer (`3c2b01`). Each nonnull object has a 0x18 control block with vtable `d1b9c0`, count pair +8 and reference +0x10.

The executor from `4e0b10` is the established generic executor `d35cf0/d35cf8`, not the server pending-request list `d35420`. A 0x30 capture stores pairs:
- +0/+8: first string/global-reference control
- +0x10/+0x18: second string/control, zero if null
- +0x20/+0x28: Consumer/control, zero if null

Under executor mutex +0x108, `3c2c6b..3c2c97` installs capture, invoker `3c30f0` and manager `3c4ec0` in a 32-byte task record and advances the deque; the growth branch installs the same fields. It unlocks and wakes executor +0x48 (`3c2cc9`). The capture manager supports shared-owner copying; destroy operation 3 (`3c4f1a`) calls `3c4fa0`, releases controls in Consumer/second-string/first-string order, and frees 0x30 bytes. Vtable relocation `d1b9d0` resolves control disposal to `3c5110`, already tied to the global-reference collector. Scheduling and successful reference deletion are not observed.

Worker `3c30f0` reads the three object values and converts the first/second strings with `4192b0` (`3c3155`, `3c316d`); null second becomes an empty native string. That helper uses JNI modified UTF-8 APIs, so this is not an arbitrary UTF-8 encoding promise. It looks up the first string through `3e4210` against `d351e0` (`3c322e`), checks lookup/payload pointers and payload +0x90, and branches to an exception construction path if those gates fail. The first string is a lookup key here, not proven to be a user-selected filesystem destination. Full registry/content semantics are outside this slice.

## Direct file/path evidence

The worker constructs an output path using global `d35230`, appends four original bytes `.ysm` at `3c3d55..3c3d66`, and later passes that path plus a buffer pointer/length to `4dfb30` at `3c410f`. Additional path manipulation involves `d35348`; full canonicalization, traversal resistance, destination-root policy and name collision behavior have not been proven.

`4dfb30` rejects length >=0x4200001 (`4dfb3e..4dfb45`). On its accepted path it prepares a stream, calls `2e29e0` with mode 0x34 (`4dfbe3..4dfbe8`), then invokes stream transfer/flush/close helpers (`4dfc17`, `4dfc21`, `4dfc29`). The open chain is instruction-proven: `2e29e0` → `2bafd0` at `2e2a15` → ELF import `fopen` at `2baffb`. Mode helper `2baee0` masks mode with 0x7d; input 0x34 indexes table slot `543f4`, whose signed relative offset selects `2baf40`; its literal is `3ecbc: "wb\0"`. Thus a reached successful open has ordinary binary-write/create/truncate semantics. No actual file was opened. The precise emitted content, protection/compression format and virtual stream-write implementation remain bounded out; the `.ysm` suffix alone does not establish a decoded file schema.

## Export completion and callback boundary

Worker-local status begins at 0 (`3c31b2`). Normal work sets it to 1 (`3c4527`); handled-error branches rejoin at `3c452c` without that normal success store (`3c4c88`, `3c4d21`, `3c4da3`). This is not an unconditional callback guarantee for all native exceptions.

For a nonnull Consumer, `3c453b..3c462a` constructs a 0x40 task with vtable `d1bb18`, completion ownership, and pointers into the still-live worker frame: +0x20 result/string aggregate, +0x28 diagnostics owner, +0x30 status byte, +0x38 Consumer. It calls `41ce80`. That helper checks collector guard `d35988`; on its ordinary branch it moves the task into a zero-reference/task pair, submits through `41ba10/41bd80`, wakes `d35958` and waits using the completion state (`41cf40..41cf92`). The wait can also exit on the wait helper's false result; no unconditional scheduler/completion assertion is added. With the guard set, it branches to `41d070`; this fallback's complete semantics remain unresolved and it must not be described as proven Consumer execution.

ELF relocation at `d1bb18` resolves task virtual +0 to `3e1380`, the JNI callback body. This body conditionally builds strings with JNI `NewStringUTF` (+0x538), converts diagnostics via `3d0310`, constructs a result through metadata manager `d35590+0x78` (`3e150c`), exactly the public constructor `com/elfmcys/yesstevemodel/o0OOOo00ooOoooo0ooO0OoOO.<init>(ZLjava/lang/Object;Ljava/lang/String;Ljava/lang/String;I)V`, and invokes the captured Consumer through manager `d356e0+0x120` (`3e1587`), followed by JNI exception handling. The latter is exactly `java/util/function/Consumer.accept(Object)V`, established by the separate zero-instruction checkpoint proof [Consumer metadata](NATIVE-SERVER-CONSUMER-METADATA-2026-10-18.json), whose hash is pinned in this receipt. Fixture metadata resolution does not prove this user's callback ran or accepted its result.

## Reload admission, state ownership and publication

`3c51fd..3c5225` locks `d353a0` where threading support is present and snapshots busy byte `d35398` into EBP. If nonzero, it skips new capture/worker creation. If zero, `3c522d` sets it to 1 before allocation and worker startup. Null state is permitted: it becomes a zero pair; a nonnull state is globally referenced at `3c5270`, with the same `d1b9c0` control type.

A 0x10 capture contains state/control. The callable uses invoker `3f24e0`, manager `3f5400`; `3c52f2` calls `41acf0` with flag 0, then `39d470` moves the wrapper into `d35370`. In the shared wrapper, creation and detach are visible independently of this flag; flag 0 must not be read as “synchronous execution.” The installed completion pair is `d35380/d35388`, wrapper initialized flag `d35390`; busy byte `d35398` remains distinct. After unlocking and temporary cleanup, `3c5396` XORs saved old busy with 1 and returns. For the observed 0/1 states, false means already busy; true means this normal path admitted/started new work. Creation/allocation failure does not establish a true return, and the entry's exception cleanup does not visibly reset the busy byte.

Worker `3f24e0` performs substantial model preparation, with separate synchronization and executor use that are not expanded into a complete loader here. Its normal tail puts success 1 in ECX (`3f46e8`); a handled-error join puts 0 (`3f5311`) and rejoins the same result construction. Exact metadata matches:
- `d35590+0x80`: `com/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO.<init>(ZLjava/lang/Object;Ljava/util/Map;[Ljava/lang/String;)V`.
- `d35590+0x48`: private static `OoOoOoooO0O00oOoO00OOo00.Oo0Oo0o00O00Oo0OOoOOoooo(Lcom/elfmcys/yesstevemodel/oO0OOO0O0O0O00O0OOooOooO;Ljava/lang/Object;)V`, the previously reviewed Java reloadCommit body.

At `3f47a6` the captured state is loaded as the second Java argument; `3f47b8` calls the static commit wrapper, `3f47c0` handles JNI exception state, and only then `3f47c7` clears native busy. Thus the native gate covers this callback call on that path, but does not cover all work Java schedules afterward. The capture manager's destruction releases its control; no leak-free all-exception guarantee, all-error busy-reset guarantee, or actual reload completion is claimed.

## Remaining boundaries

All three exact member identities are pinned by `../server-three-member-metadata.json`, SHA256 `480281d0b52a2dbce70364a84397688b4deb2e1860ee1aab7d9b758971894a9f`. That separate guarded metadata decoding and original-JAR matching establishes names/descriptors, not runtime class initialization or callback execution. No full model decoder/export format was reconstructed, no output-content validity or path security was tested, and no scheduler or callback execution was modeled. Raw native addresses are structural identities; friendly names describe the bounded role and do not restore original source symbols.
