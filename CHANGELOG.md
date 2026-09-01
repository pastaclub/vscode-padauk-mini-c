# Changelog

## 1.0.0

Initial release.

- TextMate grammar for Padauk Mini-C: compile-time directives, macro definitions
  and calls, `EQU` constants, `$` pin/register configuration, PDK13/14/15/16
  assembly mnemonics, registers and flags, SFR families, chip names, labels
  (including the `rcv#i:` macro-expanded form), `=>`, `$0`/`$1` byte index, `##`,
  `@F`/`@B`, binary/hex/unit literals and bit access.
- Language configuration: comments, brackets, folding for `.if`/`.endif` and
  `macro`/`.endm`, indentation rules.
- Snippets for the common skeletons.
- Verified with vscode-textmate against 46 Mini-C sources (3141 lines).
