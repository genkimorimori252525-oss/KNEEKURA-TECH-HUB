# User-function comment filtering is a preprocessing step

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. This focused review reuses the full MolangParser member already in [parser/binding evidence](PARSER-BINDING-STORAGE-EVIDENCE-2026-10-17.json), corroborated with a new javap view of the same exact class. No new method mappings, independent review, target parser execution or copied decompiler output is claimed.

Exact member: owner `com/elfmcys/yesstevemodel/OooOoOoOOOOo000oo0oo00oo`, name `Oo0Oo0o00O00Oo0OOoOOoooo`, descriptor `(Ljava/lang/String;)Ljava/lang/String;`, private static. Use the one-file member viewer to inspect this member alone.

## Entry and state ordering

parseExpressionUnsafe applies this helper only when its user-function flag is true. Ordinary expression parsing bypasses it. The [raw lexer](LEXER-TOKEN-DIAGNOSTICS-RECOVERY-2026-10-17.md) does not independently skip comments, so comments accepted by this preprocessing path must not be promised for every expression entry.

The helper tracks block-comment, line-comment and single-quoted-string booleans. Its loop tests string state first (offset39), line state next (64), then block state (94), then recognizes a new quote or slash pair. It scans UTF-16 char indices and builds a new string. It does not build a source-position mapping for later lexer diagnostics.

## Strings and comments have intentionally distinct character treatment

In string state it appends every character and exits on the next single quote. There is no backslash escape branch, matching the raw lexer's absence of that escape rule. A slash/star sequence inside the quoted span remains text. An unclosed quote is retained through end of input; this helper does not report it. The later lexer/parser remains responsible for its own acceptance/errors.

In line-comment state it drops characters until CR or LF, clears that state and appends one LF. For a CRLF terminator, CR is replaced by LF here; the following LF is processed outside line-comment state and appended normally. The resulting text therefore contains two LF characters at that boundary. A final line comment with no terminator disappears without an added newline.

In block-comment state it drops all characters, including line breaks, until the first adjacent `*/`; it increments the index to consume the slash. There is no nested-comment depth counter or special quoted-string state inside the block. End of input while still in a block returns the retained prefix without a dedicated unterminated-comment error.

## Removal does not preserve token separation or original positions

Opening and closing a block comment append neither whitespace nor a separator. Text on either side becomes adjacent: as a static branch consequence, `ab/* note */cd` yields the text `abcd` at this helper's output. That is a statement about preprocessing, not a target-parser test or proof that either complete input is a valid expression.

Ordinary non-comment characters are appended unchanged. A trailing slash without a following character is appended. Double quotes do not enter this helper's string state. Removed blocks can change both line and column positions seen by later lexer diagnostics; the CRLF transformation can change line counts in the other direction. No original-source-position reconciliation is implemented in this member.

## Reuse contract

Specify which parser entry enables comments, whether adjacent tokens require separator insertion, which quote/escape rules apply, and whether diagnostics refer to original or filtered text. Preserve the actual boundary instead of describing this helper generically as a complete C-style lexer. No change to the target or claim of a reproduced game failure follows from these differences.

## Concrete Java entry-flag inventory

A later [exact955-class scan](PARSER-ENTRY-FLAG-CALLERS-EVIDENCE-2026-10-17.json) validates all three target declarations and finds three direct references, with no matching bootstrap argument references:
- CustomMolangParser's pooled single-expression helper calls the unsafe facade with an explicit false constant.
- The safe facade calls the unsafe facade forwarding its incoming boolean unchanged.
- The unsafe facade conditionally calls the comment filter when that boolean is true.

There are no exact direct Java callers of the safe facade in that inventory. The comparison source marks that facade Native Access; this label is a clue, not proof of native invocation or actual flag values. The unsafe facade also passes the same boolean to MolangValue's constructor. No true-producing Java application caller was established by the inspected paths.

Therefore comments in a user-function model must not be attributed to the ordinary GUI/command pooled helper. Actual native/model construction and external or reflective entry remain outside this Java inventory. The separate user-function target-cache dossier describes lookup/evaluation after construction; it does not fill this missing producer boundary. Two inventory checks/eight corruption controls pass, not a runtime language-acceptance test.
