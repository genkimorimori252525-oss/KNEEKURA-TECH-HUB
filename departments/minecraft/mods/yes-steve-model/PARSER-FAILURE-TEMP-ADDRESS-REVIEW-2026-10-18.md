# Independent review: failure-dependent temporary address capture

Verdict: CONDITIONAL_STATIC_ACCEPTANCE. The narrow state-lifetime result is supported. It is not a target-parser reproduction, native oracle, specification violation, or demonstrated gameplay/security defect.

Reviewed primary REPORT.md/evidence.json/witness.py/receipt.json in ../../parser-failure-address. Fresh bounded extraction independently compared the seven primary owners against the fixed local JAR; added MolangContext, MolangMemory, IdentifierExpression factory and VariableExpression wrapper. The extraction uses the same existing Python classfile reader, so this is independent reasoning and extraction, not an independent disassembler implementation. check.py, fresh-evidence.json and receipt.json record the scope. No Java, original parser/evaluator, native code/assets, CI, network, downloads, or Git edits.

## Accepted chain

1. PrimaryBinding constructor installs t/temp as the same TempVariableBinding object. The binding implements transient and object-binding interfaces; scoped cleanup is a separate list/interface path.
2. ParserImpl root property lookup at429 and namespace property lookup at542 can allocate a variable before later delimiter rejection. Compound parsing returns the left expression on RPAREN at316–317; next0 parses at60, accepts only EOF/semicolon at81/91, and otherwise throws at116. This supports a token-level path IDENTIFIER(t), DOT, IDENTIFIER(a), RPAREN. Text `t.a )` remains a source-consistent illustrative candidate, not independently verified lexer output or executed input.
3. Unsafe facade invokes engine parse20 and value construction26 before transient reset34; no exception handler performs reset on failure. Pool helper catches all from protected4..11 and returns the parser on the exceptional path. Return invokes public scoped reset1 before queue.add8. A return/reset failure can prevent insertion and is excluded.
4. Constructive conditional selection sequence: begin with empty queue; rent creates parser P; its failing parse allocates a→0; normal return enqueues P; absent other pool users/entries, next poll selects that sole P. Concurrency and real-world scheduling are not asserted. A general concurrent next-rental identity guarantee would be false.
5. Binding computeIfAbsent returns an existing variable for a repeated name. A new b receives old top1; allocator stores incremented top at12 and constructs variable at15. The variable's integer field is private final and written by its constructor at6. Reset clears the map and top; it cannot renumber that emitted object.
6. The AST truly retains that object: parser factory call609 passes the namespace lookup result; IdentifierExpression factory tests variable interface61 and constructs VariableExpression at75; wrapper constructor stores that target at13. No map relookup/renumbering occurs here.
7. Temp-variable evaluation dynamically obtains the current entity context's tempStorage at9 and passes its captured address at18. MolangContext's tempStorage getter invokes its MolangMemory getter at4, which returns the stored StackMemory. Thus binding identity is compile-time while memory is current-context runtime storage.
8. StackMemory getTemp checks address < varSize at5; it reads mem[varOffset+address] at18, otherwise returns null20–21. A fixture varOffset=0,varSize=2,mem=[11,22] yields22 for captured address1 and11 for clean address0. The successful parse's reset does not change this comparison.

## Required qualifications and counterexamples

- Physical retained slots alone are insufficient: logical varSize and varOffset matter. varSize0 masks both reads as null; varSize1 yields null for address1 but11 for address0. Equal occupied values also mask a difference.
- Assignment before the corresponding read can make the returned value identical because both use the same captured address. This is not a theorem that all subsequent execution or storage layout is equivalent.
- Failure before temp binding, another parser rental, or an intervening successful transient reset defeats this particular history-dependent capture.
- Runtime root retention is not a parser-reset fact. Prior STORAGE-CALLERS dossier describes processor memory surviving clearModel and direct evaluation without universal push/pop. Fresh MolangMemory initialization body does not replace/reset StackMemory. This supports availability of retained storage in the Java path, not that any actual model follows the required sequence or that native/reflection/external callers cannot reset it.
- No runtime evaluation happens merely because parsing failed. The failure changes parse-time allocation state; a later evaluated AST and suitable runtime storage are separate necessary steps.
- Field immutability is ordinary Java object behavior; no claim covers reflection/Unsafe or external mutation.

## Review changes and test quality

The initial authored witness treated [11,22] without explicit logical-frame metadata and tested empty-frame behavior with a tautology. The author corrected both: final REPORT specifies varOffset0,varSize2, and witness now models get_temp and verifies both empty-frame reads. Independent check.py additionally verifies partial logical size, nonzero offset, equal-slot masking, and assign-before-read. These are authored symbolic tests, not original-code execution.

The primary report's strongest defensible conclusion is: successful parsing on a reused parser does not by itself guarantee allocation starts at zero independently of earlier failed parsing, and a retained live frame can expose the address difference. General bug reproduction, input-to-output execution equivalence, lexer closure, all pool schedules, and whole-model/native semantics remain unproven.
