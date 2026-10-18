# Two vector model carriers: immediate optional payload and Java joins

## Proven result and metadata boundary

Both 0x348-entry routes use the same five-input construction order: identifier String array, one geometry object, optional animation-file converter result, optional controller-file converter result, and texture helper result. They select different final metadata: M+0x148 uses d35598+0x98, M+0x160 uses d35598+0xa0. This static receipt does not assign ProjectileModelData/VehicleModelData to those slots without the separate exact metadata proof. Native collections and the optional payloads are model-owned; converter entry arguments borrow addresses into the current E. Java object results are held by temporary reference wrappers and inserted into newly allocated route arrays.

The final constructor slots are the smallest remaining identity frontier. Existing Java MODEL-INPUT-CARRIERS evidence names two five-argument carrier classes, but matching by resemblance or order is unnecessary and is not done here.

## Entry read-mode layout

At 424924/27, RBX=reader R and R14=entry E. 424934 always invokes 424a20(R,E+0x1f0); 424939 compares reader version against 22 and only versions >=22 invoke 424bc0(R,E+0x240) at 424949. These routines also contain a non-read branch; the schema below describes R+8==1 only.

### Optional aggregate O=E+0x1f0

424a43 reads tag through reader+0x10. Only tag==1 enters fresh payload construction. 424a4b..4f captures and clears O+0x48; if previously present, old auxiliary string and 0x160-stride nested elements/vector allocation are destroyed at 424a5d..424ab7. The replacement initialized at 424abc..424afc contains:

- O+8=E+0x1f8: payload vtable d1cc18.
- O+0x10/+0x18/+0x20=E+0x200/+0x208/+0x210: vector begin/end/capacity, initially zero.
- O+0x28=E+0x218: auxiliary owned string, initialized to inline buffer O+0x38.
- O+0x48=E+0x238: presence byte, set to 1 at 424afc.

424b06 reads the auxiliary string through reader+0x48. 424b09..424b46 calls payload virtual+0x10 with payload address E+0x1f8 and reader. Original ELF relocation d1cc28 resolves to 3491d0, the established counted animation-element vector parser. A non-1 read tag leaves presence zero and destroys prior contents if present, then returns. This does not imply storage outside the presence flag has been zeroed on every absent path.

### Optional aggregate C=E+0x240

424be4 reads tag; only 1 constructs. 424bec..bf0 captures/clears C+0x60. Prior string C+0x40 and ordered payload nodes are destroyed at 424bfe..424c25 when previously present. Fresh initialization at 424c2a..424c72 sets:

- C+8=E+0x248: payload vtable d1cc68.
- Payload sentinel at payload+0x10=E+0x258, root at payload+0x18=E+0x260; first/last at payload+0x20/+0x28=E+0x268/+0x270 initially sentinel; count payload+0x30=E+0x278 initially zero.
- C+0x40=E+0x280: auxiliary owned string with inline buffer C+0x50.
- C+0x60=E+0x2a0: presence byte set to 1 at 424c72.

424c7c reads the auxiliary string; 424c7f..424cbf invokes payload virtual+0x10. Original relocation d1cc78 resolves to 34ecd0, the already established controller-file ordered payload parser. Non-1 read tags clear presence and destroy former contents if needed. For versions below22 this parser is skipped: this receipt does not newly prove all constructors' default flag values or arbitrary reused-entry behavior.

## Conversion and exact final argument order

| Edge | M+148 route | M+160 route |
|---|---|---|
| Output array class metadata | d35598+98 at36ef15 | d35598+a0 at36f70b |
| NewObjectArray | 36ef3f | 36f735 |
| Geometry E+28 ->36a6e0 | 36f1ad | 36f99d |
| Gate E+238==1 | 36f2f0 | 36faf0 |
| E+1f8 ->361740 | 36f311 | 36fb11 |
| Gate E+2a0==1 | 36f316/36f362 | 36fb16/36fb62 |
| E+248 ->365a10 | 36f337 | 36fb37 |
| E+2a8 ->374750 | 36f399 | 36fb99 |
| Final constructor descriptor | d35598+98 at36f3a5 | d35598+a0 at36fba5 |
| Constructor helper364a60 | 36f3ea | 36fbea |
| SetObjectArrayElement | 36f607 | 36fe07 |

Each result array length comes from the corresponding vector byte span divided by0x348 using the existing inverse-multiply arithmetic and jint width. Both loops visit entry addresses in vector order and increment by0x348. Identifier strings come from E+8/+0x10, 0x20 stride, producing the separate first argument String array. No identifier selection lookup is added here.

At each final call, before the first push, the argument references are:

1. RCX=stack+0xa0: identifier String array.
2. R8=stack+0x20: geometry result.
3. R9=stack+0xd0: 361740 result, or null if E+238!=1.
4. Stack argument from original stack+0x70: 365a10 result, or null if E+2a0!=1.
5. Stack argument from original stack+0x100: 374750 result.

The first push at36f3df/36fbdf supplies argument5; the second push at36f3e6/36fbe6 uses adjusted stack+0x78, hence original+0x70 for argument4. This avoids swapping controller and texture inputs. Absent optional paths explicitly zero their result wrappers (36f340..36f37b and36fb40..36fb7b). A present but empty native payload still goes through its converter; it is not treated as absence by these gates.

361740 adds8 to its payload pointer at361762 and passes the retained vector header to361ba0 at361773; the resulting Java map goes into d355b0+0x60 constructor at3617a6. This is one file-wrapper object, not the raw map or an Animation array passed directly to the final carrier. 365a10 converts its ordered payload into a map; d355b8+0x38 at365c42, call365c69, constructs the controller-file wrapper. The latter slot's exact Map constructor is pinned by prior animation-controller-metadata.json. Auxiliary source strings E+218/E+280 are not read by the immediate converter setup: these inputs pass nested payload E+1f8/E+248 instead. No broad unused-field claim is made.

## Separate texture input boundary

T=E+0x2a8 is supplied to374750. It always calls375430 with T+0x10=E+0x2b8 at37476a..76. Consequently375430's nested buffer at argument+8 is E+0x2c0, exactly the byte-buffer field read by42496b through reader+0x58. Fields E+0x2e0/+0x2e4 are read through reader+0x10 at42497b/98b; >=23 additionally reads E+0x2e8/+0x2ec, otherwise explicitly sets both to1. The trailing map at E+0x310 is filled by411a10 at4249d1. E+0x2f0 is another owned string read earlier at42495b. Its semantics are not inferred here.

375430 allocates a counter-derived handle using atomic xadd at37544d and constructs a Java object through d355c0+0x38 at37548b. It stores the result in its output wrapper+0x20 at3754bb. Its immediate data path calls buffer virtual+0x18/+0x20 for pointer/length at3754f9/375505, allocates destination storage through4c4aa0, and calls5767d0 to copy that length at375543. The transitive texture registry and codec details are outside this cohort; prior texture registry d348b0 remains distinct from geometry registry d341b8.

374750 inspects T+0x80=E+0x328. If nonzero it builds a Java map, walks T+0x78=E+0x320 linked nodes, selects reference keys for numeric1 or2 at374838..48, and calls375430 again with node+0x18 at3748c6. It then invokes method metadata d355c0+0x48 on the primary Java object with that map at3749ea. No named texture subtype is inferred from these numeric keys. The method return is not used as the final carrier input: the original primary output wrapper remains the source of argument5.

## Ownership and stopping boundary

Wire read-mode parsers own and replace their nested strings/vector/tree storage. Converter calls borrow current E subobjects; the immediate final constructor receives Java references, not those native source addresses. On the ordinary successful construction path, local wrappers for texture, controller, animation, geometry and identifier array are released after the final object has been constructed; the final carrier is inserted into its route array and its local wrapper then released. Source E is not moved into the Java constructor by these instructions. JNI failures, Java constructor behavior, all exceptional cleanup and arbitrary mutation/reuse are not asserted.

Next concrete identity frontier: d35598+98/+a0 exact constructor metadata (and, if needed, d355c0+38/+48 exact texture identities). The animation/controller element schemas and renderer need no further expansion for this five-input join. Reproduction verifies7 original-byte windows,2 ELF relative targets and5 prior receipts; no original code, assets or JVM were executed and no repository files were edited.

[Evidence](NATIVE-VECTOR-MODEL-CARRIERS-EVIDENCE-2026-10-18.json). Raw excerpts and reproduction scripts remain external.

Later [exact carrier identities](NATIVE-VECTOR-CARRIER-METADATA-2026-10-18.json) join M+0x148 to the existing ProjectileModelData counterpart and M+0x160 to VehicleModelData, with [original Java retention limits](MODEL-INPUT-CARRIERS-RECOVERY-2026-10-17.md). No runtime construction is proven.
