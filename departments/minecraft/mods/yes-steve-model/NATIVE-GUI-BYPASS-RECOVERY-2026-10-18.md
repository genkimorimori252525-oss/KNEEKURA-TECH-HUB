# GUI bypass: finite dispatch and batch-header contract

Original-byte static analysis only. The GUI branch consumes the existing masked geometry batch sources. Codes 2–6 rejoin previously covered wrappers. Code 1 uses two additional callback bodies with eight matching begin/end decode sites. Output staging differs, so this is not a rendering-equivalence claim. The prior 28-site non-GUI receipt is preserved unchanged.

## Entry and dispatch

After 37bd80 returns, 3bffec..3bfff8 requires nonzero global d34c30 and the tested return bit. At 3c0032..3c0046 the GUI bypass further requires stack byte +89 nonzero and geometry payload byte +54 nonzero. At 3c0f80..3c0fe8 EBP nonzero selects 385390; zero selects 385080. Both pass the same caller stack adapter (+20), auxiliary pointer (+70), normalized stack byte +c, and worker object R14. These are concrete selector uses; this cohort does not independently rename the Java parameters.

Each wrapper calls 398e50 with incoming RDI/RSI and EDX=ECX, subtracts one from its returned code, and uses unsigned <=5 gating. Other codes return. Tables 57d58 and 57d70 contain six signed 32-bit offsets relative to their own table base; exact original bytes and decoded destinations are pinned in evidence.json.

| Code | 385080 table destination | 385390 table destination | Terminal immediate route |
|---|---|---|---|
|1|3850bc|3853cc|callback 386fb0 / 3856a0 respectively|
|2|3851a5|3854b5|384740 -> previously covered 38a580|
|3|385163|385473|384430 -> previously covered 38dbe0|
|4|385184|385494|383e10 -> previously covered 394890|
|5|385142|385452|384120 -> previously covered 391230|
|6|3851c6|3854d6|384a50 -> previously covered 388a20|

Codes 2–6 tail-jump with RSI=incoming adapter+20, original RDI, RDX=original RDX and RCX=original R8. Exact wrapper-to-producer edges are inherited from render-backends receipt rather than retraced.

## Code 1 ownership and buffers

3851f9..385238 and 385509..385548 build a temporary callback context: +0=&d34b40 (existing render work aggregate), +8=&stack output pointer returned by 398760, +10=original RDX. The callback pair holds function 386fb0 or 3856a0 and that context. The pair is published at incoming worker+20. Pending count at worker+c0 increases by the signed-low32 interpretation of (worker+8 - worker+0)/8, and generation at +40 increments. The wrappers spin on pending count and clear +20 after zero. Static installation/waiting is not proof workers execute, finish, or cannot fail.

The code 1 callbacks obtain the work aggregate from context+0. The first list has begin/end at aggregate+70/+78 and nonzero count gate +88; its 24-byte work record +8 holds the borrowed external-item container. That container has batch begin/end at +0/+8 and flag +20. The other list headers are +90/+98, +b0/+b8, +d0/+d8, gated by +a8/+c8/+e8. These match the existing work-aggregate family rather than an unrelated GUI asset buffer. Work partitions are computed from list byte span /24 and worker index/count using integer multiply/division; the scoped callback does not establish a nonzero worker-count guarantee.

For example 38581e..385849 loads work record/container/batch bounds; 385f90 advances another batch cursor by 0x38. Data records are advanced by 0x5c (385990,386250,3865a0,386f9b and corresponding zero-mode sites). No batch ownership transfer is introduced by these reads.

The output side does use staging buffers: 3850bc..385138 and 3853cc..385448 request destination via 398760, size d34268 using 36*d34c38, and resize d34288..d34290 to d34c38/4 eight-byte entries. After callback completion, 381d70 processes that index span; the wrappers copy 0x90 bytes per index from d34270 +36*uint32(index) into the destination (385300..385375 and 385610..385685). This immediate output-buffer distinction does not change the proven masked input header contract. Sorting semantics and full emission are outside scope.

## Eight additional header sites

[GUI coverage matrix](NATIVE-GUI-UNMASK-MATRIX-2026-10-18.md) gives exact decode ranges, equality gates, and quota loads for both callback bodies. All eight reconstruct:

- begin = LE64(V+0) XOR LE64(V+0x1d)
- end = LE64(V+8) XOR LE64(V+0x25)

The verified straight-line blocks use the same byte/dword XOR loads, two pshufb operations and two pshufd(0xee) assemblies as the earlier 28-site cohort. All reach begin/end equality gates. None of these decode blocks reads state V+0x1c, encoded capacity V+0x10, or capacity mask V+0x2d; none branches or calls within the reconstruction. Immediate quota V+18 loads occur at sites 1 and 3 in each body; no such load appears in the inspected immediate prefixes of sites 2 and 4. No new address, allocation-extent, ordering, divisibility or authentication validation is present in the decode blocks. This does not rule out checks elsewhere or assert memory safety.

## Reproduction and limits

Run reproduce.py to verify the pinned original SO hash, generate source-backed disassembly, assert all eight decode shapes/equality gates, and verify both dispatch tables. evidence.json records exact ranges, backing offsets and SHA256 hashes; prior receipts are hashed. Only evidence.json-listed windows are authoritative; older exploratory files in this directory are not evidence of instruction boundaries.

Finite coverage now consists of the preserved seven non-GUI producer bodies/28 sites and these two GUI code-1 bodies/eight sites. GUI codes 2–6 reuse existing bodies. This does not inventory every function in the ELF or prove runtime backend selection, worker completion, full emission equivalence, upstream quota validity, or pointer lifetime/race safety. The remaining frontier is worker execution/preconditions and output-emission semantics, deliberately not expanded here.

Evidence: [NATIVE-GUI-BYPASS-EVIDENCE-2026-10-18.json](NATIVE-GUI-BYPASS-EVIDENCE-2026-10-18.json). [Non-GUI coverage](NATIVE-GEOMETRY-UNMASK-COVERAGE-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
