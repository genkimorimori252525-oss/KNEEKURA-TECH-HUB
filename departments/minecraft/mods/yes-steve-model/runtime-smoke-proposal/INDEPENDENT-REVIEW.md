# Independent authored-harness review

Scope: FINAL-PROPOSAL.md and the Python harness, authored fake tests, manual workflow and draft lock. Read-only source/metadata review plus authored Python fake tests only. No Docker, Java, installer, original YSM, network download, repository edit, publication or dispatch was performed.

## Findings raised and corrected during review

1. The initial checksum map kept one `(hash, algorithm)` per path. Minecraft version metadata SHA-1 and the server bundle's SHA-256 describe some identical files, so the initial implementation would reject legitimate inputs. Correction: retain every declared algorithm/checksum and check all of them; same-algorithm contradictions remain fatal. An independently injected overlapping-hash fake fixture passed after correction.
2. MOJMAPS was initially classified as generated even though the pinned official version metadata declares the downloaded server mappings' SHA-1 and size. Correction: apply that declaration to the resolved MOJMAPS path.
3. Checking only existing files could silently omit declared processor outputs. Correction: require declared server processor outputs to exist; also require files whose expected hash comes from profile data and the server mappings output.
4. An exception after starting YSM initially discarded the completed control result and could report YSM as NOT_RUN. Correction: retain mutable incremental phase state, launch-attempt flag and cleanup outcome through exceptions. The authored exception-after-control regression passes.
5. JVM preflight initially accepted only major/vendor and discarded exact build evidence. Correction: cross-check release JAVA_RUNTIME_VERSION with observed java.runtime.version, require major 17/Microsoft, and retain an allowlisted build string in output. No advance JVM build label or new download was required.

## Design assessment

The harness meaningfully implements the one-cohort experiment, rather than only validating an input JSON. Before acquisition or execution it checks both consents, exact repository/ref/public hosted-runner context, expected event commit, lock digest, exact lock content and harness digest. The workflow performs the consent/context gate before checkout and checks source hashes before invoking the harness.

The installer has a separate network-enabled staging container with no YSM or credential mounts. Pinned installer/profile/official-version metadata and YSM/native checksums are checked. Production arguments are compared to the pinned installer member. Installed library inputs are classified, hashed and unknown files rejected. A shared read-only library snapshot is checked before each fresh control/YSM run, with control failure preventing YSM launch.

Runtime commands and post-create inspection enforce network=none, nonroot identity, read-only root and dependency bind mounts, dropped capabilities, no-new-privileges, builtin seccomp availability, private IPC/PID defaults, no ports/devices, bounded memory/CPU/PIDs and disabled cores. Game/world state has bounded noexec tmpfs; native extraction has separate bounded executable /tmp. Containers do not mount the host repository, credentials, home or Docker socket.

The streaming loop bounds startup, steady-state interval, stop and private captured output. OOM, timeout and exit 137 are differentiated from clean success. Public output permits only fixed results, bounded numbers, hashes and a restricted JVM build string. It makes no native-load, JNI-registration, worker-drain or renderer success claims. Cleanup uses only this run's enumerated containers with ownership labels and its exact temporary root; no broad prune is used.

## Limits

This is source/fake-fixture review, not proof that the official installer or Forge/YSM boots successfully in Docker. Real installation/runtime behavior remains deliberately untested. Failure on unexplained files or runtime network needs must remain fail-closed. The supplied lock remains NOT_EXECUTABLE and does not grant publication, EULA acceptance or native/assets execution permission.

Final hashes, line references and final test receipt are recorded below when source finalization is confirmed.

## Final verification, 2026-10-18 15:34 UTC

Conclusion: no remaining blocking source-design finding identified within this bounded review. Five findings above are corrected in the final reviewed source. This conclusion authorizes no execution or external mutation.

Final source references in `ysm_runtime_smoke.py`: multi-algorithm declarations lines 285–289 and 341–344; missing processor outputs 300–306; data-declared output and mappings checks 318–330; exact JVM identity 117–125 and the preflight call; incremental phase evidence 138–146 and run/cleanup/main reporting. The gate remains lines 43–69; sandbox construction/inspection and frozen-snapshot paths were inspected directly.

Independently ran `python -m unittest discover -s ysm-local-inputs/ghidra-static-20261018/output/runtime-harness-proposal -p 'test_*.py' -v`: 17 tests passed, no skips, 0.011 seconds. Full receipt: `test-receipt.txt` beside this report. Verified the draft lock is NOT_EXECUTABLE and its harness pin equals the source hash.

SHA-256:
- ysm_runtime_smoke.py: f202acfe320d21b28b2143c23c8fdb929a5ce7fc8ab8947c61fb10c718323c7f
- ysm_runtime_smoke.lock.json: d50b0c434dc686d7e9363411c4e2d0cf9da61ea435a233abce7f5fa88168779d
- ysm-runtime-smoke.yml: f70a2c8bae8b050ae83eac5cbaeec9ab11be283ba2cacda7431d2b6917416661
- test_ysm_runtime_smoke.py: 8f77f4564b3208484a4206c16e4c0f5036a40ee4d5662558e2b642d1b9cdd2be
