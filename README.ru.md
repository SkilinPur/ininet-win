# ininet-win

[![CI](https://github.com/SkilinPur/ininet-win/actions/workflows/ci.yml/badge.svg)](https://github.com/SkilinPur/ininet-win/actions/workflows/ci.yml)

Windows-сборка сетевого инструмента **ininet**: **сканер сети + живой монитор соединений**.

`ininet-win` отвечает на два вопроса:

1. **Что у меня в сети?** — хосты, порты, сервисы.
2. **Что сейчас происходит?** — живые соединения, кто с кем разговаривает.

Часть проектов команды [InIProject](https://iniproject.ru).

> **Linux-версия:** [SkilinPur/ininet](https://github.com/SkilinPur/ininet) — тот же
> инструмент для Linux (отдельный репозиторий, свой платформенный слой).

Язык: [English](README.md) | **Русский**

---

## Возможности (план)

- **Scan** — обнаружение хостов и сканирование портов
- **Watch** — живой список соединений с процессами
- **History** — история сканов и диффы («что изменилось»)
- **TUI / CLI** — интерактивный терминальный интерфейс и скриптуемый CLI
- **Портативный .exe** — запуск без установки Python (позже)

Полный план: [docs/ROADMAP.md](docs/ROADMAP.md)
Концепция и Windows-специфика: [docs/CONCEPT.md](docs/CONCEPT.md)

---

## Использование

```console
# список локальных интерфейсов и подсетей
ininet-win interfaces

# обнаружение живых хостов в подсети
ininet-win scan 192.168.0.0/24 --no-ports

# скан хостов + портов, вывод таблицей
ininet-win scan 192.168.0.0/24 -p 22,80,443

# вывод в JSON
ininet-win scan 192.168.0.0/24 -p 1-1024 --json

# чтение баннеров сервисов с открытых портов
ininet-win scan 192.168.0.0/24 -p 22,80,443 --banners

# живой монитор соединений (read-only)
ininet-win watch
ininet-win watch --process chrome --connected
ininet-win watch --json          # разовый снимок в JSON

# топ процессов по числу соединений
ininet-win top -l 20

# топология сети (хосты и их связи)
ininet-win topology                 # скан первой подсети + живые соединения
ininet-win topology -n 10.0.0.0/24  # явная сеть
ininet-win topology --no-live       # только результаты скана

# объём и скорость трафика по интерфейсам (лёгкий режим, без драйвера)
ininet-win traffic                  # один замер со скоростью
ininet-win traffic -i 2 -n 5        # 5 замеров каждые 2с (live)
ininet-win traffic --all --json     # включая виртуальные интерфейсы, JSON

# интерактивный терминальный интерфейс (Scan / Watch / Top / Traffic / Map / History)
ininet-win tui

# проверка прав / перезапуск с UAC
ininet-win admin
ininet-win admin --elevate

# история сканов и дифф изменений
ininet-win scan 192.168.0.0/24 --save
ininet-win history
ininet-win diff 1 2
ininet-win history --prune 20   # оставить только 20 последних
```

Опции `scan`: `--ports/-p`, `--timeout/-t`, `--port-timeout`, `--jobs/-j`,
`--no-ports`, `--banners`, `--banner-timeout`, `--json`, `--save`, `--db`.
Опции `watch`: `--interval/-i`, `--count/-n`, `--process`, `--port`, `--host`,
`--status`, `--connected`, `--json`, `--elevate`.
Опции `topology`: `--network/-n`, `--ports/-p`, `--timeout/-t`, `--no-scan`,
`--no-live`, `--json`.
Опции `traffic`: `--interval/-i`, `--count/-n`, `--all`, `--json`.
Объём считается по сетевым интерфейсам (счётчики ОС) — не по соединениям.
Для объёма по соединениям нужен ETW или драйвер захвата пакетов (не входит).
Опции `tui`: `--interval/-i`.
TUI требует необязательный extra: `pip install "ininet-win[tui]"`.

> `watch`/`top` показывают процессы для всех соединений только при правах
> администратора. Без них чужие процессы отображаются как PID 0 / пустой процесс,
> а `--elevate` перезапускает команду через UAC.

---

## Язык интерфейса

Интерфейс двуязычный (английский / русский):

- `--lang en|ru` (или `-L`) — переопределить на один запуск
- переменная окружения `ININET_LANG` — переопределить на сессию
- `ininet-win lang` — показать или сменить сохранённый язык
- `ininet-win lang ru` — переключить на русский и сохранить выбор

Приоритет: `--lang` > `ININET_LANG` > сохранённый конфиг > системная локаль. При
первом интерактивном запуске предлагается выбрать язык; в неинтерактивном режиме
используется английский. Настройка хранится в `%LOCALAPPDATA%\ininet\config.json`.

---

## Платформа

- **Windows 10/11** — основной таргет
- Основной терминал: **Windows Terminal**

---

## Требования

- Python 3.10+
- Часть функций может требовать прав администратора (будет помечено явно)

---

## Сборка (однофайловый .exe)

Нужны Windows и Python. Создаёт самодостаточный `dist/ininet-win.exe` со
встроенной иконкой, метаданными версии и локалями (для запуска Python не нужен):

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Затем двойной клик по `ininet-win.exe` (открывает TUI) или подкоманды, напр.
`ininet-win.exe scan 192.168.0.0/24`.

Официальные сборки делает CI: пуш тега вида `v0.1.0` собирает `.exe` из
исходников на `windows-latest` и прикладывает к GitHub Release
(см. `.github/workflows/release.yml`).

---

## Статус

Ранняя разработка. Этапы 0–7 — каркас, scan/watch/elevate/history,
локализация (EN/RU), интерактивный TUI и однофайловая сборка `.exe`.

---

## Лицензия

MIT — см. [LICENSE](LICENSE)
