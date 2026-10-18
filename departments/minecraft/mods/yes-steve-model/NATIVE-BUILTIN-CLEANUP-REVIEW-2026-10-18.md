# Independent builtin cleanup / notice-output review

Result: core static contract supported; no blocking semantic error found. Two precision qualifications must accompany the write/close summary.

## Verified findings

- At 3d68c0..3d68c7, RDI is global path object d352f8 and the direct call is 311020. The earlier builtin constructor spells the seven-byte suffix in instructions 3d5da3..3d5dbc, joins it to d35348 at 3d5de9, and transfers ownership into d352f8. CONFIGDIR/yes_steve_model is the upstream path provenance established by the companion path report; this review independently checked the builtin suffix and downstream argument identity, not all earlier JNI path extraction.
- Re-creation of the same builtin path is requested at 3d68eb, after cleanup. The d355f1 conditional at 3d6908 gates only the d34fd8 directory call. It does not locally guard cleanup or notice output. This is normal-path ordering, not proof of unconditional outer initializer entry; earlier exceptions can prevent reaching these calls.
- 311020 constructs traversal state with 310720, loops through 30fbf0, and removes the root through 310f50 -> 310e50 -> the remove import. The child loop contains dirfd/unlinkat with flags zero; openat/fdopendir establish directory traversal machinery. Initial errno 2 skips with zero result; errno 20 or 40 proceeds to root removal; other nonzero errors take an error path. This is a destructive operation boundary, not a read-only status check.
- Independently reconstructed d34f88 from the pinned immutable checkpoint's original-image-plus-patches view: pointer d34f98, length 10, inline bytes notice.txt. The 3d6930 join uses builtin as left and that child as right. 3d6946 supplies literal pointer 4386f and count 0x64 (100).
- 4dfb30 rejects unsigned count >= 0x4200001. Accepted maximum is 0x4200000. Open mode 0x34 survives the 0x7d mask, table entry 543f4 resolves to 2baf40 and literal 3ecbc = wb NUL. Intended open semantics therefore include create/truncate binary output.
- Open result is checked, stream-level write is attempted, then sync/flush and close. Error-state bits 0x4 and 0x1 and exception mask 0x5 are visible. Calls are normal-path sequencing, not proof every operation occurs after an earlier throw.

## Required precision

1. At 2f8def..2f8df2 the returned count is compared for inequality with the requested count. A short count is one error case; any mismatch takes the same badbit-setting branch. No exact low-level write syscall/count is established.
2. At 2e2751..2e275a the close wrapper returns nonnull only if the earlier 2e1d30 helper's return byte equals 1 AND the owned FILE close returns nonnull. fclose success alone is insufficient. The detailed termination-helper behavior was not inspected here.

## Independent byte provenance

Fresh checks validated all 23 binary windows listed in continuation-evidence.json against original ELF PT_LOAD file ranges and their recorded SHA256 values. An independent ELF dynamic-table/RELA/symbol-table calculation resolved all eight two-stage import chains: dirfd, openat, fdopendir, unlinkat, remove, fopen, fclose, closedir. The wb literal/table calculation and exact 100-byte payload hash were separately checked. This verifies static symbol identities, not actual runtime bindings.

Original image SHA256: 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22.
Checkpoint SHA256: 05122784aea6927c2a8f1d48a2fb16f98e73b0d3919ab48ea4b1725f76d106b1.
100-byte literal SHA256: 3b4af702f6e24db200a35f015230605c2f284b894f25d9de798b6e1d3ecd5141.

## Limits and scope

No target/native/JVM execution, guest resume, model/file-system success fixture, host directory enumeration/deletion, original asset decoding, or repository writes were performed by this reviewer. Only static evidence reading, independent binary parsing/hash checks, and this external review artifact were used. Complete traversal branches, symlink/race behavior, lower-level streambuf vtable targets, complete exception translation, filesystem outcomes, disk persistence, and outer initialization reachability remain unproved.
