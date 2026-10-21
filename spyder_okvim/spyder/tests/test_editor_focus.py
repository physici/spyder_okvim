# -*- coding: utf-8 -*-
"""
Tests for the filter that starts Normal mode when the editor gets focus.

Author: rainer.jacob
Date: 2026-10-21

Disclaimer: this code is AI generated (claude-sonnet-5-5).
"""

from __future__ import annotations

# Standard Libraries
from types import SimpleNamespace

# Third Party Libraries
import pytest
from qtpy.QtCore import QEvent, Qt
from qtpy.QtGui import QFocusEvent

# Project Libraries
from spyder_okvim.spyder.editor_focus import EditorFocusFilter


class _FakeStatus:
    """Minimal stand-in for ``VimStatus`` that records focus requests."""

    def __init__(self, editor: object) -> None:
        self.editor = editor
        self.editor_focus_requested = False
        self.vim_focus_calls = 0

    def get_editor(self) -> object:
        return self.editor

    def set_focus_to_vim(self) -> None:
        self.vim_focus_calls += 1


def _focus_in(reason: Qt.FocusReason) -> QFocusEvent:
    return QFocusEvent(QEvent.FocusIn, reason)


@pytest.fixture
def focus_setup(qapp):
    """Return a filter, its fake status and the fake editor."""
    editor = SimpleNamespace()
    status = _FakeStatus(editor)
    return EditorFocusFilter(status), status, editor


@pytest.mark.parametrize(
    "reason",
    [
        Qt.MouseFocusReason,
        Qt.TabFocusReason,
        Qt.OtherFocusReason,
        Qt.ActiveWindowFocusReason,
    ],
)
def test_unrequested_editor_focus_goes_to_vim(focus_setup, qtbot, reason):
    """The editor gaining focus by itself sends focus to the command line."""
    focus_filter, status, editor = focus_setup

    assert focus_filter.eventFilter(editor, _focus_in(reason)) is False
    qtbot.waitUntil(lambda: status.vim_focus_calls == 1)


def test_requested_editor_focus_is_kept(focus_setup, qtbot):
    """Commands like i ask for focus on purpose and stay in insert mode."""
    focus_filter, status, editor = focus_setup
    status.editor_focus_requested = True

    focus_filter.eventFilter(editor, _focus_in(Qt.OtherFocusReason))
    qtbot.wait(20)

    assert status.vim_focus_calls == 0


def test_popup_focus_is_kept(focus_setup, qtbot):
    """Closing a popup must not interrupt typing in insert mode."""
    focus_filter, status, editor = focus_setup

    focus_filter.eventFilter(editor, _focus_in(Qt.PopupFocusReason))
    qtbot.wait(20)

    assert status.vim_focus_calls == 0


def test_set_focus_to_editor_marks_request(vim_bot, monkeypatch):
    """The flag is set while the editor takes focus and reset afterwards."""
    _, _, editor, vim, _ = vim_bot
    status = vim.vim_cmd.vim_status
    seen = []
    monkeypatch.setattr(
        editor, "setFocus", lambda: seen.append(status.editor_focus_requested)
    )

    status.set_focus_to_editor()

    assert seen == [True]
    assert status.editor_focus_requested is False


def test_other_widgets_and_events_are_ignored(focus_setup, qtbot):
    """Only focus-in events of the current editor are considered."""
    focus_filter, status, editor = focus_setup

    focus_filter.eventFilter(SimpleNamespace(), _focus_in(Qt.MouseFocusReason))
    focus_filter.eventFilter(editor, QFocusEvent(QEvent.FocusOut, Qt.MouseFocusReason))
    qtbot.wait(20)

    assert status.vim_focus_calls == 0
