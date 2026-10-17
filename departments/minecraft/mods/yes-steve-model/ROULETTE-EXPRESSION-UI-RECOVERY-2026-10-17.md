# Roulette configuration expressions: local queue and optional relay

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. The evidence retains53 declarations/two owners and280 integrity checks/seven negative controls. This dossier reviews the expression-form branches, not every captured screen rendering/input method. No GUI, packet, target class or Molang expression was executed. Central669 mapping entries unchanged; independent semantic review NOT_RUN.

## Three GUI emitters, one codec constructor

The exact955-class [constructor inventory](ROULETTE-SUBMISSION-PRODUCERS-EVIDENCE-2026-10-17.json) first validates the target declaration, then finds four direct construction sites/four methods and zero bootstrap constructor references. Three application emitters are the radio callback and checkbox callback in AnimationRouletteScreen `oooOO0o0ooo0O000Oo0ooOoo`, and FlatSlider.applyValue in `oo0ooOoOOOO0OOoO0OOoOOo0`. The fourth site is SubmitRouletteConfig's decoder, not a GUI producer. This is not reflective/native/external closure.

The radio callback uses the selected label's expression string unchanged. The checkbox callback concatenates the configured value expression, `=` and Boolean-derived `1` or `0`. FlatSlider concatenates its configured expression, `=` and the double returned by ForgeSlider.getValue. The slider's separate getValueString uses DecimalFormat `#.##` for display; that formatted display string is not the transmitted assignment value. ForgeSlider range/step internals and actual interaction were not executed or independently reconstructed here.

## Local scheduling occurs before optional transmission

All three paths attempt local unsafe parsing and enqueue the resulting IValue on the associated AnimatableEntity with `(allowEmitting=true, pre=false, resultConsumer=null)` before considering transmission. Enqueue is not successful evaluation or completed state change.

Each emitter sends only when all three sequential conditions pass:
1. CustomMolangParser.hasOnlyRoamingAssignment(expression) is false
2. NetworkHandler.isRemoteChannelPresent() is true
3. LOW_BANDWIDTH_USAGE is false

The packet carries the associated animatable entity's ID, not an unconditional current-player ID. NetworkHandler.sendToServer independently repeats its channel-presence guard. The server relay's sender/entity lookup and the client receiver's parsing are separate boundaries, documented in [command/relay producers](MOLANG-COMMAND-PRODUCER-RECOVERY-2026-10-17.md) and [packet routing](ANIMATION-PACKET-ROUTING-RECOVERY-2026-10-17.md). The GUI's transmission filters are not server authorization checks.

## Exception ownership differs between controls

AnimationRouletteScreen's executeMolang helper catches only ParseException, logs it and returns void. Its radio and checkbox callers then continue to the lexical/channel/bandwidth conditions. Therefore a locally caught ParseException does not itself suppress their subsequent transmission attempt; a successful send still depends on all later conditions. Other runtime exceptions are not caught by this helper. The radio callback calls screen init after its transmission branch on the normal path; the checkbox callback does not.

FlatSlider keeps parsing, enqueue and the entire send branch inside one ParseException handler. Such a parsing failure jumps past the send branch to logging. This distinction follows the exact exception tables and call order; it does not demonstrate that a particular user-provided configuration fails or that a remote peer executes anything.

## Reading initial form values is deferred too

addConfigForms uses the same executeMolang helper with a result callback to read checkbox, range and radio values. The result callbacks queue Minecraft.execute work that creates/adds the corresponding widgets and updates shared offset/index arrays. These are scheduled stages, not synchronous reads performed before addConfigForms returns. Captured rendering/lifecycle support does not establish callback ordering relative to screen replacement or prove a visible race.

## The roaming predicate is lexical, not a semantic validator

The previously captured [parser-pool evidence](PARSER-POOL-LIFETIME-EVIDENCE-2026-10-17.json) contains the exact case-insensitive anchored Pattern and matcher.find call. It accepts repeated assignments whose left side has the v/variable.roaming prefix, an ASCII alphanumeric/underscore name, optional whitespace before `=`, and a nonempty non-semicolon right-hand span.

Eight [JDK-only examples](ROAMING-ASSIGNMENT-JDK-VERIFICATION-2026-10-17.json) confirm ordinary assignments, uppercase prefix and multiple assignments match; a different prefix and an empty right side do not. A whitespace-only right span matches lexically, a semicolon inside a quoted string disrupts the match, and a function-shaped right side matches. These examples do not invoke YSM or establish parser acceptance, side-effect freedom or security. Reuse the predicate only as this transport-selection heuristic, not as proof that the right side is a valid/safe expression or that all resulting state is replicated.

## Verification boundary

The fixed five-cohort [checkpoint](ROULETTE-UI-CHECKPOINT-2026-10-17.json) joins this UI snapshot, constructor inventory, command/relay, parser pool and packet receiver. Four shared method snapshots agree with zero conflicts. It does not rerun the entire project or alter earlier fixed manifests. No promotion of comparison names or mapping confidence is implied.
