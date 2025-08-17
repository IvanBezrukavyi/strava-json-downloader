
# Strava JSON Downloader (Python)

Отримуй свої активності зі Strava у **JSON** (за замовчуванням — тільки біг). Секрети тримаються у `.env`. 
Перший запуск — інтерактивний OAuth **без ручного копіювання code**: скрипт сам відкриє сторінку Strava, спіймає `code`, обміняє на токени і збереже у `.tokens.json`. Далі — автоматичний refresh.

## Можливості
- `.env` для `client_id`, `client_secret` (+ опції для OAuth та SSL)
- Автоматичний **обмін** одноразового `code` та **оновлення** токена (`.tokens.json`)
- Вікно дат через локальні дати (`--after/--before`) або epoch seconds
- Фільтр тільки **Run** (`--only-runs` за замовчуванням)
- Пагінація (`--per-page` до 200, `--max-pages`)
- `--append` — мердж + дедуплікація (по `activity.id`) у твій `--out`
- **Quick summary** після кожного запуску (кількість, км, темп, найдовша, остання активність)
- “Розумний” `--before`: якщо не заданий і вікно `after..now` порожнє — скрипт бере **останній день з результатами**
- **VS Code Runner**: 1 клік через `launch.json`/`tasks.json`
- **SSL-налаштування**: власний CA bundle/вимкнення перевірки (для діагностики)

## Встановлення
```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

## Налаштуй `.env`
Скопіюй `.env.example` → `.env` і заповни мінімум:
```
STRAVA_CLIENT_ID=...
STRAVA_CLIENT_SECRET=...
STRAVA_TOKENS_FILE=.tokens.json
STRAVA_BASE_URL=https://www.strava.com
# для інтерактивного запуску — цього досить, STRAVA_AUTH_CODE не потрібен
```

### (Опціонально) OAuth конфіг
```
STRAVA_REDIRECT_HOST=127.0.0.1
STRAVA_REDIRECT_PORT=8723
STRAVA_SCOPE=read,activity:read_all
STRAVA_OPEN_BROWSER=true
# AUTH URL можна перевизначити (зазвичай не потрібно):
# STRAVA_AUTH_URL=https://www.strava.com/oauth/authorize
```

### (Опціонально) SSL / сертифікати
```
# Використовувати перевірку сертифікатів (рекомендовано)
STRAVA_VERIFY_SSL=true
# Кастомний CA bundle (PEM), якщо корпоративний проксі підміняє TLS
# STRAVA_CA_BUNDLE=C:/path/to/org_root_ca.pem
```

## Запуск (рекомендовано — одна і та сама команда)
```bash
python main.py fetch --after 2025-06-06 --out runs.json --append
```
Що станеться:
- якщо немає `.tokens.json` і не задано `STRAVA_AUTH_CODE`, скрипт **відкриє браузер** на OAuth і сам перехопить `code`;
- якщо `--before` не задано — візьме **поточний момент (now)**;
- якщо вікно `after..now` порожнє — автоматично зсуне `before` на **останній день з даними**;
- збереже JSON (`--append` змерджить із наявним, приберуться дублі за `id`);
- виведе зведення (кількість, км, темп, найдовша, остання активність).

### Приклади
- Фіксоване вікно:
  ```bash
  python main.py fetch --after 2025-06-06 --before 2025-08-17 --out runs.json --append
  ```
- Перезапис без мерджу:
  ```bash
  python main.py fetch --after 2025-06-06 --out runs.json
  ```

## VS Code Runner (1‑клік)
У папці `.vscode` вже є:
- **Run/Debug**: *Fetch Strava runs (launch)* — обери у Run and Debug → `Ctrl+F5`.
- **Task**: *Fetch Strava runs (task)* — Terminal → Run Task…

(Опційно) хоткей для Task:
1) Command Palette → **Preferences: Open Keyboard Shortcuts (JSON)**  
2) Додай:
```json
{
  "key": "ctrl+alt+r",
  "command": "workbench.action.tasks.runTask",
  "args": "Fetch Strava runs (task)"
}
```

## SSL certificate errors (Windows / proxy)
Якщо бачиш `SSLError: certificate verify failed`:
1) Онови CA:
```bash
pip install --upgrade certifi
python -c "import certifi; print(certifi.where())"
```
2) Якщо корпоративний проксі/антивірус підміняє TLS — експортуй Root CA у `.pem` та вкажи його:
```powershell
$env:REQUESTS_CA_BUNDLE="C:\path\org_root_ca.pem"
```
або у `.env`:
```
STRAVA_CA_BUNDLE=C:/path/to/org_root_ca.pem
```
3) Лише для діагностики (НЕ рекомендується):
```
STRAVA_VERIFY_SSL=false
```

## Структура
```
strava-json-downloader/
├─ .env.example
├─ README.md
├─ requirements.txt
├─ main.py
├─ strava_api.py
├─ oauth_flow.py
├─ utils.py
└─ .vscode/
   ├─ launch.json
   └─ tasks.json
```

## Troubleshooting
- `invalid_grant` — одноразовий `STRAVA_AUTH_CODE` вже використаний або протермінований. Видали `.tokens.json`, задай свіжий `STRAVA_AUTH_CODE` (або пройди інтерактивний OAuth) і повтори.
- Порожній результат — перевір `after/before` (локальні дати vs epoch). З `--before` за замовчуванням використовується `now` + fallback на останній день з даними.
