# Molang lexical rules, token values and diagnostic positions

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Fifty declarations/eight owners,289 integrity checks/13 negative controls. Historical lexer/token mappings remain unchanged; this extends their partial method descriptions rather than claiming new original symbols. No target parsing, independent semantic review or global grammar conformance test.

Owners: lexer `oOOooOo0OO00ooO00OOO00o0`; character helper `O0Ooo00O0oO0oOOOo0o00OO0`; cursor `Oo0O00o0O0000OO0O0o0O0Oo`; token kind `OOo0OOOooo0oO0oO00O00o0o` and its Tag inner; parse exception `O0O0oooO0O0OOO0OOo0OO00o`; engine implementation `ooO0Ooo0OO0o000oo0o0o0OO`; token `o00oOO0oooO0ooo00oOo00Oo`.

## Character and keyword rules

Whitespace skipping recognizes exactly space, tab, LF and CR, not a call to Character.isWhitespace. Word starts allow ASCII a-z/A-Z or underscore. Continuation additionally allows Character.isDigit(int), which is broader than ASCII digits. Words are converted with no-argument String.toLowerCase, so locale-independent casing is not guaranteed. The keyword set in this dispatch is break, continue, return, true and false; other words become identifiers.

The lexer recognizes single-quoted strings, preserving characters until the next quote. There is no backslash-escape branch or newline rejection in that loop. EOF before closure returns an ERROR token with a diagnostic string. Double quote is not this string delimiter. Comments are not skipped here: slash and star are ordinary tokens. The separate user-function comment-filtering layer must not be conflated with raw lexer behavior.

## Numeric scanning depends on the preceding token

The body first special-cases dot after RPAREN as DOT. It then computes whether the preceding token is IDENTIFIER, even across whitespace. A digit starts the numeric branch; a dot starts it only if the previous token is not an identifier.

In the ordinary numeric path, it appends the initial character, consumes digits, then optionally consumes a dot and more digits. No exponent/sign/hex rule or float parsing appears in this scanner. A leading dot already appended as the initial character can therefore be followed by another dot through the later optional-dot branch. Static path examples include a FLOAT token string "." or ".5.6"; labeling it FLOAT does not prove the downstream parser accepts it as a number.

The previous-identifier branch instead appends '0' without initially reading another character. If its current character is a digit rather than dot, it returns FLOAT("0") at an unchanged cursor position. For a source arrangement such as identifier, whitespace, digit, this is a zero-width synthetic numeric token before a later next() can consume the digit with a different preceding token. This is not an infinite-loop claim or an executed parser fixture. Exact numeric branch offsets188..316 include the no-read alternative249..256. Normal identifiers absorb following digits without a whitespace boundary.

## Punctuation and error advancement

Two-character branches cover !=, &&, ||, <=, >=, ==, -> and ??. A single & or | yields ERROR rather than a bitwise operator. Those branches read a lookahead; if it is not the matching second character, that lookahead remains the next current character. Single-character punctuation without a lookahead performs one read at the common tail. EOF returns an EOF token with start cursor.index and end index+1 without consuming again.

## Cursor is a diagnostic counter, not a faithful cloned offset

The constructor reads the first Reader character without calling cursor.push. The read helper reads the next character, then pushes that newly read character (including -1), assigns next and returns it. Cursor.push always increments index; LF increments line and resets column to1; other values increment column. CR is not a line increment here, although the lexer skips it as whitespace. Counters track these calls and conventions, not an independently verified user-facing line-number standard.

Cursor.clone constructs a new cursor from line and column only. Its index starts0 in that constructor; it does not copy the original index. equals/hashCode likewise use line and column, excluding index. The clone bridge delegates to that typed clone. This matters if a consumer assumes cloned absolute offsets; it does not establish that normal parser diagnostics use clones or suffer a visible error.

ParseException stores the supplied Cursor reference without cloning. Message-bearing constructors append its current toString into the exception message, but cursor() later returns the retained live reference. Message text and later mutable cursor state can diverge if a caller advances the same cursor. Cause-only and cursor-only constructors do not use the append helper.

## Tokens and parser ownership

Token requires nonnull kind and requires nonnull value for HAS_VALUE kinds (ERROR, IDENTIFIER, STRING, FLOAT). It does not require value null for other kinds, validate numeric contents, or constrain start/end ordering. Equality/hash include kind, value and both indices. TokenKind.hasTag requires a nonnull tag; no-argument enum construction uses an empty tag set, while explicit tags use EnumSet.copyOf.

MolangEngineImpl retains the supplied ObjectBinding and parse(Reader) delegates to parser(reader,binding).parseAll(), with no local copy, close or catch. This body alone does not determine reader ownership in the parser or the separate engine String overload's try-with-resources path. Preserve those entrypoint distinctions when integrating a parser/editor or reporting diagnostics.

## Reuse

Use these rules to interpret bytecode and design external fixtures, not to silently repair upstream syntax behavior. Locale handling, Unicode-digit acceptance, quote escaping, token labels, numeric conversion, cursor positions and exception rendering are separate contracts. The retained exact instructions and source hashes allow a later authorized runtime fixture to test these predictions without guessing the original names.

## Selected decompiler comparison

[Vineflower receipt](LEXER-VINEFLOWER-COMPARISON-2026-10-17.json) records a single-class run of verified Vineflower1.11.1, one Java output, exit0 and zero warning/error marker lines. Its readable numeric branch retained the previous-identifier no-read alternative and leading-dot/later-dot sequence, corroborating the direct javap inspection. Only the exact original JAR was supplied as an external library; no Minecraft/Forge dependency classpath or target execution. Raw decompiled text/logs remain outside Git; this is tool corroboration, not an independent semantic review or an execution test.
