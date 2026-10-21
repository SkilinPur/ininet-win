# ininet-win

Windows-сборка сетевого инструмента **ininet**: **сканер сети + живой монитор соединений**.

`ininet-win` отвечает на два вопроса:

1. **Что у меня в сети?** — хосты, порты, сервисы.
2. **Что сейчас происходит?** — живые соединения, кто с кем разговаривает.

Часть проектов команды [InIProject](https://iniproject.ru).

> **Linux-версия:** [SkilinPur/ininet](https://github.com/SkilinPur/ininet) — тот же
> инструмент для Linux (отдельный репозиторий, свой платформенный слой).

---

## Возможности (план)

- **Scan** — обнаружение хостов и сканирование портов
- **Watch** — живой список соединений с процессами
- **History** — история сканов и диффы («что изменилось»)
- **TUI / CLI** — интерактивный режим и скриптуемый CLI
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

# живой монитор соединений (read-only)
ininet-win watch
ininet-win watch --process chrome --connected
ininet-win watch --json          # разовый снимок в JSON

# топ процессов по числу соединений
ininet-win top -l 20
```

Опции `scan`: `--ports/-p`, `--timeout/-t`, `--port-timeout`, `--jobs/-j`,
`--no-ports`, `--json`.
Опции `watch`: `--interval/-i`, `--count/-n`, `--process`, `--port`, `--host`,
`--status`, `--connected`, `--json`.

---

## Платформа

- **Windows 10/11** — основной таргет
- Основной терминал: **Windows Terminal**

---

## Требования

- Python 3.10+
- Часть функций может требовать прав администратора (будет помечено явно)

---

## Статус

Ранняя разработка. Этап 0 — каркас проекта.

---

## Лицензия

MIT — см. [LICENSE](LICENSE)
