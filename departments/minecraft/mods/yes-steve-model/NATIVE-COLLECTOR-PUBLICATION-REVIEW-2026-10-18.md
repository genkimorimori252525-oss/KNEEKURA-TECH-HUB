# Independent native-to-Java publication join

CONDITIONAL_STATIC_ACCEPTANCE of the bounded ownership/metadata/Java-body join. This review only reads original native/classfile bytes and existing separately produced metadata evidence. No target code or metadata decoder was executed by this reviewer; no assets, network, CI or Git changes.

## Native ownership and callback

The worker's0x88 records have a concrete vector identity: builder stores frame+220 into sharedbase+40 at359c17. Context is sharedbase+10 (359caf..359cb6), placed in the worker closure; worker35d250 loads that context and reads context+30 at35d603. Thus it is the same vector object, not merely a matching record size. Builder35a5d9/35a5e2 and35a5eb/35a5f3 move the vector's three words to frame+190, then zero the source220/230. Task construction35ac6b/35ac72 installs d1b5a8 and captures frame+190 at task+20 via35ac75/35ac7d.

Original RELATIVE relocations distinguish d1b5a8→35ef10 from earlierd1b580→35f620. Emitter35ef10 loads begin/end from captured vector, strides0x88, requests NewStringUTF from record+48, loads model reference record+20 and flag record+68, sets first boolean R9=false, then calls345d50 with managerd35598+58. Local JDK jni.h and original345dcc bytes independently establish the variadic adapter invokes CallStaticVoidMethodV at JNI+470. The pending-exception check follows at35efe8.

The separately guarded metadata receipt identifies+58 as exact original private-static manager callback (ModelData,String,ZZ)V; +60 is the different(String[],String[],String[],boolean[])V callback. Receipt hash, original callback/source buffers, initializer instructions, manager slot stores and publication bytes were rechecked. Payload hashes include the terminating NUL. This review reuses the decoder's stated result without rerunning it and does not convert metadata decoding into runtime initialization or task-execution evidence.

## Exact original Java join

The pinned manager class SHA203f7df0d59b7010c1da8809cbcea192b20d381fbb604f43eb5ee3f711afd3a4 was freshly parsed; all13 selected method snapshots exactly match the supplied evidence and corresponding prior publication/sync-state dossiers.

The +58 callback's first boolean is false on the inspected native path. It bypasses the deferred-default branch, calls the existing setup-default helper at bytecode15, then calls the body at22 with false. Setup-default itself can fail before the body. The body:
- invokes model construction at7 within Exception handler range[4,12);
- on ordinary nondefault caught failure logs47 and returns52, bypassing queue-add62 and progression submission97;
- on nonnull successful construction adds Pair(model,path) at62;
- on null input jumps to89 and can schedule progression97 without adding a model.

Accordingly native callback ordinary return and progression notification are both weaker than enqueue confirmation. The later tick method polls the exact same queue24, uses Pair.right as path and Pair.left as model at put53, then assigns the new map at61. Original field access74 includes ACC_VOLATILE. That is later map-reference publication, not callback-time publication, object immutability, renderer readiness or GPU completion. Map/listener behavior retains the prior dossier's qualifications.

## Boundaries

The builder's wait-shaped loop and release of its handle vector are not a result-get/exception-consumption proof. No worker-drained, task-executed, async ordering, stack-capture lifetime or unconditional eventual publication claim is established here. Earlier+60 dispatch and later+58 dispatch must not be conflated. Failures before/inside callbacks, Java caught failures, queue timing and later tick execution remain separate outcomes. Native per-model skipping and partial staging retention remain local prior results; there is no new whole-batch transaction guarantee.

Reproduce independent byte/hash/classfile checks with review_publication.py. publication-receipt.json records exact inspected metadata and method hashes, native relocation checks and the publication field flags. All artifacts remain outside Git.

Final report wording review: ../../native-model-publication/REPORT.md accepted with its conditional scheduler, wait, exception and publication limits. Final receipt rechecked at16 original windows,12 byte assertions,2 task relocations and13 matched Java methods;359bcf alignment corrected and345d50 adapter included. The separate+60 scheduling12 and alteration-body map write195/listener223 were checked against the exact original snapshots. Existing authentication-mutation and release semantics are reused from the prior Java dossier. The report correctly does not claim failed replacement preserves an old model, nor that any removal actually executed. Final reviewed report hash is recorded in publication-receipt.json.
