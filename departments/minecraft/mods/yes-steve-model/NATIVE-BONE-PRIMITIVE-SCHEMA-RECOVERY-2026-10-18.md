# Bone list item: counted fixed records, no shape-tag dispatch

## Result

3489f0 parses each0x28-byte item in the bone B+0x28 vector. The item itself contains another counted vector of0xc0-byte records followed by three boolean bytes. Each inner record reads23 float32 scalars in fixed order:3, then4 groups of5. No serialized shape tag, cuboid dimensions, JSON key, normal/position/UV naming, or shape-discriminator switch is established in this path. Vtable addresses identify native types, not wire tags.

Static-only original-byte work; no target/JVM/emulator/assets/repository edits. reproduce.py PASS:6 aligned original-code selections and4 original ELF RELATIVE records. Original SO SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. Prior modern receipt is checked unchanged at SHA2562ff0539314ec44ea0b673108268627bc122e9afe20b8188c50681414d70c83e0. evidence.json is authoritative; exploratory address-named files are not fully reviewed function claims.

## Item layout and serialized ordering

Let H be a0x28-byte item, R the reader with readmodeR+8==1.

- H+0: vtable d1cd08, RELATIVE slot d1cd18->3489f0.
- H+8,+0x10,+0x18: begin/end/capacity of0xc0-byte records Q.
- H+0x20,+0x21,+0x22: three boolean fields with no newly assigned meanings.

At348a13..348a49 old inner elements are destroyed with stride0xc0 and end reset.348a4d..348a61 reads varuint count through reader slot+0x10. Zero count skips directly to the three flags. For each record, temporary Q starts at rsp+0x28.348b66..348c33 initializes its embedded vtables and scalar fields;348c38..348c8f performs all payload reads;348a90..348b57 copies fields into retained storage and adds0xc0 to end. Growth publication is348f16..348f35. After the inner vector,348f53..348f7d reads flags H+20,H+21,H+22 via reader slot+0x40.

The previous modern receipt independently verifies reader+0x10 as the bounded five-byte varuint helper and reader+0x40 as exactly one byte accepting only0/1. Item flags therefore consume3 bytes on successful parsing.

## Inner record and immediate parser dispatch

Temporary construction installs:
- Q+0: d1cd30, whose slot+0x10 RELATIVE d1cd40 resolves3490b0.
- Q+8: d1cd58, whose slot+0x10 RELATIVE d1cd68 resolves349060.
- Q+0x20,+0x48,+0x70,+0x98: d1cd80, whose slot+0x10 RELATIVE d1cd90 resolves349010. Each embeds d1cd58 at its own+8.

The read branch calls349060 directly on Q+8 at348c41, then virtual+0x10 on Q+20,Q+48,Q+70,Q+98 at348c53,348c63,348c79,348c8f. The record's3490b0 virtual reader independently repeats those same five subobject dispatches, confirming that read and nonread paths share the structural sequence.

349060 reads three scalar fields at its argument+8,+0xc,+0x10 using reader slot+0x28.349010 first dispatches its embedded+8 subobject (349060), then reads scalar+0x20,+0x24. The prior receipt independently verifies reader+0x28 requests4 raw bytes directly into destination. No version gate or discriminator occurs in either immediate scalar helper.

Exact destination offsets in Q, in wire order:

1. Q+0x10,+0x14,+0x18
2. Q+0x30,+0x34,+0x38,+0x40,+0x44
3. Q+0x58,+0x5c,+0x60,+0x68,+0x6c
4. Q+0x80,+0x84,+0x88,+0x90,+0x94
5. Q+0xa8,+0xac,+0xb0,+0xb8,+0xbc

Consequently each Q consumes exactly92 payload bytes when these reads succeed, although its native stride is192 bytes because it contains vtables, padding, and subobjects. A successful H consumes encodedCountLength +92*count +3 bytes. This arithmetic describes only H and does not constitute a complete model decoder or malformed-input guarantee. Count representability, allocation success, stream truncation, and float validity are not newly certified.

## Smallest useful next consumer selections

A read-only scan of the already-existing geometry-build excerpt identifies a narrow next cohort inside375e30, without retracing the renderer:

-377501..377613: loads inner begin/end from group+8/+10, advances source by0xc0 at3775e6, and shows packed destination stride0x5c at3775e2. This is the immediate candidate for exact pointer joining.
-377613..377684: selects a branch and reads the four last-two-scalar pairs at Q+40,+68,+90,+b8. The following math scales these by another object's integer pair; those external inputs need provenance before naming the pairs.
-377e34..377ebe together with377560..3775fb: loads Q's first triplet and each three-scalar component, then stores a23-scalar packed record. This can establish the concrete packing map before semantic names.

These are proposed bounded selections, not a newly hashed consumer proof. First pin source pointer provenance into377501, then track those scalar loads into one packed-output path. Only after actual consumer use is proven should names such as position, normal, or UV be considered. No claim of a six-faced cuboid follows from this parser; inner count is variable.

Evidence: [NATIVE-BONE-PRIMITIVE-SCHEMA-EVIDENCE-2026-10-18.json](NATIVE-BONE-PRIMITIVE-SCHEMA-EVIDENCE-2026-10-18.json). Related [modern model/bone schema](NATIVE-MODERN-MODEL-SCHEMA-RECOVERY-2026-10-18.md). Raw ranges and reproduction scripts remain external.
