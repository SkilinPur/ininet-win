import json

from ininet_win import config as cfg


def test_default_config_path_under_ininet() -> None:
    path = cfg.default_config_path()
    assert path.name == "config.json"
    assert path.parent.name == "ininet"


def test_load_missing_returns_empty(tmp_path) -> None:
    assert cfg.load_config(tmp_path / "nope.json") == {}


def test_set_and_get_language(tmp_path) -> None:
    path = tmp_path / "config.json"
    cfg.set_language("ru", path)
    assert cfg.get_language(path) == "ru"


def test_save_creates_parents(tmp_path) -> None:
    path = tmp_path / "a" / "b" / "config.json"
    cfg.set_language("en", path)
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8"))["language"] == "en"


def test_invalid_json_returns_empty(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")
    assert cfg.load_config(path) == {}
