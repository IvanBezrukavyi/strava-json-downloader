# Strava JSON Downloader

A small utility to export your **Strava** activities as **JSON**.  
This project follows **security best practices**: secrets are stored in the **OS keychain** (Credential Manager / Keychain / Secret Service), and OAuth tokens are kept **outside the repository**.

## Table of Contents
- [Features](#features)
- [Architecture & Security](#architecture--security)
- [Requirements](#requirements)
- [Core Prerequisites](#core-prerequisites)
- [Installation](#installation)
- [Initial Setup (`init`)](#initial-setup-init)
- [Running (`fetch`)](#running-fetch)
- [CLI Options & Examples](#cli-options--examples)
- [Where tokens are stored](#where-tokens-are-stored)
- [Environment variables](#environment-variables)
- [VS Code: one-click run](#vs-code-one-click-run)
- [Desktop shortcut (Windows)](#desktop-shortcut-windows)
- [SSL/Proxy fixes on Windows](#sslproxy-fixes-on-windows)
- [Troubleshooting](#troubleshooting)
- [Recommended .gitignore](#recommended-gitignore)
- [License](#license)

---

## Features
- Export your Strava activities as **JSON**.
- **Runs only** by default (`--only-runs`), or **all types** with `--all-types`.
- Flexible **time window**: by dates (`--after/--before`) or epoch seconds.
- **Append mode** merges output and **deduplicates by `activity.id`**.
- Interactive **OAuth** (opens your browser on first run, then reuses refresh tokens).
- Quick **summary** after fetch (count, distance, moving hours, avg pace, longest run, latest).

---

## Architecture & Security
- Secrets (`client_id`, `client_secret`) live in the **OS keychain** via `keyring`.
- OAuth tokens (`.tokens.json`) are stored **outside the repo** in a per-user config directory.
- `.env` contains only **non-secret** settings (e.g., token file path).
- First run performs browser-based **OAuth** and caches tokens locally.

```
project/
├─ main.py           # CLI: subcommands `init`, `fetch`
├─ strava_api.py     # API wrapper + controlled SSL verification/CA bundle
├─ oauth_flow.py     # Local HTTP server + browser open for OAuth
├─ secrets_store.py  # keyring helpers: save/read client_id/secret
├─ utils.py          # time helpers, default token path, etc.
├─ requirements.txt
└─ .env.example
```

---

## Requirements
- Python **3.10+** (tested on 3.11–3.13)
- A Strava account and a Strava **API application** (to obtain `client_id` and `client_secret`)

---

## Core Prerequisites

Before running this project, users must obtain **client_id** and **client_secret** from Strava.

To do this:
1. Log in to your [Strava account](https://www.strava.com/).
2. Navigate to **Settings → My API Application**.
3. Create a new API application.
4. Copy the generated **Client ID** and **Client Secret**.
5. Store them securely (e.g., in your `.env` file or system keyring).

These credentials are required for authenticating with the Strava API.

## Installation
```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

> PowerShell might block scripts the first time. Allow once:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

---

## Initial Setup (`init`)
Store your credentials in the keychain and create a minimal `.env`:

```bash
python main.py init
# → enter your Strava CLIENT_ID (visible) and CLIENT_SECRET (hidden)
```

`init`:
- saves `client_id` / `client_secret` in the **OS keychain**;
- writes `.env` with a safe default path for tokens **outside the repo**.

> You can override the keychain with env vars `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET` if you really want (e.g., CI).

---

## Running (`fetch`)
Typical command:
```bash
python main.py fetch --after 2025-06-06 --out runs.json --append
```

- If **`--before` is omitted**, the upper bound is **now**.
- If the window `after..now` has no data, the client **auto-shifts** `before` to the **most recent day with results**.
- `--append` merges with the existing file and deduplicates by `activity.id`.
- On the **first ever** API call (no tokens yet), a browser tab opens—click **Authorize**. Tokens are then cached and refresh automatically.

---

## CLI Options & Examples

### Time window
- By date (local time):
  - `--after YYYY-MM-DD`
  - `--before YYYY-MM-DD` *(exclusive: internally this means the start of the next local day)*
- By epoch (UTC):
  - `--after-epoch 1749157200`
  - `--before-epoch 1755378000`

### Other flags
- `--per-page 200` — items per page (max 200).
- `--max-pages 10` — cap on total pages fetched.
- `--only-runs` / `--all-types` — filter activity types.
- `--out path.json` — output file path.
- `--append` — merge with existing output.
- `-v/--verbose` — verbose logging.

### Examples
```bash
# 1) Fetch runs, merge into runs.json:
python main.py fetch --after 2025-06-06 --out runs.json --append

# 2) Upper bound by date:
python main.py fetch --after 2025-06-06 --before 2025-08-17 --out runs.json --append

# 3) All activity types:
python main.py fetch --after 2025-06-06 --all-types --out all.json
```

---

## Where tokens are stored
Default `STRAVA_TOKENS_FILE` is a per-user config path:

- **Windows:** `%APPDATA%\strava-json-downloader\.tokens.json`  
- **macOS:** `~/Library/Application Support/strava-json-downloader/.tokens.json`  
- **Linux:** `$XDG_CONFIG_HOME/strava-json-downloader/.tokens.json` or `~/.config/strava-json-downloader/.tokens.json`

> You can override the path in `.env`, but keeping tokens outside the repo is recommended.

---

## Environment variables

### If you don’t use `init` (not recommended)
- `STRAVA_CLIENT_ID` — can be set instead of keychain.
- `STRAVA_CLIENT_SECRET` — **secret**; prefer keychain, but env var works.

### OAuth
- `STRAVA_BASE_URL` — usually `https://www.strava.com`.
- `STRAVA_AUTH_URL` — full authorize URL (derived from `BASE_URL` by default).
- `STRAVA_REDIRECT_HOST` — `127.0.0.1`.
- `STRAVA_REDIRECT_PORT` — `8723` (client will pick a free port if taken).
- `STRAVA_SCOPE` — `read,activity:read_all`.
- `STRAVA_OPEN_BROWSER` — `true|false`.

### Tokens
- `STRAVA_TOKENS_FILE` — full path to `.tokens.json` (default is the per-user config dir above).

### SSL / corporate proxies
- `STRAVA_VERIFY_SSL` — `true|false` (**false only for temporary diagnostics**).
- `STRAVA_CA_BUNDLE` — path to a custom `root_ca.pem` (corporate MITM proxy).
- Also respected: `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`.

---

## VS Code: one-click run
This repo contains `.vscode/launch.json` with:
- **Init (keyring setup)** — run once to store secrets.
- **Fetch Strava runs (launch)** — runs  
  `python main.py fetch --after 2025-06-06 --out runs.json --append`.

---

## Desktop shortcut (Windows)
1. Download the optional **desktop shortcut pack**.
2. Copy `run_strava_fetch.bat` and `CreateStravaShortcut.vbs` into your project folder.  
   If your project isn’t at `D:\repo\strava-json-downloader`, update that path inside both files.
3. Double-click `CreateStravaShortcut.vbs` → a **Fetch Strava Runs** icon appears on the Desktop.
4. Click the icon to save `runs.json` directly into **Downloads**.

---

## SSL/Proxy fixes on Windows
If you hit `SSLError: certificate verify failed`:
1. The project includes the conditional dependency  
   `python-certifi-win32; sys_platform == 'win32'` — it hooks Windows’ system certificates into `requests`.
2. If your corporate proxy re-signs TLS, export your **Root CA** as `*.pem` and set:
   - in `.env`: `STRAVA_CA_BUNDLE=C:/path/to/root_ca.pem`, or
   - as env var: `REQUESTS_CA_BUNDLE=C:\path\to\root_ca.pem`.
3. For quick diagnostics only: `STRAVA_VERIFY_SSL=false` (turn back to `true` afterwards).

---

## Troubleshooting

| Symptom | Why | Fix |
|---|---|---|
| `main.py: No such file or directory` | Running from the wrong directory | `cd` into the folder that contains `main.py` |
| `Missing credentials. Run: python main.py init` | No `client_id/secret` in keychain or env | Run `python main.py init` and enter your values |
| Browser opens but no redirect | Port blocked/in use, firewall | Set `STRAVA_REDIRECT_PORT` to another value (e.g., 8724) and retry |
| `SSLError: certificate verify failed` | Corporate TLS interception | See [SSL/Proxy fixes](#sslproxy-fixes-on-windows) |
| `429 Rate limited` | Strava API throttling | Lower `--per-page` / `--max-pages`, wait and retry |

---

## Recommended .gitignore
```
.env
.tokens.json
/data/
__pycache__/
*.pyc
```

Keep real secrets out of Git; tokens live outside the repo by default.

---

## License
MIT
