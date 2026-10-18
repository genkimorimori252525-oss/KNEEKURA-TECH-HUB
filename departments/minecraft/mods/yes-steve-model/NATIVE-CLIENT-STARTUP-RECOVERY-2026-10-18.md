# Client native startup: bounded original-byte contract

## Result

The exact Java client-setup native is `com/elfmcys/yesstevemodel/OOoo00oOOoooooooooOooOOo.Oo0Oo0o00O00Oo0OOoOOoooo()Ljava/lang/Object;` at `0x3bc7c0`. Its attempted-start latch precedes resource work. A repeated call returns null without repeating startup. Normal initial execution resolves LWJGL OpenGL exports, submits five additional native-registration records, prepares built-in resources and a Java-backed object, installs a client-sync worker and executor, then registers cleanup. Null alone therefore cannot establish that graphics resources were initialized.

The startup-body analysis executed no target code, JVM, GPU or native workers. The separate identity-closure evidence below uses guarded metadata callbacks, not a startup or graphics run. No repository files were edited. `reproduce.py` uses Python original-byte parsing and objdump only; [evidence receipt](NATIVE-CLIENT-STARTUP-EVIDENCE-2026-10-18.json) records original SO/JAR hashes, original class declaration validation, thirteen source-backed ranges, six ELF import chains, 37 literal LWJGL exports and five undecoded registration records. Address ranges are half-open. The original images are SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22` and `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.

## Exact Java join and order

Prior CLIENT-COMPAT-INITIALIZATION evidence, hash-pinned in this receipt, establishes the CLIENT/MOD event subscriber, YSM-availability early return, base-animation registration, enqueueWork boundary, 24 optional adapter calls, warning checks, then the wrapper at Runnable offset 93. The wrapper casts the native result to Component; null returns normally, a nonnull result becomes RuntimeException with a bounded 256-character component string. There is no finally guaranteeing native entry after an earlier adapter exception. These facts describe declared Java flow, not dispatched Forge startup.

The binding receipt links callback `418600` to native `3bc7c0` through original descriptor stores at `414d03/414d43/414d47/414d4e`; fresh original-JAR parsing verifies owner/name/descriptor, access 265 (public/static/native), and class hash. That binding metadata is not proof RegisterNatives ran successfully.

## Gates and latches

1. `3bc7d1..3bc87a`: get TLS via verified `__tls_get_addr`, lazily establish TLS holder +128 under flag +130, obtain its JNI environment from holder +8. The lazy holder destructor registration is `2aa2d0(41b5f0, TLS+128, d2eb40)`; that is distinct from the late shutdown registry.
2. Read global byte `d34c48` at `3bc7fc` or `3bc86d`. Nonzero goes to `3bc807` (zero result) and the return epilogue. Otherwise `3bc87a` exchanges 1 into it before the rest of setup. The previous exchanged value is not tested: this is not an atomic winner/compare-and-swap proof. No resetting store to this latch occurs in the entire entry or its cleanup blocks. A failed initial attempt may leave this latch set; global writers outside the bounded entry are not excluded.
3. TLS+3c00 guards auxiliary setup calls `344470 → 4df620 → 344520 → 3445e0` at `3bded9..3bdee8`, followed by `43bfe0(TLS+3238)` stored in d34c50. The entry then advances its TLS random state and stores a derived byte in d34c58. This is auxiliary state, not a graphics-readiness indicator.
4. Byte `d355f1==1` at `3bcb23` exits through a zero result before library/export setup. The existing registration-mechanism dossier uses this same byte as mode input to skip flag-2 declarations; the exact source/semantic name of the byte is not proved here.
5. If not skipped, call opaque helper `d14720` and test AL (`3bcb30..3bcb37`). Nonzero takes a Java FindClass/ThrowNew/DeleteLocalRef sequence (JNI offsets 30/70/b8) and then zero result. Original d14720 is redirected by an unconditional jump; its original nominal PLT symbol must NOT be used as this branch's semantics. Decoder helper d14730 supplies the exception class/message here; neither plaintext identity is asserted.

Thus a null return has at least four distinct causes: already attempted, mode skip, pending Java-exception branch, and normal completion. Java with a pending JNI exception does not necessarily execute its ordinary null-success branch.

## LWJGL setup and partial initialization boundary

Only if slot d35a38 is zero does `3bcbd3..3bcfba` perform library lookup. `dl_iterate_phdr(41d110,&path)` at `3bcc0a` examines loaded-module names. Callback `41d110` derives a filename and at `41d288..41d2b9` compares length 18 and exact bytes `liblwjgl_opengl.so` (constants 3aae0 and 39890). A match publishes its path and returns 1, stopping iteration. An empty path branches at `3bcc15` into native error construction code 0x23. `dlopen(path,5)` at `3bcc25` must be nonnull or takes another code-0x23 error. This is a lookup/open request, not an observed loaded module or functional context.

`3bcc36..3bcf9e` resolves 37 literal `Java_org_lwjgl_opengl_...` JNI exports. The receipt lists every string and callsite. They cover texture image/subimage/parameters/pixel-store/generation/deletion/binding, buffer allocation and mapping, synchronization and related operations. These are actual native export names, unlike unresolved Java metadata strings. Representative first two exports are `Java_org_lwjgl_opengl_GL11C_nglTexImage2D__IIIIIIIIJ` and `Java_org_lwjgl_opengl_GL11C_nglTexSubImage2D__IIIIIIIIJ`, stored in d35a38/d35a40. Helpers 41d500..41daa0 call verified dlsym, store the result, and branch on null into code-0x24 native errors. Inline dlsym sites also null-check and error. No GL drawing is necessary to establish these static dependencies.

Important nontransactional gate: d35a38 is populated by the FIRST lookup, before the later lookups. A later failure does not visibly roll it back here. A nonzero first slot bypasses the complete block on a later entry that reaches it. Combined with the attempted latch, neither sentinel should be treated as a complete-success state.

## Additional registration and Java object

The entry builds five 0x30-byte descriptor records (flags 2) and calls existing registration helper 327000 at `3bd5d8` with RSI=JNI environment and EDX=0. Thus that helper's flag-2 mode skip does not apply to this call. Records, in order:

- metadata 33a470, encrypted source 43370 length 47 → native 3c2320
- metadata 33a490, source 3dedd length 47 → native 3c2560
- metadata 33a4b0, source 42da9 length 61 → native 3c2650
- metadata 33a4d0, source 4279c length 61 → native 3c2740
- metadata 33a4f0, source 42de6 length 49 → native 3c2830

The callbacks call decoder d14730. The original-byte receipt pins callback code and source hashes; this work does not decode them. They are distinct targets from the previously decoded 17 JNI_OnLoad registration records. Do not call these five additional original-JAR declarations, name their classes, or claim successful runtime registration without the metadata/class evidence.

After descriptor cleanup, byte d355f1==1 zeros pair d2f988; otherwise manager d355e8 record +60 must contain both class and member handles, or takes code-0x3e error. Helper 3654b0 invokes CallStaticObjectMethodV (JNI +398) at `3bd679`. Its result is passed through 41b6e0 and a 16-byte result is stored in d2f988 (`3bd6db`). Exact Java owner/member identity and downstream object semantics remain unknown, requiring manager/callback metadata evidence. Null result has a distinct empty-owner path, not an immediate proven graphics failure.

## Built-in resource work, worker/executor, registration order

The normal path then conditionally locks mutex d338d8, constructs the literal path `assets/yes_steve_model/builtin/` with `default` and `/` at `3bd75e..3bd778`, copies global string d35258/d35260, and passes structured input through `344b80`, `43c840`, and `36d8c0`. A nonnull Java reference from the last helper is promoted with JNI NewGlobalRef (+a8) at `3bda41`; the owner is transferred into an allocated task passed to 41ce80 at `3bdb7d`. These are concrete resource/task boundaries; full file format, model validity, and execution of the task are not reconstructed. Temporary resources are destroyed and the mutex released before worker setup.

At `3bdc1b..3bdc36`, the original literal constructs `YSM Client Sync Worker`. Task entry 399ee0 is installed at `3bdc45`; 41acf0 is called with flag 1 at `3bdc81`, and 39d470 moves the wrapper to d34888 at `3bdc95`. The previously independently traced wrapper reaches pthread_create and detach when flag 1, so this is a detached worker creation request with completion-state ownership, not a raw joinable-thread handle claim. Its completion pair maps to d34898/d348a0 and flag to d348a8. No worker ran in this research.

`3bdcc8..3bdd4f` obtains a count through 2fcdf0, scales it by literal float 0.5, rounds down, selects at least 2, and passes it into constructor 37b080. The resulting ownership pair is stored in d34220/d34228 at `3bdd82`, releasing an old owner if present. The exact source of the count and full executor scheduling are outside this bounded report.

Only after this setup, `3bddf1..3bde0e` registers cleanup callable 328590 with manager 326fc0 through registry 3dbaf0. Consequently an exception earlier in setup does not reach this registration on the normal path. The registry can invoke a late callback immediately if shutdown is already requested; it is not always deferred. Normal registry dispatch is forward registration order, as independently proved in common-lifecycle-contract.

## Cleanup connection

Callback 328590 first calls 39d9a0. That helper prefix exchanges 1 into stop/request byte d338c8 at 39d9d9 before acquiring d338d8; its remaining model/resource cleanup is outside this slice. Then, if d348a8==1, callback 328590 uses completion object d34898, invokes its virtual +10, waits on state +10 through 2e3ec0, and clears d348a8 at 328601. As in common lifecycle, wait-helper false also exits the loop; flag clearing alone is not proof of actual worker completion. Finally it zeros d34220/d34228 and releases the old executor owner. No cleanup resets client attempted latch d34c48 in this callback. This links the startup's worker/executor ownership to shutdown, while not claiming all tasks were drained or resources freed.

## Error-to-Java semantics

- Normal success zeros the returned ownership record at 3bde2c..3bde49, resulting in null at 3bec58.
- A nonnull returned reference at stack+150 is converted using JNI NewLocalRef (+c8) at 3bde66, then its temporary owner is released before returning the local handle through RBX/RAX at 3bec85. This joins the established Java Component result convention.
- Landing path 3bea92 calls the C++ catch-entry helper; selector 2 takes a distinct branch that constructs diagnostic text and calls 328900 at 3beb1b. That helper performs FindClass, ThrowNew and DeleteLocalRef. It then leaves the returned ownership record zero. The actual exception class is decoder-backed and unverified here.
- Other selector values take the path `3bebb3 → 3cef00(code 0x35) → 3d0310`, constructing the owned Java-result record subsequently converted by NewLocalRef when nonnull. Exact error-component construction internals are out of scope. Error IDs 0x23/0x24/0x3e/0x35 are numeric facts, not inferred human error text.
- Multiple RAII/unwind branches exist; this is not a proof every native error is converted, all allocations roll back, or that cleanup-registration is finally-guaranteed. Escaping unwind branches remain visible near 3bee26.

## Confidence and remaining limits

Primary static review; independent semantic review NOT_RUN. Metadata availability and actual backend readiness remain distinct. Existing named renderer metadata for BufferBuilder/VertexFormat/Sodium wrappers does not prove those external classfiles or a compatible GL context exist. This startup's actual LWJGL export resolution is a separate dependency layer and does not establish rendering success. Follow-up identity closure needs only the five callback payloads above and manager d355e8/+60 metadata; no full transitive graphics expansion is needed. Opaque guard/exception decoder behavior, helper internals, actual scheduling, full failure rollback and native/Java runtime outcomes remain unproved.

## Bounded direct registration-call inventory

`inventory_registration_calls.py` scans all original executable file-backed PT_LOAD regions for E8 rel32 targeting 327000. It finds exactly two candidates, both aligned callsites with inspected argument-setting context: client `3bd5d8` (mode 0, five descriptors) and JNI setup `416175` (mode byte d355f1, seventeen descriptors). Source segments, code bytes, context hashes, and boundaries are recorded in [direct-call inventory](NATIVE-REGISTRATION-DIRECT-CALLS-2026-10-18.json). This bounds only direct E8 original-file calls; indirect calls, tail jumps, decrypted/generated instructions, runtime patches, and data later executed are excluded. It does not prove that all possible native registrations number 22, or that either registration attempt succeeds. The original 17 binding receipt remains unchanged.


## Subsequent five-identity closure

The earlier UNDECODED labels above and in evidence.json record the state of this original-byte-only startup pass. Separate receipt ../client-registration-five-classfile-verified.json (SHA25619237b6d0385d888a9cdcc4735b31ceab7cb1dc6de3f39c1bafe53ed55a57811) subsequently decoded and verified all five against official Minecraft1.20.1-declared LWJGL OpenGL3.3.1 classfiles: 3c2320→GL11C.nglDeleteTextures(IJ)V;3c2560→GL11C.nglGetTexImage(IIIIJ)V;3c2650→GL45C.nglGetTextureSubImage(IIIIIIIIIIIJ)V;3c2740→GL43C.glCopyImageSubData(IIIIIIIIIIIIIII)V;3c2830→GL43C.glTextureView(IIIIIIII)V. All owners have org/lwjgl/opengl/ prefix and methods are public/static/native. This closes those five identities, not runtime installation. The separate ../client-wrapper-contract/REPORT.md and evidence.json trace their direct forwarding/skipping and registry behavior. Original decoder, startup evidence and original17 receipts are preserved; managerd355e8/+60 remains unresolved.
