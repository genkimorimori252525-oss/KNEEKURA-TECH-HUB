# Client model receive: bounded native contract

Static original-file inspection only. No target, JVM, emulation, target threads, network/client, installer or repository mutation. [Evidence receipt](NATIVE-CLIENT-RECEIVE-EVIDENCE-2026-10-18.json) pins the original SO and JAR, selected class declarations, JNI header, source documents, and 13 exact address ranges with original-byte SHA256 and file offsets. `reproduce.py` independently regenerates those selections using Python ELF mapping and objdump binary-mode disassembly. Addresses are unrelocated ELF virtual addresses, ranges end-exclusive. Long excerpts include unreviewed regions; this report only claims the instruction sequences identified below.

## Results

The exact client `(ByteBuffer)V` binding at **0x3bee40** is a queue producer, not an immediate model parser. Its nonnull path obtains a JNI global reference and moves that reference, with a deferred cleanup callable, into a 40-byte queue record. A statically identified consumer at **0x399ee0** obtains the buffer's direct address and **capacity**, then takes state-dependent decoding and construction paths. One proven construction subpath creates a Java object carrying an incrementing native handle and registers native texture data. This is **not** the renderer's geometry registry. Bone/controller metadata and complete Java model publication are not resolved by these selections.

## 1. Java-to-native and lifetime connection

Prior exact binding receipt identifies owner `com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO`, method `o0OOooo0o0OO00OoOOOo0o0O(Ljava/nio/ByteBuffer;)V`, private static native access266. Original class bytes are rehashed and declarations reparsed here. Prior callback decoding is cited, not rerun.

The Java transport dossier establishes that the Java connection/buffer receiver stores LAST_CONNECTION before calling this native; packet decoding supplies a direct buffer with no explicit local flip/rewind. Native receive saves its third argument RDX at3bee49. The JNIEnv pointer is obtained via thread-local environment wrapper, not assumed to remain the incoming RDI:3bee4c..3bee7f and41b460.

At3beead..3beeb6 a global byte d35570 gates processing. If clear, nonnull buffer reaches JNI **NewGlobalRef** (+0xa8, slot21) at3beecd. The returned reference is placed at record+0x20; callable manager326fc0 and cleanup3451f0 occupy +0x10/+0x18. No payload bytes are copied in this entry selection. The original argument uses a separate wrapper whose cleanup2aade0 is exactly RET; distinguish it from the retained global reference.

Producer lookup39e3f0 derives a producer key from thread-local base+0x134, searches the table d343c8, and may allocate a producer linked into d34398. This table is queue bookkeeping, not a model registry. Enqueue39e760 uses block index modulo32 and stride40. At39e795..39e7ca it moves the callable fields, copies reference+0x20 into the slot, zeros the source reference, and advances the producer index. On success receive increments d34608's counter and may call d148f0. These instructions show queue publication/wakeup structure, not observed scheduling or guaranteed delivery. Allocation/queue failures can take cleanup paths rather than publication.

Null input, when the global gate is clear, instead calls39d9a0 at3bf04e. Its prefix exchanges d338c8 to1 and takes/clears shared state d33880/d33888. This is consistent with the separately documented Java syncAbort(null), but does not prove comprehensive reset, successful cancellation, or LAST_CONNECTION clearing.

Cleanup3451f0 forwards the stored reference into another queue through41ba10/41bd80, and may signal d35958. Existing NATIVE-GLOBAL-REFERENCE-COLLECTOR evidence covers that separate deletion path to JNI DeleteGlobalRef. Do not conflate receive queue d34398/d34608 with the collector queue d356e8 or claim observed cleanup execution.

## 2. Consumer and actual buffer semantics

399ee0 takes a JNIEnv* as its first argument and retains it in R15. It consumes the same d34608 counter and d34398 producer chain. Representative dequeue39a580..39a597 computes a40-byte slot and calls39d8e0 with destination stack+0x20.39d8e0 moves slot+0x20 to destination+0x20 and clears the source; the consumer therefore obtains the identical global-ref object in stack+0x40. Other dequeue branches use the same mover.

At39a724..39a758 it loads that object, skips null, then calls:
-39a73b: JNI GetDirectBufferAddress, table+0x730/slot230; saves result at stack+0x148.
-39a752: JNI GetDirectBufferCapacity, table+0x738/slot231; saves result at stack+0x140.

JNI slots are independently extracted from the locally available JDK jni.h and checked in reproduce.py. No ByteBuffer position/limit read, duplicate, rewind or flip appears in this boundary sequence. The inputs to the subsequently selected decoder are exactly address and capacity. This refines the Java dossier's formerly unresolved native interpretation; it does not establish how every later helper interprets the memory, immutability, payload validity, or a vulnerability. There is no null-address/negative-capacity validation between these calls and the shown branch dispatch; admissible inputs and guarantees from upstream/runtime remain unresolved.

Consumer has a second state/task source d34610/d34880 and a retained state pointer at stack+0x48; this is not itself the buffer reference. With state nonnull, d35570 clear, state+0x100 clear and state tag==1,39a815..39a857 obtains two values through state+8 virtual slots+0x18/+0x20 and calls3d0b20(address,capacity,valueA,valueB,output,3). On true return39a8a5 calls3577c0 with parsed fields and state+0xf8. Resulting map state is moved into state+0x88 onward. State tag2 instead calls3d0b20 with selector5 at39aca6. Fallback39c625..39c64a calls the same helper with fixed data d1ba88, length0x38, selector1. These selector values are observed constants, not assigned protocol message names.

3d0b20's selected prefix reads a trailing8-byte value at address+capacity-8, computes helper573dd0 over the preceding bytes with a fixed argument, and compares at3d0b62. It subsequently builds stream wrappers and uses indirect dispatch. Proposed descriptive name: `validate_and_decode_selected_payload`; no cryptographic algorithm, complete schema, or complete bounds-safety claim is made. The prefix's checks are not a full audit and do not establish valid wire inputs.

## 3. Proven texture registration subpath

3577c0 is a large builder reached conditionally from successful selector3 decode; only selected calls/dataflow are interpreted. It invokes Java object/array helpers and multiple native builders. At3584d2 it loads a current source element, tests byte+0x68==1, takes its +0x30 subobject, and calls375430 at358507. Proposed name `build_received_model_components` for3577c0 is descriptive, not a recovered C++ symbol.

375430:
-37544d atomically reserves a handle from d34948, increments the old value at375480, and passes that handle as an argument to object constructor helper364a60 via metadata descriptor loaded from manager d355c0+0x38.
-3754db..3754e9 takes lock d34920 conditionally on the image's threading flag.
-3754ef..375554 obtains/copies opaque source data and copies16 bytes of source+0x28 metadata. Field meanings are unresolved.
-375556 onward looks up handle in registry buckets d348b0, bucket count d348b8, linked sentinel/head d348c0 and element count d348c8.
-375662..3756ba allocates a0x58-byte node, stores handle+8, opaque data wrapper+0x10, copied data pointer+0x18, and additional wrapper+0x40.3757d8..375959/alternate rehash paths link the node and increment element count.
-375960 onward fills derived opaque data in the +0x40 wrapper;375a85 releases the lock via tail call.

This registry is connected to **NativeTexture**, not inferred from naming: exact native binding3bf0c0 is the native upload on owner `O0O00000Ooooo00oooo0ooo0`; existing Java dossier identifies that owner as NativeTexture. Original class extends Minecraft AbstractTexture, stores long nativeId, and declares upload()V/free(J)V.3bf0ff..3bf134 obtains the long handle through the manager d355c0+0x40 member (JNI GetLongField+0x328) and3bf149 onward looks it up under the same d34920 lock in the same d348b0/b8/c0/c8 registry. This establishes a receive-build-to-texture-storage connection. It does not prove an upload actually ran, GL success, texture byte format, or all constructor metadata decoded.

The renderer/GeoModel registry documented independently in the renderer/lifetime evidence is d341b8/c0/c8/d0 with lock d341f8. No alias, transfer, or exact model/bone/controller bridge to that registry is proven here. Do not merge these two registries just because both store native handles.

## Explicit remaining boundaries

-Concrete bone/controller definitions, field names and ordering after3577c0 remain unresolved; Java model composition documents are context, not proof of native schema.
-Java construction member descriptors behind d35598/d356e0 and other manager offsets were not decoded by this read-only task; indirect invocation cannot be named solely from plausible model classes.
-The full parse/protection/data transform behind3d0b20 and its virtual calls is not recovered. Selectors1/3/5 remain numeric.
-Actual consumer startup, target scheduling, synchronization success, native buffer validity, model readiness and final publication are not executed or claimed.
-Original input bytes are immutable in this investigation; the target's mutable-buffer lifetime remains distinct from holding a JNI global reference. Retention prevents ordinary object collection, not caller mutation.

## Verification

Run `python reproduce.py` in this directory. Result: PASS;13 original-byte ranges,2 original class declarations,JNI slots21/22/29/230/231 verified. Original research artifacts and raw disassembly stay outside Git; this report and compact evidence are published separately. Earlier exploratory `.bin/.asm` excerpts, if present, are superseded by evidence.json's authoritative selected ranges; do not treat a truncated disassembly as a complete function.
