# Particle vector on the fresh animation wire-read path

## Conclusion

On the normally completed fresh-element input path through3491d0 ->34a2a0, the particle vector A+0x148/+0x150/+0x158 remains the zero triple and therefore has count zero. Both append paths and growth relocation preserve that result. For a produced element reaching the immediate converter without intervening mutation, it requests a zero-length ParticleEventKeyFrame array and skips its element-construction loop. This conclusion is limited to this exact fresh path and established reader/object boundaries. It is not an absence claim for reused objects, other native producers, Java-created animations or global particle support; nor is it a theorem about arbitrary memory corruption/malformed input.

Static original SO SHA-256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. Five authoritative original-byte windows and prior receipt hashes are in evidence.json. reproduce.py additionally checks only authored address and zero-count algebra. No original targets, assets, callback decoders, JVM or runtime tests executed.

## 1. Fresh initialization

3492a4 sets R15=RSP+0x40;3492a9 sets RBX=A=RSP+0x28. The input iteration jumps to349407. Element table d1cec0 is stored at A; defaults and absent optional flags follow.

At34945d XMM0 is zeroed. 349460 stores16zero bytes at R15+0x138 = A+0x150. 349468 stores16zero bytes at R15+0x128 = A+0x140. Together these cover the complete24-byte particle triple A+0x148..A+0x15f. The remaining stores clear the other vectors. 349490 passes A to34a2a0 at349496. This initialization occurs for every newly parsed temporary, not merely the first element.

## 2. Parser preserves the triple within its established schema

The complete34a2a0..34b170 window, already explained in animation-element-contract, consumes the name, promoted number, selector, three version-gated optional values, optional bool, bone vector A+0x100, instruction-like vector A+0x118, and version>=11 string/number event vector A+0x130. Normal return is34a4b3..34a4c4; count loops rejoin the corresponding later sections. There is no particle vector section after the A+0x130 loop.

The root-owned vector writes/moves in this parser address A+0x100..0x117, +0x118..0x12f and +0x130..0x147. Neither root direct stores nor a particle-vector helper call targets A+0x148..0x15f. Nested parsers receive their specific subobjects or separately initialized temporaries, per the prior bounded schema proof. This combines normal object/reader field contracts with original control flow; it does not assume that an arbitrary substituted virtual callback respects memory boundaries. A simple byte-pattern search alone is not the proof.

## 3. Both destination routes preserve the triple

After parsing,34949b..3494a8 compares retained-vector end/capacity.

Spare-capacity route: RBP is the destination element. At3493b6 the temporary begin/end are loaded from RSP+0x170 = A+0x148;3493be stores them to destination+0x148. 3493c5 loads capacity from RSP+0x180 = A+0x158;3493cd stores it to destination+0x158. Moved temporary fields are zeroed3493d4..3493dc. The enclosing end advances0x160 at3493e7, followed by temporary destruction3493f7 and the next freshly initialized iteration.

Growth route: allocation349544 and destination addressing precede the element move.349ae7..349afe copies exactly the same three temporary words into RBX+0x148/+0x150/+0x158, then clears temporary words349b05..349b0d. Already retained elements are relocated with their particle triples copied unchanged at349c37..349c51 and moved sources zeroed349c59..349c62 before source destruction. Final vector-header stores349f43/349f47/349f53 publish begin/end/capacity and rejoin temporary cleanup3493ef.

Induction over fresh input elements: each temporary has zero triple after initialization and the scoped parser; each inserted element receives that triple; relocation preserves earlier zero triples. Input mode first clears prior retained elements3491ed..349214, so reusing the outer vector allocation does not import a former element's particle contents into these new elements. Directly invoking the element parser on a reused nonempty A is a different path and is not covered by this zero-initialization argument.

## 4. Converter consequence

361ba0's particle branch begins362659. 36266e loads A+0x150 and362675 subtracts A+0x148. Both are zero on the fresh path, so the shift/inverse multiplication at36267f..36268d yields count0. It passes jint0 to NewObjectArray at3626a0, using class metadata d355b0+0x130. The signed count test3626ae/3626b0 branches directly to362b40, skipping all particle element conversion and constructor calls.

362b40 tests the returned array reference. On successful allocation the reference is retained at stack+0x150 by362b99 and passed into the final Animation constructor via363042 (adjusted stack addressing), as established by the previous argument-order proof. No success is inferred if JNI allocation fails or throws.

Separately verified exact metadata identifies d355b0+0x130 as ParticleEventKeyFrame owner com/elfmcys/yesstevemodel/oOo0o0OoO0OO0oO0ooOOoooO, constructor(D,String,String,String,String)V. This metadata names the array's elements; it does not establish a nonempty source. The original Java particle-field reader scan remains a separate, symbol-specific observation, not evidence of global absence.

## Finite stop

The fresh-wire source question is closed within this path: no missed writer was found, and the initialization/moves explain empty particle storage. An investigation of another producer or direct reused-object parser call would require a separate scope. Do not generalize this proof to all assets, formats, versions outside the accepted pipeline, emission implementations or runtime support.

[Evidence](NATIVE-PARTICLE-FRESH-WIRE-EVIDENCE-2026-10-18.json). Raw binary excerpts and reproduction scripts remain external. Read the [current reuse guide](NATIVE-REUSE-GUIDE-2026-10-18.md) for later metadata/Java refinements to this static cohort.

[Exact event identities](NATIVE-ANIMATION-ELEMENT-METADATA-2026-10-18.json) name the particle class. This producer proof is not a whole-program census of intervening writers.
