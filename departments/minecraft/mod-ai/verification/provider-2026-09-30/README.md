# Real provider-tool fixture acceptance — 2026-09-30

## Result and scope

PASS: the existing, unchanged `providers.prepare_transform` adapter executed the real pinned Vineflower and tiny-remapper JARs through its default `run_process` runner on a freshly compiled Java 17 input JAR. Both returned `status=OK`; repeated identical calls returned `cache_hit=true` with the same receipt hashes. No adapter patch was needed. No mocked provider or replacement adapter was used.

This is **synthetic Java17 fixture acceptance only**, not Minecraft MOD, Forge, mapping-dataset, game/client, Windows, classpath-completeness, source/binary-equivalence, or performance acceptance. The handwritten Tiny mapping uses the adapter's `obf` and `mojmap` namespace labels, but contains **no Mojang mapping data**. The manifest explicitly uses `COMPARATIVE`, loader `fixture`, and version `0.0.0`; it does not claim a registered Forge workspace.

## Pinned official inputs

All three executable downloads were checked against their official published SHA-256 values before execution. No credentials, global package install, environment settings, repository edits, publication, or Forge upgrade was performed.

- Vineflower 1.11.1, official project distribution via Maven Central: https://repo.maven.apache.org/maven2/org/vineflower/vineflower/1.11.1/vineflower-1.11.1.jar
  - Published checksum: same URL with `.sha256`
  - SHA-256: `a615d07ddbbcd489369674f40e42df639c32be95410890b38f173d5c1e2ea39c`
  - Upstream release: https://github.com/Vineflower/vineflower/releases/tag/1.11.1
  - Official distribution guidance: https://vineflower.org/
- tiny-remapper 0.11.2 fat JAR, official Fabric Maven: https://maven.fabricmc.net/net/fabricmc/tiny-remapper/0.11.2/tiny-remapper-0.11.2-fat.jar
  - Published checksum: same URL with `.sha256`
  - SHA-256: `0376b17b92f858956e018da672affb5485c18085db681f9547664996e82b6688`
  - Source JAR inspected read-only: https://maven.fabricmc.net/net/fabricmc/tiny-remapper/0.11.2/tiny-remapper-0.11.2-sources.jar
- Eclipse Temurin JDK 17.0.20.1+1, Linux x64 HotSpot, official Adoptium metadata: https://api.adoptium.net/v3/assets/latest/17/hotspot?architecture=x64&image_type=jdk&os=linux&vendor=eclipse
  - Pinned archive: https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.20.1%2B1/OpenJDK17U-jdk_x64_linux_hotspot_17.0.20.1_1.tar.gz
  - SHA-256: `3808d1d15e3ec6bd5b84057fb5d84c33d8a1536a258146bcea2e603fc726e08e`
  - Archive size: 193,252,603 bytes
  - Local java identity: OpenJDK Runtime Environment Temurin-17.0.20.1+1, build 17.0.20.1+1; `java`, `javac`, and `javap` are under `jdk-17.0.20.1+1/bin/`
  - `bin/java` SHA-256: `f5aed21d3a0b0f4b05d3a3f9fe71263916d5bc0d47b53aa52a3340b90f0b4805`
  - `release` SHA-256: `973f28729da43962dfba2e39b2a27ab736122f3a1bf829e06abfbde2a731c711`
  - `lib/modules` SHA-256: `6a1b657bd845397ab30fe2d4d78d80c4fdc05107182843669fc928655c227241`

## Existing adapter identity

- Checkout HEAD: `f5651fe5ebbaf4df9526f4644054705d74f0215f`
- Path: `src/kneekura_tech_hub/minecraft/providers.py`
- Git blob: `6a75753f898567fd944cba590e9498db66a1272d`
- SHA-256: `ff6c8e247f3977de81503862735c970d3c8b6fe6303e47562219f5ccc62a9081`
- `git diff -- providers.py tests/test_minecraft_providers.py` was empty after acceptance

## Fixture and observed output

The fixture `fixture.obf.a` contains a private integer field, a constructor, `b(int)` adding its field to its argument, and `c(String)` performing string concatenation. It was compiled with real `javac --release 17 -g -parameters`; the classfile major version was checked as 61.

- Input JAR SHA-256: `7d5346aeae6c8ccf82e4b1ab3c9877a45eed60d4e6f7514b5d83b16bd523a3b2`
- Input source SHA-256: `616f56c279291ddec50bc7a65d74a3d3d8ab176029a93cead73bc266f8c38af7`
- Handwritten Tiny v2 mapping SHA-256: `ff4c5ec71bb58064c200537f939a2403ea307c06b10fa659a388f4b7c8dc925a`
- Original prepared index: `e263036b85578dab0403a68c9a2f5b71d716847b06b5531361cfcdb43edf5ade`

Vineflower produced `fixture/obf/a.java`. The returned index's search and inspect APIs returned the complete readable source, including `return this.value + x;`. Recompiling that actual output with the same JDK17 succeeded.

- Vineflower receipt: `b801ca6ad1fbf5e99671ed8048174033319ea317c0ddd625445aade950ac11fb`
- Normalized output archive: `160a6b3694c26d72036fae825392ea3ea5c769a180e95f79d22d72f447776b66`

Tiny-remapper produced `demo/NamedExample.class` and removed the original class path from the output. Preparing the actual remapped bytes with real JDK17 `javap` verified:

- owner `demo/NamedExample`
- field `power:I`
- method `increment:(I)I`, whose bytecode references `demo/NamedExample.power:I`
- method `greeting:(Ljava/lang/String;)Ljava/lang/String;`

A small separately compiled Java17 smoke caller against the actual remapped output exited zero and printed `PASS: synthetic Java17 fixture increment=12 and greeting=Hello, fixture`. This is fixture behavior, not MOD behavior.

- tiny-remapper receipt: `274184908efc45457f8fa8ca5faa90a7169237ba792525cbd95c321cf39ca8df`
- Normalized output archive: `829e359160ff7c88d6f56ed773b349342da228dce43457af7f82d472ef09e9eb`
- Raw tool output archive: `3cf5813dd20d071e14febc93ce30c30d65159c0ab3e3fafd025917d38626e072`
- Remapped class bytes: `2f84cf48d7bf0858e223e51296d3741ec31250582b0d9d50a2c6a2cccab4719e`

## Recorded commands and evidence

Commands from `provider-acceptance/`:

```sh
PYTHONPATH=../tech-hub/src ../venv/bin/python run_acceptance.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../tech-hub/src ../venv/bin/python verify_fixture.py
```

The first script refuses to overwrite an existing `evidence-baseline` directory. It calls `prepare_transform` directly with no `runner` argument. Each tool is configured with `allow_execute=true`, an explicit Java17 path, exact JAR hash/version, 256 MiB, one thread, 120-second timeout, and empty explicitly ordered library classpath. The adapter supplies its standard CLI arguments unchanged.

Regression command from the repository:

```sh
PATH=PROVIDER_ACCEPTANCE/jdk-17.0.20.1+1/bin:$PATH PYTHONDONTWRITEBYTECODE=1 ../venv/bin/python -m pytest -q -p no:cacheprovider tests/test_minecraft_providers.py
```

Result: **9 passed in 6.53 seconds**. This is a focused regression run, not the full repository suite.

`evidence-baseline/` retains input profile/index, provider configs, actual output receipts/logs/archives, cache-hit receipts, complete source and bytecode inspections, exact symbol results, and final verification commands/results. `evidence-baseline/cas/` stores the content-addressed tool JARs, input, outputs, mapping, logs and receipts with durable pins. Every CAS blob hash and every pin target was revalidated successfully. `acceptance-baseline.log`, `fixture-verification.log`, and `provider-regression.log` retain command output.

Still untested: real MOD input JARs, real Forge-resolved classpaths, official mapping datasets, large/malformed external tool workloads, classpath-dependent decompilation/remapping, external tool cancellation/timeout under real heavy load, Windows, packaging into a MOD, and any game/client acceptance.

## Public summary and retained local evidence

[SUMMARY.json](SUMMARY.json) is a derived report containing results, versions and
hashes. The two small authored fixture inputs are adjacent. Raw receipts, stdout,
local machine paths and provider binaries are not published. The original sealed
archive SHA-256 is `e4c51621ecd93b55a61d816c3947359a96f469735b777542d98b25cfb975d6f3`;
it remains local. Original hashes identify private evidence; a checkout alone is
not its complete raw-byte replay bundle.
