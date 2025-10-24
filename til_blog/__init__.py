"""Compatibility shim to expose the src/til_blog package when running without installation."""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
_src_root = _root.parent / "src"
_pkg_root = _src_root / "til_blog"

if not _pkg_root.exists():
    raise ImportError(
        "The til_blog package could not be located. Expected to find 'src/til_blog'."
    )

if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))

__path__ = [str(_pkg_root)]
__all__ = []
