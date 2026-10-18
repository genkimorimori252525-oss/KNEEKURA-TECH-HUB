# FMLPaths.CONFIGDIR: bounded receiver/path modeling plan

## Recommendation

A generic typed object/path model is worthwhile for this small JNI frontier, but an explicit virtual path scenario is required first. The existing initialized forgeclient fixture does not establish FMLPaths setup or a real game/configuration directory. Do not automatically extend that boolean to populate absolutePath. Recommended first scope: a declared FMLPaths setup state with a supplied normalized absolute virtual Unix-path value, bounded ASCII component domain, no filesystem claims; unknown receiver/provider/path states must stop.

No model was implemented and no checkpoint resumed. Both pending workers remain unexecuted in the unchanged source checkpoint. This is a plan supported by original classfiles, native bytes and zero-instruction checkpoint data reads.

## Exact immediate native contract

Checkpoint SHA256 05122784aea6927c2a8f1d48a2fb16f98e73b0d3919ab48ea4b1725f76d106b1. Its stopped stack return address is 3d54ed. Original instruction 3d54e7 is JNI GetStaticObjectField. checkpoint-slots.json joins original global-slot loads to preserved field/method metadata:

1. d35588+38: FMLPaths.CONFIGDIR:Lnet/minecraftforge/fml/loading/FMLPaths;, static. A typed enum-object reference is required, not a class handle or a Path handle. Native nonnull check 3d54ed..f0.
2. d35588+40: FMLPaths.absolutePath:Ljava/nio/file/Path;, instance field. GetObjectField at3d5568 receives the object from step1. Native nonnull check3d556e..71.
3. d356e0+58: java/nio/file/Path.normalize()Ljava/nio/file/Path;. Call3d55e8 through36d530→CallObjectMethodV JNI+118 at36d5ac. Receiver is step2, no Java arguments. Native checks nonnull.
4. d356e0+48: java/nio/file/Path.toString()Ljava/lang/String;. Call3d57bc through the same generic invocation helper. Receiver is step3, no Java arguments. Native checks nonnull.
5. String extraction4192b0 called3d581f: GetStringUTFChars JNI+548 at4192d2; GetStringUTFLength +540 at4192e9; copies exact modified-UTF8 byte length into owned native string and releases the borrow via JNI+550. This is a string/borrow lifetime contract, not permission to treat arbitrary objects as strings.
6. 3d5841 passes extracted bytes/length to35c9c0. Native constructs the literal 15-byte child name `yes_steve_model` at3d5850..5877 and passes both path values to35caa0 at3d58a5. No actual prefix path is present in these original instructions. Stop this proposed first model before expanding subsequent filesystem-dependent operations or inferring directory existence.

The native sequence does not call Path.toAbsolutePath. That operation appears in Forge's producer of absolutePath, below. Exception checks and local-reference deletion must continue through the existing generic JNI semantics; none may be replaced by per-address success returns.

## Source-derived facts versus scenario inputs

Pinned fmlloader-1.20.1-47.4.0.jar SHA256 d17c218af5c62fa4928019614aa8a5075279f8545efe21325baf46b80f4a5ac9; FMLPaths class SHA256 c8fc0d33845a5aa3c285115f320cf23dc016fe0cdab183dd2cd3e8d8257675c5.

- FMLPaths extends Enum. CONFIGDIR is a public static final enum field, access0x4019. `<clinit>` offsets35..54 constructs it with literal name CONFIGDIR, integer2 and component array containing literal `config`. The integer is constructor metadata, not a source of a configuration-directory path.
- The constructor `(String,int,String[])` computes relativePath using computePath→Paths.get and sets isDirectory=true. It does not assign absolutePath. absolutePath is private mutable instance field (access2), with default-null state until separately assigned.
- setup(IEnvironment) reads environment property key GAMEDIR, then Optional.orElseThrow; missing input constructs RuntimeException("No game path found"). setup calls loadAbsolutePaths with that external Path. Neither this property nor its value follows from the forgeclient production/dist fixture.
- loadAbsolutePaths bytecode27/32/37/42 sets each absolutePath to supplied gamePath.resolve(relativePath).toAbsolutePath().normalize(). It then conditionally checks Files.isDirectory and may call Files.createDirectories; IOException is wrapped in RuntimeException. The assignment precedes those filesystem operations, so observing or declaring the field alone is not proof successful complete setup or existing directories.
- For CONFIGDIR under ordinary declared Unix provider semantics, the relative suffix is source-derived `config`. The base game path, provider/filesystem identity, default directory when resolving relative input, setup phase, encoding and relevant exception state require explicit fixture inputs or stronger evidence. No actual host values may be borrowed silently.

Pinned java.base.jmod SHA256 f8d258a856a691c81ad9dd16964635bbc8a8fdd7f40edec37dcf3d904feb7ae1; Path class SHA256 a742da0be8612380a06ebd1b770f2554567fd0cf34e90398b5fc5797604c5e66. Its normalize/toString/toAbsolutePath declarations do not determine concrete receiver implementation. The archived UnixPath/UnixFileSystem classfiles provide one available implementation, not proof any installed game uses it.

UnixPath.normalize uses component operations, can return this (including unchanged path at bytecode339..340), or construct a new path; it is not a universal identity method. UnixPath.toString decodes stored bytes via Util.toString and UnixFileSystem.normalizeJavaPath, caching the string. Pinned UnixFileSystem.normalizeJavaPath returns its input. UnixPath.toAbsolutePath returns this for absolute paths; relative paths require filesystem.defaultDirectory and may check SecurityManager access to user.dir. Those extra dependencies need not be modeled if the declared receiver domain is already absolute and normalized, but they must not be silently assumed for general paths.

## Proposed generic model and finite tests, not implementation

1. Add a separately declared immutable scenario configuration for FMLPaths state: class-initialized-only with null absolutePath, or explicit populated absolutePath plus provider identity. Do not reuse FMLEnvironment initialized=true as this precondition. To derive from a gamePath, require that explicit virtual path and a declared setup-state snapshot; derive the literal config suffix algebraically, with no simulated filesystem success.
2. Use typed object identities in a side table: FMLPaths enum singleton, concrete bounded Path value (provider identity, absolute flag, normalized components and encoding), and Java String value. Distinguish object identities from local/global reference handles; returning this may produce an alias local reference, whose deletion must not invalidate another live reference.
3. Dispatch by verified owner/name/descriptor, method staticness and compatible live receiver type, never by native PC. GetObjectField resolves only the actual modeled receiver's absolutePath field. normalize accepts the explicitly supported path domain and returns the mathematically correct value/identity; initially an already-normalized ASCII absolute domain can be checked and preserved. Unsupported providers, relative paths, dot/dot-dot cases outside the audited domain, unknown identities or deleted handles stop rather than receive guessed values.
4. toString returns a typed String from the supported path encoding. Implement/retain generic modified-UTF8 length, byte borrowing and release tracking, with exact length and null termination rules. ASCII-only fixtures make ordinary UTF8 and modified-UTF8 coincide, but that must remain an explicit restriction, not a global conversion claim.
5. Proposed authored unit cases: separate FMLPaths setup flag, null absolutePath, wrong class-vs-object receiver, wrong field/staticness, normalized path identity aliasing, release of one alias while another remains live, exact String byte length/borrow-release, unsupported provider/relative/non-ASCII cases, pinned metadata/hash mismatch, and unchanged original checkpoint. They would test the authored model only, not original initialization or filesystem effects.

Decision needed before implementation: choose the bounded virtual provider/path/setup-state inputs. Without them, keep the existing CONFIGDIR stop. A path-only continuation can establish deterministic reference and string dataflow; it cannot establish a working Forge installation, successful native initialization, or real filesystem outcomes.

## Evidence

class-evidence.json contains original declarations, complete parsed method instruction records and hashes for FMLPaths, Path, UnixPath and UnixFileSystem. inspect_classes.py only reads archives using Python. checkpoint-slots.json and inspect_checkpoint.py reconstruct immutable checkpoint bytes/recorded metadata without a CPU or guest instructions. Source-backed native windows and their hashes are in evidence.json; all original inputs/checkpoint hashes were rechecked after reading. Exploratory 3d5480 window starts mid-instruction and is expressly not an authoritative range.

[Evidence](NATIVE-FORGE-PATH-MODEL-PLAN-EVIDENCE-2026-10-18.json). Raw excerpts and reproduction scripts remain external.

Implementation decision: a separate explicit virtual Unix/ASCII normalized-path scenario is being implemented and tested. The authored example game path is /fixture/ysm-game, not an observed user/host path. No main checkpoint has yet resumed under this new model; populated absolutePath is not filesystem/setup success.
