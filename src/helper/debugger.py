"""Debugger file."""

import logging
import sys


class DebugContext:
    """Debug context to trace any function calls inside the context."""

    def __init__(self, name, enabled):
        """Initialise debugger."""
        self.name = name
        self.enabled = enabled
        self.logging = logging.getLogger(__name__)

    def __enter__(self):
        """Set trace calls on entering debugger."""
        self.logging.debug("Entering debug context for %s", self.name)
        sys.settrace(self.trace_calls)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove trace on exiting debugger."""
        sys.settrace(None)
        return False

    def trace_calls(self, frame, event, _arg):
        """Trace calls be made."""
        if event != "call":
            return None
        if frame.f_code.co_name != self.name:
            return None
        return self.trace_lines

    def trace_lines(self, frame, event, _arg):
        """Print out lines for function."""
        if event not in ["line", "return"]:
            return
        co = frame.f_code
        func_name = co.co_name
        line_no = frame.f_lineno
        local_vars = frame.f_locals
        text = f"  {func_name} {event} {line_no} locals: {local_vars}"
        self.logging.debug(text)


def debug(enabled=False):
    """Debug decorator to call the function within the debug context."""

    def decorated_func(func):
        def wrapper(*args, **kwargs):
            with DebugContext(func.__name__, enabled):
                return_value = func(*args, **kwargs)
            return return_value

        return wrapper

    return decorated_func
