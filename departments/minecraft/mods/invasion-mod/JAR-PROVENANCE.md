# Invasion 1.1.2 — Distributed JAR Provenance

## Uploaded artifact

- filename: \`Invasion_1.1.2_1.7.10.jar\`
- size: **1,189,673 bytes**
- SHA-256: \`944f4c33687ef256bf692666421a757345519b1318df96de95565a53c2e28ddc\`
- SHA-1: \`be07920e0e793d331f5eb934c884448363a4cf52\`
- ZIP entries: **327**
- \`.class\` entries: **231**
- \`mcmod.info\`: Invasion mod **1.1.2**, Minecraft **1.7.10**, authors Lieu / Elsee / UnstoppableN, dependency MinecraftForge
- manifest: only \`Manifest-Version: 1.0\`
- license file inside JAR: **not found**

Representative class SHA-256 values:

| Class | SHA-256 |
|---|---|
| \`invmod/common/nexus/IMWaveBuilder.class\` | \`7cd55bc35391e2bf2316ce49a80a1d3aa4f6611719a53d6fc0b9b940158e7fd1\` |
| \`invmod/common/entity/PathfinderIM.class\` | \`7c279b1a5e4ca0af23713a7357b0c381ae3ec1ca2bac3fad40cd33f0ec4be2e4\` |
| \`invmod/common/entity/ai/AttackerAI.class\` | \`f0569854f6025ecfd155df774c4d3a1a68f9041e811b3bfbe01f2fd8439b5674\` |

## Public-source candidate

Pinned candidate:

- repository: \`UnstoppableN/Invasion-mod\`
- commit: [644a52ddea104c206d022bef9edc135c060cba1d](https://github.com/UnstoppableN/Invasion-mod/tree/644a52ddea104c206d022bef9edc135c060cba1d)
- date: 2014-11-25
- complete tree inventory: **392 blobs**
- Java source files: **231**
- resources under \`src/main/resources\`: **75**
- recursive tree response: not truncated

At the pinned revision, \`mod_Invasion.java\` declares version 1.1.2 and the resource metadata identifies the same authors/dependency. The source contains the same 231 top-level compiled classes represented in the uploaded JAR inventory, and selected \`javap\` inspection of the uploaded bytecode matches important source semantics such as the synchronized legacy pathfinder, scaffold search depths and the Zombie Pigman pattern defect.

## Proof boundary

This is **strong correspondence evidence**, not a reproducible-build proof.

Not independently proven:

- every class bytecode instruction was compiled from commit 644a52ddea104c206d022bef9edc135c060cba1d;
- compiler/ForgeGradle/mapping versions exactly match the uploaded binary;
- resources are byte-identical to the public source tree;
- the public source represents every distributed patch.

Use the uploaded JAR hash for binary claims and the pinned commit for source claims. Where both were checked (notably the Pigman pattern defect), the record says so explicitly.

## License boundary

Neither the uploaded JAR nor the pinned legacy source tree exposes a license-like file. This analysis therefore does not infer a redistribution or code-copying permission from repository visibility. Reuse recommendations concern **techniques and independently reimplemented behavior**, not copying source wholesale. See [LICENSE-PROVENANCE.md](LICENSE-PROVENANCE.md).
