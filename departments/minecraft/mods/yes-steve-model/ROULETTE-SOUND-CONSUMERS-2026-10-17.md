# Configured button sound versus ordinary UI click sound

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. This joins the already captured ExtraAnimationButton carrier and roulette screen with a fixed955-class exact-symbol inventory. No target, GUI, audio decoder or native routine was executed.

ExtraAnimationButton retains its sound string and exposes it through its getter. The [inventory](ROULETTE-SOUND-CONSUMERS-EVIDENCE-2026-10-17.json) validates both getter and field declarations before searching direct field reads/invocations and bootstrap argument references. It finds:
- zero exact Java invocation references to the sound getter
- one exact GETFIELD read of the sound field, inside that getter itself
- zero matching bootstrap argument references

The result's generic calls array contains that one field-read site; it must not be misreported as a call to the getter. This is not closure over reflection, inherited symbolic-owner references, native code, external mods or every possible method-handle representation.

The screen's recorded ordinary selection/configuration click paths instead request Minecraft's sound manager to play SimpleSoundInstance.forUI using the fixed UI_BUTTON_CLICK sound and volume1. Those requests are independent of the stored button sound string; no retrieval of that string occurs at these captured sites. Other ordinary sound/effect emitters remain separate paths in the existing sound lifecycle dossiers.

Therefore the carrier's getSound name and field presence alone do not establish configurable roulette-button audio playback through the inspected Java route. This is not a universal claim that the field is unused at runtime or a request to implement/patch that feature. Two exact-inventory checks and eight corruption controls pass; central mapping and confidence remain unchanged.
