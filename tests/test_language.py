import pytest

from ininet_win import config as cfg
from ininet_win import language


@pytest.fixture(autouse=True)
def _isolate_config(tmp_path, monkeypatch):
    monkeypatch.setenv(language.ENV_VAR, "")
    monkeypatch.delenv("ININET_LANG", raising=False)
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr(language.cfg, "default_config_path", lambda: cfg_path)
    return cfg_path


def test_flag_takes_priority(monkeypatch) -> None:
    monkeypatch.setenv("ININET_LANG", "en")
    lang, prompted = language.resolve_language("ru", prompt=False)
    assert lang == "ru"
    assert prompted is False


def test_env_used_when_no_flag(monkeypatch) -> None:
    monkeypatch.setenv("ININET_LANG", "ru")
    lang, _ = language.resolve_language(prompt=False)
    assert lang == "ru"


def test_config_used_when_no_flag_or_env() -> None:
    cfg.set_language("ru")
    lang, _ = language.resolve_language(prompt=False)
    assert lang == "ru"


def test_defaults_to_en_when_nothing_set(monkeypatch) -> None:
    monkeypatch.setattr(language, "_system_lang", lambda: None)
    monkeypatch.setattr(language, "_is_interactive", lambda: False)
    lang, prompted = language.resolve_language(prompt=True)
    assert lang == "en"
    assert prompted is False
