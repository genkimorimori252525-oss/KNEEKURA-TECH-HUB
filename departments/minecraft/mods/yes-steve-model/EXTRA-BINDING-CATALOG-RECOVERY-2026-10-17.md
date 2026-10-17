# Additional ctrl / tlm / math name navigation

Exact-artifact navigation, not new semantic mappings. Source: fixed YSM 2.6.5 Forge 1.20.1 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. Independent semantic review NOT_RUN; target runtime not executed; central map unchanged.

The catalog follows three fixed constructors and direct static adapter calls with the corresponding namespace-binding argument type. It visits34 methods through31 adapter edges, retaining both real and missing-provider branches without deciding their runtime conditions.

- ctrl:84 literal registration sites,60 unique names (36 base plus24 optional-adapter names).
- tlm:32 sites,16 unique names (real/fallback).
- math:33 sites and names, including pi/e constants and legacy aliases.
- Total149 sites for109 unique names.

This complements the prior171 base query/YSM names. Together the lookup can navigate280 distinct names, not280 fully recovered semantics or runtime-available symbols. Optional provider conditions and differing fallback types remain in the relevant dossiers. Math behavior was already studied in the earlier MOLANG-MATH cohort; this adds navigation rather than redoing or promoting that work.

[EXTRA-QUERY-NAME-LOOKUP-2026-10-17.jsonl](EXTRA-QUERY-NAME-LOOKUP-2026-10-17.jsonl) intentionally points to registration sites (caller/method/descriptor/offset), not an invented normalized implementation target. One query can have multiple sites. [Detailed evidence](EXTRA-BINDING-CATALOG-EVIDENCE-2026-10-17.json) includes caller Code hashes, exact instruction slices from each literal name to registration, resolved value bootstraps, class hashes and adapter edges. Arbitrary dynamic namespace mutation, external registrations and runtime branch outcomes are not covered.

Use the existing opt-in locator:

```sh
python tools/evidence_locator_ysm_265.py --query ctrl.tac_is_aim
python tools/evidence_locator_ysm_265.py --query tlm.is_entity
python tools/evidence_locator_ysm_265.py --query math.sin
```

Results retain source catalog, target kind and branch-not-evaluated scope. Do not collapse real/fallback entries into an always-active callback. The locator performs no automatic rebuild or tool checks. --check-selected hashes the bounded query catalogs and returned evidence files, not the whole repository.

Reproduce the catalog with tools/extra_binding_catalog_ysm_265.py and --jar/--evidence/--lookup; --capture explicitly writes it, while --out verifies it and negative controls. Ambiguous literal-name segments fail rather than guess. The verifier compares exact graph/projection, and mutations of names, missing sites/edges, artifact identity and fabricated runtime reachability are rejected. It does not validate the semantics of every callback.

Related: [controller flow](CONTROLLER-QUERY-INDEX-2026-10-17.md), [typed guard behavior](TYPED-QUERY-GUARDS-RECOVERY-2026-10-17.md), [base catalog](QUERY-REGISTRATION-RECOVERY-2026-10-17.md), [maid defaults](MAID-QUERY-ADAPTER-RECOVERY-2026-10-17.md), [gun callbacks](GUN-ANIMATION-ADAPTERS-RECOVERY-2026-10-17.md).
