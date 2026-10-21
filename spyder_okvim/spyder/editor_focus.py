# -*- coding: utf-8 -*-
"""
Start in Normal mode whenever the editor receives focus.

Author: rainer.jacob
Date: 2026-10-21

Disclaimer: this code is AI generated (claude-sonnet-5-5).
"""

from __future__ import annotations

# Third Party Libraries
from qtpy.QtCore import QEvent, QObject, Qt, QTimer

# Focus changes that must not be turned into Normal mode, because the user did
# not leave the editor: a popup (menu, completion list) closed again.
_IGNORED_REASONS = (Qt.PopupFocusReason,)


class EditorFocusFilter(QObject):
    """
    Event filter that sends focus from the editor to the vim command line.

    The command line is where Normal mode lives. Whenever the current editor
    gains focus without a command asking for it (mouse click, tab switch,
    start of Spyder), focus moves on to the command line, as Vim starts in
    Normal mode. Commands such as ``i`` use
    :meth:`spyder_okvim.vim.status.VimStatus.set_focus_to_editor` and are
    not redirected.

    Public methods: :meth:`eventFilter`.
    """

    def __init__(self, vim_status: object, parent: QObject | None = None) -> None:
        """
        Create the filter.

        Parameters
        ----------
        vim_status : object
            The shared ``VimStatus``. It provides ``get_editor``,
            ``editor_focus_requested`` and ``set_focus_to_vim``.
        parent : QObject | None
            Optional Qt parent.
        """
        super().__init__(parent)
        self.vim_status = vim_status

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Redirect unrequested focus of the current editor to the command line.

        Parameters
        ----------
        obj : QObject
            The object that received the event.
        event : QEvent
            The event. Only ``FocusIn`` events are considered.

        Returns
        -------
        bool
            Always False, the focus event itself is never consumed.
        """
        if event.type() != QEvent.FocusIn:
            return False
        if self.vim_status.editor_focus_requested:
            return False
        if event.reason() in _IGNORED_REASONS:
            return False
        if obj is not self.vim_status.get_editor():
            return False

        # Wait until Qt has finished delivering the focus event
        QTimer.singleShot(0, self._redirect_to_vim)
        return False

    def _redirect_to_vim(self) -> None:
        """
        Move focus to the command line unless a command is running.

        The check is repeated here because the timer can fire while a command
        runs (Qt spins the event loop inside e.g. file switches). Moving focus
        then would end Visual mode in the middle of the command.
        """
        if self.vim_status.editor_focus_requested:
            return
        self.vim_status.set_focus_to_vim()
