# Selected Vineflower comparison — 2026-10-17

## Actual tool use

The owner's explicit request to use the Tech Hub tools when useful was followed
with a bounded Vineflower 1.11.1 comparison. The existing tool shelf was read at
PR #112 head `9899df9bbfe4b5aaf3568ee1eefa88da57cb2cf5`:
[tool-shelf documentation](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/9899df9bbfe4b5aaf3568ee1eefa88da57cb2cf5/departments/minecraft/mod-ai/reverse-engineering/README.md).
That PR was open/unmerged when inspected. No merge or copying its changes into
this research branch was performed. This run uses the shelf's explicit standalone
comparison runner, not a claim that a MOD-AI CAS profile transform was completed.

Vineflower was obtained from the shelf's pinned Maven Central URL, SHA-256
`a615d07ddbbcd489369674f40e42df639c32be95410890b38f173d5c1e2ea39c`.
The receipt records the wrapper/catalog hashes and observed OpenJDK version.
Only the decompiler JVM ran; YSM was not loaded as an application or executed.
No REA provider, CFR, target recompilation, game, network packet or native model
implementation was run. The chosen task is Java control-flow comparison, for
which adding unrelated engines would not establish stronger runtime evidence.

## Input and result boundaries

Eight unchanged .class entries were copied from the pinned official YSM JAR into
a deterministic selected archive. They comprise four top-level owners and four
nested classes: enchantment query, MolangContext, Bedrock controller family and
ForeignVariableBinding family. Original/input/per-class hashes were verified,
and the original complete JAR was supplied as a read-only library copy.
Minecraft/Forge dependency JARs were not supplied as a separate classpath.

The tool exited 0 and produced four Java files, with nested declarations folded
into their outer files. Their hashes were verified against the runner receipt.
No WARN/ERROR marker lines were found in the recorded log; that narrow log check
is not semantic completeness or absence of all decompiler limitations.
Binaries, raw log, run directory and full generated source remain outside Git.
[VINEFLOWER-COMPARISON-2026-10-17.json](VINEFLOWER-COMPARISON-2026-10-17.json) preserves
portable identities and a normalized command without local machine paths.

## Findings corroborated against instruction evidence

| Selected body | Readable decompiler result | Existing exact evidence |
|---|---|---|
| Enchantment query loop | Constant argument index 1 on each loop iteration | EQUIPMENT-EFFECT-QUERY, opcode offset 78 |
| MolangContext child constructor | Same eight copied fields; no controller/debug/emission inheritance | CHILD-CONTEXT-ARROW PUTFIELD sequence |
| Bedrock existing-state aggregation | Separate all/any updates; zero applied holders sets any true | TIME-CONTROLLER-QUERY and BEDROCK-CONTROLLER |
| Foreign variable evaluation | Name-ID wrapper reads foreignStorage or returns null | FOREIGN-BINDING |

The comparison improved readability of control flow and nested lambdas without
silently replacing obfuscated symbols or changing discovered behavior. It is a
second representation of the same bytes, not a new independent human semantic
review, original-source restoration, execution proof or full 955-class coverage.
The central mapping count remains 669.

## Reuse

For future complicated Java branches, first use existing source/bytecode records.
When a decompiler view materially helps, select the affected owners and nested
classes, preserve original class-byte hashes, and run the pinned shelf tool with
a new run name. Keep the existing MOD-AI CAS/provider path for indexed transforms;
this small comparison does not replace it. Consult REA only for a suitable,
explicitly scoped operation and its own dependencies/permissions.
