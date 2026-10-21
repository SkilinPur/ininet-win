import sys
from unittest import mock

from ininet_win.platform import elevate


def test_is_admin_on_non_windows() -> None:
    with mock.patch.object(elevate.sys, "platform", "linux"):
        assert elevate.is_admin() is False


def test_is_admin_true() -> None:
    with (
        mock.patch.object(elevate.sys, "platform", "win32"),
        mock.patch.object(elevate.ctypes, "windll") as windll,
    ):
        windll.shell32.IsUserAnAdmin.return_value = 1
        assert elevate.is_admin() is True


def test_is_admin_false() -> None:
    with (
        mock.patch.object(elevate.sys, "platform", "win32"),
        mock.patch.object(elevate.ctypes, "windll") as windll,
    ):
        windll.shell32.IsUserAnAdmin.return_value = 0
        assert elevate.is_admin() is False


def test_relaunch_non_windows() -> None:
    with mock.patch.object(elevate.sys, "platform", "linux"):
        assert elevate.relaunch_as_admin([]) is False


def test_relaunch_success() -> None:
    with (
        mock.patch.object(elevate.sys, "platform", "win32"),
        mock.patch.object(elevate.ctypes, "windll") as windll,
    ):
        windll.shell32.ShellExecuteW.return_value = 42
        assert elevate.relaunch_as_admin(["watch"]) is True


def test_relaunch_refused() -> None:
    with (
        mock.patch.object(elevate.sys, "platform", "win32"),
        mock.patch.object(elevate.ctypes, "windll") as windll,
    ):
        windll.shell32.ShellExecuteW.return_value = 5
        assert elevate.relaunch_as_admin(["watch"]) is False


def test_module_args_not_frozen() -> None:
    with mock.patch.object(sys, "frozen", False, create=True):
        assert elevate._module_args() == ["-m", "ininet_win"]


def test_module_args_frozen() -> None:
    with mock.patch.object(sys, "frozen", True, create=True):
        assert elevate._module_args() == []


def test_quote() -> None:
    assert elevate._quote("plain") == "plain"
    assert elevate._quote("with space") == '"with space"'
    assert elevate._quote("") == '""'
