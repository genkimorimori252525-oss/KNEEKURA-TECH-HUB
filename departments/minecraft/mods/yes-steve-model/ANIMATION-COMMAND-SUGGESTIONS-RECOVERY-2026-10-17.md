# Server animation command and suggestion provenance

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Fifteen declarations across PlayAnimationCommand comparison owner `oO0Oo0OO0ooo000o0ooo0O00` and CommandRegistry `OoOo0000o0o0o00o0o0Oo00o`. The latter's registration method was already captured in the Molang-command cohort; this full owner snapshot extends that partial scope without replacing its receipt. No command, game or network payload was executed.

## Play request versus successful playback

The play subtree's predicate calls CommandUtil.hasPermission(source,2). The previously captured [command utility](MOLANG-COMMAND-PRODUCER-RECOVERY-2026-10-17.md) defines its permission-level OR local-player alternative; this must not be simplified to an unconditional operator-only gate. Root registration remains governed by YSM availability.

The arguments use EntityArgument.players and StringArgumentType.string for the animation, with an animation suggestion provider. The command gets the selected ServerPlayers, then visits their model-info capabilities when present. Exactly "stop", compared by String.equals, calls ModelInfoCapability.stopAnimation; other strings call playAnimation. The ordinary command tail returns1, not the number of applied targets and not evidence that a clip exists or was rendered. No local model-animation lookup or playback acknowledgement occurs in this body.

Existing [server/full evidence](SERVER-FULL-SYNC-RECOVERY-2026-10-17.md) contains the two ModelInfoCapability methods. Both delegate to the property tracker with sync=!dirty; stop supplies the empty string. The [producer](SERVER-PROPERTY-PRODUCER-RECOVERY-2026-10-17.md) preserves extra-animation state and stages according to its old/new-name and sync rules; ordinary tick/full paths handle transmission. This command does not itself call the client's animation player.

The [entity-load receiver](ENTITY-LOAD-APPLICATION-RECOVERY-2026-10-17.md) interprets the extra-animation field on the client: nonempty requests play, empty requests stop, subject to entity/capability availability and deferral. Clip resolution and scheduling belong to the existing controller/input dossiers. A command may finish normally before any of those stages completes.

## Animation suggestions are not target-specific validation

CommandRegistry registers separate models, animations and textures suggestion providers. Each checks that its source is a SharedSuggestionProvider.

For animation suggestions, physical DEDICATED_SERVER immediately returns Suggestions.empty. The other branch obtains ClientModelManager.getDefaultModel().playerModel().animations(), formats those names and adds the literal stop to a HashSet. It does not inspect the selected target players' current models. Therefore a suggested name is not proof of a clip in every target model, and a missing suggestion is not an execution ban. The default-model dereference has no separate local readiness guard.

Model suggestions use ServerModelManager's model-map keys on physical dedicated server, otherwise ClientModelManager's keys. This is physical distribution, not a per-command determination that the selected entity lives locally. Texture suggestions read the model_id command argument, check the corresponding side's map and obtain that model's textures. The dedicated-server branch uses its list; the client branch maps its Optional model to the texture key list. Both prepend the literal "-" to their newly collected list. It is not appended when the outer model-map membership test fails.

Suggestion generation does not validate user authorization to apply a model, force loading, fetch resources or execute model changes. Those separate command/native paths are not expanded here.

## Exact string formatting boundary

filterSuggestionStr sends the input's UTF-16 chars, narrowed to char, through Brigadier StringReader.isAllowedInUnquotedString and returns the original string if every tested character is accepted. The alternate branch performs String.replace for double quote→backslash+double quote, then apostrophe→backslash+apostrophe, then formats with a surrounding pair of double quotes. The captured constant code points are respectively [34,37,115,34], [34], [92,34], [39], [92,39]; javap display escaping must not be mistaken for extra literal backslashes in the format itself.

This helper contains no independent pass to escape existing backslashes. Its output is not certified here as a round-trip serializer for every Brigadier input: the external parser's accepted escape grammar and actual input domain were not executed or verified in this cohort. No speculative fix or malformed command was introduced.

## Reuse limits

Keep suggestions, command argument parsing, target capability presence, server property staging, dirty/full dispatch, client application and clip playback as separate success criteria. The expanded registry snapshot provides actual bootstrap/constant records, not original-name recovery or live command registration proof. Independent semantic review remains NOT_RUN and central669 mappings remain unchanged.
