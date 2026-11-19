"""Target compatibility (PLAN P2): fail closed, substitute only by explicit table, never to air."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .blockstate import BlockState, BlockStateError, parse_state
from .ir import BuildingIR
from .profile import Registry

MAX_LISTED_POSITIONS = 32


class SubstitutionError(ValueError):
    pass


@dataclass
class CompatResult:
    status: str  # LOSSLESS | SUBSTITUTED | BLOCKED
    ir: BuildingIR | None
    issues: list[dict] = field(default_factory=list)
    substitutions: list[dict] = field(default_factory=list)
    partial_states: int = 0


def load_substitutions(data: bytes, registry: Registry) -> dict[str, BlockState]:
    """``{"from": "to"}``; keys are a full state string or a bare block id. Targets must be legal
    and must not be air: replacing a block with air is deletion, not substitution."""
    def no_duplicates(pairs):
        keys = [k for k, _ in pairs]
        if len(set(keys)) != len(keys):
            raise SubstitutionError("DUPLICATE_SUBSTITUTION_KEY")
        return dict(pairs)
    try:
        doc = json.loads(data, object_pairs_hook=no_duplicates)
    except (ValueError, RecursionError) as exc:
        if isinstance(exc, SubstitutionError):
            raise
        raise SubstitutionError(f"INVALID_SUBSTITUTION_JSON: {exc}") from exc
    if not isinstance(doc, dict) or len(doc) > 1024:
        raise SubstitutionError("INVALID_SUBSTITUTION_TABLE")
    table: dict[str, BlockState] = {}
    for key, target in doc.items():
        try:
            source = parse_state(key)
            to = parse_state(target)
        except (BlockStateError, TypeError) as exc:
            raise SubstitutionError(f"INVALID_SUBSTITUTION_ENTRY: {key!r}") from exc
        if to.is_air:
            raise SubstitutionError(f"SUBSTITUTION_TO_AIR_FORBIDDEN: {key!r}")
        reason = registry.check(to)
        if reason:
            raise SubstitutionError(f"SUBSTITUTION_TARGET_INVALID: {target!r} ({reason})")
        if str(source) in table:  # e.g. "a[x=1,y=2]" and "a[y=2,x=1]" normalize to the same key
            raise SubstitutionError(f"DUPLICATE_SUBSTITUTION_KEY: {key!r}")
        table[str(source)] = to
    return table


def check(ir: BuildingIR, registry: Registry, substitutions: dict[str, BlockState] | None = None) -> CompatResult:
    """Validate every placed state against the target registry. Deterministic for a given table."""
    substitutions = substitutions or {}
    out: dict = {}
    failures: dict[tuple[str, str], list] = defaultdict(list)
    applied: dict[tuple[str, str], list] = defaultdict(list)
    partial = 0
    for pos in sorted(ir.cells):
        state = ir.cells[pos]
        reason = registry.check(state)
        if reason is None:
            out[pos] = state
            props = registry.blocks[state.block_id]
            if len(state.properties) < len(props):
                partial += 1
            continue
        target = substitutions.get(str(state)) or substitutions.get(state.block_id)
        if target is not None:
            out[pos] = target
            applied[(str(state), str(target))].append(pos)
            continue
        failures[(str(state), reason)].append(pos)
    issues = [{"state": s, "reason": r, "count": len(p), "positions": [list(x) for x in p[:MAX_LISTED_POSITIONS]],
               "candidates": _candidates(s, r)} for (s, r), p in sorted(failures.items())]
    subs = [{"from": f, "to": t, "count": len(p), "positions": [list(x) for x in p[:MAX_LISTED_POSITIONS]]}
            for (f, t), p in sorted(applied.items())]
    if issues:
        return CompatResult("BLOCKED", None, issues, subs, partial)
    mapped = BuildingIR(cells=out, air_intent=ir.air_intent, source=ir.source, paste_origin=ir.paste_origin,
                        warnings=list(ir.warnings))
    return CompatResult("SUBSTITUTED" if subs else "LOSSLESS", mapped, [], subs, partial)


def _candidates(state: str, reason: str) -> list[str]:
    """Only mechanical, non-guessing hints. Choosing a replacement material is a human/AI decision."""
    if reason.startswith(("INVALID_PROPERTY:", "INVALID_PROPERTY_VALUE:")):
        s = parse_state(state)
        bad = reason.split(":", 1)[1].split("=", 1)[0]
        kept = tuple(p for p in s.properties if p[0] != bad)
        return [str(BlockState(s.block_id, kept))]
    return []


def summarize(ir: BuildingIR) -> dict:
    states = Counter(str(s) for s in ir.cells.values())
    return {"distinct_states": len(states), "top_states": states.most_common(10)}
