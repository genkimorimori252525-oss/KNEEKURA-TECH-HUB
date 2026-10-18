# Bounded native audio contract, 2026-10-18

PRIMARY_STATIC_REVIEW_ONLY. No native/target/JVM/emulator/audio execution, installation, repository edits, or registration-success claim. `verify_audio.py` reparsed the original JAR with the existing Python classfile parser and matched all 10 wrapper methods exactly against the frozen Java evidence. The five binding records are reused as identity evidence, not re-emulated. Original ELF program headers establish VA=file offset throughout the captured code ranges; raw-binary objdump was required because ordinary ELF section disassembly does not expose these ranges.

Inputs: SO SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`; JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. [evidence receipt](NATIVE-AUDIO-CONTRACT-EVIDENCE-2026-10-18.json) contains half-open byte ranges and hashes, exact bindings and source-document hashes. `original-java-wrapper.json` contains freshly parsed declarations, instruction offsets and Code hashes. Assembly is in `entries.asm` and `packet-copy.asm`.

## Exact original-Java join

All five natives belong to `com/elfmcys/yesstevemodel/ooOo0oOo0o000O00oOOO0oo0`, original class SHA-256 `8ac84d2ca4a53157492fa1de3c95635b178586aa524629a14fbaacdb5b4a71a4`. Names below are exact; role labels derive from callers and bodies, not descriptors alone.

- 0x3c1400 `O00OOOooOoooOoo0o0o0oO0O()J`: wrapper constructor invokes it at bytecode 5, stores final long at 9, rejects zero with OutOfMemoryError at 19–26.
- 0x3c1600 `Oo0Oo0o00O00Oo0OOoOOoooo(JLjava/nio/ByteBuffer;)Z`: wrapper `Oo0Oo0o00O00Oo0OOoOOoooo(ByteBuffer)V` checks isDirect at 1; slice at 22; native at 25; false raises UnsupportedAudioFileException at 31–38; only success assigns original supplied buffer to retained field at 41.
- 0x3c1850 `o0OOooo0o0OO00OoOOOo0o0O(JLjava/nio/ByteBuffer;)I`: wrapper of same name with `(ByteBuffer)I` checks directness, slices at 22, invokes at 25 and returns unmodified int at 28.
- 0x3c20d0 `Oo0Oo0o00O00Oo0OOoOOoooo(J)V`: no-argument wrapper of same name calls at 4, then clears Java retained input at 9.
- 0x3c2100 `o0OOooo0o0OO00OoOOOo0o0O(J)V`: no-argument wrapper of same name calls at 4 and returns; no long zeroing/idempotence guard.

Existing Java pool/adapters establish init/decode/reset/destroy roles: acquire pooled wrapper, initialize on input; return resets; tick expiry destroys. EOF is separate from close. The existing SOUND-LIFECYCLE index and AUDIO-DECODER-JAVA-BOUNDARY report remain authoritative for callers beyond this freshly reparsed wrapper.

## Handle is an encoded pointer, not a registry ID

0x3c140f–1414 requests 0xf8 bytes from allocator-family helper 0xccc1e0. Let its result be P; the embedded state S=P+8. Creation initializes fields, requests 0x6994 bytes at 0x3c14b3–14b8 through 0xcbf560, and calls 0xc674a0 with that block and channels=2. On success `[P]=S` and `[S+0xc0]` is the second block. At 0x3c14da–14ee it returns `ROL64(P, byte[0xd34c58]) XOR qword[0xd34c50]` (x86 rotation masks count to 6 bits).

All four consumers reject H=0; also reject H equal to the XOR key (which would decode to null). They compute `P=ROR64(H XOR key, count)`, then directly dereference `[P]`. No registry lookup, generation check, type tag validation or membership test occurs in these entries. An arbitrary nonzero/stale H can therefore lead to invalid memory access; no execution was used to test it. Global key initialization and uniqueness/nonzero guarantees are outside this bounded trace. Do not import geometry-registry conclusions.

Creation returns zero on explicit allocation-null path 0x3c1504 and on its caught failure tail 0x3c15f8. The second allocation/init failure path builds a C++ exception-like object and has cleanup landing paths; exhaustive exception unwinding and allocation guarantees are not proven. No JNI ThrowNew appears in this entry. Java maps returned zero to OutOfMemoryError but this is not proof every native failure returns normally.

## Exact JNI buffer boundary and ownership

Init obtains a cached/thread-local JNI environment through helper paths 0xd14e80 / 0x41b640 / 0x41b690; it does not simply use incoming RDI throughout. At 0x3c1670 it calls table offset 0x730, slot 230, GetDirectBufferAddress(buffer); at 0x3c1682 offset 0x738, slot 231, GetDirectBufferCapacity(buffer). Decode makes the same two calls at 0x3c18c9 and 0x3c18dc. Names/slots are cross-checked against the existing `jni-slot-catalog.json` (header hash recorded there). These are the only direct JNI calls in the five entry bodies; helper environment management is a separate dependency. No NewGlobalRef/DeleteGlobalRef or Java position/limit getter occurs in the entry bodies.

Because Java passes a slice, address corresponds to caller position and capacity corresponds to caller remaining. Init rejects null address and capacity -1 or 0 (`unsigned(capacity+1)<2` at 0x3c1696–169e). It stores the raw address at S+0x50, capacity at S+0x58, and input cursor zero at S+0x60. This is borrowed storage, not a full-input copy and not native ownership of the Java memory. Java strong retention occurs only after true is returned. Direct-buffer reachability does not establish Netty reference-count lifetime, protection against external release, or immutability.

The packet helper 0x4d8040 reads the borrowed address/extent/cursor at 0x4d81a0–81df, calls bounded-but-not-expanded page parser 0x4d8730 and advances cursor at 0x4d820e–8213. It can return a packet pointer directly at 0x4d824f–825d or assemble bytes in an owned scratch buffer (0x4d8133–8164). Thus input must remain valid through decoding; packet copies do not remove that requirement.

Init consumes a packet and requires length >=18 at 0x3c1728, literal `OpusHead` at 0x3c1735–1742, and channel byte at +9 equal to 1 or 2 at 0x3c1748–1752. It calls the state initializer 0xc674a0 with this channel count, handles nonzero result as false, reads signed word header+16 for 0xc69ac0, and records preskip header+10. Full Opus header/container validation is NOT established by these few checks. It loops obtaining packets while S+0x20==0; bounded termination for malformed inputs is not proven. Success sets S[0]=1 at 0x3c17cf and returns true.

Failure after input assignment can leave mutated state and a borrowed input pointer; it does not run reset here. A prior active flag is not cleared at the beginning of init, so reinitialization failure on an already active object cannot be characterized as safely inactive. Java's success-only retained-input assignment makes this a lifetime concern, not proof of an observed bug in the normal pool path.

## Decode extent, output and return values

Decode rejects H=0/null-decoded handle, null direct address, or capacity=-1 by returning 0. It then checks active flag: inactive yields -1 at 0x3c1fe1. Only after that does capacity 0 yield 0. Odd nonzero capacity is rounded down by one at 0x3c1feb; capacity 1 therefore becomes a zero-byte request after the active check. Java cursor is not advanced. No output pointer is retained in S by the visible body: its destination/address/extent/cursor are stack locals at 0x3c1917–1928; internal pending PCM has its own storage.

Positive results are output byte counts, not samples. Direct decode reserves 2*sample_count bytes (0x3c1aa4, 0x3c1ad8–1afa), calls 0xc68c60 at 0x3c1b13; stereo needs enough physical room for channels*2*sample_count before the direct path, then compacts samples in place (0x3c1b29–1c05). The scratch path calls 0xc68c60 at 0x3c1c8d, applies preskip and pending-output handling. Copy helper 0x4d82c0 compares requested copy bytes against destination remaining and increments its byte cursor; result is returned through EBX at 0x3c1ec5. This supports byte-count interpretation while codec correctness and all malformed-input arithmetic remain unverified.

Observed explicit return branches (not an exhaustive specification of dependencies):
- 0: several invalid boundary values or no more packet/output bytes. Therefore 0 alone is not a unique native EOF marker; the Java adapter treats it as EOF/cache publication.
- -1: state flag not active.
- -3: nonzero packet extent whose low signed 32-bit length is <=0 (0x3c19e3–19e6 → 0x3c1ec0).
- -4: packet mode 3 but one-byte packet, or computed sample count >5760 (0x3c1a00 / 0x3c1a9e → 0x3c1eb9).
- -5: helper 0x4d8430 returns false on scratch stereo compaction path (0x3c1cd3 → 0x3c208e); full helper contract not expanded.
- -7: direct decoder returns a nonnegative sample count different from expected (0x3c1b20 → 0x3c1f4f); clears active flag and borrowed pointer/length.
- codec helper negative result minus 100: direct 0x3c1f45 or scratch 0x3c2084. Scratch also resets pending storage length before return.

Output may already have been modified before an error return; no transactional rollback or partial-success guarantee is shown. The adapter treats any negative value as failure/EOF; that does not mean resources were destroyed.

## Reset, destruction, rewind limits

Reset 0x3c20d0–20fb decodes H, loads S, clears active byte S[0] and the two qwords S+0x50/S+0x58. It does not clear input cursor, free allocations, seek, rewind, or invoke codec reset. Java then clears its retained input. Reset disables decoding and releases this wrapper's input reference; fresh init is required for reuse. Init explicitly sets the input cursor to zero and reinitializes codec/state, so reopening via init can start over on its supplied slice. This must not be advertised as a native seek/rewind API.

Destroy 0x3c2100–2198 decodes H and releases S+0xc0, S+0xd0 and S+0x80 when nonnull, then P via helper 0xcc74a0. These are the codec block and two owned scratch allocations populated by creation/helper paths; borrowed Java input S+0x50 is not released. The helper has allocator metadata operations, not JNI buffer release. Reset retains these allocations for pool reuse; destroy retires them.

Destroy does not invalidate the Java final handle. A second destroy/use-after-destroy is not guarded beyond H=0/key checks and can touch freed memory. No concurrent-use locking is present in these entry bodies; Java pool synchronization does not prove all calls on the decoder are serialized. Abnormal native exception translation, JNI pending exceptions, environment attach/detach failures, malformed container termination, allocation-failure completeness, native byte order correctness and real playback are unresolved.

## Bounded dependencies / stopping point

0xc674a0, 0xc68c60 and 0xc69ac0 are codec-state initialization/decode/control-like helpers by call/data flow; exact exported/library names are deliberately not assigned without symbol/byte evidence. 0x4d8730 page parsing, 0x4c4aa0 scratch sizing, 0x4c4990 scratch range access, 0x4d8430 stereo helper, allocator family and C++ exception helpers remain bounded dependencies. This task stops at lifecycle/buffer/return contracts rather than broad codec reverse engineering. Existing exact binding evidence does not prove runtime RegisterNatives or JNI_OnLoad completion.
