# Typed retained Decision drill-down

`queryDecisionDrilldown` reads retained observations only. It requires one exact UUID, complete session/run/snapshot/process/Arena/selection identity, a known channel, a maximum 10,000-tick window, at most 256 items and at most 64 returned cache nodes. Duplicate observation IDs are refused. Matching identity filters never convert a foreign revision or process into the requested subject.

Channels: `path_search`, `goal_transitions`, `brain_memory_changes`, `movement_control`, `base_malus`, `sensor_execution`. Path cache and actual return are paired only by captured search ID within the exact context. Missing endpoints stay `NOT_CAPTURED`; limited returned nodes retain explicit truncation. The captured cache does not become an evaluated-neighbor or terrain field.

Memory changes cite both complete snapshots, retain their interval and unknown exact change tick, and break the baseline across partial capture or a gap exceeding the requested bound (default 10 ticks). TTL countdown is excluded from stored-value changes. No detected memory change is a causal explanation for attack or selection. Empty output does not prove no change.

CLI example for the retained native-r7 Path evidence:

```text
node debug-workspace/cli.mjs evidence-decision 22222222-3333-4444-5555-000000000001 --config <native-r7-config> --channel path_search --revision 3 --arena-epoch 0 --start-tick 41000 --end-tick 41005 --limit 8 --max-nodes 3
```

This command does not initialize or ingest the store and does not rewrite finalized canonical evidence. Eight focused contracts passed. An actual CLI query on all 1,949 native-r7 canonical rows returned the exact Path pair, with unchanged canonical/finalization hashes. Live regional terrain queries, overview/visual presentation and MOD SDK are separate pending slices.
