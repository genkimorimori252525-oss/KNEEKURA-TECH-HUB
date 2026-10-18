# Native raw-keyframe field pairs → original Java preparation

Static/guarded metadata bridge only. Original JAR methods were reparsed and matched to retained EASING-RAW-FACTORY evidence; no target Java execution, runtime-success claim, or central mapping promotion. Readable names below are pinned source counterparts, not original symbols.

## Twelve exact fields

All belong to com/elfmcys/yesstevemodel/ooOooo0oOooOO0O0O00000oO; all are private instance fields (access 0x0002). All expression fields have descriptor Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;. Numeric fields have D.

- preX/preXValue: K+0x20; manager 0xc0/0xc8; `O00OOOooOoooOoo0o0o0oO0O:D` / `oOOOo0OOO0ooooo0O00OO0o0:Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;`; exact raw-init reads at bytecode 19/15; native helper call 0x364d4d.
- preY/preYValue: K+0x58; manager 0xd0/0xd8; `OOOOo0O0oO0OOo0O0O0Oo0O0:D` / `Ooooo0oooO0oooOOOoO0000O:Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;`; exact raw-init reads at bytecode 33/29; native helper call 0x364d71.
- preZ/preZValue: K+0x90; manager 0xe0/0xe8; `oo0OoO00oOoo000O0000o0oo:D` / `oooooooOOoOOoO00OooOo00O:Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;`; exact raw-init reads at bytecode 47/43; native helper call 0x364d95.
- postX/postXValue: K+0xd0; manager 0xf0/0xf8; `Oo00o0OooOOo0ooOoo0oO0o0:D` / `o0OOO0o0o0OOo000oO00o00O:Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;`; exact raw-init reads at bytecode 90/86; native helper call 0x364dc6.
- postY/postYValue: K+0x108; manager 0x100/0x108; `O0OooOo0oOOoOoOoOooO000o:D` / `ooOO000o0O0OOOoO0Oo0o0Oo:Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;`; exact raw-init reads at bytecode 104/100; native helper call 0x364df8.
- postZ/postZValue: K+0x140; manager 0x110/0x118; `OOOo0OOOoOO0O00Oo00ooOOO:D` / `oOo0o0000OOOO0OooooO00oo:Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;`; exact raw-init reads at bytecode 118/114; native helper call 0x364e2a.

## Native storage and field writes

The existing record parser proof establishes mandatory components K+0x20/+0x58/+0x90 and optional components K+0xd0/+0x108/+0x140. Its nine original-byte windows were rehashed. Joining the exact fields to original raw-init operands supports the bounded preX/preY/preZ and postX/postY/postZ source correspondence; this does not rename raw wire fields globally.

Helper 0x365540 examines V+8. Kind 1 loads double V+0x10 and invokes SetDoubleField at 0x365575 using the numeric descriptor. Kind 2 passes the string at V+0x18 to parser facade 0x3742d0 with ECX=0, then sends the returned object through 0x365780 → SetObjectField at 0x3657a0 using the expression descriptor. These are alternative writes, not both fields being populated. Parser success or expression evaluation is not established. Wire numbers were read as float32 before promotion; this immediate double write performs no radians conversion, sign change, or unit scaling.

## Flag forwarding and original Java processor

Native 0x364b91 saves incoming ECX. 0x364fb3 zero-extends its low byte into R8D; 0x364fc3 forwards the object array and that Boolean argument through 0x3654b0 / CallStaticObjectMethodV to the exact public static array overload. That method calls ReferenceArrayList.wrap then forwards the Boolean unchanged to the List overload. The List overload iterates each raw frame and invokes its (Z)V initializer before constructing output frames by list index. No local sorting appears. Dependency-specific wrap copy/view behavior remains unverified.

## Timestamp and contiguous alias

Manager +0xb0 identifies Oo0Oo0o00O00Oo0OOoOOoooo:D. Native SetDoubleField receives K+8 unchanged. The exact getter ()F reads this field and uses d2f at bytecode 4. Therefore factory calculations use the narrowed float getter values; no seconds/ticks multiplier is proven by this boundary.

Manager +0x120 identifies O0ooooOO0oOo000O0Oo00OOO:Z. Native missing-second branch writes true at 0x364e70; the present branch does not explicitly write false here. Original raw init reads this same Boolean at bytecode 62. If true, bytecodes 70/73 assign the exact preValue object to postValue, establishing reference aliasing, not merely equal values. Otherwise it builds a separate post vector from the second three pairs. PreValue is published at bytecode 58, before this branch. A nonnull preValue at entry causes immediate return, so later flags do not rebuild cached wrappers.

## RotationValue bridge

Original raw init passes the same rotation flag to all six component preparations. Exact Boolean constants at bytecodes 23/37/51 and 94/108/122 are true/true/false, matching source X/Y/Z flip parameters for both pre/post. With null expression reference, the helper narrows the numeric double to float; rotation calls processValue then wraps the result in FloatValue. A nonnull expression is returned unchanged for nonrotation and wrapped in RotationValue for rotation. Original processValue performs float→double, Math.toRadians(double), double→float, and optional negation; dynamic eval obtains the wrapped expression value before applying that operation. This proves the static path, not a successful runtime evaluation or numerical parity with a different radians implementation.

## AllocObject caveat

Manager +0xa8 is the public <init>()V method descriptor, whose resolved owner/class handle is consumed by NewObjectArray and AllocObject. The inspected loop calls AllocObject at 0x364c3c and populates fields; it does not invoke the constructor. Consequently source constructor comments are unnecessary to establish this local allocation path, and cannot prove global constructor nonuse. Java raw primitive/object defaults and later init logic must not be confused with constructor execution. Complete initialization, exceptional cleanup, and asset-driven behavior remain unproven.

## Evidence

- Bridge JSON SHA256: 4355c433f58b3530b24b3fdeba2fe17529e0e4f2e43630550df10281cbd14c9a
- Twelve-field receipt SHA256: 4ca7cf8fe41a3cb5e631ffce5240d8c333a53e83a291fb54d7e1124127e7361d
- EASING evidence SHA256: 6fa4b9ca2e36ee37adb5e081142e8936607ba67deb9acb485990c834b8bbac2b
- Repeated Java audit SHA256: 8f35835f97c8edb0eab58cbfd1c8fe699b679395a984acaa30c23f0f6982c400
- Prior native evidence SHA256: 6ec8596d4a65f5481b6472bcead4c641c8105abce4274c4434d7ee0655b26b9d
- Repeated existing audit: 162 checks and 16 negative controls, zero failures. Bridge independently matched all 27 retained original methods and five source hashes.

[Evidence](NATIVE-KEYFRAME-JAVA-BRIDGE-2026-10-18.json). Full raw extraction artifacts and reproduction scripts remain external. This report does not promote the central map or prove actual runtime success.
