# Independent controller-chain review

CONDITIONAL_STATIC_ACCEPTANCE of ../../native-controller-exceptions/REPORT.md. Original SO byte-backed reads, unwind-metadata decoding and authored static graph checks only. No target/Java/native/assets execution, network, CI or Git changes.

## Independent findings

All12 supplied original code/metadata windows and8 named byte assertions match the pinned SO. Independent decoding reproduces all8 LSDA edges: four366110 helper callsites have action0 cleanup pads; controller365a10 call365b39 has action3 landing365ee9; three36d8c0 controller calls have action0 cleanup pads. The inherited helper374392 and worker35d54b edges remain covered by prior independent receipts.

Using a separate objdump text mode and independently authored queue traversal, all8 selected pads were checked. Every reachable local branch target is an instruction boundary. Under the explicit assumption that called cleanup/construction helpers return normally, no ordinary ret or trap is reached. The four controller-data pads end at368d4f→322a00; the inner controller catch ends at365fdb or366041→2abe00; the three materializer pads end at373548→322a00. This proves bounded control-flow connectivity, not infallible destructors or execution of the target.

The controller action table is independently decoded at145da9, bytes0100027d: filter2 chains to filter1. Typebase145db8, filter1 entry145db4 zero/catch-all. Filter2 entry145db0 is pcrel-indirect tod307a8; its R_X86_64_RELATIVE relocation targetsd1d9e0. The original type-name relocationd1d9e8→65eb0 contains N3err12YSMExceptionE. Thus the controller's filter2 is explicitly backed by original YSMException RTTI, not inferred from a code shape and not interchangeable with the worker's std::exception type. The report conservatively does not require that name for its two-branch conclusion.

The code0x5b claim is directly supported: ESI=0x5b at365fad and366016, followed by calls329990; instruction3299a1 writes SI at payload offset0. The first branch passes the caught object to4dbfc0; the other calls4db980. Both later call the already-reviewed nonreturning throw-like2abe00. Their normal controller insertion365b75 is not a continuation from these pads.

## Scope and limits

Accepted outcome: for the four selected controller parser paths and three selected enclosing materializer calls, normal unwind/cleanup/error construction leads to the previously reviewed per-model worker skip, not usable controller fallback or necessarily whole-batch failure. The Java facade's already-caught fallback remains a separate ordinary-return case.

The code0x5b result is conditional on allocations, context calls, cleanup and constructors completing. No claim of exact Java Throwable identity, complete nested-error semantics, transactionality, preservation of every side effect, eventual batch completion or final Java/renderer publication is accepted. Called-helper transitive CFGs and exceptional failures during these cleanup paths remain outside this review.

Final report wording retains these boundaries and is accepted. Its hash and independent graph terminal sets are in controller-receipt.json. Reproduce with review_controller.py; this also refreshes its inherited worker metadata checks. All output is outside Git.
