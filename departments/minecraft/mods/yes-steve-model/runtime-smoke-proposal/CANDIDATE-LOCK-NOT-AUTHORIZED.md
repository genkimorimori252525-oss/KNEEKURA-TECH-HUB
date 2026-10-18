# Candidate execution lock: NOT AUTHORIZED TO EXECUTE

The separate `ysm_runtime_smoke.candidate.lock.json` has `status: REVIEWED_COMPLETE` and `unresolved: []` after independent technical review. These fields express technical review completeness only. They do not accept the Minecraft EULA, grant publication or dispatch permission, or authorize YSM native execution or built-in asset use.

The original `ysm_runtime_smoke.lock.json` remains the unchanged NOT_EXECUTABLE draft. Source and workflow are unchanged. The candidate is intended to become the deployment lock only after the parent obtains the concrete bundled user approval. The workflow's two consent inputs still default to false. The actual approved repository commit must still be specified and match the workflow event. No actual commit approval exists yet.

Candidate SHA-256: `78320878720286c2c495477e3910d1e40ca592e808f700d712c96542329762af`

The candidate passes the pure harness validator using an authored synthetic context and fake consent strings. No IO adapter, Docker, Java, installer, download, target execution, publication or dispatch was invoked. Synthetic validation data is test data, not user authorization.

Technical review does not constitute a successful integration run. Docker/installer/JVM/server behavior and snapshot/build observations remain unobserved until an explicitly authorized bounded run; the guard logic stops rather than relaxing policy if the real environment differs. Native load/JNI/workers and client/render checks remain unsupported measurements exactly as documented in README.md.
