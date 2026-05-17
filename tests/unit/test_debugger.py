"""Unit tests for DebugContext and debug decorator."""

# pylint: disable=protected-access,too-few-public-methods

import sys
import types
from unittest.mock import MagicMock, patch

from apyhiveapi.helper.debugger import DebugContext, debug


class TestDebugContextInit:
    """Tests for DebugContext.__init__."""

    def test_stores_name(self):
        ctx = DebugContext("my_func", True)
        assert ctx.name == "my_func"

    def test_stores_enabled(self):
        ctx = DebugContext("my_func", False)
        assert ctx.enabled is False

    def test_creates_logger(self):
        ctx = DebugContext("my_func", True)
        assert ctx.logging is not None


class TestDebugContextEnter:
    """Tests for DebugContext.__enter__."""

    def test_sets_sys_trace(self):
        ctx = DebugContext("my_func", True)
        with patch.object(sys, "settrace") as mock_settrace:
            result = ctx.__enter__()
            mock_settrace.assert_called_once_with(ctx.trace_calls)
        assert result is ctx

    def test_returns_self(self):
        ctx = DebugContext("my_func", True)
        with patch.object(sys, "settrace"):
            returned = ctx.__enter__()
        assert returned is ctx

    def test_disabled_context_does_not_set_sys_trace(self):
        ctx = DebugContext("my_func", False)
        with patch.object(sys, "settrace") as mock_settrace:
            returned = ctx.__enter__()
        mock_settrace.assert_not_called()
        assert returned is ctx


class TestDebugContextExit:
    """Tests for DebugContext.__exit__."""

    def test_clears_sys_trace(self):
        ctx = DebugContext("my_func", True)
        with patch.object(sys, "settrace") as mock_settrace:
            ctx.__exit__(None, None, None)
            mock_settrace.assert_called_once_with(None)

    def test_restores_previous_trace(self):
        previous_trace = object()
        ctx = DebugContext("my_func", True)
        ctx._previous_trace = previous_trace
        with patch.object(sys, "settrace") as mock_settrace:
            ctx.__exit__(None, None, None)
        mock_settrace.assert_called_once_with(previous_trace)

    def test_disabled_context_exit_does_not_clear_trace(self):
        ctx = DebugContext("my_func", False)
        with patch.object(sys, "settrace") as mock_settrace:
            ctx.__exit__(None, None, None)
        mock_settrace.assert_not_called()

    def test_returns_false(self):
        ctx = DebugContext("my_func", True)
        with patch.object(sys, "settrace"):
            result = ctx.__exit__(None, None, None)
        assert result is False

    def test_returns_false_with_exception_info(self):
        ctx = DebugContext("my_func", True)
        with patch.object(sys, "settrace"):
            result = ctx.__exit__(ValueError, ValueError("oops"), None)
        assert result is False


class TestTraceCalls:
    """Tests for DebugContext.trace_calls."""

    def _make_frame(self, func_name):
        code = MagicMock(spec=types.CodeType)
        code.co_name = func_name
        frame = MagicMock()
        frame.f_code = code
        return frame

    def test_non_call_event_returns_none(self):
        ctx = DebugContext("my_func", True)
        frame = self._make_frame("my_func")
        assert ctx.trace_calls(frame, "line", None) is None

    def test_return_event_returns_none(self):
        ctx = DebugContext("my_func", True)
        frame = self._make_frame("my_func")
        assert ctx.trace_calls(frame, "return", None) is None

    def test_call_event_wrong_name_returns_none(self):
        ctx = DebugContext("my_func", True)
        frame = self._make_frame("other_func")
        assert ctx.trace_calls(frame, "call", None) is None

    def test_call_event_matching_name_returns_trace_lines(self):
        ctx = DebugContext("my_func", True)
        frame = self._make_frame("my_func")
        # Bound methods create a new object on each access, so compare __func__
        result = ctx.trace_calls(frame, "call", None)
        assert result.__func__ is ctx.trace_lines.__func__


class TestTraceLines:
    """Tests for DebugContext.trace_lines."""

    def _make_frame(self, func_name="my_func", line_no=10, local_vars=None):
        code = MagicMock(spec=types.CodeType)
        code.co_name = func_name
        frame = MagicMock()
        frame.f_code = code
        frame.f_lineno = line_no
        frame.f_locals = local_vars or {}
        return frame

    def test_non_line_non_return_event_does_nothing(self):
        ctx = DebugContext("my_func", True)
        frame = self._make_frame()
        with patch.object(ctx.logging, "debug") as mock_debug:
            ctx.trace_lines(frame, "call", None)
            mock_debug.assert_not_called()

    def test_exception_event_does_nothing(self):
        ctx = DebugContext("my_func", True)
        frame = self._make_frame()
        with patch.object(ctx.logging, "debug") as mock_debug:
            ctx.trace_lines(frame, "exception", None)
            mock_debug.assert_not_called()

    def test_line_event_logs_debug(self):
        ctx = DebugContext("my_func", True)
        frame = self._make_frame(func_name="my_func", line_no=42, local_vars={"x": 1})
        with patch.object(ctx.logging, "debug") as mock_debug:
            ctx.trace_lines(frame, "line", None)
            mock_debug.assert_called_once()
            logged_text = mock_debug.call_args[0][0]
            assert "my_func" in logged_text
            assert "line" in logged_text
            assert "42" in logged_text

    def test_return_event_logs_debug(self):
        ctx = DebugContext("my_func", True)
        frame = self._make_frame(func_name="my_func", line_no=55)
        with patch.object(ctx.logging, "debug") as mock_debug:
            ctx.trace_lines(frame, "return", None)
            mock_debug.assert_called_once()


class TestDebugDecorator:
    """Tests for the debug decorator factory."""

    def test_decorated_function_returns_value(self):
        @debug(enabled=False)
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_decorated_function_called_with_args(self):
        calls = []

        @debug(enabled=False)
        def record(*args, **kwargs):
            calls.append((args, kwargs))
            return "ok"

        result = record(1, key="val")
        assert result == "ok"
        assert calls == [((1,), {"key": "val"})]

    def test_decorator_enabled_true_executes_function(self):
        @debug(enabled=True)
        def multiply(x, y):
            return x * y

        with patch.object(sys, "settrace"):
            result = multiply(3, 4)
        assert result == 12

    def test_decorator_enabled_false_executes_function(self):
        @debug(enabled=False)
        def greet(name):
            return f"hello {name}"

        assert greet("world") == "hello world"

    def test_wraps_preserves_return_type(self):
        @debug(enabled=False)
        def get_list():
            return [1, 2, 3]

        assert get_list() == [1, 2, 3]

    def test_context_manager_used_during_call(self):
        entered = []

        original_enter = DebugContext.__enter__

        def tracking_enter(self):
            entered.append(self.name)
            return original_enter(self)

        with patch.object(DebugContext, "__enter__", tracking_enter):

            @debug(enabled=False)
            def my_target():
                return 99

            result = my_target()

        assert result == 99
        assert "my_target" in entered
