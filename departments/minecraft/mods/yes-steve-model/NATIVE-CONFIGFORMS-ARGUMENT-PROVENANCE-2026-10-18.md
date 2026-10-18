# Static native ConfigForms argument join

Original SO and JAR hashes pinned in NATIVE-CONFIGFORMS-ARGUMENT-EVIDENCE-2026-10-18.json. Reproduction verifies ten selected original-byte ranges, five metadata callback sources, and six constructor snapshots against original JAR classfiles. No guest/native/JVM, decoder callback, original asset, filesystem callback or checkpoint was executed/resumed. No repository edits.

## Exact native result

Nested F entries parsed by356840 have four strings +08/+28/+48/+68, followed by three float32 values promoted into doubles +88/+90/+98 and the segmented string-pair collection +a0. At3a85c9..3a8723 all four strings become Java strings. F+08 is the native discriminator only: despite that conversion, it is not supplied to any selected constructor. Non-`range`/non-`radio` values take the default branch, including unknown values; native does not test exact `checkbox`.

All selected constructors receive F+28, F+48, F+68 in that order. Default uses d355a0+78 at3a8795. Range uses +80 at3a8850 and receives F+88/+90/+98 in xmm0/1/2. Radio uses +88 at3a8da1 and receives the same three strings followed by the map reference.

Radio3a88a5 allocates two equally sized object arrays via d356e0+80. Segmented iteration begins at F+d8; record stride40, block stride200, and block pointer progression preserve stored record order. Each record's first string (+00) goes to array A[index] at3a8aa6; second (+20) goes to B[index] at3a8b54. d355e8+50 constructs from A,B at3a8c3f. Its result is the radio constructor's fourth argument. This proves positional pair preservation, not duplicate-key semantics, Java map identity or successful construction by itself.

At3a8fde each selected result goes into the array allocated from d355a0+70. The array is passed as argument4 at3a922d to the previously exactly identified ExtraAnimationButton constructor. Existing Java retention/UI evidence is reused, not re-audited or promoted.

## Conditional Java field join

The original constructor snapshots match classfiles byte-for-byte. Provided the remaining metadata callbacks resolve to the corresponding candidates:

- F+28 = ConfigForms.title (field o0OOooo0o0OO00OoOOOo0o0O)
- F+48 = ConfigForms.description (O00OOOooOoooOoo0o0o0oO0O)
- F+68 = ConfigForms.value (oOOOo0OOO0ooooo0O00OO0o0)
- F+88/+90/+98 = RangeForms.step/min/max, respectively
- F+a0 pair first/second = RadioForms.labels ordered label-name/expression pair
- ConfigForms.type is installed by the concrete Java constructor (`checkbox`, `range`, `radio`); it is not a direct copy of F+08. Thus the native default branch can normalize unknown discriminators to checkbox, if +78 identity is confirmed.

These are explicitly conditional cross-language joins until exact metadata results exist. The identical callback source lengths and matching ABI signatures corroborate candidates but do not prove identity.

## Finite decoder frontier (not executed here)

All are method descriptors, flags8:

- d355a0+70:40faa0, source46d02 length134; candidate ConfigForms four-string constructor
- d355a0+78:40fac0, source4682e length116; candidate CheckboxForms three-string constructor
- d355a0+80:40fae0, source4776a length119; candidate RangeForms three-string/three-double constructor
- d355a0+88:40fb00, source42f55 length168; candidate RadioForms three-string/FifoHashMap constructor
- d355e8+50:40fda0, source418a0 length100; candidate FifoHashMap(Object[],Object[]) constructor

Initializer addresses, source hashes, callback bytes and source-length declarations are in NATIVE-CONFIGFORMS-ARGUMENT-EVIDENCE-2026-10-18.json. d356e0+80's array class identity is separately unverified here. No inferred identity is represented as decoded.

## Limits

No runtime selection, initialization, object construction, expression evaluation, model load, native duplicate policy, overflow handling or whole-program correctness established. Existing native parser ownership and Java UI/queue evidence remain at their prior confidence. This artifact closes native argument provenance and reduces exact naming to five finite metadata sources.

## Later exact closure

The [completed Java join](NATIVE-CONFIGFORMS-JAVA-JOIN-2026-10-18.md) and [five exact metadata identities](NATIVE-CONFIGFORMS-METADATA-2026-10-18.json) resolve the conditional statements in this historical argument-provenance report. [Array-class proof](NATIVE-CONFIGFORMS-ARRAY-CLASS-2026-10-18.json) is read-only checkpoint evidence, not a new callback.
