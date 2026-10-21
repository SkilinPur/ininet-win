from typer.testing import CliRunner

from ininet_win import __version__
from ininet_win.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_scan_invalid_cidr() -> None:
    result = runner.invoke(app, ["scan", "not-a-network"])
    assert result.exit_code == 2


def test_scan_help() -> None:
    result = runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0
    assert "--ports" in result.stdout


def test_watch_stub() -> None:
    result = runner.invoke(app, ["watch"])
    assert result.exit_code == 0
