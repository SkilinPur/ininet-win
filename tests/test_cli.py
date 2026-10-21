from typer.testing import CliRunner

from ininet_win import __version__
from ininet_win.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_scan_stub() -> None:
    result = runner.invoke(app, ["scan", "192.168.0.0/24"])
    assert result.exit_code == 0
