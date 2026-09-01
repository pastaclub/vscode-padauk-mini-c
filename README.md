# Padauk Mini-C for VS Code

Syntax highlighting for **Padauk Mini-C**, the C-like language used by the Padauk
FPPA toolchain (PMS / PMC / PFS / PFC / PDK microcontrollers).

## What it highlights

| Construct | Example |
|---|---|
| Compile-time directives | `.define`, `.if` / `.else` / `.endif`, `.ifdef`, `.ifidni`, `.repeat`, `.forc`, `.endm`, `.errz` |
| Message directives (text, not code) | `.echo Clock: %8d.6:SYS_CLK MHz`, `.warning ...`, `.error ...` |
| Chip setup | `.ADJUST_IC SYSCLK=IHRC/4, IHRC=16MHz, VDD=3.3V;` — units included |
| Macro definitions and calls | `MULT macro x, y` / `.endm`, bare calls like `MULT i, 3` |
| `EQU` constants | `System_Clock EQU 8000000` |
| Pin / register configuration | `$ PA.6 Out, High;`, `$ TM2C SYSCLK, Period;` |
| PDK assembly mnemonics | `t0sn`, `swapc`, `pushaf`, `pcadd`, `idxm`, `ret`, … (PDK13/14/15/16 sets) |
| Registers and flags | `A`, `SP`, `PC`, `CF`, `ZF`, `AC`, `OV` |
| SFRs | `PA`, `PBC`, `PADIER`, `TM2C`, `ADCRGC`, `LPWMG0DTL`, `INTEN`, … |
| Chip names | `PMS171B`, `PMS150C`, `PFS154`, … |
| Labels | `next:`, and the macro-expanded form `loc#i:` / `goto loc#i;` |
| Mini-C operators | `=>` compile-time assign, `$0`/`$1` byte index, `##` concat, `@F` / `@B` local labels |
| Bit access | `PA.6`, `i.0`, `arr[1].0` |
| Numbers | `0b_1100_0000`, `0xff`, `0FFh`, `16MHz`, `3.3V` |

Plus: `//` and `/* */` comments, folding of `.if`/`.endif` and `macro`/`.endm` blocks,
matching indentation rules, and snippets (`fppa0`, `isr`, `macro`, `.if`, `.forc`,
`adjustic`, `$`, …).

## File association

The language id is `padauk`. Because Mini-C lives in `.c` / `.h` files, the extension
deliberately does **not** claim those extensions globally — that would break real C
projects. Instead, associate your Padauk tree in `settings.json`:

```jsonc
"files.associations": {
  "/path/to/your/Padauk/**/*.c": "padauk",
  "/path/to/your/Padauk/**/*.h": "padauk"
}
```

Files named `.pdkc`, `.pdkh` or `.minic` are picked up automatically. You can also switch
a single file with the language selector in the status bar (or `Cmd+K M`).

## Maintaining the grammar

The TextMate grammar is generated. Edit the word lists at the top of
`tools/gen_grammar.py` (SFR names, mnemonics, directives, pin-config words), then:

```sh
python3 tools/gen_grammar.py
```

then re-run `./install.sh` and reload the VS Code window. The installed copy under
`~/.vscode/extensions/local.padauk-minic-1.0.0` is a build artifact - this repo is the
source of truth.

## Install

```sh
./install.sh
```

That regenerates the grammar, packs a `.vsix` and installs it with the `code` CLI
(needs only python3, zip and the `code` command - no npm, no vsce). Then reload the
window: `Developer: Reload Window`.

To remove it: `code --uninstall-extension local.padauk-minic`.

## License

MIT
