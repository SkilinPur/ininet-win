from typer.testing import CliRunner

from ininet_win import __version__
from ininet_win.cli import app
from ininet_win.i18n import translator

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
    result = runner.invoke(app, ["watch", "--json"])
    assert result.exit_code == 0


def test_top_json() -> None:
    result = runner.invoke(app, ["top", "--json"])
    assert result.exit_code == 0


def test_admin_command() -> None:
    result = runner.invoke(app, ["admin"])
    assert result.exit_code == 0


def test_history_empty(tmp_path) -> None:
    db = tmp_path / "h.db"
    result = runner.invoke(app, ["history", "--db", str(db)])
    assert result.exit_code == 0


def test_diff_missing_snapshot(tmp_path) -> None:
    db = tmp_path / "d.db"
    result = runner.invoke(app, ["diff", "1", "2", "--db", str(db)])
    assert result.exit_code == 2


def test_lang_flag_localizes_output() -> None:
    try:
        result = runner.invoke(app, ["--lang", "ru", "version"])
        assert result.exit_code == 0
        assert translator.current_language() == "ru"
    finally:
        translator.set_language("en")


def test_lang_show() -> None:
    result = runner.invoke(app, ["--lang", "en", "lang"])
    assert result.exit_code == 0
    assert "en" in result.stdout
    assert "ru" in result.stdout


def test_lang_set_invalid() -> None:
    result = runner.invoke(app, ["--lang", "en", "lang", "zz"])
    assert result.exit_code == 2


def test_lang_set_valid(tmp_path, monkeypatch) -> None:
    from ininet_win import language

    monkeypatch.setattr(language.cfg, "default_config_path", lambda: tmp_path / "c.json")
    result = runner.invoke(app, ["--lang", "en", "lang", "ru"])
    assert result.exit_code == 0
    assert (tmp_path / "c.json").is_file()
    translator.set_language("en")


def test_main_no_args_launches_tui(monkeypatch) -> None:
    import sys

    from ininet_win import cli

    called = {"tui": False}

    def fake_run_tui(*_args, **_kwargs) -> None:
        called["tui"] = True

    monkeypatch.setattr("ininet_win.tui.app.run_tui", fake_run_tui)
    monkeypatch.setattr(sys, "argv", ["ininet-win"])
    cli.main()
    assert called["tui"] is True


def test_main_with_subcommand_dispatches(monkeypatch) -> None:
    import sys

    from ininet_win import cli

    called = {"app": False}

    def fake_app(*_args, **_kwargs) -> None:
        called["app"] = True

    monkeypatch.setattr(cli, "app", fake_app)
    monkeypatch.setattr(sys, "argv", ["ininet-win", "version"])
    cli.main()
    assert called["app"] is True
