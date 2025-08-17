
# Strava JSON Downloader (Python)

Fetch your Strava activities as JSON and (optionally) filter to **runs**. 
Secrets are kept in `.env`. The script automatically exchanges your one-time **authorization code** for tokens and then refreshes the access token on subsequent runs.

## Features
- `.env` for `client_id`, `client_secret`, and **one-time** auth `code`
- Automatic token exchange & refresh (`.tokens.json` on disk)
- Fetch activities in a date window (`--after`, `--before`) or by raw epoch seconds
- Filter to **Run** type only (`--only-runs` ON by default)
- Save full JSON to a file (`--out`) + brief console summary
- Handles pagination (`--max-pages`, default 10; `--per-page`, default 200)

## 1) Create a Strava API App (if you haven't)
- In your Strava account -> *Settings* -> *My API Application*.
- Copy `Client ID` and `Client Secret`.
- Generate an **Authorization Code** using Strava's OAuth (follow their docs or your existing flow).
  > The `code` is **one-time**. After the first run the script saves `refresh_token` in `.tokens.json` and you no longer need `STRAVA_AUTH_CODE` in `.env`.

## 2) Fill your `.env`
Copy `.env.example` to `.env` and set values:
```
STRAVA_CLIENT_ID=172550
STRAVA_CLIENT_SECRET=xxx_your_secret_xxx
STRAVA_AUTH_CODE=xxx_one_time_code_xxx
STRAVA_TOKENS_FILE=.tokens.json
STRAVA_BASE_URL=https://www.strava.com
```
> After the first successful run, you can remove `STRAVA_AUTH_CODE` from `.env`.

## 3) Install & Run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Example: fetch all runs between 2025-06-06 and 2025-08-17 (local dates)
python main.py fetch --after 2025-06-06 --before 2025-08-17 --out runs.json

# Or pass epoch seconds:
python main.py fetch --after-epoch 1749177600 --before-epoch 1755388800 --per-page 200 --out runs.json
```

## 4) CLI Usage
```
python main.py fetch [options]

Options:
  --after YYYY-MM-DD         Start date (local). Mutually exclusive with --after-epoch
  --before YYYY-MM-DD        End date (local, exclusive). Mutually exclusive with --before-epoch
  --after-epoch SECONDS      Start epoch seconds (UTC)
  --before-epoch SECONDS     End epoch seconds (UTC)
  --per-page N               Page size (default 200, max 200 per Strava)
  --max-pages N              Max pages to request (default 10)
  --only-runs / --all-types  Filter to activities with type == "Run" (default: only runs)
  --out FILE                 Save JSON to this file (default: data/activities_<timestamp>.json)
  -v, --verbose              Print more details
```

## Notes
- Strava returns a **15-minute** access token. We auto-refresh using the stored `refresh_token`.
- Rate limits: 100 requests per 15 min, 1000 per day (subject to change). Script stops if rate-limited and shows headers.
- Filtering by type happens **client-side**; Strava does not support a `type` filter on `GET /athlete/activities`.

## Project Layout
```
strava-json-downloader/
├── .env.example
├── README.md
├── requirements.txt
├── main.py
├── strava_api.py
└── utils.py
```

## Troubleshooting
- If you see `invalid_grant`, your one-time `code` was already used or expired. Remove `.tokens.json`, set a fresh `STRAVA_AUTH_CODE` and run again.
- If your time window is empty, check your `after`/`before` values (UTC epoch or local dates). 


### Smart `--before` (за замовчуванням)
- Якщо ти не вказуєш `--before/--before-epoch`, скрипт бере **сьогоднішній день (now)**.
- Якщо у вікні `after..now` результатів **нема**, скрипт **автоматично відступить** до "останнього дня з результатами" і повторить запит, щоби віддати тобі найсвіжіші доступні активності.
- Тобі достатньо завжди запускати: `python main.py fetch --after 2025-06-06 --out runs.json`.


## Recommended one-liner (always the same)
Run this every time to keep your JSON up to date from a fixed start date to "now":

```bash
python main.py fetch --after 2025-06-06 --out runs.json --append
```
- If there are no activities in `after..now`, the script automatically falls back to the **most recent day with results**.
- `--append` merges with the existing `runs.json`, deduplicates by activity **id**, and keeps the latest data per activity.
- After saving, the script prints a **quick summary**: total activities, total distance, average pace, longest run.

### Examples
Fetch a wider window explicitly, still appending & deduping:
```bash
python main.py fetch --after 2025-06-06 --before 2025-08-17 --out runs.json --append
```

### Output files
- `runs.json` — merged dataset of your (Run) activities as raw Strava JSON
- `data/activities_*.json` — ad‑hoc dumps if you don't pass `--out`

### Notes
- Distances are in kilometers in the summary (source: Strava `distance` is meters).
- Average pace is calculated as `sum(moving_time) / sum(distance)` and formatted as `mm:ss min/km`.


## VS Code Runner (1-click run)
You can run the fetch command from VS Code without typing it each time.

### Option A — Run/Debug (launch.json)
Already included: `.vscode/launch.json` with **Fetch Strava runs (launch)**.
1) Open the **Run and Debug** panel in VS Code.
2) Choose **Fetch Strava runs (launch)** from the dropdown.
3) Press **Ctrl+F5** (Run Without Debugging) or **F5** (Debug).

Once selected, VS Code remembers this config — next time just hit **Ctrl+F5**.

### Option B — Task (tasks.json) + hotkey
Already included: `.vscode/tasks.json` with a task **Fetch Strava runs (task)**.
- Run it via **Terminal → Run Task… → Fetch Strava runs (task)**.

Optional: add a keyboard shortcut for one-press run.
1) Open **Command Palette → Preferences: Open Keyboard Shortcuts (JSON)**.
2) Add:
```json
{
  "key": "ctrl+alt+r",
  "command": "workbench.action.tasks.runTask",
  "args": "Fetch Strava runs (task)"
}
```
Press **Ctrl+Alt+R** any time to fetch & append.



## One-time OAuth without copy/paste
On the very first run, if no tokens are found and no `STRAVA_AUTH_CODE` is set,
the script now starts a **local OAuth flow** automatically:
- spins up a tiny HTTP server on `http://127.0.0.1:<port>/exchange_token`
- opens your browser to Strava's consent page
- after you click **Authorize**, the code is captured automatically and tokens are saved to `.tokens.json`

Config (optional) in `.env`:
```
STRAVA_REDIRECT_HOST=127.0.0.1
STRAVA_REDIRECT_PORT=8723
STRAVA_SCOPE=read,activity:read_all
STRAVA_OPEN_BROWSER=true
```
> You still need to confirm in the browser (security requirement), but no more copying the `code`.
