# ConfigForms native→Java join: exact metadata closure

The five completed isolated metadata receipts now match every candidate owner/constructor descriptor, callback hash/source and original-JAR constructor hash. No mismatch. NATIVE-CONFIGFORMS-JAVA-JOIN-2026-10-18.json contains full exact obfuscated identities, descriptors, class/code hashes and verified constructor instructions. Original conditional NATIVE-CONFIGFORMS-ARGUMENT-PROVENANCE-2026-10-18.md/NATIVE-CONFIGFORMS-ARGUMENT-EVIDENCE-2026-10-18.json remain unchanged.

## Closed field provenance

For nested record F parsed by356840:

- F+28→ConfigForms.title (o0OOooo0o0OO00OoOOOo0o0O)
- F+48→ConfigForms.description (O00OOOooOoooOoo0o0o0oO0O)
- F+68→ConfigForms.value (oOOOo0OOO0ooooo0O00OO0o0)
- F+88→RangeForms.step; F+90→min; F+98→max. These are serialized float32 values promoted to native doubles before three Java double arguments.
- F+a0→RadioForms.labels: each stored pair's first string is its label name, its second string its expression. The native conversion preserves the two positions and stored iteration order through parallel Object[] arrays and the exactly identified FifoHashMap(Object[],Object[]) constructor.

Exact Java constructor checks: ConfigForms bytecode offsets6/11/16/22 store type/title/description/value respectively. Each concrete subclass forwards its own literal type plus argument1/2/3. RangeForms offsets12/18/24 store double local slots4/6/8 into step/min/max fields. RadioForms offset12 stores reference local4 into its labels field. These snapshots re-match the original JAR, not merely comparison source.

## Unknown native discriminators normalize to checkbox

F+08 is converted to a Java string, but not supplied to any selected concrete constructor. Only exact five-byte `range` and `radio` select specialized branches; every other discriminator follows +78, now exactly identified as CheckboxForms(String,String,String). That constructor supplies literal `checkbox` to ConfigForms. Thus a completed default-branch construction yields Java type checkbox even if the native discriminator differed. This is static path semantics, not evidence that malformed input successfully loads or renders.

## Array-class distinction

Manager d355a0+70 resolves ConfigForms.<init>(String,String,String,String). At3a856b NewObjectArray uses its class handle only, allocating ConfigForms[]; it does not invoke the abstract ConfigForms constructor. Selected concrete forms enter that array at3a8fde, and the same array reaches ExtraAnimationButton's previously identified constructor at3a922d.

The immutable next6 checkpoint independently closes the radio array element class without new execution: d356e0+80→descriptor404001011440→class790000000900→java/lang/Object, associated method Object.toString()String. NewObjectArray uses the class handle, not that method. Therefore these are Object[] arrays containing Java strings. Nearby manager+78 is String.<init>()V with method handle7c0000000080; its handle suffix is not the manager+80 slot. See NATIVE-CONFIGFORMS-ARRAY-CLASS-2026-10-18.json.

## Evidence and retained limits

join_exact_receipts.py reads completed receipts and original classfiles only. read_array_class_checkpoint.py reads immutable checkpoint JSON, checks original BSS backing and decodes stored sparse pages only; it never constructs/resumes a CPU or runs callbacks. Five exact metadata callbacks were executed in a separate isolated guarded pass; this join only reads the receipts. No JVM, original model/assets, filesystem callback or target runtime invoked here.

Readable semantic names retain their earlier primary-static correspondence scope; no source-artifact equivalence, central mapping promotion or independent semantic review claimed. No runtime initialization, object construction, UI rendering, expression evaluation or model-load success established. Native duplicate-key policy, bounds/overflow behavior and broader reader validation remain outside this join.

[Exact metadata receipt](NATIVE-CONFIGFORMS-METADATA-2026-10-18.json); [argument provenance](NATIVE-CONFIGFORMS-ARGUMENT-PROVENANCE-2026-10-18.md); [original classfile field join](NATIVE-CONFIGFORMS-JAVA-JOIN-2026-10-18.json); [array class](NATIVE-CONFIGFORMS-ARRAY-CLASS-2026-10-18.json).
