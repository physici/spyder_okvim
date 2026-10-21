"""Expose Vim core classes.

This package gathers all classes implementing the Vim emulation logic.
Users should import them directly from ``spyder_okvim.vim``.

Disclaimer: parts of this module were generated with AI assistance
(claude-sonnet-5-5).
"""

from .cursor import VimCursor
from .label import InlineLabel
from .macro import MacroManager
from .search import SearchInfo
from .state import (
    DotCmdInfo,
    FindInfo,
    InputCmdInfo,
    KeyInfo,
    RegisterInfo,
    SubstituteInfo,
    VimState,
)
from .status import VimStatus

__all__ = [
    "VimState",
    "FindInfo",
    "InputCmdInfo",
    "DotCmdInfo",
    "KeyInfo",
    "RegisterInfo",
    "SubstituteInfo",
    "SearchInfo",
    "MacroManager",
    "InlineLabel",
    "VimCursor",
    "VimStatus",
]


