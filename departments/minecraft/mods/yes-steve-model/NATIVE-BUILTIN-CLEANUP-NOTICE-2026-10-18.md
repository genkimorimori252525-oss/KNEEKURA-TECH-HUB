# Initialization cleanup and notice-output contract

Static-only continuation; original target never executed, checkpoint never resumed, no target/game files written. Prior NATIVE-INIT-PATH-CONSUMERS-2026-10-18.md is unchanged.

## Exact target identity

Pinned checkpoint05122784... contains native global path d34f88 with pointer d34f98, length10, bytes `notice.txt`. These inline-owned bytes identify the right operand at3d6924. Join3d6930 constructs <CONFIGDIR>/yes_steve_model/builtin/notice.txt. Call3d6946 passes that path, literal4386f, and exact byte count100 to4dfb30. The payload says the directory is cleared each game start in English and Chinese. NATIVE-BUILTIN-CLEANUP-NOTICE-IMPORTS-2026-10-18.json retains exact100 bytes, without decoding any assets.

## Cleanup is a real destructive operation boundary

Before recreating directories,3d68c7 calls311020 on global builtin path d352f8.311020 constructs a traversal context through310720, iterates via30fbf0, counts iterations, then calls310f50 to remove the root.310720 invokes openat at31077b with dirfd=-100 and this path, then fdopendir at31078e; two-stage ELF resolution confirms these imports.30fbf0 uses dirfd and unlinkat, including child unlinkat flags0 at30fc82; it can descend using openat/fdopendir. The full traversal branch domain is not modeled here. Root removal is310f50→310e50→remove at310e5c. This establishes recursive-removal intent from code, independently of the notice text.

311020 treats initial errno2 as absent (returns zero), errno20/40 as a case proceeding to root removal, and other nonzero errors as exception paths. Root remove returns success true on zero, false with cleared error on errno2, and propagates other errors. Directory-stream ownership and closedir are visible in310720; traversal iterator cleanup uses30e350. No directory entries, symlink behavior across every branch, race-free outcome or deletion success is asserted. Never model this as a harmless directory check.

## Bounded notice stream protocol

4dfb30 rejects unsigned length >=0x4200001 before normal IO. For length100 it constructs a stream at stack+28, enables error-state exception bits0x5, and inspects the path. When3194f0 indicates a parent component,31dc00 constructs its parent and313c20 requests parent-directory creation/status handling; that owned temporary is then destroyed.

4dfbe8 calls2e29e0 with path bytes and openmode0x34.2e29e0→2bafd0→2baee0 resolves mode through original jump table54324: entry0x34 leads to literal `wb`.2baffb invokes verified fopen(path,"wb"). Thus intended semantics include binary output and truncation/create, not read-only access or appending. Underlying FILE pointer is stored in its owner, with ownership byte+8 set1 only on success. Null open result causes stream failbit0x4 at4dfbfd..4dfc07.

4dfc17 calls2f8db0 with exact bytes/count. Its streambuf virtual call at2f8dec uses slot+0x60, then compares returned count with requested count at2f8def; any count mismatch (not only a short count) sets badbit0x1.4dfc21 calls2f89b0, whose streambuf slot+0x30 synchronizes/flushes and treats -1 as error.4dfc29 calls2e26c0; this terminates buffering and calls2bb030, which invokes verified fclose at2bb053 for an owned FILE, clears its stored pointer even on error, and returns null on close failure.4dfc2e..4dfc4b converts null to failbit0x4.4dfc55 destroys the stream. Exception paths include cleanup/rethrow and application-specific wrapping; full catch-type translation is not decoded.

These are source-backed stream-level write/flush/close contracts. Exact streambuf runtime vtable targets and the eventual lower-level write syscall/import chain are not yet resolved; do not claim a specific fwrite/write operation or one syscall of100 bytes. Full-count acceptance, flush success and close success are separate predicates. The close wrapper returns nonnull only when the earlier buffer-termination helper2e1d30 returns byte1 and owned FILE close succeeds (2e2751..275a); fclose success alone is insufficient. Even all three do not prove durable disk persistence.

## Reusable contract boundary

Any future virtual-IO scenario needs path-specific namespace entries and ownership, directory enumeration/deletion policy and resulting namespace changes; separate parent mkdir status; an open operation with truncation/create semantics; live FILE/stream identity; bounded payload/count and short-write states; sync/close failure; exception and destruction behavior. It must not import host contents or silently delete actual files. A scenario intended only to examine retained path values must stop before these operations rather than fabricate success.

Next unresolved identities: traversal entry/symlink branches and enumeration reads; concrete streambuf vtable write/sync targets; exact exception translation. These are narrower useful research tasks, not permission to broaden OS fixture success.

## Destructive-boundary caveat and precise trigger

The reviewed straight-line normal path performs cleanup at3d68c0..68c7 after temp/ysm directory handling and remote_model_info path retention return normally; no intervening local condition guards this builtin call. This does not prove the outer initialization routine is entered unconditionally, or that prior exceptions cannot prevent reaching it. The actual argument is the owned global path d352f8, source-derived earlier as CONFIGDIR/yes_steve_model/builtin. Cleanup precedes the separate recreation call on that same global at3d68eb. No real directory contents were inspected, enumerated, removed or otherwise changed, and no cleanup fixture was modeled. This destructive-operation finding supersedes any description of the later initialization phase as directory-only checks.

[Independent focused review](NATIVE-BUILTIN-CLEANUP-REVIEW-2026-10-18.md) checked23 original byte windows,8 import chains and the notice filename, with count-mismatch and close-termination refinements incorporated here. [Receipt](NATIVE-BUILTIN-CLEANUP-REVIEW-2026-10-18.json). This is a static semantic check, not a runtime test.
