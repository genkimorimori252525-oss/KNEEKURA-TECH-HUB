# Geometry creation and receive-builder bridge

Separate static cohort following model-receive-contract. No prior receipt modified. No target/JVM execution, emulation, native threads, network, or repository edits. `reproduce.py` reparses original ELF/JAR bytes and emits hashed selections; PASS:17 ranges,3 classes and8 JNI slots. Long ranges contain unreviewed sequences; only the specific dataflow below is asserted. Exact Java constructor identities behind manager d355a8 are independently proven by the separate guarded callback receipt [constructor metadata receipt](NATIVE-GEOMETRY-CONSTRUCTOR-METADATA-2026-10-18.json), SHA256 `462fbeda3a87caf946822b2e11bf06333d38e7890881a7ae6dfe77af0797ed14`. This task did not execute those callbacks; it integrates their original-JAR-verified result. Callback return is not target initialization or construction success.

## Finding

The receive builder has a concrete deferred-callable route to geometry creation:

3577c0 -> stores callable35d250 -> if dispatched,35d250 calls36d8c0 -> branch calls36a6e0 ->375e30 builds/inserts geometry ->36a6e0 assembles Java bone/geometry constructor arguments, including returned geometry handle.

This is distinct from the texture375430/d348b0 route. The geometry registry is exactly d341b8 and therefore joins the independently documented renderer/release lifetime evidence. Callable installation does not prove its invocation, successful parsing/construction, or model publication in a real session.

## Deferred boundary, without fabricated direct edge

At359fdc the receive builder allocates a0x30 capture.359fee..35a024/35a051..35a062 populate capture+0,+8,+0x10,+0x18,+0x20,+0x28.35a028/35a066 store the capture pointer in a0x20 task record.35a02b..35a03d and35a069..35a07b store callable35d250 at task+0x18 and manager35e210 at+0x10.35a07f..35a0aa advances the containing work deque;35a0d2..35a0fb unlocks/notifies associated synchronization objects. Captures include a retained reference-counted object. Exact scheduler consumer/when it runs is outside this selection.

35d250 reads its capture at35d261..35d27e, obtains a thread JNIEnv and iterates captured index range. Abort byte d338c8 can skip work. On the shown non-aborted branch35d54b directly calls36d8c0 with output,JNIEnv,selected native model data and an integer option. IMPORTANT:35d0c0 is a different function ending at35d242; its direct calls from3577c0 are deque-management support, not this model-construction call.

36d8c0 has direct calls36df27/36dfa2/36f1ad/36f99d to36a6e0, with distinct data/flag selections.36a6e0 calls375e30 at36b192 with output=&stack2c8 and source aggregate=&stack160. The additional flags/options are copied into375e30's frame; meaning of every option is not inferred.

## Registry allocation, insertion and returned handle

375e30 constructs native geometry in a vector of0x78-byte records.378b73..378cae creates a0x68 reference-counted allocation: vtable d1b8a0 at+0, counts at+8, geometry payload at+0x10. The payload includes native record vector begin/end/capacity and additional index data. A pair {payload_pointer,control_block_pointer} is retained at stack+d0.

378cb5 atomically increments64-bit counter d341f0;378cbe increments returned old value to obtain the new handle.378cc1 saves its low32 bits at stack+0x198.378cd3..378ce1 conditionally acquires geometry lock d341f8. Hash-table lookup uses d341b8 buckets,d341c0 bucket count,d341c8 head/sentinel,d341d0 entry count.378dd7 allocates a0x20 node;378deb stores full64-bit handle at node+8;378df8 stores the payload/control pair at node+0x10/+0x18.378eff..37903d or rehash branches link the node and increment count.

This is the same registry and node layout consumed by renderer3bf750 and release3c1160 in the published NATIVE-RENDER-LIFETIME receipt. It is not d348b0 texture storage.

After further record processing,37a213..37a282 copies a byte vector into the caller output triple+0/+8/+0x10;37a28e..37a295 copies the saved low32 handle to output+0x18;37a29a..37a2a1 releases the lock.36a6e0 receives that output at stack2c8:36c410 loads stack2e0 into R10D, zero-extending it to64 bits;36c421 passes R10 as the final Java constructor argument. Thus native registry keys are64-bit while this return/publication path carries the low32 bits then zero-extends. This is a static width observation, not a demonstrated rollover bug or exhaustion test.

## Native records and Java bone descriptors share an ordered source

The source aggregate passed to375e30 is36a6e0's stack160.375f13..375f77 uses source+0x40/+0x48, exactly the caller's stack1a0/+1a8 pointer vector.375fc5 dereferences each vector entry into a wrapper;375fb8 advances by8 and each emitted record advances by0x78.36b219..36b267 later walks that same vector by ascending index and obtains the same underlying native bone pointer through wrapper+0.

Consequently the native record order and Java bone-descriptor array order share the same producer vector. This is stronger than the Java label `sortedBones`, but does not alone prove a particular graph sort algorithm, uniqueness or absence of cycles.

Native record assignments at3761c6..37623f:
- wrapper+0x44 byte -> record+0x70 byte
- wrapper+0x48 int32 -> record+0x6c int32
- underlying bone+0x68,+0x6c,+0x70 float -> record+0x60,+0x64,+0x68 after multiplying each by0.0625

The multiplier is original bytes0000803d at0x48574, independently parsed as float0.0625. Meanings of wrapper+0x44/+0x48 are not assigned from offset similarity. Renderer may interpret record+0x6c/+0x70 separately; use its exact selection.

Exact GeoBone constructor call at36b345:
- NewStringUTF at36b27d reads underlying bone+0x40 as name data.
-36b2e3..36b2ef passes underlying+0x61,+0x62,+0x63 as three booleans.
-36b2f5..36b333 passes underlying+0x68,+0x6c,+0x70,+0x74,+0x78,+0x7c as six floats, promoted to double for C variadic invocation.
-36b345 calls364a60, verified JNI NewObjectV(+0xe8), using manager d355a8+0x40's class/constructor handles.
-36b6e5..36b6fb inserts the resulting object at the same source index using SetObjectArrayElement(+0x570).

Original GeoBone constructor declaration is(String;ZZZFFFFFF)V. Existing GEOMETRY-AUTHORED-DEFAULTS evidence gives the ordered Java meanings: three visibility booleans,three pivots,three rotations. The separately confirmed exact metadata identity establishes the direct common-source distinction: Java stores authored pivot values while the native geometry records hold pivots divided by16. It does not establish rotation units or transform order.

## Geometry Java constructor and properties

36b1b7..36b1cd creates the bone-object array using class handle from d355a8+0x40.36c3cc selects d355a8+0x38, and36c3f8..36c42c passes object array,other array references,properties object,byte-derived boolean array,and zero-extended handle into NewObjectV. Original GeoModel constructor declaration matches:
`([Lcom/elfmcys/yesstevemodel/oO0OO0OooO0Oo0OoO0oOooo0;[[Ljava/lang/String;[ZLcom/elfmcys/yesstevemodel/OOoOoO0000OooOOoO0ooOOOo;[ZJ)V`.

36c21b selects d355a8+0x48 and36c23f..36c26c calls NewObjectV with identifier-like string,four doubles from native source+0x48/+0x50/+0x58/+0x60,and a double[] copied from source+0x68/+0x70. The separately confirmed descriptor is exactly GeoModelProperties.<init>(Ljava/lang/String;DDDD[D)V. Existing Java authored-defaults evidence maps these four doubles to texture height/width and visible-bounds height/width; the array is the supplied bounds-offset reference.

No Java final-field write is assumed to originate here directly: this is a constructor call and argument publication; the original Java constructor owns its field initialization and cleanup registration.

## Exact metadata chain and independently confirmed identities

Manager d355a8 built407761..4078f2:
-+0x38: callback410380 stored4077c1; descriptor pointer assigned4077ec; encrypted source459cb,length0xc0.
-+0x40: callback4103a0 stored407835; descriptor assigned407862; encrypted source44c67,length0x59.
-+0x48: callback4103c0 stored4078aa; descriptor assigned4078d0; encrypted source400c6,length0x56.
-Manager published4078d4 and resolved4078ed.

Callbacks are selected and hashed but NOT executed here. The separate guarded metadata receipt confirms all three <init> names and exact original classfile declarations (access1,public,nonstatic,nonnative): +0x38 is GeoModel owner OOoOoooOOooO0o0000o0O0o0; +0x40 is GeoBone owner oO0OO0OooO0Oo0OoO0oOooo0; +0x48 is GeoModelProperties owner OOoOoO0000OooOOoO0ooOOOo. All share prefix com/elfmcys/yesstevemodel/. Each guarded callback returned normally, but runtime member resolution, invocation and constructed objects remain unproven. Exact identity is based on that independent receipt, not merely signature resemblance.

## Bounds and unresolved work

No complete native decoder schema, controller semantics, graph validation, geometry rendering algorithm or task scheduler execution is recovered here. The original receive queue, builder work deque and global-ref collector remain distinct. Constructor failures/partial native insertion rollback are not fully audited. No runtime success, upload, readiness or leak assertion is made.

[Evidence receipt](NATIVE-GEOMETRY-BUILD-EVIDENCE-2026-10-18.json) is the authoritative original-byte manifest. Earlier exploratory excerpts can start/end inside neighboring functions; only cited aligned sequences and manifest entries support claims. Previous model-receive-contract/evidence.json is unchanged.
