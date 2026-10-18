# YSM2.6.5 provider contract index

Use [NATIVE-PROVIDER-CONTRACT-INDEX-2026-10-18.json](NATIVE-PROVIDER-CONTRACT-INDEX-2026-10-18.json) as a navigation and scope index, not a decoder or fresh semantic audit. Every referenced receipt has its current SHA256 pinned. Numeric offsets are hexadecimal unless explicitly stated otherwise. Context letters are local to each receipt.

| Selector | Entry | Returned pair | Fourth-byte evidence |
|---|---|---|---|
|1|4c8150, direct case|Supplied pair|Bytes preserved; format unknown|
|2|4ceab0|PNG IHDR width/height|Exact RGBA8 on successful output path; byte3 is alpha|
|3|4ce470|Supplied pair|Traced mode12 candidates synthesize255; alternate setup/precision remains open|
|4|4d3ff0|Supplied pair|Conditional plane overwrite at byte3; alternate converter596090 remains open|
|5|4cad00|Context pair copied through619290|Conditional fill/copy/scale stage at byte3; subsequent paths remain open|

Selectors2–5 are static registrations at registryd35cb8; selector1 bypasses that registry. No runtime selector or successful image decode was observed. Neither common four-byte storage nor a fourth-byte consumer establishes universal RGBA semantics.

Allocation/pitch caveat: selectors3/4 use the supplied pair for allocation and pitch while internal dimensions govern processing. Selector5 returns a context pair but allocates/pitches from the supplied pair. Their equality is unproved. Selector2's contiguous allocation and separately narrowed recorded size also require the receipt's arithmetic qualifications.

## Authoritative receipts for each claim
- [Registration, selector1 copy and initial provider provenance](NATIVE-PROVIDER-OUTPUT-FORMAT-RECOVERY-2026-10-18.md)
- [Selector2 exact PNG/RGBA8 contract](NATIVE-PNG-OUTPUT-CHANNEL-RECOVERY-2026-10-18.md), with pinned [W3C PNG specification](https://www.w3.org/TR/2025/REC-png-3-20250624/)
- [Selector3 entry/pitch](NATIVE-SELECTOR3-CHANNEL-BOUNDARY-RECOVERY-2026-10-18.md) and [conditional callback stores](NATIVE-SELECTOR3-CALLBACK-RECOVERY-2026-10-18.md)
- [Selector4 bounds/output](NATIVE-SELECTOR4-OUTPUT-RECOVERY-2026-10-18.md) and [fourth-byte scatter](NATIVE-SELECTOR4-FOURTH-BYTE-RECOVERY-2026-10-18.md)
- [Selector5 output stage](NATIVE-SELECTOR5-OUTPUT-RECOVERY-2026-10-18.md) and [nearest pair writer](NATIVE-SELECTOR5-PAIR-PROVENANCE-RECOVERY-2026-10-18.md)

Earlier broad receipts are chronological: their unresolved format statements are refined only for the specific branches covered by later receipts. Consult the later provider-specific report for current scope. Do not turn selector4/5 stage evidence into a universal final-buffer assertion, or selector3's255 into semantic alpha/channel names.

Repository integration verifies five selectors and all16 local report/evidence hashes. Original external validation scripts remain external; this navigation validation does not repeat a semantic audit.
