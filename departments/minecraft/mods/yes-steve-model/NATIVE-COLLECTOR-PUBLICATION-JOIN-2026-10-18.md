# Native staging records to Java model-map publication

## Finding and boundary

The worker's successful 0x88-byte staging records have a concrete downstream consumer: the builder moves their vector into its frame+0x190, and collector task 0x35ef10 emits each record through manager 0xd35598+0x58. Exact decoded metadata and the original classfile identify this as the non-default Java add-model callback. On successful Java construction it queues the model; a later queue-draining tick publishes a replacement volatile model-map reference. This closes the identity/ownership connection between the native staging and the previously established Java publication contract.

All of this is a conditional static path. Neither a staged record nor ordinary callback return proves enqueue, tick execution, final renderer use, or GPU readiness. The separate +0x60 callback schedules map alterations and must not be confused with the per-record +0x58 callback.

## Original native ownership and invocation evidence

Addresses are original ELF virtual addresses. The accompanying receipt pins the original SO, raw windows, relocation records and instruction assertions.

* Builder 0x3577c0 stores the address of frame+0x220 at shared allocation base+0x40 (0x359c0f/0x359c17). Its worker context is base+0x10 (0x359cb2), captured at 0x359fee. Worker 0x35d250 obtains that context at 0x35d261/0x35d264 and reads context+0x30 at 0x35d603: the same vector. The earlier worker report establishes successful record append and per-item exception skip, without final Java publication.
* Completion loop 0x35a432–0x35a4a0 inspects completion state and waits; 0x35a4a9 calls the release loop 0x35e4f0. This is not a proof of result-get or stored-exception consumption; transitive virtual helper semantics remain outside this join.
* The builder moves the vector triple from frame+0x220 to frame+0x190 at 0x35a5d9/0x35a5e2/0x35a5f3 and zeros the source at 0x35a5ff/0x35a608. Task setup at 0x35ac72–0x35ac7d installs vtable 0xd1b5a8 and captures the address of frame+0x190 in task+0x20; dispatch is 0x35ac97→0x41ce80. ELF RELATIVE relocation maps that vtable slot to 0x35ef10.
* Emitter 0x35ef10 reads the vector through task+0x20 at 0x35ef1e–0x35ef29 and advances by 0x88 at 0x35ef50. It makes a Java string from record+0x48 (0x35ef62/0x35ef6c), loads manager+0x58 at 0x35efad, passes record+0x20 model reference in RCX (0x35efce), string in R8 (0x35efd8), false in R9 (0x35efdb), and record+0x68 as the second boolean on the stack (0x35efca/0x35efd2). Call 0x35efe0 enters varargs adapter 0x345d50; its JNI table call at 0x345dcc uses +0x470, CallStaticVoidMethodV. Pending-exception checker follows at 0x35efe8.
* Earlier task setup 0x35a716 uses vtable 0xd1b580 (RELATIVE target 0x35f620), captures different vectors and dispatches at 0x35a747. That task calls manager+0x60 at 0x35fe43, then checker 0x35fe4b. Lexically earlier dispatch does not establish completion or Java executor ordering relative to the later emitter.

The existing native scheduler dossier describes 0x41ce80's guarded dispatch/wait and unresolved fallback 0x41d070. This report does not prove that a task runs or drains, or that the captured stack-vector lifetime is sufficient on every scheduler path.

## Exact metadata and original classfile join

Both members belong to `com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO`, name `Oo0Oo0o00O00Oo0OOoOOoooo`, access 10 (private static):

* +0x58: `(Lcom/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO;Ljava/lang/String;ZZ)V`.
* +0x60: `([Ljava/lang/String;[Ljava/lang/String;[Ljava/lang/String;[Z)V`.

Manager initializer callback stores/selectors at 0x40728c–0x40737d and manager publication 0x40773e back these slots. The separate parent-approved guarded metadata callbacks resolved both exact payloads in independent next6 clones; neither Java method bodies nor a real worker were executed. The metadata receipt records preserved inputs, registers/frame state and unchanged JNI ledger. See the integration document `NATIVE-COLLECTOR-CALLBACK-METADATA-2026-10-18.md` and its compact JSON. The main JNI/runtime frontier is unchanged.

Original class SHA256: `203f7df0d59b7010c1da8809cbcea192b20d381fbb604f43eb5ee3f711afd3a4`. `java_join.py` freshly reads the original JAR class and verifies 13 complete method records against existing publication/sync evidence, rather than deriving identities from decompiled names or signatures alone.

## Java success, failure and commit

Bytecode offsets below are within the named original methods; readable labels reuse the existing Java dossiers.

1. +0x58 add-model bridge: native first boolean false takes branch 1→15, calls setup-default helper `oooooooOOoOOoO00OooOo00O()V` at 15, then internal body `o0OOooo0o0OO00OoOOOo0o0O` with the same descriptor at 22. Setup-default can fail before the internal body. The true/default deferred branch is not selected by this emitter.
2. Internal body: non-null data invokes the model builder at 7. Only builder range [4,12) is covered by its Exception handler at 15. For the native false/default flag, caught Exception logs at 47 and returns at 52: no queue add at 62 and no progress scheduling at 97. Logging failures, Errors and setup-default failures are not swallowed by that builder handler. Null data takes 1→89, reaches progress scheduling at 97, and adds no model.
3. Successful construction creates Pair(model,path) at 59 and calls the concurrent queue's add at 62. It later schedules progress via Minecraft.execute at 97. Queue addition is a different boundary from map-reference publication.
4. Tick `Oo00o0OooOOo0ooOoo0oO0o0()V` returns if the queue is empty; otherwise copies the existing map at 17, polls at 24 until null, puts Pair.right String → Pair.left model at 53, and writes the replacement map at 61. The field has access 74 (private static volatile). Listener dispatch at 70 follows that write. Later same-key entries consumed in this loop overwrite earlier entries in its copied map. This establishes reference publication only, not deep immutability or a renderer frame barrier.
5. +0x60 array callback captures its array references and calls Minecraft.execute at 12. Its synthetic runnable copies the map, removes entries, changes retained model authentication state, inserts renamed entries, and assigns the map at 195; conditional listener dispatch follows at 223. Existing Java analysis already establishes its shallow, nontransactional behavior and separately scheduled release work. Its execution/completion relative to add-model tick is not established here.

Consequently the native per-item parser/materializer skip can yield incomplete staging, and Java construction can independently drop an emitted record while returning normally. Neither mechanism establishes all-or-nothing replacement. In particular, failed replacement does not guarantee preservation of the old model: the separate alteration path may remove or mutate old entries. Conversely this evidence does not establish that removal actually ran in a given execution. Original Java/native model ownership remains as evidenced by these references and callbacks; no substitute execution or reconstructed ownership is assumed.

## Provenance, verification, and remaining limits

Original JAR SHA256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; original SO SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. `receipt.json` pins 16 original-byte windows, 12 instruction assertions, two task relocations, 13 matched Java methods, metadata receipt hash and reused dossiers. All local verification is read-only parsing/disassembly of original code or comparison of evidence; raw original-code extracts remain outside Git.

Reused: `CLIENT-MODEL-PUBLICATION-RECOVERY-2026-10-17.md`, `CLIENT-MODEL-SYNC-STATE-RECOVERY-2026-10-17.md`, `NATIVE-SERVER-EXPORT-RELOAD-RECOVERY-2026-10-18.md`, and the adjacent worker/controller exception reports. Independent review is supplied separately under [publication review](NATIVE-COLLECTOR-PUBLICATION-REVIEW-2026-10-18.md) and [review receipt](NATIVE-COLLECTOR-PUBLICATION-REVIEW-2026-10-18.json).

Still open: full collector scheduler/drain/lifetime contract; stored native completion-exception consumption; actual execution and renderer observation/order. No model rollback, complete batch transaction, universal later success, asset interpretation, or runtime-validation claim is added. Runtime remains blocked; central mapping completeness and source/artifact divergence classifications are unchanged.

Published native/Java integrity receipt: [publication evidence](NATIVE-COLLECTOR-PUBLICATION-EVIDENCE-2026-10-18.json). Independent verdict: CONDITIONAL_STATIC_ACCEPTANCE.
