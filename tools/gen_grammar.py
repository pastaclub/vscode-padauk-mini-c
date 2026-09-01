#!/usr/bin/env python3
"""Generates syntaxes/padauk.tmLanguage.json and language-configuration.json.

Edit the word lists below and re-run:  python3 tools/gen_grammar.py

Two regex dialects are involved: the grammar is matched by Oniguruma (inline
(?i:...) flags are fine), while language-configuration.json is compiled with
JavaScript RegExp, which has no inline flags - hence the ci() expansion there.
"""
import json, os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- word lists -------------------------------------------------------------

# Mini-C control flow
CONTROL = ["if", "elseif", "else", "while", "do", "for", "switch", "case",
           "default", "break", "continue", "goto", "return"]

# Types / storage
TYPES = ["void", "bit", "byte", "word", "sbyte", "sword", "struct"]
MODIFIERS = ["static", "extern", "const", "volatile", "signed", "unsigned"]

# PDK13/14/15/16 instruction mnemonics (from the free-pdk instruction set tables).
# 'goto' and 'ret' also exist as Mini-C statements; they are listed under CONTROL/here.
INSTRUCTIONS = [
    "add", "addc", "and", "call", "ceqsn", "clear", "cneqsn", "comp", "dec",
    "delay", "disgint", "dzsn", "engint", "icall", "idxm", "igoto", "inc",
    "izsn", "ldspth", "ldsptl", "ldt16", "ldtabh", "ldtabl", "mov", "mul",
    "nadd", "neg", "nmov", "nop", "not", "or", "pcadd", "popaf", "popw",
    "popwpc", "pushaf", "pushw", "pushwpc", "reset", "ret", "reti", "set0",
    "set1", "sl", "slc", "sr", "src", "stopexe", "stopsys", "stt16", "sub",
    "subc", "swap", "swapc", "t0sn", "t1sn", "tog", "wait0", "wait1",
    "wdreset", "xch", "xor",
]

# Compile-time directives (case-insensitive in the Padauk toolchain).
# A catch-all rule highlights any other .foo directive too.
DIRECTIVES = [
    "adjust_ic", "romadr", "ramadr", "outfile", "chip", "sysclk", "align",
    "code", "data", "stack", "reassembly", "noreassembly", "list", "nolist",
    "local", "exitm", "endm", "repeat", "forc", "for", "while", "break",
    "ifidni", "ifidn", "ifdifi", "ifdif", "ifndef", "ifdef", "elseif", "elif",
    "else", "endif", "if", "echo", "printf", "message", "warning", "error",
    "errz", "delay", "wait0", "wait1", "define", "undef",
]

# CPU registers / flags
REGISTERS = ["A", "SP", "PC", "CF", "ZF", "AC", "OV"]

# Named special function registers that don't fit the family patterns below
SFR_MISC = [
    "INTEN", "INTRQ", "INTEGS", "INTEGS2", "MISC", "MISC2", "MISCLVR",
    "CLKMD", "EOSCR", "IHRCR", "ILRCR", "BGTR", "GDIER", "RSTSTT", "T16M",
    "SP", "FPPA", "FPPAE", "ROP", "MULOP", "MULRH", "TMBASE", "PWMGCLK",
    "PWMGCUBH", "PWMGCUBL", "PWMG0C", "PWMG0S", "PWMG0DTH", "PWMG0DTL",
    "PWMG1C", "PWMG1S", "PWMG1DTH", "PWMG1DTL", "PWMG2C", "PWMG2S",
    "PWMG2DTH", "PWMG2DTL", "COMPCH", "GPCC", "GPCS", "OSCR", "RSTC",
]

# Clock sources / build-time constants that read as language constants
CONSTANTS = ["IHRC", "ILRC", "EOSC", "SYSCLK", "VDD", "GND", "HIGH", "LOW"]

# Words used inside `$` register/pin configuration statements
PINCONFIG = [
    "in", "out", "pull", "high", "low", "enable", "disable", "period", "pwm",
    "inverse", "invert", "rising", "falling", "both", "sysclk", "ihrc", "ilrc",
    "eosc", "vdd", "bandgap", "adc", "xtal", "8bit", "12bit", "10bit", "no",
    "yes", "up", "down", "clean", "bit",
]

UNITS = ["Hz", "KHz", "kHz", "MHz", "mV", "V", "ms", "us", "ns"]


def alt(words):
    """Regex alternation, longest first so e.g. 'ifdefi' beats 'ifdef'."""
    return "|".join(sorted((re.escape(w) for w in words), key=len, reverse=True))


# Words that must never be mistaken for a bare macro invocation at line start
NON_MACRO = sorted(set(CONTROL + TYPES + MODIFIERS + INSTRUCTIONS +
                       ["macro", "EQU", "equ"]))

# --- grammar ----------------------------------------------------------------

grammar = {
    "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
    "name": "Padauk Mini-C",
    "scopeName": "source.padauk",
    "fileTypes": ["c", "h", "pdkc", "pdkh", "minic"],
    "patterns": [
        {"include": "#comments"},
        {"include": "#preprocessor"},
        {"include": "#directives"},
        {"include": "#macro-definition"},
        {"include": "#equ-definition"},
        {"include": "#pin-config"},
        {"include": "#function-definition"},
        {"include": "#label"},
        {"include": "#strings"},
        {"include": "#numbers"},
        {"include": "#units"},
        {"include": "#keywords"},
        {"include": "#instructions"},
        {"include": "#registers"},
        {"include": "#chips"},
        {"include": "#local-label"},
        {"include": "#macro-param"},
        {"include": "#byte-index"},
        {"include": "#function-call"},
        {"include": "#operators"},
        {"include": "#bit-access"},
        {"include": "#macro-call"},
    ],
    "repository": {

        "comments": {"patterns": [
            {"name": "comment.block.padauk",
             "begin": "/\\*", "end": "\\*/",
             "captures": {"0": {"name": "punctuation.definition.comment.padauk"}}},
            {"name": "comment.line.double-slash.padauk",
             "begin": "//", "end": "$",
             "beginCaptures": {"0": {"name": "punctuation.definition.comment.padauk"}}},
        ]},

        # #include "os.c"  /  #include <foo.h>
        "preprocessor": {"patterns": [{
            "name": "meta.preprocessor.padauk",
            "begin": "^[ \\t]*(#)[ \\t]*(include|define|undef|ifdef|ifndef|if|elif|else|endif|pragma|error|line)\\b",
            "beginCaptures": {
                "1": {"name": "punctuation.definition.directive.padauk"},
                "2": {"name": "keyword.control.directive.padauk"}},
            "end": "(?=//)|(?=/\\*)|$",
            "patterns": [{"include": "#strings"}, {"include": "#numbers"}],
        }]},

        # .define FOO 1   /   .if   /   .endm   /   any other .directive
        "directives": {"patterns": [
            {"match": "(?:^|(?<=[\\s(;{}]))(\\.(?i:define|undef))[ \\t]+([A-Za-z_][A-Za-z0-9_]*)",
             "captures": {
                 "1": {"name": "keyword.control.directive.padauk"},
                 "2": {"name": "entity.name.function.preprocessor.padauk"}}},
            {"begin": "(?:^|(?<=[\\s(;{}]))(\\.(?i:echo|warning|error|message))\\b",
             "beginCaptures": {"1": {"name": "keyword.control.directive.padauk"}},
             "end": "(?=//)|(?=/\\*)|$",
             "contentName": "string.unquoted.message.padauk"},
            {"name": "keyword.control.directive.padauk",
             "match": "(?:^|(?<=[\\s(;{}]))\\.(?i:" + alt(DIRECTIVES) + ")\\b"},
            {"name": "keyword.control.directive.padauk",
             "match": "(?:^|(?<=[\\s(;{}]))\\.[A-Za-z_][A-Za-z0-9_]*\\b"},
        ]},

        # myMacro macro p1, p2
        "macro-definition": {"patterns": [{
            "match": "^[ \\t]*([A-Za-z_][A-Za-z0-9_]*)[ \\t]+(?i:(macro))\\b",
            "captures": {
                "1": {"name": "entity.name.function.macro.padauk"},
                "2": {"name": "storage.type.macro.padauk"}},
        }]},

        # System_Clock EQU 8000000
        "equ-definition": {"patterns": [{
            "match": "^[ \\t]*([A-Za-z_][A-Za-z0-9_]*)[ \\t]+(?i:(equ))\\b",
            "captures": {
                "1": {"name": "entity.name.constant.padauk"},
                "2": {"name": "storage.type.equ.padauk"}},
        }]},

        # $ PA.6 Out, High;   /   $ TM2C SYSCLK, Period;
        "pin-config": {"patterns": [{
            "name": "meta.pin-config.padauk",
            "begin": "(?:^|(?<=[\\s;{}()]))(\\$)(?![0-9])",
            "beginCaptures": {"1": {"name": "keyword.control.pin-config.padauk"}},
            "end": "(?=;)|$",
            "patterns": [
                {"include": "#comments"},
                {"name": "support.constant.pin-config.padauk",
                 "match": "\\b(?i:" + alt(PINCONFIG) + ")\\b"},
                {"include": "#numbers"},
                {"include": "#registers"},
                {"include": "#chips"},
                {"include": "#bit-access"},
                {"include": "#operators"},
            ],
        }]},

        # void FPPA0(void) {   /   extern void initChain(void);
        "function-definition": {"patterns": [{
            "match": "\\b(?:(extern|static)[ \\t]+)?(void|bit|byte|word)[ \\t]+([A-Za-z_][A-Za-z0-9_]*)[ \\t]*(?=\\()",
            "captures": {
                "1": {"name": "storage.modifier.padauk"},
                "2": {"name": "storage.type.padauk"},
                "3": {"name": "entity.name.function.padauk"}},
        }]},

        # next:   /   rcv#i:
        "label": {"patterns": [{
            "match": "^[ \\t]*(?!(?:case|default)\\b)([A-Za-z_][A-Za-z0-9_]*)((?:#[A-Za-z0-9_]+)?)[ \\t]*(:)(?!:)",
            "captures": {
                "1": {"name": "entity.name.label.padauk"},
                "2": {"name": "entity.name.label.padauk"},
                "3": {"name": "punctuation.separator.label.padauk"}},
        }]},

        "strings": {"patterns": [
            {"name": "string.quoted.double.padauk", "begin": "\"", "end": "\"",
             "patterns": [{"name": "constant.character.escape.padauk", "match": "\\\\."}]},
            {"name": "string.quoted.single.padauk", "begin": "'", "end": "'",
             "patterns": [{"name": "constant.character.escape.padauk", "match": "\\\\."}]},
            # .ifidni IC, <PMS171B>
            {"name": "string.other.angle.padauk",
             "match": "(?<=[\\s,(])<[A-Za-z0-9_./\\\\-]+>"},
        ]},

        "numbers": {"patterns": [
            {"name": "constant.numeric.binary.padauk", "match": "\\b0[bB][01_]+\\b"},
            {"name": "constant.numeric.hex.padauk", "match": "\\b0[xX][0-9a-fA-F_]+\\b"},
            {"name": "constant.numeric.hex.padauk", "match": "\\b[0-9][0-9a-fA-F_]*[hH]\\b"},
            {"match": "\\b([0-9][0-9_]*(?:\\.[0-9]+)?)(" + alt(UNITS) + ")\\b",
             "captures": {
                 "1": {"name": "constant.numeric.decimal.padauk"},
                 "2": {"name": "keyword.other.unit.padauk"}}},
            {"name": "constant.numeric.decimal.padauk", "match": "\\b[0-9][0-9_]*\\.[0-9]+\\b"},
            {"name": "constant.numeric.decimal.padauk", "match": "\\b[0-9][0-9_]*\\b"},
        ]},

        # VDD=4500 mV,  IHRC=16000000 Hz
        "units": {"patterns": [{
            "match": "(?<=[0-9A-Za-z_])[ \\t]+(" + alt(UNITS) + ")\\b(?=[ \\t]*[,;)])",
            "captures": {"1": {"name": "keyword.other.unit.padauk"}},
        }]},

        "keywords": {"patterns": [
            {"name": "keyword.control.padauk", "match": "\\b(" + alt(CONTROL) + ")\\b"},
            {"name": "storage.type.padauk", "match": "\\b(" + alt(TYPES) + ")\\b"},
            {"name": "storage.modifier.padauk", "match": "\\b(" + alt(MODIFIERS) + ")\\b"},
            {"name": "storage.type.macro.padauk", "match": "\\b(?i:macro|equ)\\b"},
        ]},

        # Assembly mnemonics, only where a statement can start
        "instructions": {"patterns": [{
            "match": "(?:^|(?<=[;{}:)]))[ \\t]*\\b(" + alt(INSTRUCTIONS) + ")\\b",
            "captures": {"1": {"name": "keyword.other.instruction.padauk"}},
        }]},

        "registers": {"patterns": [
            {"name": "variable.language.register.padauk",
             "match": "\\b(" + alt(REGISTERS) + ")\\b"},
            # Port families: PA PB PC PAC PBPH PADIER ...
            {"name": "support.variable.sfr.padauk",
             "match": "\\bP[A-C](?:C|PH|PL|DIER)?\\b"},
            # Timers: TM2C TM2S TM2B TM3CT T16M ...
            {"name": "support.variable.sfr.padauk", "match": "\\bTM[0-9][A-Z]{1,3}\\b"},
            # ADC: ADCC ADCM ADCR ADCRH ADCRL ADCRGC ...
            {"name": "support.variable.sfr.padauk", "match": "\\bADC[A-Z]{0,4}\\b"},
            # PWM generators, incl. the LPWM variants
            {"name": "support.variable.sfr.padauk", "match": "\\bL?PWMG[0-9][A-Z]*\\b"},
            {"name": "support.variable.sfr.padauk", "match": "\\b(" + alt(SFR_MISC) + ")\\b"},
            {"name": "support.constant.padauk", "match": "\\b(" + alt(CONSTANTS) + ")\\b"},
        ]},

        # PMS171B, PFS154, PMS150C ...
        "chips": {"patterns": [{
            "name": "support.constant.chip.padauk",
            "match": "\\b(?:PMS|PFS|PMC|PFC|PDK)[0-9][0-9A-Za-z]*\\b",
        }]},

        # goto @F;  /  @B:
        "local-label": {"patterns": [{
            "name": "constant.language.local-label.padauk", "match": "@[A-Za-z0-9_]+",
        }]},

        # a##b concatenation, and the send#i form used inside .repeat/.forc bodies
        "macro-param": {"patterns": [
            {"name": "keyword.operator.concat.padauk", "match": "##"},
            {"match": "(?<=[A-Za-z0-9_])(#)([A-Za-z_][A-Za-z0-9_]*)",
             "captures": {
                 "1": {"name": "keyword.operator.macro.padauk"},
                 "2": {"name": "variable.parameter.macro.padauk"}}},
        ]},

        # potVal$1 - byte index into a word variable
        "byte-index": {"patterns": [{
            "match": "(?<=[A-Za-z0-9_\\]])(\\$)([0-9])",
            "captures": {
                "1": {"name": "keyword.operator.byte-index.padauk"},
                "2": {"name": "constant.numeric.padauk"}},
        }]},

        "function-call": {"patterns": [{
            "match": "\\b([A-Za-z_][A-Za-z0-9_]*)[ \\t]*(?=\\()",
            "captures": {"1": {"name": "entity.name.function.call.padauk"}},
        }]},

        "operators": {"patterns": [
            # compile-time assignment
            {"name": "keyword.operator.assignment.compile-time.padauk", "match": "=>"},
            {"name": "keyword.operator.padauk",
             "match": "<<=|>>=|<<|>>|<=|>=|==|!=|&&|\\|\\||\\+\\+|--|[-+*/%&|^!~<>]=|[-+*/%&|^!~<>=]"},
            {"name": "punctuation.separator.padauk", "match": "[,;]"},
        ]},

        # PA.6, payload.0, potStat[1].0, INC.FPPA_NUM
        "bit-access": {"patterns": [{
            "match": "(?<=[A-Za-z0-9_\\]])(\\.)([0-9]+|[A-Za-z_][A-Za-z0-9_]*)",
            "captures": {
                "1": {"name": "punctuation.accessor.padauk"},
                "2": {"name": "variable.other.bit.padauk"}},
        }]},

        # Bare macro invocations: `ADJUST_IC;` or `isPow2 RX_BUF_SIZE, RX_BUF_SIZE_IS_POW2`
        "macro-call": {"patterns": [
            {"match": "^[ \\t]*(?!(?:" + alt(NON_MACRO) + ")\\b)([A-Za-z_][A-Za-z0-9_]*)[ \\t]*(?=;)",
             "captures": {"1": {"name": "entity.name.function.macro.call.padauk"}}},
            {"match": "^[ \\t]*(?!(?:" + alt(NON_MACRO) + ")\\b)([A-Za-z_][A-Za-z0-9_]*)[ \\t]+(?![ \\t])(?![-+*/%&|^=<>!~?:,;.\\[\\]{}()])",
             "captures": {"1": {"name": "entity.name.function.macro.call.padauk"}}},
        ]},
    },
}

out = os.path.join(HERE, "syntaxes", "padauk.tmLanguage.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(grammar, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", out)


# --- language configuration -------------------------------------------------
# JavaScript RegExp has no (?i:...), so case-insensitive words are expanded
# into character classes: "if" -> "[iI][fF]".

def ci(word):
    return "".join(c if not c.isalpha() else "[%s%s]" % (c.lower(), c.upper())
                   for c in word)


BLOCK_OPENERS = ["if", "ifdef", "ifndef", "ifidn", "ifidni", "ifdif", "ifdifi",
                 "repeat", "forc", "for"]
BLOCK_CLOSERS = ["endif", "endm"]

open_dir = "|".join(ci(w) for w in sorted(BLOCK_OPENERS, key=len, reverse=True))
close_dir = "|".join(ci(w) for w in sorted(BLOCK_CLOSERS, key=len, reverse=True))
macro_def = "[A-Za-z_]\\w*[ \\t]+" + ci("macro") + "\\b"

langcfg = {
    "comments": {"lineComment": "//", "blockComment": ["/*", "*/"]},
    "brackets": [["{", "}"], ["[", "]"], ["(", ")"]],
    "autoClosingPairs": [
        {"open": "{", "close": "}"},
        {"open": "[", "close": "]"},
        {"open": "(", "close": ")"},
        {"open": "\"", "close": "\"", "notIn": ["string", "comment"]},
        {"open": "'", "close": "'", "notIn": ["string", "comment"]},
        {"open": "/*", "close": " */", "notIn": ["string"]},
    ],
    "surroundingPairs": [["{", "}"], ["[", "]"], ["(", ")"],
                         ["\"", "\""], ["'", "'"], ["<", ">"]],
    "folding": {
        "offSide": False,
        "markers": {
            "start": "^\\s*(?:\\.(?:" + open_dir + ")\\b|" + macro_def + ")",
            "end": "^\\s*\\.(?:" + close_dir + ")\\b",
        },
    },
    "indentationRules": {
        "increaseIndentPattern":
            "^\\s*(?:\\.(?:" + open_dir + "|" + ci("else") + "|" + ci("elseif") +
            ")\\b|" + macro_def + ").*$|^.*\\{[^}\"']*$",
        "decreaseIndentPattern":
            "^\\s*(?:\\.(?:" + close_dir + "|" + ci("else") + "|" + ci("elseif") +
            ")\\b|[})]).*$",
    },
    "onEnterRules": [
        {"beforeText": "^\\s*//.*$",
         "action": {"indent": "none", "appendText": "// "}},
    ],
}

out = os.path.join(HERE, "language-configuration.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(langcfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", out)
