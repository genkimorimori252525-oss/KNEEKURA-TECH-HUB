# Focused native → Java keyframe join review

## Findings first

No substantive contradiction found in the six-pair join or the five requested boundary claims. Bounded pass, conditional on the retained metadata callback payload receipts: callbacks were not decoded again.

Terminology correction in the older keyframe-element-contract/REPORT.md: “Enum identities ... unresolved” should say “selected object identities”. The declared easing field type o00o00ooO000OoOoooO0000O has original classfile access 0x0601 (public, interface, abstract), without ACC_ENUM; it is not an enum. No concrete selector-table identities or interpolation algorithm are concluded here.

## Independent evidence checked

The exact original SO and JAR SHA-256 values supplied for this review matched. Re-extracted nine authoritative original ELF-backed windows and disassembled them with objdump, rather than treating saved assembly as authority. Rechecked 51 individual instruction anchors for 17 manager descriptors, five metadata helper windows, seven bridge windows, all 17 declarations against original classfiles, and the three directly relevant class hashes. Reparsed raw-record, processor, and easing classfiles with the existing static classfile parser; compared available retained method bodies and independently inspected raw-init operand flow. All 120 mechanical checks passed. Pinned RawBoneKeyFrame.java SHA-256 independently matches bfe43d97ee48e6d55975b9576b289e1be7d837e35f3441f13c311cf82f496bb1.

## Six pair anchors

Native R14 is K+0xd0 (364bf7). For each entry below, the numeric/expression manager pair selects the exact private D / IValue fields read at the given original raw-init bytecode offsets, in expression-then-double invocation order. Pre and post each feed the three vector constructor operands in X/Y/Z source-candidate order.

| Role | Component | Manager pair | Helper call | Numeric/expression Java reads |
|---|---|---|---|---|
| preX | K+0x20 | +0xc0/+0xc8 | 364d4d | 19/15 |
| preY | K+0x58 | +0xd0/+0xd8 | 364d71 | 33/29 |
| preZ | K+0x90 | +0xe0/+0xe8 | 364d95 | 47/43 |
| postX | K+0xd0 | +0xf0/+0xf8 | 364dc6 | 90/86 |
| postY | K+0x108 | +0x100/+0x108 | 364df8 | 104/100 |
| postZ | K+0x140 | +0x110/+0x118 | 364e2a | 118/114 |

The exact obfuscated fields and classfile operands are preserved in independent-extraction.json. Source names are bounded counterparts, not recovered original symbols. Native helper kind 1 loads V+0x10 into XMM0 and invokes JNI +0x380 at 365575; kind 2 follows V+0x18 through parser facade 3742d0 and invokes object setter +0x340 through 365780. The writes are alternatives, not evidence both slots are populated. No numeric scale/sign conversion appears in this immediate native path.

## Boundary conclusions

- Flag: ECX saved at 364b91, movzbl of saved low byte to R8D at 364fb3, forwarded at 364fc3 through 3654b0 and JNI +0x398 at 36552c. This is low-byte forwarding, not a nonzero-to-1 canonicalization proof. The array overload loads Boolean local 1 at bytecode 4 and delegates at 5 unchanged. Original callers in the checked window supply 1/0/0.
- Timestamp: 364caa loads K+8 as double, 364cbd uses JNI SetDoubleField with manager +0xb0. The exact Java getter reads Oo0Oo0o00O00Oo0OOoOOoooo:D at bytecode 1 then d2f at 4. No time-unit multiplier is established.
- Missing second: test at 364da1 branches to manager +0x120 and SetBooleanField(true) at 364e70. Present path bypasses that store; no explicit false assignment was found in this loop. Java init reads that same Boolean at 62 and, when true, gets preValue at 70 and stores that exact reference into postValue at 73. The pre field is already published at 58; its nonnull guard at 1/4/7 can prevent rebuilding on later calls. This is identity aliasing, not merely numerical equality.
- Allocation: +0xa8 is a constructor descriptor whose class handle at descriptor+0 is used by NewObjectArray and AllocObject. JNI +0xd8 at 364c3c allocates the record without calling its constructor; the original constructor body exists and only invokes Object.<init>. Local allocation evidence cannot establish that no caller ever invokes the constructor, nor prove successful initialization or exception recovery.
- Axis flags: bytecodes 22/36/50 and 93/107/121 reload the same rotation local; 23/37/51 and 94/108/122 are true/true/false. This matches the pinned pre/post X/Y/Z preparation operands.

## Limits

No target/native/JVM/emulation execution; no callback redecoding; no assets; no repository modifications; no interpolation/runtime algorithm expansion. Metadata payload decoding/state restoration is inherited from the retained receipts, not independently reproduced by this static review. No runtime success, whole-source identity, global constructor nonuse, dependency copy/view behavior, selector object identity, complete cleanup, or numeric parity claim. Independent extraction and objdump outputs are retained beside this report; they are local research artifacts, not a repository promotion.

[Evidence](NATIVE-KEYFRAME-JOIN-FOCUSED-REVIEW-2026-10-18.json). Full raw extraction artifacts and reproduction scripts remain external. This report does not promote the central map or prove actual runtime success.
