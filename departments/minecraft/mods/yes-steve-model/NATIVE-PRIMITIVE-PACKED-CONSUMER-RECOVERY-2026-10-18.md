# Serialized scalar records to native packed records

## Result and scope

The source-pointer join is exact: geometry builder375e30 reads wrapper->bone->bone+0x28 item vector, then item+8's0xc0-byte records. On the selected output branches it writes0x5c-byte packed records containing the same first triplet and four three-scalar groups; each group's final two components come from branch-dependent processing of the corresponding serialized pair. A raw192-byte native source record is therefore repacked to92 bytes, but this is not a universal unchanged copy of all23 serialized floats.

The external scaling pair is from separate0x28-byte records produced by4c8000, not bone data. Its generic provider remains dispatched, so the report uses neutral scalar and pair names rather than asserting positions, normals, UVs, cuboids, or dimension names from layout.

Static-only, no assets/target/emulator/JVM/repository edits. reproduce.py PASS:14 aligned original-byte ranges. Original SO SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. Prior primitive evidence is checked unchanged at238ef3bc8bed8a8bae14fbbbb2e26b66eeb9e626eee14deb1cc64057acdb09fd. evidence.json records exact backing and hashes. This is a selected-path storage contract, not a broad renderer audit.

## Source identity before semantic interpretation

Prior hierarchy evidence establishes aggregate A+0x40/+0x48 as the flattened pointer vector whose entries W hold original bone B at W+0.375e30 uses that aggregate. At375fc5 the pointer-vector entry becomes r14=W, and375fe0 saves W at stack+0x20.

376c0d reloads saved W,376c12 dereferences W+0 to B,376c15/376c19 load B+0x28/+0x30. Thus r15=H is exactly the0x28-byte item serialized by3489f0.376c30 advances H by0x28.376c4a/+4e reads its inner begin/end, and checks byte span against0x480 at376c60.0x480 equals six0xc0 records, but this is only a special-path gate, not a parser restriction or a proof that all records represent cubes. Other lengths go to3774b0.

377501 reads H+8 into r14=Q and H+0x10 into saved end;3775e6 advances Q by0xc0. This is the same native record parsed in the prior cohort. The output fast path377560 advances destination r12 by0x5c at3775e2. Alternate fast path378111..378191 advances its distinct destination rdi by the same0x5c.

## External integer-pair provenance

375e87 stores incoming third argument rdx as T at stack+0x118;375e8f stores incoming rcx as element count at+0x120. The loop's index k is multiplied by0x28 at3775fb..377610, yielding D=T+0x28*k.377644 reads D+0x20 and D+0x24 together as an8-byte pair, zero-extends each32-bit lane, and converts the values to float lanes using the shown integer-to-double-to-float sequence.

The call-chain provenance is explicit:
-36a6e0 saves incoming rcx in r15 and incoming r8 in r14 at36a6f1..f4.36a81a/+822 store them at stack+0x220/+0x228.36b180/+188 load them as rdx/rcx for375e30.
-At the selected36d8c0 caller,36dea6 obtains rcx from local vector begin stack+0xb0;36deae..36dec2 computes r8=(end-begin)/0x28.36df27 calls36a6e0 with this pair; other caller branches are not generalized here.
-36da71..36da99 allocates the0x28-stride vector.36db11..36db18 calls4c8000 with output stack and input S=source item+0x38.36db64/+69 copies the returned8 bytes at output+0x20 to D+0x20, then36db6d advances0x28.
-4c8000 reads selector S+0x28. If selector==1,4c811a calls4c8150, then4c811f/+123 copies S+0x20 unchanged to output+0x20. Since S=item+0x38, that pair originated at item+0x58/+0x5c on this branch.
-For selectors other than1,4c8000 searches registryd35cb8 using selector;4c808e..4c80a3 tail-dispatches provider object's virtual+0x10, passing S. Missing provider enters an error path. The provider's output pair provenance is not resolved by these selections.

This proves where the scaling pair enters and a conditional exact producer, but not universal image dimensions or positivity/nonzero bounds. Those labels/preconditions remain unproven.

## Selected consumer operations and packing

377613 selects a branch using a local mode derived from a caller integer at375e4c..375eae; do not confuse this mode with a serialized record tag. In the selected mode path,377666..37767b reads each Q pair from offsets+0x40,+0x68,+0x90,+0xb8.377684 starts multiplying the first pair by the converted D pair. Subsequent rounding/bounds/provider-specific classification was deliberately not fully reconstructed here.

At377e34..377e98 the code loads:
- Q+0x10/+0x14/+0x18 into the first three scalar lanes.
- Q+0x30/+0x34/+0x38, Q+0x58/+0x5c/+0x60, Q+0x80/+0x84/+0x88, Q+0xa8/+0xac/+0xb0 into four three-scalar groups.
- The final-two lanes of each packed group are already held in xmm11,xmm7,xmm4,xmm8 and their extracted high lanes. Their relation to raw Q pairs depends on the intervening path; they are not asserted equal to the original pairs.

For packed destination P on fast path377560:
- P+0,+4,+8 = Q+0x10,+0x14,+0x18.
- P+0xc,+0x10,+0x14 = Q+0x30,+0x34,+0x38; P+0x18,+0x1c = processed pair0.
- P+0x20,+0x24,+0x28 = Q+0x58,+0x5c,+0x60; P+0x2c,+0x30 = processed pair1.
- P+0x34,+0x38,+0x3c = Q+0x80,+0x84,+0x88; P+0x40,+0x44 = processed pair2.
- P+0x48,+0x4c,+0x50 = Q+0xa8,+0xac,+0xb0; P+0x54,+0x58 = processed pair3.

The final movlhps/movups at3775d8..3775dc merges the fourth three-scalar tail with its processed pair.378111..378190 uses shuffles/insertps to write the same layout to the alternate destination.

At377e9a the classifier value eax==1 selects the first output route (and marks a per-external-item byte).3780e0 accepts classifier1/2 or a separate caller flag for that same route; otherwise classifier3 selects the alternate route, and other values skip this Q. Thus source-record count is not automatically equal to either output-vector count. Classifier meanings and final vector ownership/publication are outside this bounded selection.

## Stop and concrete next frontier

The storage join is complete for these selected paths. Next, if needed, inspect the immediate pair-provider d35cb8 registration/virtual dispatch for the actual selector used, or the finite branch region377684..377e34 to prove processed-pair semantics and classifier values. Do not infer pixel dimensions, UVs, opacity, or normal names without that evidence. Final packed-vector attachment can separately start at378430; no broader renderer retrace is needed.

Evidence: [NATIVE-PRIMITIVE-PACKED-CONSUMER-EVIDENCE-2026-10-18.json](NATIVE-PRIMITIVE-PACKED-CONSUMER-EVIDENCE-2026-10-18.json). Related [primitive wire fields](NATIVE-BONE-PRIMITIVE-SCHEMA-RECOVERY-2026-10-18.md). Raw ranges and reproduction scripts remain external.
