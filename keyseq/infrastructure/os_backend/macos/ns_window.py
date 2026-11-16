"""Resolve Tk drawables to their native NSWindow objects."""
import ctypes
import logging

_LOG = logging.getLogger(__name__)
_function = None
_lookup_attempted = False
_failure_logged = False


def ns_window_for(widget, *, function=None, objc=None):
    """Return the NSWindow for a Tk widget, or None when it cannot be resolved."""
    global _function, _lookup_attempted, _failure_logged
    try:
        if function is None:
            if not _lookup_attempted:
                _lookup_attempted = True
                try:
                    _function = ctypes.CDLL(None).Tk_MacOSXGetNSWindowForDrawable
                    _function.restype = ctypes.c_void_p
                    _function.argtypes = [ctypes.c_void_p]
                except Exception:
                    _function = None
            function = _function
        if function is None:
            raise RuntimeError("Tk NSWindow lookup function unavailable")
        pointer = function(widget.winfo_toplevel().winfo_id())
        if not pointer:
            return None
        if objc is None:
            import objc as objc_module
            objc = objc_module
        return objc.objc_object(c_void_p=pointer)
    except Exception:
        if not _failure_logged:
            _LOG.exception("Could not resolve Tk NSWindow")
            _failure_logged = True
        return None
