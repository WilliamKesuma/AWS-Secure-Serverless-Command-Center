"""Compatibility shim for environments missing the stdlib cgi module.

This module attempts to expose FieldStorage from the standard `cgi` module.
If the runtime doesn't include `cgi` (newer Python builds may omit it), the
shim provides a placeholder FieldStorage that raises ImportError when used.

This keeps code that does `import legacy_cgi as cgi` working at import time
while still failing early and cleanly if multipart parsing is attempted.
"""
try:
    import cgi as _cgi
    FieldStorage = _cgi.FieldStorage
except Exception:  # pragma: no cover - runtime-specific
    class FieldStorage:
        def __init__(self, *args, **kwargs):
            raise ImportError("cgi.FieldStorage not available in this Python runtime")

__all__ = ["FieldStorage"]
