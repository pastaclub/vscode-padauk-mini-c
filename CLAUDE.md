# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A VS Code extension providing syntax highlighting for **Padauk Mini-C**, the C-like
language of the Padauk FPPA toolchain (PDK / PMS / PFS microcontrollers). It is a
declarative extension only — no `main`, no activation code, no runtime. Everything is a
TextMate grammar, a language configuration and snippets.

## Commands

```sh
./install.sh                 # regenerate, package a .vsix, install it via the code CLI
python3 tools/gen_grammar.py # regenerate the grammar + language configuration only
./tools/gen_icon.sh          # rasterise icon.svg -> icon.png (needs rsvg-convert)
code --uninstall-extension pastaclub.padauk-minic
```

`install.sh` needs only python3, zip and the `code` CLI — no npm, no vsce. It writes the
vsixmanifest and content-types itself. After installing, VS Code needs a window reload
(`Developer: Reload Window`) to pick up grammar changes.

## Generated files — do not hand-edit

`syntaxes/padauk.tmLanguage.json` and `language-configuration.json` are **both generated**
by `tools/gen_grammar.py`. Edit the word lists at the top of that script (SFRs, mnemonics,
directives, pin-config words, units) and re-run it. Hand edits to the JSON are lost on the
next build. Same for `icon.png`, generated from `icon.svg`.

## Two regex dialects

This has caused a real bug and will again:

- The **grammar** is matched by Oniguruma. Inline `(?i:...)` flags, lookbehind and
  possessive quantifiers all work.
- **`language-configuration.json`** (folding markers, indentation rules, onEnter rules) is
  compiled with **JavaScript** `RegExp`, which has no inline flags. `(?i:...)` there throws
  at load time and silently kills folding/indent. The generator's `ci()` helper expands
  case-insensitive words into `[iI][fF]`-style character classes for that file.

Padauk directives are case-insensitive and the corpus really does contain `.ENDM`,
`.FORC`, `.RAMADR` and `.OutFile` alongside lowercase ones, so case-insensitivity is not
optional.

## TextMate pitfalls this grammar already works around

- **Earliest match position wins**, and only then does pattern order break ties. A rule
  anchored at `^[ \t]*` starts matching at column 0 and therefore beats any mid-line rule
  on that line, regardless of list order. This is why the `macro-call` rules carry a
  negative lookahead over `NON_MACRO` (every keyword, type and mnemonic) — without it,
  `  return;` would be scoped as a macro invocation.
- **Greedy whitespace backtracks.** `[ \t]+(?!=)` does not do what it looks like: the
  engine shortens the whitespace run until the lookahead passes. `PAPH   = 0b_1100_0000;`
  was mis-scoped as a macro call this way. The fix in place is `[ \t]+(?![ \t])(?!...)`,
  which forces the run to be consumed whole.
- Bit access (`PA.6`, `payload.0`) and directives (`.define`) are told apart by what
  precedes the dot: directives require line start or whitespace/`(`/`;`/`{`/`}` before
  them, bit access requires an identifier char or `]`.

## Verifying grammar changes

Do not eyeball grammar edits — tokenize the real corpus with the same engine VS Code uses.
There is no npm dependency in this repo, so build the harness outside it:

```sh
npm install vscode-textmate vscode-oniguruma   # in a scratch dir
```

Then load `syntaxes/padauk.tmLanguage.json` into a `vsctm.Registry` (with
`oniguruma.loadWASM` from `vscode-oniguruma/release/onig.wasm`), call
`grammar.tokenizeLine` over each line carrying `ruleStack` forward, and print
`text → last scope` per token. Run it across:

```sh
find ~/MyData/Padauk \( -name '*.c' -o -name '*.h' \) | grep -v /OBJ/   # 46 files, ~3100 lines
```

Then audit by scope — e.g. list every token scoped `entity.name.function.macro.call` or
`keyword.other.instruction` and check each is genuinely one. That audit is what caught both
pitfalls above. Note `vscode-oniguruma` is CJS: use `createRequire`, not `import * as`.

Caveat: `vsce` collects no files when run from a path under `/private/tmp/claude-*`
(it silently packages an empty vsix). It works normally from the repo. `install.sh`
avoids vsce entirely.

## Build direction

The repo builds **into** `~/.vscode/extensions/pastaclub.padauk-minic-<version>/`. That
directory is a build artifact — never copy anything back out of it into the repo. It has
happened once: `package.json` was overwritten by the installed copy, which carries VS
Code's `__metadata` bookkeeping and had lost the `"icon"` line. `install.sh` now aborts if
it sees `__metadata` or a missing/undeclared icon.

## File association

The language id is `padauk`. Mini-C lives in `.c` / `.h` files, but the extension
deliberately does **not** claim those extensions — that would break real C projects on the
same machine (this user has ESP-IDF and PlatformIO installed). It claims only `.pdkc`,
`.pdkh`, `.minic`, and the firmware tree is associated through a path-scoped
`files.associations` glob in the user's VS Code settings, not from this repo.

## Publishing

Not published yet. Publishes as `pastaclub.padauk-minic`. `vsce package` runs warning-free.

**Build Marketplace uploads with `npx @vscode/vsce package`, not `install.sh`.** The
hand-written manifest in `install.sh` is fine for local installs but does not synthesise
the Marketplace search tags (`__ext_pdkc`, `__web_extension`, …) that vsce adds. It also
once encoded `<Categories>` as nested `<Category>` elements — the Visual Studio manifest
style — which the Marketplace rejects on upload with "The category 'Programming Languages'
is not available in language 'en-us'". Categories must be a comma-separated string. Bump
`version` for every publish; Open VSX (`ovsx`) is the second target for VSCodium/Cursor
users.

## Conventions

- Do not commit or push unless explicitly asked.
- Keep `CHANGELOG.md` in step with `version` in `package.json`.
