# Main geometry: two distinct flag contracts

## Result
A = S+0x10a = M+0x49a changes a geometry-build batch-routing condition. B = S+0x10c = M+0x49c is retained as registry payload+0x54, then gates the already documented renderer bypass with a separate renderer argument. They are independent inputs at these boundaries; they are not interchangeable switches. No new human-facing names are inferred.

Static original bytes only; no target/native/JVM execution, asset read/decoding, checkpoint restore, or repository edits. reproduce.py re-exports 17 source-backed windows and verifies the pinned image SHA256. Only stated sequences in the larger windows are reviewed.

## Argument identities and storage
36def6 zero-extends M+49a into EAX; 36defd zero-extends M+49c into R10D. Pushes 36df1d/36df1f and call36df27 put A and B in 36a6e0 arguments8 and9 respectively.

36a6e0 pushes six registers and subtracts0x328, totaling0x358 bytes relative to entry RSP. Thus stack+360 is argument7, +368 argument8, +370 argument9, +378 argument10. 36b0f5 loads A into R14D; 36b0ed loads B into EBP. At36b16c A is zero-extended to R9D (375e30 argument6); 36b164 zero-extends B to EAX, pushed36b191 (375e30 argument7). The unrelated argument7 of36a6e0 goes through R15B/R8D and must not be confused with A.

375e30 pushes six registers and subtracts0x3e8 (total0x418). 375e53 reads its argument7 from+420. 375e9f stores A/R9B to native frame+129;375ea7 stores B/AL to+12a. The source flags are read, not overwritten, on this path.

## A: exact byte-level build branch
376c4a..376c58 loads begin/end at current source-group+8/+10, subtracts them and saves byte span L at frame+2c0. 376c60..376c6c requires L==0x480 before the geometric classification calculation; otherwise3774b0 writes0 to frame+c. Within that calculation the successful exits set AL=1 before writing EAX to frame+c (377091,377186,377245,37730f,3773dc,377498); classification failure reaches3774b0. Only its low byte C is relevant here. Do not infer a mathematical classifier name from these thresholds.

378430..37844a computes exactly:
    T = (((L == 0x480 ? 1 : 0) & A_byte) | C_byte)
    T == 0: jump378550
    T != 0: fall through378450
These are bytewise AND/OR operations. Arbitrary nonzero A is NOT equivalent to true: an even A byte has low bit0. The inherited section390 contract says reader+40 validates wire booleans0/1. The truth table below is limited to that canonical domain. C's low byte is0/1 on the reviewed producer paths; C can become1 only after L==0x480.

The branch affects grouping and allocation, not merely a stored label. Nonzero T tests a first temporary buffer for emptiness at378450, then appends a copied batch to a per-record collection reached through frame+2b0 (378471..37853e), advances its0x38-byte batch end, and later handles another buffer at37872b. Zero T instead enters378550: second temporary-buffer size==0x228 takes378564, other nonempty sizes take3785d9. The relevant record collection headers are initialized at376570 (record+0 via frame+38),376690 (record+18 via frame+2a0),3768d0 (record+48 via frame+2b0). Empty buffers may skip append work, so changing A does not guarantee a different emitted model.

C also controls quotas independently:378466/378740 use default3 when C==0; C!=0 goes to378b31/378b4e to compute a capped value5. Setting A does not set C or force those latter quota paths.

## B: retained byte and immediate renderer consumer
378b79 allocates0x68 bytes. The native payload address is allocation+10 (378c31). 378c8d reads native frame+12a and378c95 writes allocation+64, therefore payload+54=B. This is an exact byte copy with no normalization or test in that store. The payload/control pair is placed into registry node+10/+18 at378df8, joining d341b8's existing registry contract.

Renderer3bf750 reads the node pair at3bf969..3bf978 and obtains payload R13 at3bf9bc. At3c0041 it tests byte[R13+54] against0. The preceding3c0032/3c003f requires renderer frame+89 !=0; that byte comes from entry frame+188 via EBP at3bf7ad and3bf82f. We preserve that concrete argument provenance without assigning a new Java GUI/mode name. Existing gui-bypass-contract supplies the documented route label.

These tests are reached only after the earlier3bffec..3bfff8 gate: global d34c30 !=0 and the tested return bit of37bd80. If the separate argument and B are both nonzero, branch3c0046 goes to3c0f80. Current EBP!=0 selects385390 at3c0f9e; EBP==0 selects385080 at3c0fe3. Otherwise execution reaches398e50 at3c005e and ordinary dispatch. The renderer argument stored at+89 and the later EBP mode are not asserted to be the same value. This is branch eligibility after prior gates, not a guarantee of rendering or worker completion.

## Canonical two-flag truth table
Let Q=(L==0x480), C be the classification byte, and G=(renderer frame+89 !=0). Renderer results below apply only after its preceding gates and on the matched retained payload.

| A | B | Build takes378450 iff | Renderer bypass takes3c0f80 iff |
|---|---|---|---|
|0|0|C|never|
|0|1|C|G|
|1|0|Q OR C|never|
|1|1|Q OR C|G|

On the reviewed producer paths C implies Q, so Q OR C simplifies to Q, but retaining C in the equation makes the local branch provenance explicit. A changes this build decision only for Q=true,C=0. B changes this renderer decision only for G=true and preceding gates satisfied. For noncanonical bytes use the raw T equation; B's consumer still uses any-nonzero testing.

## Bounds
The read354e00/version gates and selector1=`main` identity are inherited from prior receipts, not redone. Other selector/vector routes explicitly supply zeros as previously proven. No claim that every process retains the registry unchanged, no inventory of every payload+54 access in the ELF, no new UI names, no exact full geometric-classification semantics, and no renderer-equivalence claim. Original bytes suffice to close the requested argument-storage-immediate-branch gap.

[Source window and inherited-contract evidence](NATIVE-MAIN-GEOMETRY-FLAGS-EVIDENCE-2026-10-18.json). The reproduction script and raw byte windows remain external.
