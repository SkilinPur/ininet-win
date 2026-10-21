import json

import pytest

from ininet_win.i18n import (
    DEFAULT_LANG,
    SUPPORTED_LANGS,
    available_langs,
    load_catalog,
    locales_dir,
    normalize_lang,
    translator,
)


def test_supported_langs_have_files() -> None:
    assert set(available_langs()) == set(SUPPORTED_LANGS)


def test_locale_files_share_keys() -> None:
    en = set(load_catalog("en"))
    ru = set(load_catalog("ru"))
    assert en, "en catalog must not be empty"
    assert en == ru, f"missing keys in ru: {en - ru}; extra in ru: {ru - en}"


def test_locale_files_are_valid_json() -> None:
    for lang in SUPPORTED_LANGS:
        raw = (locales_dir() / f"{lang}.json").read_text(encoding="utf-8")
        data = json.loads(raw)
        assert isinstance(data, dict)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ru", "ru"),
        ("ru-RU", "ru"),
        ("ru_RU", "ru"),
        ("EN", "en"),
        ("en-US", "en"),
        ("de", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_lang(value, expected) -> None:
    assert normalize_lang(value) == expected


def test_t_falls_back_to_key() -> None:
    translator.set_language("en")
    assert translator.t("this.key.does.not.exist") == "this.key.does.not.exist"


def test_t_formats_placeholders() -> None:
    translator.set_language("en")
    assert translator.t("lang.set", lang="en") == "Language: en"


def test_set_language_switches_catalog() -> None:
    try:
        translator.set_language("ru")
        assert translator.current_language() == "ru"
        assert translator.t("lang.set", lang="ru") == "Язык: ru"
        translator.set_language("en")
        assert translator.t("lang.set", lang="en") == "Language: en"
    finally:
        translator.set_language(DEFAULT_LANG)


def test_set_language_unknown_falls_back_to_default() -> None:
    try:
        assert translator.set_language("zz") == DEFAULT_LANG
        assert translator.current_language() == DEFAULT_LANG
    finally:
        translator.set_language(DEFAULT_LANG)
