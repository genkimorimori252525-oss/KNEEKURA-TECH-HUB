# Mahoraga adaptation deep dive

## Generic damage adaptation

Adaptation logic is distributed across attack-event and active-state procedures.

The wheel/body helmet item NBT acts as a persistence ledger.

For an incoming damage source, a string-derived source key indexes an adaptation value.

Observed progression:

- new/low value starts adaptation state/message
- repeated exposure increases the keyed value by **2**
- value is capped around **10**
- once adaptation has progressed, the original damage event can be cancelled
- replacement generic damage becomes approximately:
  `original damage / adaptation value`

At full generic adaptation, special environmental responses exist for fire-family damage, starvation, drowning and freezing.

## Environmental adaptation

This current behavior strongly corroborates the ver50 author changelog: “Mahoraga: now capable of adapting environmental damage.”

The exact pre-v50 implementation is not available, so no before/after bytecode diff is claimed.

## Limitless-specific adaptation

Infinity bypass is separate from the generic per-damage-source 0–10 ledger.

`AntiInfinityProcedure` checks a Mahoraga wheel/body NBT value for `skill205` and treats a threshold around **100** as sufficient to bypass Infinity.

Generic damage adaptation and Limitless-specific adaptation therefore have separate identities and scales.

## AI / world cut

Mahoraga AI procedures coordinate target following, attack calculation, strength scaling, wheel/body/sword equipment and world-cut progression.

`MahoragaCutTheWorldProcedure` uses area attack + block-destruction semantics and advancement/state gates.

## Engineering extraction

Prefer a typed structure:

```text
AdaptationKey -> progress -> mitigation stage -> completion response
```

The X1-style concept is strong, but stable namespaced damage identifiers are preferable to stringified DamageSource values for long-term persistence.
