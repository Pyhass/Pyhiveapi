"""Unit tests for hive.py module-level functions and the Hive class."""

# pylint: disable=protected-access,too-few-public-methods

import sys
import traceback
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apyhiveapi.hive import Hive, exception_handler, trace_debug


class TestExceptionHandler:
    """Tests for the exception_handler custom sys.excepthook."""

    def _make_tb(self):
        try:
            raise ValueError("boom")
        except ValueError:
            return sys.exc_info()[2]

    def test_calls_logger_error(self):
        tb = self._make_tb()
        with patch("apyhiveapi.hive._LOGGER") as mock_logger:
            with patch("traceback.print_exc"):
                exception_handler(ValueError, ValueError("boom"), tb)
        mock_logger.error.assert_called_once()

    def test_calls_print_exc(self):
        tb = self._make_tb()
        with patch("apyhiveapi.hive._LOGGER"):
            with patch("traceback.print_exc") as mock_print:
                exception_handler(ValueError, ValueError("boom"), tb)
        mock_print.assert_called_once()

    def test_error_message_contains_filename(self):
        tb = self._make_tb()
        with patch("apyhiveapi.hive._LOGGER") as mock_logger:
            with patch("traceback.print_exc"):
                exception_handler(ValueError, ValueError("boom"), tb)
        error_args = mock_logger.error.call_args[0]
        assert len(error_args) >= 2

    def test_uses_last_traceback_entry(self):
        def inner():
            raise RuntimeError("inner error")

        tb = None
        try:
            inner()
        except RuntimeError:
            _, _, tb = sys.exc_info()

        entries = traceback.extract_tb(tb)
        last_entry = entries[-1]

        with patch("apyhiveapi.hive._LOGGER") as mock_logger:
            with patch("traceback.print_exc"):
                exception_handler(RuntimeError, RuntimeError("inner error"), tb)

        call_args = mock_logger.error.call_args[0]
        assert last_entry.filename in str(call_args) or last_entry.name in str(
            call_args
        )


class TestTraceDebug:
    """Tests for trace_debug function."""

    def _make_frame(self, filename="some/module.py", func_name="my_func", line_no=10):
        code = MagicMock()
        code.co_name = func_name
        code.co_filename = filename
        frame = MagicMock()
        frame.f_code = code
        frame.f_lineno = line_no
        frame.__str__ = lambda self: filename
        return frame

    def test_returns_trace_debug_itself(self):
        frame = self._make_frame(filename="unrelated/module.py")
        result = trace_debug(frame, "call", None)
        assert result is trace_debug

    def test_non_pyhiveapi_frame_returns_trace_debug(self):
        frame = self._make_frame(filename="/home/user/other/file.py")
        result = trace_debug(frame, "call", None)
        assert result is trace_debug

    def test_non_pyhiveapi_frame_does_not_log(self):
        frame = self._make_frame(filename="/home/user/other/file.py")
        with patch("apyhiveapi.hive._LOGGER") as mock_logger:
            trace_debug(frame, "call", None)
        mock_logger.debug.assert_not_called()


class TestTraceDebugPyhiveapiFrame:
    """Lines 60-79: trace_debug processes frames whose str() contains 'pyhiveapi/'."""

    class _PyhiveapiFrame:
        """Fake frame with str() containing 'pyhiveapi/' to trigger the guard."""

        def __init__(self, func_name="my_func", line_no=42):
            co = MagicMock()
            co.co_name = func_name
            co.co_filename = "/home/user/pyhiveapi/hive.py"
            self.f_code = co
            self.f_lineno = line_no
            caller = MagicMock()
            caller.f_lineno = 10
            caller.f_code = MagicMock()
            caller.f_code.co_filename = "/home/user/pyhiveapi/session.py"
            self.f_back = caller

        def __str__(self):
            return f"<frame for pyhiveapi/hive.py at line {self.f_lineno}>"

    def _set_debug(self, func_name):
        import apyhiveapi.hive as hive_module

        saved = list(hive_module.debug)
        hive_module.debug.clear()
        hive_module.debug.append(func_name)
        return hive_module, saved

    def _restore_debug(self, hive_module, saved):
        hive_module.debug.clear()
        hive_module.debug.extend(saved)

    def test_call_event_for_pyhiveapi_frame_logs_debug(self):
        """Lines 60-77: 'call' event logs function name, line, and caller info."""
        hive_module, saved = self._set_debug("my_func")
        try:
            frame = self._PyhiveapiFrame(func_name="my_func")
            with patch("apyhiveapi.hive._LOGGER") as mock_logger:
                result = trace_debug(frame, "call", None)
            assert result is trace_debug
            mock_logger.debug.assert_called_once()
        finally:
            self._restore_debug(hive_module, saved)

    def test_return_event_for_pyhiveapi_frame_logs_return_value(self):
        """Lines 78-79: 'return' event logs the return value."""
        hive_module, saved = self._set_debug("my_func")
        try:
            frame = self._PyhiveapiFrame(func_name="my_func")
            with patch("apyhiveapi.hive._LOGGER") as mock_logger:
                result = trace_debug(frame, "return", "my_return_value")
            assert result is trace_debug
            mock_logger.debug.assert_called_once_with("returning %s", "my_return_value")
        finally:
            self._restore_debug(hive_module, saved)

    def test_pyhiveapi_frame_func_not_in_debug_does_not_log(self):
        """Lines 60, 63->81: func_name not in debug list — body is skipped."""
        hive_module, saved = self._set_debug("other_func")
        try:
            frame = self._PyhiveapiFrame(func_name="my_func")  # not in debug
            with patch("apyhiveapi.hive._LOGGER") as mock_logger:
                result = trace_debug(frame, "call", None)
            assert result is trace_debug
            mock_logger.debug.assert_not_called()
        finally:
            self._restore_debug(hive_module, saved)

    def test_non_call_non_return_event_does_not_log(self):
        """Lines 60-79: an event that is neither 'call' nor 'return' produces no log."""
        hive_module, saved = self._set_debug("my_func")
        try:
            frame = self._PyhiveapiFrame(func_name="my_func")
            with patch("apyhiveapi.hive._LOGGER") as mock_logger:
                result = trace_debug(frame, "line", None)
            assert result is trace_debug
            mock_logger.debug.assert_not_called()
        finally:
            self._restore_debug(hive_module, saved)


class TestHiveInit:
    """Tests for Hive.__init__ device module composition."""

    async def test_initializes_action(self):
        from apyhiveapi.devices.action import HiveAction

        async with Hive(username="use@file.com", password="") as hive:
            assert isinstance(hive.action, HiveAction)

    async def test_initializes_heating(self):
        from apyhiveapi.devices.heating import Climate

        async with Hive(username="use@file.com", password="") as hive:
            assert isinstance(hive.heating, Climate)

    async def test_initializes_hotwater(self):
        from apyhiveapi.devices.hotwater import WaterHeater

        async with Hive(username="use@file.com", password="") as hive:
            assert isinstance(hive.hotwater, WaterHeater)

    async def test_initializes_hub(self):
        from apyhiveapi.devices.hub import HiveHub

        async with Hive(username="use@file.com", password="") as hive:
            assert isinstance(hive.hub, HiveHub)

    async def test_initializes_light(self):
        from apyhiveapi.devices.light import Light

        async with Hive(username="use@file.com", password="") as hive:
            assert isinstance(hive.light, Light)

    async def test_initializes_switch(self):
        from apyhiveapi.devices.plug import Switch

        async with Hive(username="use@file.com", password="") as hive:
            assert isinstance(hive.switch, Switch)

    async def test_initializes_sensor(self):
        from apyhiveapi.devices.sensor import Sensor

        async with Hive(username="use@file.com", password="") as hive:
            assert isinstance(hive.sensor, Sensor)

    async def test_session_is_self(self):
        async with Hive(username="use@file.com", password="") as hive:
            assert hive.session is hive

    async def test_init_with_debug_list_sets_trace(self):
        import apyhiveapi.hive as hive_module

        original_debug = hive_module.debug[:]
        hive_module.debug = ["some_func"]
        try:
            with patch.object(sys, "settrace") as mock_settrace:
                async with Hive(username="use@file.com", password=""):
                    mock_settrace.assert_called_with(trace_debug)
        finally:
            hive_module.debug = original_debug
            sys.settrace(None)

    async def test_init_with_empty_debug_does_not_set_trace(self):
        import apyhiveapi.hive as hive_module

        original_debug = hive_module.debug[:]
        hive_module.debug = []
        try:
            with patch.object(sys, "settrace") as mock_settrace:
                async with Hive(username="use@file.com", password=""):
                    mock_settrace.assert_not_called()
        finally:
            hive_module.debug = original_debug


class TestSetDebugging:
    """Tests for Hive.set_debugging."""

    async def test_non_empty_list_enables_trace(self):
        async with Hive(username="use@file.com", password="") as hive:
            with patch.object(sys, "settrace") as mock_settrace:
                hive.set_debugging(["some_func"])
                mock_settrace.assert_called_once_with(trace_debug)

    async def test_empty_list_disables_trace(self):
        async with Hive(username="use@file.com", password="") as hive:
            with patch.object(sys, "settrace") as mock_settrace:
                mock_settrace.return_value = None
                result = hive.set_debugging([])
                mock_settrace.assert_called_once_with(None)
                assert result is None

    async def test_updates_module_debug_variable(self):
        import apyhiveapi.hive as hive_module

        async with Hive(username="use@file.com", password="") as hive:
            with patch.object(sys, "settrace"):
                hive.set_debugging(["target_func"])
            assert hive_module.debug == ["target_func"]
            hive_module.debug = []

    async def test_set_debugging_returns_settrace_result(self):
        sentinel = object()
        async with Hive(username="use@file.com", password="") as hive:
            with patch.object(sys, "settrace", return_value=sentinel):
                result = hive.set_debugging(["func"])
            assert result is sentinel


class TestForceUpdate:
    """Tests for Hive.force_update."""

    async def test_lock_free_calls_poll_devices(self):
        async with Hive(username="use@file.com", password="") as hive:
            hive._poll_devices = AsyncMock(return_value=True)
            result = await hive.force_update()
        assert result is True
        hive._poll_devices.assert_awaited_once()

    async def test_lock_free_returns_poll_result(self):
        async with Hive(username="use@file.com", password="") as hive:
            hive._poll_devices = AsyncMock(return_value=False)
            result = await hive.force_update()
        assert result is False

    async def test_lock_held_returns_false(self):
        async with Hive(username="use@file.com", password="") as hive:
            hive._poll_devices = AsyncMock(return_value=True)
            await hive.update_lock.acquire()
            try:
                result = await hive.force_update()
            finally:
                hive.update_lock.release()
        assert result is False
        hive._poll_devices.assert_not_awaited()

    async def test_update_task_cleared_after_poll(self):
        async with Hive(username="use@file.com", password="") as hive:
            hive._poll_devices = AsyncMock(return_value=True)
            await hive.force_update()
            assert hive._update_task is None

    async def test_update_task_cleared_even_on_exception(self):
        async with Hive(username="use@file.com", password="") as hive:
            hive._poll_devices = AsyncMock(side_effect=RuntimeError("poll failed"))
            with pytest.raises(RuntimeError, match="poll failed"):
                await hive.force_update()
            assert hive._update_task is None
