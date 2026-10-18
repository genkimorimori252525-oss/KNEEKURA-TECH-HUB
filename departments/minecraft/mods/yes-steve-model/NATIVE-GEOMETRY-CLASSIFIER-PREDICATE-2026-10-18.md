# Geometry classification byte C: bounded arithmetic predicate

## Result
The previously unnamed C is an ordered six-record angle test. For each record, form the average of four supplied float3 values; subtract the average of those six record averages; skip a sufficiently short resulting direction; otherwise compare an angle derived from that direction and a separately supplied reference vector against90. C becomes1 on the first ordered angle above90, and0 if none passes. Only the direction length is divided out. The reference vector is not normalized here and is not named a normal by this evidence.

This closes a reusable arithmetic/control-flow recipe, not a visual classification name. It is not safely replaceable by a sign-of-dot-product test because binary32 division, clamp, acosf and rounded degree conversion precede the strict threshold.

## Input layout
At376c4a..376c58, RBX is current source-group+8 (begin); L=source-group+10 minus begin. If L!=0x480, branch376c6c reaches3774b0 and writes C=0. The prior zero-span test is also ORed into this rejection, and is redundant when L==0x480. No dereference of the component fields below occurs on the rejected branch.

For L==0x480, the code reads six indexed blocks, each0xc0 bytes. These mathematical names do not assign a wire class or visual role:
- P[i,j] is the binary32 triple at RBX + i*0xc0 +0x30+j*0x28, j=0..3.
- N[i] is the binary32 reference triple at RBX + i*0xc0 +0x10, +0x14, +0x18.
- i=0..5 in ascending order.

Exact four triple starts by record:
0:30,58,80,a8; reference10.
1:f0,118,140,168; reference d0.
2:1b0,1d8,200,228; reference190.
3:270,298,2c0,2e8; reference250.
4:330,358,380,3a8; reference310.
5:3f0,418,440,468; reference3d0.
All offsets are hexadecimal. MOVSD loads of the first two components carry two packed float32 lanes; they do not imply double arithmetic. ADDPS/MULPS and scalar ADDSS/MULSS/DIVSS/SQRTSS operate in binary32. All triples lie inside the0x480 span; this static observation does not validate the actual pointer's allocation extent.

## Exact arithmetic schedule
Let add,sub,mul,div,sqrt denote separate SSE binary32 operations under the ambient MXCSR, with no fusion or reassociation. Zero below is positive zero. For each component k, M[i,k] is its record average:

For x/y of record0 and z of every record:
    s=add(P[i,0,k],+0)
    s=add(s,P[i,1,k]); s=add(s,P[i,2,k]); s=add(s,P[i,3,k])
    M[i,k]=mul(s,0.25f)
For x/y of records1..5, the addition operand order is instead:
    s=add(P[i,0,k],+0)
    s=add(P[i,1,k],s); s=add(P[i,2,k],s); s=add(P[i,3,k],s)
    M[i,k]=mul(s,0.25f)
This distinction does not change ordinary finite addition but is retained for NaN operand selection, signed-zero/rounding concerns and exact source correspondence.

For every component:
    s=add(M[0,k],+0)
    s=add(s,M[1,k]); ... ; s=add(s,M[5,k])
    G[k]=div(s,6.0f)

All six record averages and G are computed before the tests. For each i ascending:
    D[k]=sub(M[i,k],G[k])
    xy=add(mul(D.x,D.x),mul(D.y,D.y))
    r=sqrt(add(mul(D.z,D.z),xy))
    if ordered(epsilon >= r): continue
    xyDot=add(mul(D.x,N[i].x),mul(D.y,N[i].y))
    dot=add(mul(D.z,N[i].z),xyDot)
    q=div(dot,r)
    lo=MAXSS(destination=-1.0f,source=q)
    clamped=MINSS(destination=+1.0f,source=lo)
    a=acosf(clamped)
    degrees=div(mul(a,180.0f),pi_f)
    if ordered(degrees > 90.0f): C=1; exit
C=0 after all six continue/fail.

This is a description, not an implemented reference program. The first test uses XMM3 for r; later tests use XMM0, but the operation order is the same. Dot arithmetic never divides by |N[i]|. Neither |N[i]|==1 nor nonzero is established by this slice.

## Exact constants
Original bytes interpreted little-endian binary32:
-3d170:0000803e0000803e0000000000000000, packed [0.25,0.25,0,0].
-482dc:0000803e, scalar0.25.
-482b8:0000c040, divisor6.
-4865c:bd378635, epsilon=9.999999974752427e-7 (bits0x358637bd).
-482bc:000080bf, lower clamp -1.
-4818c:0000803f, upper clamp+1.
-48578:00003443, multiplier180.
-48624:db0f4940, pi_f=3.1415927410125732 (bits0x40490fdb).
-48228:0000b442, strict threshold90.

No extra angular epsilon or tolerance is applied at the final threshold. The only explicit near-zero threshold is applied to r. Norm exactly epsilon skips. Degrees exactly90 does not set C.

## Imported function proof
Six CALLs at377041,377148,37721d,3772e7,3773b4,377481 target d14860. Its FF25 instruction uses slot d308b8; original slot value13d6ef0 points to a second FF25 thunk using184d0d8. The original dynamic relocation is R_X86_64_JUMP_SLOT for acosf@GLIBC_2.2.5, symbol index0x1c, addend0. reproduce.py verifies both displacements, the intermediate pointer, every CALL displacement, and the relocation line via readelf --use-dynamic.

This proves the requested imported symbol, not the runtime-resolved implementation, symbol interposition absence, a specific libm rounding guarantee, or a successful call. The original function was not invoked.

## Comparison, NaN and output details
The skip instruction is UCOMISS epsilon,r followed by JAE. In the ordered case epsilon>=r sets CF=0 and skips. Unordered comparison sets CF=1, so NaN r does NOT take the skip branch; it proceeds to dot/div/clamp/call. This must not be encoded as simply `if (!(r>epsilon)) skip`, which would incorrectly skip NaNs.

MAXSS(-1,q) and MINSS(+1,lo) use the indicated source operand on unordered cases. Thus a NaN q is passed through these operations rather than replaced with a finite endpoint. On ordinary inputs they clamp to[-1,+1]. SNaN/quieting and exceptions remain subject to instruction and runtime floating-point behavior; no exception masks or MXCSR mode are established here.

After degree conversion UCOMISS degrees,90 followed by JA accepts only ordered greater-than. Equality or unordered results do not accept. For conventional nontrapping NaN propagation, a NaN angle does not set C and testing proceeds. The report does not claim malformed inputs always return normally: floating exceptions or external acosf behavior can interrupt processing.

Each angle path executes MOV AL,1 then the store [frame+c] := EAX before its final compare (377091,377186,377245,37730f,3773dc,377498). Only the low byte is guaranteed1; upper bits of this provisional dword are not specified. A successful JA exits to3774b8 with that byte1. A failed test proceeds to another test, and final failure or final short-direction skip reaches3774b0, overwriting the entire dword with0. Thus C here means the eventual low byte at frame+c, not a function return value and not a claim that every provisional dword equals1.

## Authored reference and boundary

A [bounded authored reference](NATIVE-GEOMETRY-CLASSIFIER-REFERENCE-2026-10-18.md) now implements this arithmetic dependency recipe with explicit binary32 rounding, SSE source-on-unordered clamps, ordered comparisons and injected acos provenance. It passes13 focused and4 independent authored checks. The reference does not execute original code or parse original assets. RN-even/gradual-underflow assumptions and the unknown target acosf/MXCSR remain explicit; it is not a bit-exact native execution oracle.

No target/native/JVM/guest execution, asset input, runtime fixture or checkpoint restoration was used for this source analysis. Evidence contains the original classifier bytes, constants, import chain and pinned image SHA256. Reproduction PASS verifies6 byte ranges,9 constant spans and6 call targets. Floating environment, external libm exactness and visual interpretation remain bounded.

[Source constants, windows and import evidence](NATIVE-GEOMETRY-CLASSIFIER-PREDICATE-EVIDENCE-2026-10-18.json). Raw windows and reproduction script remain outside Git.
