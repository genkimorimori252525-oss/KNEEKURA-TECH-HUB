# Twilight Forest 4.3.2508 — Distributed JAR Provenance

Status: **artifact identity located; binary hash still pending execution in a network-capable/local environment**

## Official distributed target

CurseForge identifies the ANCHOR artifact as:

- project ID: `227639`
- file ID: `5468648`
- release: `4.3.2508`
- filename: `twilightforest-1.20.1-4.3.2508-universal.jar`
- Minecraft: `1.20.1`
- loader metadata: Forge / NeoForge
- uploaded: 2024-06-24
- reported size: 22.3 MB
- Curse Maven coordinate: `curse.maven:the-twilight-forest-227639:5468648`

Official page:

`https://www.curseforge.com/minecraft/mc-mods/the-twilight-forest/files/5468648`

## Public-source candidate

Pinned candidate:

`TeamTwilight/twilightforest@a7dd8f13c653e137f977f5ffaa870fcb20fc1625`

Why it is the strongest public-source candidate currently known:

1. it is on the public 1.20.1 line;
2. its timestamp is immediately before the 4.3.2508 upload window;
3. its commit changes the Discord URL to `https://discord.experiment115.com/`;
4. the 4.3.2508 release notes explicitly list that Discord URL fix.

This is strong chronology/content evidence, not proof that the distributed bytecode was built from exactly this commit.

## Why binary and source stay separate

Upstream issue #2345 later recorded a developer statement that a Japanese translation fix already existed in source but apparently had not been uploaded to CurseForge. Therefore:

```text
public 1.20.1 source history
        ≠ automatically
distributed 4.3.2508 JAR contents
```

The Hub intentionally keeps those evidence tracks separate.

## Automated verifier

Run:

```powershell
python departments/minecraft/mods/twilight-forest/tools/verify_anchor_jar.py
```

or supply a local JAR:

```powershell
python departments/minecraft/mods/twilight-forest/tools/verify_anchor_jar.py --jar "C:\path\to\twilightforest-1.20.1-4.3.2508-universal.jar"
```

The verifier records:

- JAR SHA-256 and SHA-1;
- exact byte size;
- ZIP/class/resource counts;
- `META-INF/MANIFEST.MF`;
- `META-INF/mods.toml`;
- `pack.mcmeta`;
- resource-by-resource correspondence against the pinned source candidate.

### Resource correspondence technique

The TECH HUB already stores the source candidate's complete Git tree including each Git blob SHA.

For each resource in the JAR, the verifier calculates the Git object hash:

```text
SHA1("blob " + byte_length + NUL + raw_bytes)
```

and compares it directly with the source-candidate blob SHA.

This can prove exact byte correspondence for resource files **without cloning the upstream source again**.

## Proof boundary

Even a 100% resource match does not automatically prove compiled class identity because Java compilation, remapping/reobfuscation and build inputs transform source into bytecode.

The final provenance record must therefore distinguish:

- **binary identity** — SHA-256 of the actual distributed JAR;
- **resource correspondence** — exact source↔JAR byte matches;
- **metadata correspondence** — manifest/mod metadata;
- **compiled-code identity** — separate evidence if ever required.

Until the verifier is executed against the distributed file, ANCHOR remains `IN_PROGRESS`.
