# ininet-win

Windows build of the **ininet** network tool: a **network scanner + live connection monitor**.

`ininet-win` answers two questions:

1. **What is on my network?** — hosts, ports, services.
2. **What is happening right now?** — live connections, who talks to whom.

Part of the [InIProject](https://iniproject.ru) projects.

> **Linux version:** [SkilinPur/ininet](https://github.com/SkilinPur/ininet) — the same
> tool for Linux (separate repository, its own platform layer).

Language: **English** | [Русский](README.ru.md)

---

## Features (roadmap)

- **Scan** — host discovery and port scanning
- **Watch** — live connection list with processes
- **History** — scan history and diffs ("what changed")
- **TUI / CLI** — interactive mode and a scriptable CLI
- **Portable .exe** — run without installing Python (later)

Full plan: [docs/ROADMAP.md](docs/ROADMAP.md)
Concept and Windows specifics: [docs/CONCEPT.md](docs/CONCEPT.md)

---

## Usage

```console
# list local interfaces and subnets
ininet-win interfaces

# discover live hosts in a subnet
ininet-win scan 192.168.0.0/24 --no-ports

# scan hosts + ports, print as a table
ininet-win scan 192.168.0.0/24 -p 22,80,443

# JSON output
ininet-win scan 192.168.0.0/24 -p 1-1024 --json

# live connection monitor (read-only)
ininet-win watch
ininet-win watch --process chrome --connected
ininet-win watch --json          # one-shot JSON snapshot

# top processes by connection count
ininet-win top -l 20

# privilege check / relaunch with UAC
ininet-win admin
ininet-win admin --elevate

# scan history and diffs
ininet-win scan 192.168.0.0/24 --save
ininet-win history
ininet-win diff 1 2
ininet-win history --prune 20   # keep only the latest 20
```

`scan` options: `--ports/-p`, `--timeout/-t`, `--port-timeout`, `--jobs/-j`,
`--no-ports`, `--json`, `--save`, `--db`.
`watch` options: `--interval/-i`, `--count/-n`, `--process`, `--port`, `--host`,
`--status`, `--connected`, `--json`, `--elevate`.

> `watch`/`top` show processes for all connections only with administrator rights.
> Without them, other users' processes appear as PID 0 / empty process, and
> `--elevate` relaunches the command via UAC.

---

## Language

The interface is bilingual (English / Russian):

- `--lang en|ru` (or `-L`) — override for a single run
- `ININET_LANG` environment variable — override for the session
- `ininet-win lang` — show or change the saved language
- `ininet-win lang ru` — switch to Russian and save the choice

Precedence: `--lang` > `ININET_LANG` > saved config > system locale. On the first
interactive run you are asked to choose a language; non-interactive runs default to
English. The preference is stored in `%LOCALAPPDATA%\ininet\config.json`.

---

## Platform

- **Windows 10/11** — primary target
- Primary terminal: **Windows Terminal**

---

## Requirements

- Python 3.10+
- Some features may require administrator rights (will be marked explicitly)

---

## Status

Early development. Stage 0 — project skeleton, plus scan/watch/elevate/history and
localization (EN/RU).

---

## License

MIT — see [LICENSE](LICENSE)
