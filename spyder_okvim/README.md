# Spyder OkVim

Vim-style modal editing for the [Spyder](https://www.spyder-ide.org/) IDE.

OkVim is a Spyder plugin (`spyder_okvim`, version 0.10.6, MIT licensed, upstream
author ok97465) that lets you drive Spyder's code editor with Vim commands. It
adds a command line and a mode indicator to Spyder's status bar and translates
typed keys into cursor movements, edits, and Spyder actions such as running a
cell or formatting a file.

Upstream project: <https://github.com/ok97465/spyder_okvim>

> This repository is a working copy of the installed package inside
> `site-packages`. See [Working on this copy](#working-on-this-copy).

## Requirements

- Python 3.9 or newer
- Spyder 6.1.0 or newer
- `qtpy` (PyQt5, PySide2 or PySide6 backend, whichever Spyder uses)

If `spyder-vim` is installed, uninstall it first to avoid conflicts.

## Installation

```bash
pip install spyder-okvim
```

Spyder discovers the plugin through the `spyder.plugins` entry point
`spyder_okvim = spyder_okvim.spyder.plugin:OkVim`. Restart Spyder after
installing or changing the plugin.

## How it works

Spyder's editor keeps keyboard focus in **INSERT** mode. Every other mode is
handled by a one-line command box in the status bar.

- Pressing `Esc` anywhere in the editor moves focus to the command box and
  returns to **NORMAL** mode.
- Each keystroke typed into the command box is passed to an executor chosen by
  the current mode: normal, visual, visual-line, or the active submode (for
  example the pending part of `d`, `g`, `f` or `/`).
- Counts work as in Vim (`3w`, `2d2W`). Nested counts are multiplied.
- When a command is complete the command box is cleared.

Supported modes: Normal, Visual, Visual Line, and Insert (editor focused).

### Starting in Normal mode

As in Vim, the editor starts in **NORMAL** mode. Whenever the editor receives
focus without a command asking for it (Spyder start, clicking into the editor,
switching tabs or files), focus is moved on to the command box
(`spyder/editor_focus.py`). Consequences:

- After a mouse click you are in Normal mode; press `i`, `a`, `o`, `I`, `A` or
  `O` to type.
- Commands that enter Insert mode on purpose (`i`, `a`, `o`, `c`-family, ...)
  are not redirected.
- Focus returning from a popup (menu, completion list) is left alone, so
  typing is not interrupted.
- There is no preference to turn this off. Remove the filter installation in
  `OkVim.on_initialize` (`spyder/plugin.py`) to restore the old behaviour.

## Features

### Motions

| Group | Keys |
|---|---|
| Character and line | `h j k l`, `0 ^ $`, `G`, `gg`, `:{number}` |
| Words | `w W b B e` |
| Screen and scrolling | `H M L`, `Ctrl-D Ctrl-U Ctrl-F Ctrl-B`, `zt zz zb` |
| Find on line | `f F t T ; ,` |
| Matching pair | `%` |
| Search | `/pattern`, `n`, `N`, `*`, `#` (`n`/`N` also follow `:s`) |
| Whitespace keys | `Enter`, `Space`, `Backspace` |
| Python structure | `[[ ]]` (def), `{{ }}` (block), `[c ]c` (cell), `[d ]d` (warning or error) |

### Operators and edits

- `d`, `c`, `y`, `<`, `>`, `gu`, `gU`, `g~`, `gc` (toggle comment), each combined
  with any motion or text object, for example `diw`, `c%`, `ygg`, `d2w`.
- Line forms: `dd`, `cc`, `yy`, `<<`, `>>`, `gcc`.
- Single edits: `x s r C D S ~ J p P`, `u`, `Ctrl-R`, and `.` (repeat).
- `&` and `g&` repeat the last `:s` (see [Substitute](#substitute-spattern-replacement-g)).
- `Ctrl-A` and `Ctrl-X` increment and decrement the number under the cursor.

### Text objects

`iw iW aw`, `i( a(` (also `b`), `i{ a{` (also `B`), `i[ a[`, `i' a'`, `i" a"`, and
`ic` for the current `# %%` cell (`yic`, `dic`, `cic`).

### Registers, marks, macros

- Registers via `"{name}`. The `"+` register is the system clipboard.
- Marks: `m{a-z}` sets a file-local mark, `m{A-Z}` sets a global mark that is
  saved to `bookmarks.json` in the plugin config folder. Jump with `'` or a
  backtick. `:marks` lists them.
- Jump list: `Ctrl-O` and `Ctrl-I` move back and forward. Entries are added by
  `Ctrl-P` file jumps and `gd`. `:jumps` lists them.
- Macros: `q{register}` to record and `@{register}` to replay. Macro support is
  experimental.

### vim-surround

- `ys{motion}{char}` add, `ds{char}` delete, `cs{old}{new}` change.
- `S{char}` in visual mode.
- Characters: `' " ( ) [ ] { }`, plus `b` for `)` and `B` for `}`.

### Jump motions

- **EasyMotion**: press the leader key twice, then `w`, `b`, `j`, `k`,
  `f{char}` or `F{char}`. Labels appear on the targets. It works with operators.
- **Sneak**: `s{two chars}` jumps forward and `S{two chars}` jumps backward
  within the viewport. Extra matches are labelled and reached with `;`. Use `z`
  instead of `s` after an operator, because `s` belongs to surround there.
  Controlled by the `use_sneak` option.

### Spyder integration

| Key | Action |
|---|---|
| `<leader>f` | Format the current file |
| `<leader>b` | Toggle breakpoint |
| `<leader>r` | Run selection or current line |
| `<leader><Enter>` | Run cell and advance |
| `<leader>p` | Spyder switcher |
| `<leader>s` | Spyder symbol switcher |
| `<leader>i` | Auto-import |
| `K` | Inspect the object under the cursor |
| `gd` | Go to definition |
| `gt`, `gT` | Next and previous file tab |
| `ZZ`, `ZQ` | Save and close, close |
| `Ctrl-P` | Fuzzy file finder |
| `Ctrl-C` | Clear search highlight and tooltip |

The leader key defaults to `Space`.

### Ex commands

`:w`, `:q`, `:q!`, `:wq`, `:n` (new file), `:{number}`, `:marks`, `:jumps`,
and `:%s/pattern/replacement/[gc]` (substitute in the whole file) or
`:s/pattern/replacement/[gc]` (substitute in the current line).

Unknown commands are silently ignored.

#### Substitute: `:%s/pattern/replacement/[g]`

- `:%s/...` applies to the whole document. `:s/...` applies to the current line
  only, as in Vim. These are the only supported ranges.
- `pattern` is a regular expression (Python `re` syntax).
- Without `g`, only the first match on each line is replaced. With `g`, every
  match on each line is replaced.
- The replacement may use `\1`..`\9` for capture groups, `&` (or `\0`) for the
  whole match, and `\t` for a tab. `\&`, `\\` and `\/` give a literal `&`, `\`
  and `/`.
- The delimiter `/` can be escaped as `\/` in the pattern.
- The whole substitution is a single undo step.
- Case sensitivity follows the `ignorecase` and `smartcase` options.
- After a successful `:s`, the pattern becomes the current search pattern: its
  matches are highlighted and `n` / `N` jump between them across the whole
  document (wrapping around). After a `g` substitution usually no matches are
  left, as in Vim.

#### Confirming each match: the `c` flag

Add `c` to the flags (`:%s/a/b/c`, `:%s/a/b/gc` or `:%s/a/b/cg`) to be asked
about every match. The match is highlighted, the cursor jumps to it and the
message area shows `replace? (3/12) y/n/a/q/l`. Without `g` only the first match
per line is offered.

| Key | Action |
|---|---|
| `y` | Replace this match and go to the next |
| `n` | Skip this match |
| `a` | Replace this and all remaining matches |
| `l` | Replace this match and quit |
| `q`, `Esc` | Quit, keeping the replacements accepted so far |

Each `y` is applied immediately and is its own undo step, as in Vim; `a` applies
all remaining matches as one step. If nothing was accepted the cursor returns to
where it started; otherwise it moves to the last changed line. The pattern
becomes the search pattern and the command is remembered for `&` and `g&`, but
`g&` does not ask for confirmation again (the `c` flag is not stored).
Unknown keys are ignored. `E486` is reported if the pattern is invalid or has no
match.

#### Repeating a substitution

| Key | Action |
|---|---|
| `&` | Repeat the last `:s` on the current line, without flags |
| `g&` | Repeat the last `:s` on the whole file, with the flags of the original command (`g` is kept) |

Without the `g` flag, `:%s/a/b/` replaces the first match per line. To change
the next occurrence by hand, use `n` to jump to it, or `&` on the line. `.` does
not repeat `:s` (as in Vim). `&` and `g&` do not overwrite the stored flags.
Without a previous `:s` they report `E35: No previous regular expression`.

## Configuration

Open *Preferences > OkVim* in Spyder. Options (section `spyder_okvim`):

- `ignorecase`, `smartcase` for search
- `use_sneak`
- `highlight_yank` and its duration (default 400 ms)
- Colors for the cursor, selection, search matches and yanked text
- `leader_key`

`Ctrl-P` clashes with a Spyder global shortcut by default. Reassign Spyder's
binding if you want to use the fuzzy finder.

## Known limitations

- Does not work while the Spyder editor is undocked from the main window.
- Macro recording and playback are experimental.
- `:q!` and `ZQ` close the file the same way as `:q` and `ZZ` without a
  separate discard path (marked `TODO` in the source).
- `:s` supports only the whole-file (`%`) and current-line ranges and only the
  `g` and `c` flags. `:s` uses Python `re`
  syntax while `/` search uses Qt's regular expressions, so exotic patterns may
  behave slightly differently when `n` / `N` follow a `:s`.

## Source layout

```text
spyder_okvim/
├── __init__.py            package version
├── conftest.py            pytest fixtures with a fake Spyder editor stack
├── spyder/                Spyder integration
│   ├── plugin.py          OkVim plugin class, status-bar widget, Esc shortcut
│   ├── vim_widgets.py     command line, mode label, shortcuts, macro worker
│   ├── editor_focus.py    event filter that starts Normal mode on editor focus
│   ├── config.py          option names and defaults
│   └── confpage.py        preferences page
├── executor/              key parsing, one class per mode or submode
│   ├── executor_base.py   regex parsing, symbol-to-method mapping, submodes
│   ├── executor_normal.py normal mode
│   ├── executor_visual.py / executor_vline.py
│   ├── executor_sub.py    d/c/y motions, g, z, Z, f/t, sneak, search, [ ]
│   ├── executor_colon.py  ":" commands
│   ├── executor_leader.py leader key actions
│   ├── executor_easymotion.py
│   ├── executor_surround.py
│   ├── mixins.py          shared movement and selection commands
│   └── decorators.py      @submode helper
├── vim/                   core state
│   ├── status.py          VimStatus, the shared state object
│   ├── state.py           mode enum and small data classes
│   ├── cursor.py          block cursor, selections, yank highlight
│   └── macro.py, search.py, label.py
└── utils/                 helpers
    ├── motion_helpers.py  cursor motion calculations
    ├── action_helpers.py  edits (yank, put, delete, surround, case, comment)
    ├── search_helpers.py  search and sneak
    ├── bookmark_manager.py, jump_list.py, cell_helpers.py, easymotion.py
    └── file_search, list_dialog, jump_dialog, mark_dialog (dialogs)
```

### Design notes

- **Executors.** An executor matches input with `(\d*)(key)` and calls the
  method named after the key. Symbols map to names through
  `SYMBOLS_REPLACEMENT` (`$` becomes `dollar`, `^` becomes `caret`, `/` becomes
  `slash`). A method can return `RETURN_EXECUTOR_METHOD_INFO` to enter a
  submode.
- **Operators and motions are decoupled.** An operator registers a deferred
  function. The follow-up motion computes a `MotionInfo` (cursor position,
  selection range, `MotionType`) and the deferred function applies it.
- **Dot repeat.** The last change's command text and the editor keys typed
  afterwards are stored in `DotCmdInfo` and replayed.
- **State.** `VimStatus` owns the mode, registers, jump list, bookmarks, macro
  manager and search state, and is passed to every executor and helper.

## Working on this copy

This directory is the installed package, so edits take effect the next time
Spyder starts. There is no hot reload: restart Spyder after each change.

Because it lives in `site-packages`:

- `pip install -U spyder-okvim`, `pip uninstall spyder-okvim` or a reinstall
  can overwrite or delete files here. Commit your work first.
- The package is not installed in editable mode, so the code in `site-packages`
  is the code Spyder runs.

### Tests

The tests use `pytest` and `pytest-qt` and build a fake Spyder editor stack in
`conftest.py`. They live in `executor/tests`, `spyder/tests` and `utils/tests`.

```bash
pip install pytest pytest-qt
python -m pytest --pyargs spyder_okvim
```

A display (or `QT_QPA_PLATFORM=offscreen`) is needed to create the Qt widgets.

## License

MIT, see the upstream project.
