# -*- coding: utf-8 -*-
"""Executor for ":" command-line input.

Disclaimer: parts of this module (the ``:%s`` substitute support) were generated
with AI assistance (claude-sonnet-5-5).
"""

# Standard Libraries
import re

# Third Party Libraries
from qtpy.QtWidgets import QDialog

# Project Libraries
from spyder_okvim.executor.executor_base import ExecutorSubBase
from spyder_okvim.utils.action_helpers import SubstituteMatch
from spyder_okvim.utils.jump_dialog import JumpListDialog
from spyder_okvim.utils.mark_dialog import MarkListDialog
from spyder_okvim.vim import VimState


def _split_substitute(arg: str) -> tuple[str, str, str]:
    """
    Split the argument of a ``:%s`` command into its three fields.

    Parameters
    ----------
    arg : str
        Text after the ``s``, for example ``/pattern/replacement/g``. The first
        character is the ``/`` delimiter.

    Returns
    -------
    tuple[str, str, str]
        Pattern, replacement and flags. Missing trailing fields are empty.
        ``\\/`` is unescaped to ``/``; all other backslash sequences are kept.
    """
    fields = [""]
    idx = 1
    while idx < len(arg):
        char = arg[idx]
        if char == "\\" and idx + 1 < len(arg):
            escaped = arg[idx + 1]
            fields[-1] += "/" if escaped == "/" else char + escaped
            idx += 2
            continue
        if char == "/" and len(fields) < 3:
            fields.append("")
        else:
            fields[-1] += char
        idx += 1

    while len(fields) < 3:
        fields.append("")
    pattern, replacement, flags = fields
    return pattern, replacement, flags


class ExecutorSubstituteConfirm(ExecutorSubBase):
    """
    Ask for confirmation of each match of a ``:s`` command with the ``c`` flag.

    The matches are collected up front. Every accepted replacement is applied
    at once, as its own undo step. The positions of the matches still to come
    are shifted by the change in text length caused by earlier replacements.

    Keys: ``y`` replace this match, ``n`` skip it, ``a`` replace this and all
    remaining matches, ``l`` replace this match and quit, ``q`` or ``Esc`` quit.

    Public methods: :meth:`start`, :meth:`finish`, :meth:`on_escape`.
    """

    def __init__(self, vim_status):
        super().__init__(vim_status)
        self.allow_leaderkey = False

        self.pattern = ""
        self.replacement = ""
        self.replace_all = False
        self.matches: list[SubstituteMatch] = []
        self.applied: list[SubstituteMatch] = []
        self.index = 0
        self.shift = 0
        self.pos_original = 0

    def start(
        self,
        pattern: str,
        replacement: str,
        replace_all: bool,
        matches: list[SubstituteMatch],
    ) -> None:
        """
        Begin a confirmation session and show the first match.

        Parameters
        ----------
        pattern : str
            Regular expression of the substitute command.
        replacement : str
            Replacement text of the substitute command.
        replace_all : bool
            Whether the ``g`` flag was given.
        matches : list[SubstituteMatch]
            The matches to offer, in document order. Must not be empty.
        """
        self.pattern = pattern
        self.replacement = replacement
        self.replace_all = replace_all
        self.matches = matches
        self.applied = []
        self.index = 0
        self.shift = 0
        self.pos_original = self.get_editor().textCursor().position()

        self.vim_status.sub_mode = self
        self._show_current()

    def __call__(self, txt: str) -> bool:
        """
        Handle one answer key.

        Parameters
        ----------
        txt : str
            Text in the command line, normally a single key.

        Returns
        -------
        bool
            Always True, so the command line is cleared after every key.
        """
        key = txt[-1]
        if key == "y":
            self._replace(self.matches[self.index : self.index + 1])
            self._next()
        elif key == "n":
            self._next()
        elif key == "a":
            self._replace(self.matches[self.index :])
            self.finish()
        elif key == "l":
            self._replace(self.matches[self.index : self.index + 1])
            self.finish()
        elif key == "q":
            self.finish()
        return True

    def on_escape(self) -> None:
        """Quit the session, keeping the replacements made so far."""
        self.finish()

    def _replace(self, items: list[SubstituteMatch]) -> None:
        """
        Replace the given matches in the document now.

        Parameters
        ----------
        items : list[SubstituteMatch]
            Consecutive matches, as collected before any replacement was made.
        """
        # Earlier replacements moved the text, so shift the stored positions.
        # Matches are in document order, so one running shift is enough.
        shifted = []
        for item in items:
            shifted.append(
                SubstituteMatch(
                    start=item.start + self.shift,
                    end=item.end + self.shift,
                    text=item.text,
                    block_no=item.block_no,
                )
            )
            self.shift += len(item.text) - (item.end - item.start)

        self.helper_action.apply_substitutions(shifted)
        self.applied.extend(items)

    def _next(self) -> None:
        """Advance to the next match, or finish after the last one."""
        self.index += 1
        if self.index >= len(self.matches):
            self.finish()
        else:
            self._show_current()

    def _show_current(self) -> None:
        """Select the current match and display the prompt."""
        vs = self.vim_status
        match = self.matches[self.index]
        start = match.start + self.shift
        end = match.end + self.shift
        vs.cursor.set_cursor_pos(start)
        vs.cursor.create_selection(start, end)
        vs.set_message(f"replace? ({self.index + 1}/{len(self.matches)}) y/n/a/q/l")

    def finish(self) -> None:
        """Leave the submode and report the result."""
        vs = self.vim_status
        vs.sub_mode = None
        editor = self.get_editor()
        editor.clear_extra_selections("vim_selection")

        applied = self.applied
        n_line = len({item.block_no for item in applied})
        if applied:
            # Vim leaves the cursor on the last substituted line
            block = editor.document().findBlockByNumber(applied[-1].block_no)
            vs.cursor.set_cursor_pos(block.position())
        else:
            vs.cursor.set_cursor_pos(self.pos_original)

        vs.last_substitute.set(self.pattern, self.replacement, self.replace_all)
        self.helper_motion.search(self.pattern)

        if not vs.is_normal():
            vs.to_normal()
        vs.set_message(f"{len(applied)} substitutions on {n_line} lines")

        self.matches = []
        self.applied = []


class ExecutorColon(ExecutorSubBase):
    """Interpreter for ``:`` commands entered in the command line."""

    def __init__(self, vim_status):
        super().__init__(vim_status)
        self.allow_leaderkey = False

        self.editor_widget = vim_status.editor_widget
        self.executor_confirm = ExecutorSubstituteConfirm(vim_status)

    def __call__(self, txt: str) -> bool:
        """Parse ``txt`` and execute the corresponding ex command.

        Args:
            txt: Command string typed by the user, including the trailing ``\r``.

        Returns:
            if return is True, Clear command line.

        """
        if txt[-1] == "\b":
            cmd_line = self.vim_status.cmd_line
            if len(txt) <= 2:
                self.vim_status.sub_mode = None
                return True
            else:
                cmd_line.setText(txt[:-2])
        if txt[-1] != "\r":
            return False

        if txt[0] != ":" or len(txt) <= 2:
            self.vim_status.sub_mode = None
            return True

        # ':' is saved to input cmd_info at ExecutorBase.
        # So we need only txt[1:].
        self.update_input_cmd_info(None, None, txt[1:])

        txt = txt[1:-1]  # remove :, \r

        # The substitute pattern may contain spaces, so it is handled before
        # the command name is split off at the first whitespace.
        if txt.startswith("%s/"):
            if not self.substitute(txt[2:], whole_file=True):
                self.vim_status.sub_mode = None
            return True
        if txt.startswith("s/"):
            if not self.substitute(txt[1:], whole_file=False):
                self.vim_status.sub_mode = None
            return True

        cmd = txt.split(None, 1)
        args = cmd[1] if len(cmd) > 1 else ""
        cmd = cmd[0]

        if cmd.isdigit():
            self.goto_line(int(cmd))
        else:
            for symbol, text in self.SYMBOLS_REPLACEMENT.items():
                cmd = cmd.replace(symbol, text)

            try:
                method = self.__getattribute__(cmd)
            except AttributeError:
                print("unknown command", cmd)
            else:
                method(args)

        self.vim_status.sub_mode = None

        return True

    def w(self, arg=""):
        """Save current file."""
        self.save_current_file()
        self.vim_status.cursor.draw_vim_cursor()

    def q(self, arg=""):
        """Close current file."""
        self.close_current_file()
        self.vim_status.set_focus_to_vim()

    def qexclamation(self, arg=""):
        """Close current file without saving."""
        # TODO :
        self.close_current_file()
        self.vim_status.set_focus_to_vim()

    def wq(self, arg=""):
        """Save and close current file."""
        self.w(arg)
        self.q()

    def n(self, args=""):
        """Create new file."""
        self.create_new_file()
        self.vim_status.set_focus_to_vim()

    def marks(self, arg=""):
        """Show bookmarks and jump to the selected one."""
        vs = self.vim_status
        marks = vs.bookmark_manager.list_bookmarks()

        dlg = MarkListDialog(marks, vs.main)
        result = dlg.exec_()
        # When running tests ``exec_`` is patched to return ``None`` so the
        # selected mark must be retrieved regardless of the returned value.
        # Only reject the action explicitly when ``QDialog.Rejected`` (0) is
        # returned.
        mark = (
            dlg.get_selected_mark()
            if result is None or result == QDialog.Accepted
            else None
        )
        if mark:
            vs.push_jump()
            vs.jump_to_bookmark(mark)
            vs.push_jump()

        vs.set_focus_to_vim()

    def jumps(self, arg=""):
        """Display the jumplist in a popup dialog."""
        vs = self.vim_status

        dlg = JumpListDialog(vs, vs.main)
        dlg.exec_()

        vs.set_focus_to_vim()

    def substitute(self, arg: str, whole_file: bool = True) -> bool:
        """
        Run ``:%s/pat/rep/[flags]`` or ``:s/pat/rep/[flags]``.

        The flags are ``g`` (every match in a line) and ``c`` (confirm each
        match), alone or combined as ``gc`` or ``cg``.

        Parameters
        ----------
        arg : str
            Text after ``s``, starting with the ``/`` delimiter.
        whole_file : bool
            Process every line (``:%s``) if True, otherwise only the current
            line (``:s``).

        Returns
        -------
        bool
            True if the ``c`` flag started an interactive confirmation, which
            keeps the confirmation submode active.
        """
        vs = self.vim_status
        pattern, replacement, flags = _split_substitute(arg)
        flags = flags.strip()

        if not pattern:
            vs.set_message("E35: No previous regular expression")
            return False
        if not set(flags) <= {"g", "c"} or len(set(flags)) != len(flags):
            vs.set_message(f"E488: Trailing characters: {flags}")
            return False

        replace_all = "g" in flags
        if "c" in flags:
            return self._start_confirm(pattern, replacement, replace_all, whole_file)

        self.helper_action.run_substitute(pattern, replacement, replace_all, whole_file)
        return False

    def _start_confirm(
        self, pattern: str, replacement: str, replace_all: bool, whole_file: bool
    ) -> bool:
        """
        Collect the matches and start asking for confirmation.

        Parameters
        ----------
        pattern : str
            Regular expression (Python ``re`` syntax).
        replacement : str
            Replacement text.
        replace_all : bool
            Offer every match in a line if True, otherwise only the first.
        whole_file : bool
            Process every line if True, otherwise only the current line.

        Returns
        -------
        bool
            True if the confirmation submode was started.
        """
        vs = self.vim_status

        block_range = None
        if not whole_file:
            block_no = self.get_editor().textCursor().blockNumber()
            block_range = (block_no, block_no)

        try:
            matches = self.helper_action.collect_substitutions(
                pattern, replacement, replace_all, block_range
            )
        except re.error as err:
            vs.set_message(f"E486: Invalid pattern: {err}")
            return False

        if not matches:
            vs.set_message(f"E486: Pattern not found: {pattern}")
            return False

        self.executor_confirm.start(pattern, replacement, replace_all, matches)
        return True

    def goto_line(self, num):
        """Move cursor according to :number command."""
        vs = self.vim_status
        vs.push_jump()
        if vs.vim_state == VimState.NORMAL:
            motion_info = self.helper_motion.G(num, True)
            vs.cursor.apply_motion_info_in_normal(motion_info)
        elif vs.vim_state in (VimState.VISUAL, VimState.VLINE):
            motion_info = self.helper_motion.j(num)
            if vs.vim_state == VimState.VISUAL:
                vs.cursor.apply_motion_info_in_visual(motion_info)
            else:
                vs.cursor.apply_motion_info_in_vline(motion_info)
            vs.to_normal()
        vs.push_jump()
