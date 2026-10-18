# Independent worker-boundary addendum

CONDITIONAL_STATIC_ACCEPTANCE: resource user-function escaping-Java-error route can reach a per-model handler that skips the current item and proceeds to the next item. It is not necessarily an outer completion failure. Static original-ELF evidence only; no target execution, assets, network, CI or Git edits.

## Exact exception coverage

Original GNU_EH_FRAME header185656c (file16bd56c), encoding011b033b, indexes worker35d250 to FDE187d128/CIE1867a70. Its LSDA1450ac has a row at1450d6 covering [35d53d,35d550), including materializer call35d54b (35d548 is argument setup). The landing pad is35de5e, action3, not35defd and not outer35e143. Pad35de5e jumps to35def1 then35df03.

Action-table base1451cc contains0100027d. Action3 starts at1451ce with filter2 and next displacement-3 to filter1; filter1 has no next action. Type1 is zero/catch-all. The type2 pcrel-indirect reference1451d0 resolves throughd307c0's RELATIVE relocation tod2cb18; its original type-name relocation resolves to bytes St9exception. This is a read of original RTTI and relocations, not a recovered name inferred from machine-code shape.

Worker cleanup at35df03..25 conditionally destroys the current model through345030 and frees its0x5d0 allocation. Selector2 and its alternate both call311020, set EBX=4 at35df40/35df5c, call2aad30 and jump35dcd2. Assuming these operations complete normally, BL&3 is zero at35dd1d; the path increments the item index35dd2e and jumps35dd39→35d310 when items remain. Existing successful records are not removed on this inspected route. This is a local item-skip continuation, not proof of end-to-end successful publication.

## Narrow resource-parser connection

The exact original LSDA rows for helper3742d0 call374392 and resource materializer36d8c0 call370a03 have action0 (cleanup only):
- helper: FDE187fd30, LSDA1473d8, [37438f,374397)→374498
- materializer: FDE187f184, LSDA146720, row containing370a03→372eea (exact range in worker-receipt.json)

Helper374498 cleans wrappers and calls322a00 at3744ae. Materializer372eea preserves the exception in RBX and jumps3733f1. Cleanup calls3733f4/373401 precede wrapper-release branches373406..37346d, converging373504. Further cleanup calls37350c,373519,373526,373533 and373540 end with RBX→RDI and322a00 at373548. There is no catch/recovery action in either selected LSDA row. Under normal cleanup, this is the resource-specific outward unwinding route to the worker's per-item handler.

Controller behavior is deliberately not generalized from this resource route. The controller365a10 has its own action3 catch at call365b39→365ee9 and code5b transformation/throw-like paths, deserving separate treatment. No claim is made that every parser error follows precisely the resource route or retains code3c unchanged.

## Limits

Cleanup, retention, allocation and handler helpers may fail. Full transitive cleanup correctness and complete unwinder behavior remain outside this check. The outer35e143..35e18f route calling360570 is distinct from the ordinary per-item handler path above; this review does not assign an exact std::promise/std::exception_ptr API identity from shapes or certify future/promise semantics. It also does not prove final Java rethrow identity, whole-model rollback, old-model preservation, or eventual renderer publication.

Reproduce: review_worker.py. worker-receipt.json records original SO hash, all worker LSDA rows, the two-action chain, twelve control-flow assertions, resource-chain rows and hashed original code/metadata ranges. All artifacts are outside Git.

Final wording review: ../../native-worker-publication/REPORT.md accepted within its stated resource-only scope. Record writes35d741/35d84d and logical-end updates35d943/35dbf9 independently checked in the original-byte worker window. The report correctly distinguishes staging retention from final publication and does not claim future/promise failure.
