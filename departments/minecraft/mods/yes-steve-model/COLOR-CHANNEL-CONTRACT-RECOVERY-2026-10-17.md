# Packed color and normalized Java renderer channels

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Color owner `ooO00Oo0oooOoO0OOOOoo0Oo` contributes20 declarations,111 integrity checks/six negative controls. Whole-owner evidence retains HSB/brightness/equality support, but this dossier reviews packed-channel conversion and concrete renderer consumers, not every mathematical branch. No target/GPU/native execution or central mapping promotion.

## Packed ARGB, not already-normalized floats

The private constructor retains one final int. ofTransparent(int) preserves all bits; its name does not force alpha to zero. ofOpaque(int) ORs with0xff000000. Integer ofRGBA masks each supplied channel with255, shifts A/R/G by24/16/8, and ORs blue. This wraps low bits instead of saturating arbitrary integers to0..255.

The float overload multiplies each float by255.0f, converts that product to double, adds0.5d, then converts to int before invoking the integer-masking overload. This is not a separate clamp or Math.round call. RGB overloads supply alpha1f or255. Channel getters use signed shifts followed by&255 (blue uses only&255), yielding integer channels0..255; getColor returns the raw packed signed int.

Nine [JDK-only arithmetic cases](COLOR-CHANNEL-JDK-VERIFICATION-2026-10-17.json) model those language operations:0,.5,1 map to0,128,255;2 maps to254 after masking; NaN maps to0, positive infinity to255 and negative infinity to0 after cast/mask. A separate integer example checks ARGB ordering and masking, and another checks the opaque OR. These are not YSM calls or proof that nonfinite/out-of-range inputs reach rendering.

## The observed renderer route uses WHITE and channel getters

The existing IGeoRenderer default color method returns the static WHITE object, whose initializer stores packed−1 (0xffffffff). The exact [consumer inventory](COLOR-CHANNEL-CONSUMERS-EVIDENCE-2026-10-17.json) validates18 public method targets and that field before scanning955 classes. It records34 direct reference sites in10 methods and zero matching bootstrap argument references. Seventeen sites are outside Color:
- one GETSTATIC of WHITE in the interface default
- eight channel-getter calls in GeoReplacedEntityRenderer (four for preRender, four for render)
- four in GeoEntityRenderer
- four in GeoProjectilesRenderer

The other17 sites are internal Color method calls. No other exact external calls to the selected Color methods are present in this inventory. In particular, availability of float factories does not establish that those factories supply the observed model tint. Native/reflection/external use and alternate symbolic-owner references remain outside this count.

The three already captured renderer paths divide each returned integer channel by255f, then pass RGBA floats through their respective Java render/preRender calls. The replaced renderer requests color before its renderType-null main-body skip. The default WHITE path therefore supplies four1.0f values at this conversion, but the interface default alone does not prove every external subclass uses that default. No premultiplication, gamma conversion or physical color-space claim is made.

## Keep Java preparation separate from native interpretation

The [Java renderer boundary](JAVA-RENDER-BOUNDARY-RECOVERY-2026-10-17.md) forwards these arguments together with model/input/output buffers. It does not expose the native implementation's final blending, texture multiplication or output pixels. Packed color conversion is a reusable Java contract, not reconstruction of the full rendering algorithm.

The fixed five-cohort checkpoint joins the new class/inventory with interface, replaced-renderer and vehicle/projectile-renderer evidence. Ten repeated method snapshots agree with zero conflicts. That is snapshot consistency, not independent semantic review. No whole-project CI or optional tool installation was needed.
