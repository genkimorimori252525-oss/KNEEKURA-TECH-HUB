# Numeric-token rejection and parser entry ownership

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. New15 declarations across engine/parser interfaces (including abstract members without Code),90 checks/seven negative controls. Parser implementation and facade bodies are REUSED from PARSER-BINDING-STORAGE; lexer/engine implementation from LEXER-TOKEN-DIAGNOSTICS. No target execution, independent semantic review or new mapping promotion.

## A FLOAT token does not establish an accepted literal

ParserImpl.parseSingle's FLOAT branch first calls lexer.next at offset85, then reads the old token's value and calls Float.parseFloat at99. A lookahead read error can occur before conversion. NumberFormatException is not locally converted into ParseException by this branch; advancing the lexer is not rolled back on failure.

The own-source JDK-only probe [LexicalNumberJdkContract](tools/LexicalNumberJdkContract.java) verifies eight Float.parseFloat cases plus one Character.isDigit check. "." and ".5.6" are rejected, while ".5" is accepted. Arabic-Indic digit U+0661 is recognized by Character.isDigit but rejected by Float.parseFloat. The JDK accepts "1e3" and "0x1p0", but that does not add exponent/hex syntax to the target lexer, which splits those strings differently. This is nine standard-library contract checks, not nine executed target parser tests.

The [lexer dossier](LEXER-TOKEN-DIAGNOSTICS-RECOVERY-2026-10-17.md) establishes possible scanner token strings. Joining those calls with the JDK contract predicts rejection at conversion for malformed numeric strings; it does not show a real model contained them or that a game crash occurred.

## Error and result state

ParserImpl.next0 explicitly rejects an initial ERROR token with ParseException. After a compound expression, it requires EOF or SEMICOLON; otherwise it throws a semicolon diagnostic. A preceding identifier may fail binding lookup even earlier. Consequently a lexer-produced zero-width FLOAT after an identifier is not evidence of a successfully accepted extra expression.

ParserImpl.next writes its current-expression field only after next0 returns normally. On an exception, lexer state may already have advanced while current still contains the previous value (or the initial unset sentinel). There is no local rewind/retry transaction. Cursor references in exceptions are the live lexer cursor, as described by the diagnostic carrier dossier.

MolangEngine's String overload wraps a StringReader in try-with-resources, rethrows ParseException, and wraps other IOException in a new ParseException with Cursor(0,0). Its diagnostic text says failure to close the string reader, but the IOException catch also spans parsing inside the try. It does not catch NumberFormatException merely because that exception arose during parsing.

The higher geckolib MolangParser.parseExpression facade catches Exception and normally returns FloatValue.ZERO after logging/optional debug delivery. This is distinct from the unsafe entry and not a catch-all Throwable guarantee. Error reporting itself can fail; no nested guarantee is added. On the successful unsafe path, resetTransient occurs after engine parsing and value construction; a prior exception bypasses that reset. [Parser-pool lifetime](PARSER-POOL-LIFETIME-RECOVERY-2026-10-17.md) separately captures the rental finally/resetScoped behavior.

## Reader ownership depends on entry point

- MolangEngineImpl.parse(Reader) creates a parser and invokes its instance parseAll. The default instance parseAll loops next until null, collecting expressions, and performs no close. The engine Reader entry therefore leaves reader closure to its caller on these inspected paths.
- MolangEngine.parse(String) owns and closes its newly created StringReader, including exceptional exits with ordinary suppressed-close handling.
- MolangParser static parseAll(Reader,binding) and parseAll(String,binding) use try-with-resources on the created parser. ParserImpl.close delegates lexer.close, which delegates Reader.close. These static convenience methods close their reader through that chain after successful parser construction, on normal or exceptional body exits.
- Factory construction failure happens before the resource variable is established and is not covered by the later try-with-resources close. Factory and parseAll entry points must not be treated as identical ownership contracts.

No asynchronous sharing, recovery of failed readers or actual I/O failure was exercised. The new interface snapshot preserves exception tables so later adapters can choose an entry point without inferring ownership from a method name alone.
