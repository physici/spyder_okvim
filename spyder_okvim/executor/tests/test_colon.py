# -*- coding: utf-8 -*-
"""Tests for :mod:`spyder_okvim.executor.executor_colon`.

Disclaimer: the substitute tests were generated with AI assistance
(claude-sonnet-5-5).
"""

# Third Party Libraries
import pytest
from qtpy.QtCore import QEvent, Qt
from qtpy.QtGui import QKeyEvent

# Project Libraries
from spyder_okvim.executor.executor_colon import _split_substitute


@pytest.mark.parametrize(
    "text, cmd_list, cmd_line_expected",
    [
        ("", [":", "k", "k"], ":kk"),
        ("", [":", "k", "k", Qt.Key_Escape], ""),
    ],
)
def test_colon_cmd(vim_bot, text, cmd_list, cmd_line_expected):
    """Test colon command."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text(text)
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()

    cmd_line = vim.vim_cmd.commandline
    for cmd in cmd_list:
        if isinstance(cmd, str):
            qtbot.keyClicks(cmd_line, cmd)
        else:
            qtbot.keyPress(cmd_line, cmd)

    assert cmd_line.text() == cmd_line_expected


@pytest.mark.parametrize(
    "text, cmd_list",
    [
        ("", [":", Qt.Key_Return]),
        ("", [":", Qt.Key_Left, "d", Qt.Key_Enter]),
    ],
)
def test_colon_corner_case_cmd(vim_bot, text, cmd_list):
    """Test colon command."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text(text)
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()

    cmd_line = vim.vim_cmd.commandline
    for cmd in cmd_list:
        if isinstance(cmd, str):
            qtbot.keyClicks(cmd_line, cmd)
        else:
            qtbot.keyPress(cmd_line, cmd)

    assert cmd_line.text() == ""
    assert vim.vim_cmd.vim_status.sub_mode is None


def test_colon_w_command(vim_bot):
    """Test :w."""
    main, editor_stack, editor, vim, qtbot = vim_bot
    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, ":")
    qtbot.keyClicks(cmd_line, "w")
    qtbot.keyPress(cmd_line, Qt.Key_Return)
    main.editor.save.assert_called_once_with()
    main.editor.save.reset_mock()


def test_colon_q_command(vim_bot):
    """Test :q."""
    main, editor_stack, editor, vim, qtbot = vim_bot
    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, ":")
    qtbot.keyClicks(cmd_line, "q")
    qtbot.keyPress(cmd_line, Qt.Key_Return)
    main.editor.close_file.assert_called_once_with()
    main.editor.close_file.reset_mock()


def test_colon_q_command_without_close_file(vim_bot):
    """Test :q when close_file API is missing."""
    main, editor_stack, editor, vim, qtbot = vim_bot
    orig_close_file = main.editor.close_file
    delattr(main.editor, "close_file")
    with pytest.raises(AttributeError):
        vim.vim_cmd.executor_normal_cmd.executor_colon.q()
    main.editor.close_file = orig_close_file


def test_colon_qexclamation_command(vim_bot):
    """Test :q!."""
    main, editor_stack, editor, vim, qtbot = vim_bot
    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, ":")
    qtbot.keyClicks(cmd_line, "q")
    qtbot.keyClicks(cmd_line, "!")
    qtbot.keyPress(cmd_line, Qt.Key_Return)
    main.editor.close_file.assert_called_once_with()
    main.editor.close_file.reset_mock()


def test_colon_wq_command(vim_bot):
    """Test :wq."""
    main, editor_stack, editor, vim, qtbot = vim_bot
    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, ":")
    qtbot.keyClicks(cmd_line, "w")
    qtbot.keyClicks(cmd_line, "q")
    qtbot.keyPress(cmd_line, Qt.Key_Return)
    main.editor.save.assert_called_once_with()
    main.editor.close_file.assert_called_once_with()
    main.editor.save.reset_mock()
    main.editor.close_file.reset_mock()


def test_colon_n_command(vim_bot):
    """Test :n."""
    main, editor_stack, editor, vim, qtbot = vim_bot
    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, ":")
    qtbot.keyClicks(cmd_line, "n")
    qtbot.keyPress(cmd_line, Qt.Key_Return)
    main.editor.new.assert_called_once_with()


def test_colon_backspace_command(vim_bot):
    """Test backspace in ex cmd."""
    main, editor_stack, editor, vim, qtbot = vim_bot
    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, ":")
    qtbot.keyClicks(cmd_line, "n")
    qtbot.keyPress(cmd_line, Qt.Key_Backspace)

    assert cmd_line.text() == ":"
    assert vim.vim_cmd.vim_status.sub_mode is not None

    qtbot.keyPress(cmd_line, Qt.Key_Backspace)

    assert cmd_line.text() == ""
    assert vim.vim_cmd.vim_status.sub_mode is None


def test_colon_marks_command(vim_bot, monkeypatch):
    """Test :marks opens dialog and jumps to the selected mark."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("a\nb\nc\n")
    vs = vim.vim_cmd.vim_status
    vs.cursor.set_cursor_pos(2)
    vs.reset_for_test()

    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, "ma")
    vs.cursor.set_cursor_pos(0)

    # Project Libraries
    from spyder_okvim.utils import mark_dialog

    monkeypatch.setattr(mark_dialog.MarkListDialog, "exec_", lambda self: None)
    monkeypatch.setattr(
        mark_dialog.MarkListDialog, "get_selected_mark", lambda self: "a"
    )

    qtbot.keyClicks(cmd_line, ":")
    qtbot.keyClicks(cmd_line, "marks")
    qtbot.keyPress(cmd_line, Qt.Key_Return)

    assert editor.textCursor().position() == 2


def test_colon_marks_escape_focus(vim_bot, monkeypatch):
    """Focus returns to command line when dialog closed with ESC."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("a\nb\nc\n")
    vs = vim.vim_cmd.vim_status
    pos_before = editor.textCursor().position()

    # Project Libraries
    from spyder_okvim.utils import mark_dialog

    monkeypatch.setattr(mark_dialog.MarkListDialog, "exec_", lambda self: 0)
    # Return a mark even though the dialog was rejected to ensure the
    # executor ignores it when ESC is pressed.
    monkeypatch.setattr(
        mark_dialog.MarkListDialog, "get_selected_mark", lambda self: "a"
    )

    called = []
    monkeypatch.setattr(vs, "jump_to_bookmark", lambda *a: called.append(True))

    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, ":")
    qtbot.keyClicks(cmd_line, "marks")
    qtbot.keyPress(cmd_line, Qt.Key_Return)

    assert editor.textCursor().position() == pos_before
    assert cmd_line.hasFocus()
    assert not called


def test_colon_jumps_dialog_navigation(vim_bot, monkeypatch):
    """Jump dialog tracks jumplist navigation across files."""
    _, stack, editor, vim, qtbot = vim_bot
    vs = vim.vim_cmd.vim_status
    orig_file = stack.get_current_filename()
    stack.set_current_filename(stack.get_filenames()[0])
    vs.cursor.set_cursor_pos(0)
    vs.reset_for_test()

    # Create jumps across multiple files
    vs.push_jump()
    stack.set_current_filename(stack.get_filenames()[1])
    vs.push_jump()
    stack.set_current_filename(stack.get_filenames()[2])
    vs.push_jump()

    # Project Libraries
    from spyder_okvim.utils import jump_dialog

    captured = {}

    def fake_exec(self):
        captured["dlg"] = self
        return None

    monkeypatch.setattr(jump_dialog.JumpListDialog, "exec_", fake_exec)

    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, ":jumps")
    qtbot.keyPress(cmd_line, Qt.Key_Return)

    dlg = captured["dlg"]
    dlg.list_viewer.setFocus()
    assert dlg.list_model.rowCount() == 3
    assert dlg.list_viewer.currentIndex().row() == vs.jump_list.index - 1

    qtbot.keyPress(dlg.list_viewer, Qt.Key_O, modifier=Qt.ControlModifier)
    assert stack.get_current_filename() == stack.get_filenames()[1]
    assert dlg.list_viewer.currentIndex().row() == vs.jump_list.index - 1

    qtbot.keyPress(dlg.list_viewer, Qt.Key_I, modifier=Qt.ControlModifier)
    assert stack.get_current_filename() == stack.get_filenames()[2]
    assert dlg.list_viewer.currentIndex().row() == vs.jump_list.index - 1

    dlg.reject()
    assert cmd_line.hasFocus()

    # Restore state for other tests
    stack.set_current_filename(orig_file)


@pytest.mark.parametrize(
    "arg, expected",
    [
        ("/a/b/g", ("a", "b", "g")),
        ("/a/b/", ("a", "b", "")),
        ("/a/b", ("a", "b", "")),
        ("/a", ("a", "", "")),
        ("/a\\/b/c\\/d/g", ("a/b", "c/d", "g")),
        ("/a\\\\/b/", ("a\\\\", "b", "")),
        ("/(x)/\\1\\&/", ("(x)", "\\1\\&", "")),
    ],
)
def test_split_substitute(arg, expected):
    """Split a substitute argument into pattern, replacement and flags."""
    assert _split_substitute(arg) == expected


def _run_ex(vim, qtbot, command):
    """Type an ex command followed by Enter into the command line."""
    cmd_line = vim.vim_cmd.commandline
    qtbot.keyClicks(cmd_line, ":")
    qtbot.keyClicks(cmd_line, command)
    qtbot.keyPress(cmd_line, Qt.Key_Return)


@pytest.mark.parametrize(
    "text, command, expected",
    [
        # Without g only the first match per line is replaced
        ("aa a\nb a a\n", "%s/a/X/", "Xa a\nb X a\n"),
        ("aa a\nb a a\n", "%s/a/X/g", "XX X\nb X X\n"),
        # Spaces in pattern and replacement
        ("one two\n", "%s/one two/three four/", "three four\n"),
        # Capture groups, whole-match and escaped ampersand
        ("ab cd\n", "%s/(\\w)(\\w)/\\2\\1/g", "ba dc\n"),
        ("foo\n", "%s/foo/[&]/", "[foo]\n"),
        ("foo\n", "%s/foo/\\&/", "&\n"),
        # Escaped delimiter and empty replacement
        ("a/b\n", "%s/\\//-/", "a-b\n"),
        ("remove me\n", "%s/ me//", "remove\n"),
        # Missing trailing delimiter
        ("abc\n", "%s/b/X", "aXc\n"),
    ],
)
def test_colon_substitute(vim_bot, text, command, expected):
    """Test :%s replaces text in the whole document."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text(text)
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()

    _run_ex(vim, qtbot, command)

    assert editor.toPlainText() == expected
    assert vim.vim_cmd.commandline.text() == ""
    assert vim.vim_cmd.vim_status.sub_mode is None


def test_colon_substitute_undo_is_single_step(vim_bot):
    """The whole substitution is undone with one undo."""
    _, _, editor, vim, qtbot = vim_bot
    text = "a\na\na\n"
    editor.set_text(text)
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()

    _run_ex(vim, qtbot, "%s/a/b/")
    assert editor.toPlainText() == "b\nb\nb\n"

    editor.undo()
    assert editor.toPlainText() == text


def test_colon_substitute_cursor_on_last_changed_line(vim_bot):
    """The cursor ends on the last substituted line."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("a\nb\na\nb\n")
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()

    _run_ex(vim, qtbot, "%s/a/x/")

    assert editor.textCursor().blockNumber() == 2


@pytest.mark.parametrize(
    "command, message",
    [
        ("%s/zzz/y/", "E486: Pattern not found: zzz"),
        ("%s/(/y/", "E486: Invalid pattern"),
        ("%s/a/b/x", "E488: Trailing characters: x"),
        ("%s//b/", "E35: No previous regular expression"),
    ],
)
def test_colon_substitute_errors(vim_bot, command, message):
    """Errors are reported in the status bar and leave the text unchanged."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("abc\n")
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()

    _run_ex(vim, qtbot, command)

    assert editor.toPlainText() == "abc\n"
    assert message in vim.vim_cmd.vim_status.msg_label.text()


@pytest.mark.parametrize(
    "start_block, command, expected",
    [
        # Only the first match in the current line is replaced
        (0, "s/temp/temperature", "temperature temp\ntemp temp\n"),
        (1, "s/temp/temperature", "temp temp\ntemperature temp\n"),
        # With g every match in the current line is replaced
        (1, "s/temp/T/g", "temp temp\nT T\n"),
        # Pattern with spaces
        (0, "s/temp temp/x y/", "x y\ntemp temp\n"),
    ],
)
def test_colon_substitute_current_line(vim_bot, start_block, command, expected):
    """Test :s works on the current line only."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("temp temp\ntemp temp\n")
    block = editor.document().findBlockByNumber(start_block)
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(block.position())
    vim.vim_cmd.vim_status.reset_for_test()

    _run_ex(vim, qtbot, command)

    assert editor.toPlainText() == expected
    assert vim.vim_cmd.commandline.text() == ""
    assert vim.vim_cmd.vim_status.sub_mode is None


def test_colon_substitute_current_line_not_found(vim_bot):
    """:s reports an error if the current line has no match."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("abc\ntemp\n")
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()

    _run_ex(vim, qtbot, "s/temp/x/")

    assert editor.toPlainText() == "abc\ntemp\n"
    assert "E486: Pattern not found: temp" in vim.vim_cmd.vim_status.msg_label.text()


def test_colon_substitute_sets_search_pattern(vim_bot):
    """n and N follow the pattern of the last :s command."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("foo bar foo\nbaz foo\n")
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()
    cmd_line = vim.vim_cmd.commandline

    # Replacement equals the pattern, so matches remain at 0, 8 and 16
    _run_ex(vim, qtbot, "%s/foo/foo/")
    assert vim.vim_cmd.vim_status.search.txt_searched == "foo"
    assert editor.textCursor().position() == 12

    qtbot.keyClicks(cmd_line, "n")
    assert editor.textCursor().position() == 16

    qtbot.keyClicks(cmd_line, "N")
    assert editor.textCursor().position() == 8


def test_ampersand_repeats_on_current_line_without_flags(vim_bot):
    """& repeats the last :s on the current line only, without the g flag."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("a a\na a\na a\n")
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()
    cmd_line = vim.vim_cmd.commandline

    _run_ex(vim, qtbot, "%s/a/X/")
    assert editor.toPlainText() == "X a\nX a\nX a\n"

    qtbot.keyClicks(cmd_line, "gg")
    qtbot.keyClicks(cmd_line, "&")
    assert editor.toPlainText() == "X X\nX a\nX a\n"


def test_g_ampersand_repeats_on_whole_file(vim_bot):
    """g& repeats the last :s on every line."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("a a\na a\n")
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()
    cmd_line = vim.vim_cmd.commandline

    _run_ex(vim, qtbot, "%s/a/X/")
    assert editor.toPlainText() == "X a\nX a\n"

    qtbot.keyClicks(cmd_line, "g&")
    assert editor.toPlainText() == "X X\nX X\n"


def test_repeat_substitute_keeps_original_flags(vim_bot):
    """& does not overwrite the flags that g& reuses."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("a\n")
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()
    cmd_line = vim.vim_cmd.commandline

    _run_ex(vim, qtbot, "%s/a/aa/g")
    assert editor.toPlainText() == "aa\n"

    # Without g only the first "a" is doubled
    qtbot.keyClicks(cmd_line, "&")
    assert editor.toPlainText() == "aaa\n"

    # g& uses the g flag of the original command again
    qtbot.keyClicks(cmd_line, "g&")
    assert editor.toPlainText() == "aaaaaa\n"


@pytest.mark.parametrize("keys", ["&", "g&"])
def test_repeat_substitute_without_previous(vim_bot, keys):
    """& and g& report an error if there was no previous :s."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text("abc\n")
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(0)
    vim.vim_cmd.vim_status.reset_for_test()

    qtbot.keyClicks(vim.vim_cmd.commandline, keys)

    assert editor.toPlainText() == "abc\n"
    assert (
        "E35: No previous regular expression" in vim.vim_cmd.vim_status.msg_label.text()
    )


def _start_confirm(vim_bot, text, command, pos=0):
    """Set up the editor, run a substitute command and return the pieces."""
    _, _, editor, vim, qtbot = vim_bot
    editor.set_text(text)
    vim.vim_cmd.vim_status.cursor.set_cursor_pos(pos)
    vim.vim_cmd.vim_status.reset_for_test()

    _run_ex(vim, qtbot, command)
    return editor, vim, qtbot


@pytest.mark.parametrize(
    "text, command, answers, expected, message",
    [
        # Without g only the first match per line is offered
        ("a a\na a\n", "%s/a/X/c", "yy", "X a\nX a\n", "2 substitutions on 2 lines"),
        # With g every match is offered, in either flag order
        ("a a\na a\n", "%s/a/X/gc", "ynyy", "X a\nX X\n", "3 substitutions on 2 lines"),
        ("a a\n", "%s/a/X/cg", "yy", "X X\n", "2 substitutions on 1 lines"),
        # n skips every match
        ("a a\n", "%s/a/X/gc", "nn", "a a\n", "0 substitutions on 0 lines"),
        # a replaces this and all remaining matches
        ("a a a\n", "%s/a/X/gc", "na", "a X X\n", "2 substitutions on 1 lines"),
        # l replaces this match and quits
        ("a a a\n", "%s/a/X/gc", "nl", "a X a\n", "1 substitutions on 1 lines"),
        # q quits and keeps what was accepted so far
        ("a a a\n", "%s/a/X/gc", "yq", "X a a\n", "1 substitutions on 1 lines"),
        # Keys without meaning keep the prompt open
        ("a a\n", "%s/a/X/gc", "zy" + "n", "X a\n", "1 substitutions on 1 lines"),
        # Replacement features work as without c
        ("ab\n", "%s/(a)(b)/\\2\\1/c", "y", "ba\n", "1 substitutions on 1 lines"),
    ],
)
def test_colon_substitute_confirm(vim_bot, text, command, answers, expected, message):
    """The c flag asks for each match and applies the accepted ones."""
    editor, vim, qtbot = _start_confirm(vim_bot, text, command)
    vs = vim.vim_cmd.vim_status
    cmd_line = vim.vim_cmd.commandline

    # The text is untouched until the session ends
    assert editor.toPlainText() == text
    assert vs.sub_mode is not None

    for answer in answers:
        qtbot.keyClicks(cmd_line, answer)

    assert editor.toPlainText() == expected
    assert cmd_line.text() == ""
    assert vs.sub_mode is None
    assert message in vs.msg_label.text()


def test_colon_substitute_confirm_escape(vim_bot):
    """Esc quits the session and keeps the replacements accepted so far."""
    editor, vim, qtbot = _start_confirm(vim_bot, "a a a\n", "%s/a/X/gc")
    vs = vim.vim_cmd.vim_status

    qtbot.keyClicks(vim.vim_cmd.commandline, "y")
    vim.vim_cmd.commandline.esc_pressed()

    assert editor.toPlainText() == "X a a\n"
    assert vs.sub_mode is None
    assert vs.is_normal()


def test_colon_substitute_confirm_selects_current_match(vim_bot):
    """The match being asked about is the cursor position and selection."""
    editor, vim, qtbot = _start_confirm(vim_bot, "ab\nab\n", "%s/b/X/c")
    cmd_line = vim.vim_cmd.commandline

    assert editor.textCursor().position() == 1
    selection = editor.get_extra_selections("vim_selection")[0].cursor
    assert (selection.selectionStart(), selection.selectionEnd()) == (1, 2)
    assert "(1/2)" in vim.vim_cmd.vim_status.msg_label.text()

    qtbot.keyClicks(cmd_line, "n")
    assert editor.textCursor().position() == 4
    assert "(2/2)" in vim.vim_cmd.vim_status.msg_label.text()

    # Quit so the open prompt does not leak into the next test
    qtbot.keyClicks(cmd_line, "q")
    assert vim.vim_cmd.vim_status.sub_mode is None


def test_colon_substitute_confirm_applies_each_answer_at_once(vim_bot):
    """y changes the text immediately and later matches are shifted correctly."""
    text = "a a\na\n"
    editor, vim, qtbot = _start_confirm(vim_bot, text, "%s/a/long/gc")
    cmd_line = vim.vim_cmd.commandline

    qtbot.keyClicks(cmd_line, "y")
    assert editor.toPlainText() == "long a\na\n"
    selection = editor.get_extra_selections("vim_selection")[0].cursor
    assert (
        editor.toPlainText()[selection.selectionStart() : selection.selectionEnd()]
        == "a"
    )

    qtbot.keyClicks(cmd_line, "n")
    assert editor.toPlainText() == "long a\na\n"

    qtbot.keyClicks(cmd_line, "y")
    assert editor.toPlainText() == "long a\nlong\n"
    assert vim.vim_cmd.vim_status.sub_mode is None


def test_colon_substitute_confirm_undo_steps(vim_bot):
    """Each y is one undo step, while a replaces all the rest in one step."""
    text = "a\na\na\n"
    editor, vim, qtbot = _start_confirm(vim_bot, text, "%s/a/b/c")

    for answer in "yya":
        qtbot.keyClicks(vim.vim_cmd.commandline, answer)
    assert editor.toPlainText() == "b\nb\nb\n"

    # The a answer replaced the last match in a single step
    editor.undo()
    assert editor.toPlainText() == "b\nb\na\n"
    editor.undo()
    assert editor.toPlainText() == "b\na\na\n"
    editor.undo()
    assert editor.toPlainText() == text


def test_colon_substitute_confirm_cursor_and_search(vim_bot):
    """The cursor ends on the last replaced line and n follows the pattern."""
    editor, vim, qtbot = _start_confirm(vim_bot, "a\nb\na\nb\n", "%s/a/a/c")
    cmd_line = vim.vim_cmd.commandline

    qtbot.keyClicks(cmd_line, "yy")

    assert editor.textCursor().blockNumber() == 2
    assert vim.vim_cmd.vim_status.search.txt_searched == "a"


def test_colon_substitute_confirm_nothing_accepted_restores_cursor(vim_bot):
    """The cursor returns to its start if no replacement was accepted."""
    editor, vim, qtbot = _start_confirm(vim_bot, "xx\na\nb\na\n", "%s/a/X/c", pos=1)

    qtbot.keyClicks(vim.vim_cmd.commandline, "nn")

    assert editor.toPlainText() == "xx\na\nb\na\n"
    assert editor.textCursor().position() == 1


def test_colon_substitute_confirm_current_line_only(vim_bot):
    """:s with c only offers the matches of the current line."""
    editor, vim, qtbot = _start_confirm(vim_bot, "a a\na a\n", "s/a/X/gc", pos=4)

    qtbot.keyClicks(vim.vim_cmd.commandline, "yy")

    assert editor.toPlainText() == "a a\nX X\n"
    assert vim.vim_cmd.vim_status.sub_mode is None


def test_colon_substitute_confirm_remembers_for_repeat(vim_bot):
    """g& repeats a confirmed substitute with the g flag but without asking."""
    editor, vim, qtbot = _start_confirm(vim_bot, "a a\na a\n", "%s/a/X/gc")
    cmd_line = vim.vim_cmd.commandline

    qtbot.keyClicks(cmd_line, "yn" + "yn")
    assert editor.toPlainText() == "X a\nX a\n"

    qtbot.keyClicks(cmd_line, "g&")
    assert editor.toPlainText() == "X X\nX X\n"


@pytest.mark.parametrize(
    "command, message",
    [
        ("%s/zzz/y/c", "E486: Pattern not found: zzz"),
        ("%s/(/y/c", "E486: Invalid pattern"),
        ("%s/a/b/cc", "E488: Trailing characters: cc"),
        ("%s/a/b/cx", "E488: Trailing characters: cx"),
    ],
)
def test_colon_substitute_confirm_errors(vim_bot, command, message):
    """Errors are reported without starting a confirmation session."""
    editor, vim, _ = _start_confirm(vim_bot, "abc\n", command)

    assert editor.toPlainText() == "abc\n"
    assert vim.vim_cmd.vim_status.sub_mode is None
    assert message in vim.vim_cmd.vim_status.msg_label.text()
