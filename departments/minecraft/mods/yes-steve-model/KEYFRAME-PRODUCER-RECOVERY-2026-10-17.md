# Keyframe point producers: bounded static recovery

Date: 2026-10-17. Independent static review passed. Seven integrated method roles, no new class claims. Full closure: five owners, sixteen methods (seven reviewed roles and nine support methods), five source hashes and complete declarations/bootstrap records.

## Provenance and limits

Artifact SHA256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, 63,269,843 bytes. Candidate official source revision: `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Source labels guide comparison; this does not establish whole-source/artifact equivalence. Historical source/artifact divergence findings remain preserved. No target execution. Complete operand snapshots prove evidence fidelity; semantic claims additionally require source/bytecode review.

## Observed local semantics

- BoneKeyFrame constructor stores the start and duration and computes end as their float sum, without validation. `isBegin` promotes its float argument to double and compares strictly below double `1e-5`; NaN is false. This is not a float-epsilon comparison: the float nearest `1e-5` is slightly below the double threshold and passes. `isEnd` compares strictly above float `0.9999899864196777`; equality and NaN are false. Both signed zeros satisfy the begin gate and fail the end gate.
- TransitionKeyFrame starts at zero and uses the supplied first start tick as duration. Its point getter evaluates begin unless `isEnd` is true, then evaluates post. It does not interpolate. Its transition-destination getter evaluates begin. NaN selects begin.
- LinearKeyFrame checks begin first, then end. Endpoint branches evaluate only the selected point; the end gate selects postPoint, not the interior endPoint. The interior branch evaluates begin then end, then delegates vector interpolation to MathUtil. NaN passes both gates into the interior branch. No local clamp or exception handler exists.
- CatmullRomKeyFrame uses the same gates. The interior branch evaluates left, begin, end and right in that order before calling MathUtil's Catmull formula. Its end-gate result evaluates the separate post value, not necessarily the interior end value. Evaluator exceptions can prevent later evaluations; the method supplies no local catch.
- Vector3v allocates a Vector3f, evaluates x, y, z through interface `evalAsFloat` in order, then invokes its three-float constructor. It has no local handler or memoization. Dynamic evaluator implementations and inherited IValue error handling remain separate boundaries; these call sites do not prove that every implementation catches errors.

Offsets and exact references supporting each proposed role appear in `KEYFRAME-PRODUCER-EVIDENCE-2026-10-17.json`. The companion mapping proposals are limited to those seven roles. Constructor, getter and abstract declaration support is retained without inflating the proposal count.

## Verification

`tools/keyframe_producer_ysm_265.py` requires the fixed JAR, evidence and pinned source checkout. A fresh run passed 125 checks and 20 corrupted-evidence negative controls. It verifies the complete sixteen-method identity set against fresh bytes, all code operands/handlers, five declarations and bootstrap records, fixed source path/hash set and actual source hashes/revision. Scanning the full artifact also confirms the three direct BoneKeyFrame subclasses in scope.

Negative controls cover artifact mismatch, removed method/support/instructions/owner/source/bootstrap records, float-to-double promotion, NaN comparison and strict gate changes, transition/linear branch changes, endpoint and component reference changes, Catmull delegate changes and an invented local handler. They validate audit sensitivity, not runtime behavior or an independent proof of the semantic labels.

## Connected remaining work

EasingType factory selection and raw-keyframe list indexing/duration construction remain unresolved here. Follow their transition, linear and Catmull construction paths next, then BoneKeyFrameProcessor selection and cache lifecycle. External value evaluation, JOML behavior and higher-level playback timing remain bounded dependencies.
