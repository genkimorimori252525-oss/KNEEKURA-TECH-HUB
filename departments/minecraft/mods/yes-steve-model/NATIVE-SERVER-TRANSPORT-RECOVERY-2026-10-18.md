# Server synchronization transport boundary

## Findings

Server enqueue and receive use distinct native structures. Enqueue `3c5500` builds a native request with recipient metadata, copied model-ID strings and retained callback, then links it into pending list `d35420`. Receive `3c6a40` submits a UUID-keyed callable to the generic executor object reached through `d35cf0`. The callable, if invoked, matches the UUID against active-request recipient records, obtains direct-buffer address/capacity, and conditionally calls the shared decoder. A null buffer is also queued and takes cancellation-oriented keyed branches. Submission or return does not prove scheduler execution, completed cancellation, Java callback delivery or remote model readiness.

Original SO SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`; original JAR SHA256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. No target/JVM/emulator execution or repository edits. Exact ranges, original-file backing and hashes are in the [evidence receipt](NATIVE-SERVER-TRANSPORT-EVIDENCE-2026-10-18.json); reproduce.py verifies fifteen ranges, two original-JAR declarations, nine JNI slots and the buffer-release relocation.

## Exact Java boundaries

Both methods belong to `com/elfmcys/yesstevemodel/OoOoOoooO0O00oOoO00OOo00` and have obfuscated name `Oo0Oo0o00O00Oo0OOoOOoooo`:

- `3c5500`: `([Ljava/util/UUID;[Ljava/lang/String;[Ljava/lang/String;Ljava/lang/Object;)V`, access266, private static native. Analytic name: sync enqueue.
- `3c6a40`: `(Ljava/util/UUID;Ljava/nio/ByteBuffer;)V`, access265, public static native. Analytic name: sync receive.

The existing SERVER-MODEL-SYNC-JAVA evidence establishes the enqueue arguments as recipient UUIDs, corresponding recipient names, requested model IDs and completion state. Its abort helper passes UUID and null to the receive overload. The recovered native paths refine these handoffs; they do not replace the Java scheduling/publication evidence or assert actual RegisterNatives success.

## UUID conversion and key identity

Both entries use helper `41b6e0`: receive at3c6a92, enqueue per recipient at3c5806. It reads manager `d356e0` descriptor slots+0x98 and+0xa0, checks descriptor/field handles, then invokes JNI GetLongField (+0x328) at41b71b and41b75a. The output is a0x18-byte object: vtable at+0, first long+8, second long+0x10.

The separate [UUID metadata receipt](NATIVE-SERVER-UUID-METADATA-2026-10-18.json) pins those metadata slots to `java/util/UUID.mostSigBits:J` and `leastSigBits:J`, respectively. Its SHA256 is `92413cf63dcbe19a8dc534c084b8f025a8b3684e6ee3f4ad3aad4a44841c5fa0`. That proof restores a guarded metadata fixture and reads it with zero guest instructions; it is metadata identity evidence, not a runtime read of a user's UUID or proof of the actual loaded JDK.

The native key therefore consists of `(mostSigBits,leastSigBits)` copied unchanged as two64-bit values. The shown key conversion does not format a UUID string or byte-swap the longs. Recipient-map equality compares both longs (e.g.3c59f0..3c5a00; receive403b68..403b72). Hash mixing uses both values and constant0x9e3779b9; cryptographic or wire-encoding properties are not inferred.

## Enqueue builds owned native request data synchronously

`3c5500` saves its four Java arguments, obtains a thread-local JNIEnv wrapper, and allocates a0xe8-byte request Q at3c5652. Its initial recipient hash-container occupies Q+0..0x37; a separate model-string collection begins Q+0x38. These are request-local containers, not either model registry.

The recipient loop count comes solely from UUID-array GetArrayLength at3c571e. At each index it reads UUID and name with GetObjectArrayElement at3c5772 and3c57bd. There is no matching name-array-length comparison in this visible loop; this does not establish behavior for invalid/mismatched inputs or upstream validation.

After UUID value extraction, helper4192b0 copies the name through GetStringUTFChars(+0x548), GetStringUTFLength(+0x540), and ReleaseStringUTFChars(+0x550). It copies exactly the returned modified-UTF-8 byte length into owned native string storage and appends a zero byte. Thus this is JNI modified UTF-8, not an asserted ordinary UTF-8 conversion.

A recipient UUID is also retained as a Java global reference at3c5845. A0x78-byte control block is allocated3c587e with payload starting+0x10. It contains the UUID valuepair at control+0x18/+0x20, reference-owner state at+0x28..+0x48, and copied name string at+0x50 onward. Cleanup callback3451f0 and manager326fc0 are installed; the original local owner is cleared as the global reference moves into the recipient object (3c58bc..3c58e1). Recipient-map keys use the UUID valuepair, not Java reference identity. Hash membership/collision handling is visible, but recipient ordering and duplicate-selection policy are not promoted as a transport guarantee here.

The third String[] is iterated independently using GetArrayLength3c5e1a and GetObjectArrayElement3c5ea3. Each ID is copied with4192b0 at3c5ee8, compared by length/bytes against existing native strings, and the insertion path moves owned string storage into32-byte records (3c622f..3c630a). This is collection construction, not proof of eventual transmission order.

For a nonnull fourth argument, NewGlobalRef at3c643a retains the completion state. Q+0xe0 stores the reference; Q+0xd0/+0xd8 hold manager326fc0 and cleanup3451f0. A null argument follows the alternative branch without that global-reference call.

Finally3c64e2 acquires lockd35520; a0x18-byte list node stores Q at node+0x10 (3c6500), links through2b8e80 with sentinel d35420 (3c6504..3c650e), increments d35430, and calls the wake helper on d353f0 (3c651a..3c6521), then unlocks. The request is queued by native ownership, rather than retaining whole Java argument arrays. The exact consumer transfer from this pending list to active request d35450 was not traced in this bounded cohort.

## Receive captures a UUID key and buffer owner

`3c6a40` copies the UUID valuepair first. It obtains an executor shared-pointer pair through4e0b10 at3c6ad4. The helper reads globals d35cf0(object) andd35cf8(control), with a separate fallback4e0be0 if no object exists. That fallback's initialization/scheduling is outside this cohort.

For a nonnull buffer, JNI NewGlobalRef(+0xa8) is called at3c6b01. A0x18-byte reference control block is created with vtable d1b9c0, reference counts at+8 and global reference at+0x10. The callable capture C is0x28 bytes:

- C+0: UUID-key vtable d1c150
- C+8/+0x10: most/least significant UUID longs
- C+0x18: buffer global reference
- C+0x20: owning reference control block

The executor object's mutex at+0x108 protects enqueue. A32-byte task record stores capture pointer at+0, manager404ee0 at+0x10, and invoker403a10 at+0x18 (`3c6b70..3c6baf`). Its deque write cursor is object+0xe8; block boundary and growth use0x200-byte blocks. After cursor publication3c6cef, the routine unlocks and signals via object+0x48. These offsets belong to the executor object; they must not be conflated with pending-request globals or client receive queue d34398/d34608.

Null buffers bypass NewGlobalRef and set capture buffer/control to zero at3c6e7f..3c6e85, then take the same enqueue path. Therefore the null abort request is deferred, rather than completing cancellation inside the JNI entry.

## Captured buffer lifetime

Manager404ee0 copies captures while incrementing the reference control block and releases the control on destruction. Its vtable dispose call is+0x10. Original ELF relocation at d1b9d0 resolves that slot to3c5110. That destructor reads control+0x10 and, subject to its shutdown guard, submits the global reference through41ba10/41bd80 to the existing global-reference collector and signals its wake mechanism. It does not directly establish when DeleteGlobalRef actually runs. The collector queue and executor queue remain distinct.

This global reference keeps the Java buffer reachable across deferred invocation. It is not a byte snapshot, an exclusive lock, a proof against concurrent content mutation, or a promise of prompt release.

## Conditional receive callback and buffer extent

Invoker403a10 first checks active pointer d35450. It locksd35520, takes a reference to the active object/control d35450/d35458, and then protects the active request with object+0x1b0. UUID matching operates on active recipient keys at node+0x10/+0x18. No matching active recipient means this is not a generic unconditional decoder call.

On the matched nonnull-buffer branch, JNI GetDirectBufferAddress is called403c4e and GetDirectBufferCapacity403c61. Address is saved unchanged; capacity is carried through R14. For recipient state byte+0x20 equal1,403d0b..403d1f passes address in RDI, capacity in RSI, request-derived additional arguments and selector2 to shared decoder3d0b20. This differs from the client's selector3/5 paths.

No Java position(), limit() or remaining() read appears in this extraction-to-decoder slice. The proven extent is the JNI capacity, not the buffer's logical remaining bytes. The slice does not establish whole-decoder validation, directness/error handling, byte order, capacity safety or a protocol schema. No payload/protection algorithm is recovered here.

For a null capture, callback404b98 iterates pending requests keyed by UUID via405200 and calls405000/405470 on a separate structure d35438. If an active recipient matches,404c0f checks its state and conditionally writes state5 with exchange, sometimes invoking406180. These are concrete cancellation-oriented operations. Their helpers, completion semantics and every state transition remain unresolved; no completed-abort guarantee follows.

## Boundaries retained

Three distinct structures are now evidenced: native pending synchronization requests atd35420, generic deferred receive tasks on the executor fromd35cf0, and the client's receive queue atd34398. Global-reference collection is another distinct queue. Active-requestd35450 is checked by the receive callback, but the pending-to-active handoff is not proven by this report. No scheduler, real connection, callback, decoding or cancellation was executed.
