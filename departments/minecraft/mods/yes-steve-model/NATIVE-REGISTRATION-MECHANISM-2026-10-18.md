# YSM native registration: bounded static map

Source: immutable libysm-core.so from native-static-20261017. Exact image, checkpoint, source-payload and instruction-range SHA256 values are in NATIVE-EXACT-BINDINGS-2026-10-18.json. That receipt records the completed separate guarded callback experiment. It is not evidence of JNI_OnLoad completion or runtime RegisterNatives success.

## Registration mechanism

After 0x413bc6 calls resolver 0x4193c0 for manager global 0xd35588, 0x413bd3 calls 0x3d5280. Its concrete static-field accesses include GetStaticBooleanField (+0x490) at 0x3d52bb and GetStaticObjectField (+0x488) at 0x3d52f5 and 0x3d5373. Then 0x413c82 calls 0x406b00, which constructs another 12 managers and invokes the same resolver for each. Their aggregate object storage admits 143 descriptor-pointer slots after the common 0x38-byte prefix; this is a storage-layout inference, not a proven count of successful API lookups or distinct Java classes.

Only after 0x406b00 returns does 0x413c97 begin constructing the 17 registration descriptors. Thus the current early-manager checkpoint has no allocated final registration table. Original instructions do preserve all 17 callback/native-function pairings; adjacent stores establish the pairing without assuming Java declaration order.

The main function calls 0x327000 at 0x416175 with RDI pointing to the descriptor vector, RSI=JNIEnv*, RDX=byte[0xd355f1]. Each descriptor is 0x30 bytes: metadata callable storage at +0..+0x18, native function pointer +0x20, flags +0x28. First six flags are zero; remaining eleven flags are 2. With nonzero incoming mode the helper skips descriptors whose flags & 2 is nonzero (0x3270ad..0x3270b9).

At 0x3270d1 it invokes each metadata callback, parses the resulting bounded string through 0x328e60, and groups records by class. Intermediate records are 0x48 bytes. At 0x327d40..0x327d4b it packs 0x18-byte JNINativeMethod entries with name +0, signature +8, and function pointer +0x10 (sourced from intermediate record +0x40). At 0x327e4b the class argument comes from the group +8; RDX is the packed array; ECX is (end-begin)/24. At 0x327e73 it calls JNIEnv table offset 0x6b8, slot 215, RegisterNatives.

## Resolver layout and checkpoint-specific progress

At unicorn-jni-fmlcore-next6.checkpoint.json only: global 0xd35588 points to manager 0x4040010985a0. Field pointer vector +0/+8/+0x10 is begin/end/capacity: 0x404001058100 / 0x404001058148 / 0x404001058180, exactly 9 entries. Method pointer vector +0x18/+0x20/+0x28 is 0x4040010044c0 / 0x4040010044d0 / 0x4040010044d0, exactly 2 entries. Each descriptor is 0x38 bytes: class handle +0, memberID +8, metadata callable +0x10..+0x28, flags +0x30.

At this historical checkpoint both methods and seven fields have nonzero resolved IDs. The active field is vector slot 0x404001058138, descriptor 0x404001012140; one further descriptor 0x404001012180 follows. Both have zero class/member IDs. Seven distinct class handles occur among the resolved records; this does not bound later classes. The main guarded JNI scenario continued independently, so these counts describe only the named checkpoint.

Further resolver calls in 0x406b00 (callsite / global / manager size):
- 0x4070d3 / 0xd35590 / 0xa0
- 0x407757 / 0xd35598 / 0xa8
- 0x4078ed / 0xd355a8 / 0x50
- 0x40870d / 0xd355b0 / 0x148
- 0x4089d6 / 0xd355b8 / 0x68
- 0x408b22 / 0xd355c0 / 0x50
- 0x408e82 / 0xd355e8 / 0x70
- 0x408ffc / 0xd355c8 / 0x58
- 0x409664 / 0xd355a0 / 0xa8
- 0x40a71e / 0xd355d0 / 0x190
- 0x40a7ab / 0xd355d8 / 0x40
- 0x40a838 / 0xd355e0 / 0x40

## Isolated metadata recovery boundary

recover-native-bindings.py forks the named stopped checkpoint into an independent guarded CPU, establishes a fresh synthetic top-level callback frame, and calls only the 17 metadata callbacks at 0x418540 + index*0x20. Each calls protected helper 0xd14730 and returns its fixed-length decoded metadata payload. The experiment verifies known bytes, expected length, NUL termination, callee-saved registers, and completed callback frames. It does not resume the interrupted JNI frame and does not execute host target code or a JVM. Each exact decoded owner/name/descriptor is then matched against the pinned original YSM JAR using JavaMetadata, including ACC_NATIVE, with classfile SHA256 recorded. The trace and JSON distinguish ENTRY_RETURN of the metadata callback from registration success.

Execution detail: callbacks are sequential within each isolated cloned-state batch, not independently reset per callback. The initial run decoded indices 0 and 1, then index 2 stopped at its 2,000,000-instruction budget. That stop is preserved. Subsequent batches restore the same original checkpoint independently: A covers indices 2..9; B covers 10..16. Each callback gets a fresh synthetic top-level frame; decoder allocations/state persist inside its batch. Per-run quotas remain at the harness-supported 4,000,000 instructions / 180 seconds; at most one resource-stop continuation of the same active callback is permitted. No semantic stop is bypassed. Per-pair exact descriptor-store evidence is separately recorded in native-binding-store-proof.json. original-jar-native-declarations.json enumerates all 17 ACC_NATIVE declarations under com/elfmcys/ in the pinned original JAR for final set comparison.
