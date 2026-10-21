# ininet-win

[![CI](https://github.com/SkilinPur/ininet-win/actions/workflows/ci.yml/badge.svg)](https://github.com/SkilinPur/ininet-win/actions/workflows/ci.yml)

Windows build of the **ininet** network tool: a **network scanner + live connection monitor**.

`ininet-win` answers two questions:

1. **What is on my network?** — hosts, ports, services.
2. **What is happening right now?** — live connections, who talks to whom.

Part of the [InIProject](https://iniproject.ru) projects.

> **Linux version:** [SkilinPur/ininet](https://github.com/SkilinPur/ininet) — the same
> tool for Linux (separate repository, its own platform layer).

Language: **English** | [Русский](README.ru.md)

---

## Features

- **Scan** — host discovery and TCP port scanning, with banner grabbing for
  service identification
- **Watch** — live connection list mapped to owning processes
- **Top** — top processes by number of connections
- **Topology** — a host graph combining scan results and live connections
- **Traffic** — per-interface volume and rate (light mode, no driver, no admin)
- **History** — saved scan snapshots and diffs ("what changed")
- **TUI** — interactive terminal UI (Scan / Watch / Top / Traffic / Map / History)
- **CLI** — scriptable commands with rich tables and JSON output
- **Bilingual** — English / Russian interface
- **Portable .exe** — single-file build, runs without installing Python

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

# grab service banners from open ports
ininet-win scan 192.168.0.0/24 -p 22,80,443 --banners

# live connection monitor (read-only)
ininet-win watch
ininet-win watch --process chrome --connected
ininet-win watch --json          # one-shot JSON snapshot

# top processes by connection count
ininet-win top -l 20

# network topology (hosts and their links)
ininet-win topology                 # scan first subnet + live connections
ininet-win topology -n 10.0.0.0/24  # explicit network
ininet-win topology --no-live       # scan results only

# per-interface traffic volume and rate (light mode, no driver)
ininet-win traffic                  # one sample with rates
ininet-win traffic -i 2 -n 5        # 5 samples every 2s (live)
ininet-win traffic --all --json     # include virtual interfaces, JSON

# interactive terminal UI (Scan / Watch / Top / Traffic / Map / History)
ininet-win tui

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
`--no-ports`, `--banners`, `--banner-timeout`, `--json`, `--save`, `--db`.
`watch` options: `--interval/-i`, `--count/-n`, `--process`, `--port`, `--host`,
`--status`, `--connected`, `--json`, `--elevate`.
`topology` options: `--network/-n`, `--ports/-p`, `--timeout/-t`, `--no-scan`,
`--no-live`, `--json`.
`traffic` options: `--interval/-i`, `--count/-n`, `--all`, `--json`.
Volume is per network interface (OS counters) — not per connection. Per-connection
volume would require ETW or a packet-capture driver (not included).
`tui` options: `--interval/-i`.
The TUI needs the optional extra: `pip install "ininet-win[tui]"`.

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

## Build (single-file .exe)

Requires Windows and Python. Creates a standalone `dist/ininet-win.exe` with
embedded icon, version metadata and locales (no Python needed to run it):

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Then double-click `ininet-win.exe` (starts the TUI) or call subcommands, e.g.
`ininet-win.exe scan 192.168.0.0/24`.

Official builds are produced by CI: pushing a tag like `v0.1.0` builds the
`.exe` from source on `windows-latest` and attaches it to a GitHub Release
(see `.github/workflows/release.yml`).

---

## Status

Feature-complete for the core scope (Stages 0–9): scanning, live monitoring,
history/diffs, service detection, the interactive TUI, topology and traffic,
localization and a single-file `.exe` build. Alerts and a public release
(Stage 10) are left as optional future work.

---

## License

MIT — see [LICENSE](LICENSE)
