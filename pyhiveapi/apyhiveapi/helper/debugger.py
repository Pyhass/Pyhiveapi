"""Debugger file."""
import logging


class DebugContext:
    """Debug context to trace any function calls inside the context."""

    def __init__(self, name, enabled):
        """Initialise debugger."""
        self.name = name
        self.enabled = enabled
        self.logging = logging.getLogger(__name__)
        self.debugOutFolder = ""
        self.debugOutFile = ""
        self.debugEnabled = False
        self.debugList = []

    def __enter__(self):
        """Set trace calls on entering debugger."""
        print("Entering Debug Decorated func")
        # Set the trace function to the trace_calls function
        # So all events are now traced
        self.traceCalls

    def traceCalls(self, frame, event, arg):
        """Trace calls be made."""
        # We want to only trace our call to the decorated function
        if event != "call":
            return
        elif frame.f_code.co_name != self.name:
            return
        # return the trace function to use when you go into that
        # function call
        return self.traceLines

    def traceLines(self, frame, event, arg):
        """Print out lines for function."""
        # If you want to print local variables each line
        # keep the check for the event 'line'
        # If you want to print local variables only on return
        # check only for the 'return' event
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
