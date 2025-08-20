
from datetime import datetime, timedelta
from dateutil import tz
import os, platform
def to_epoch_seconds_from_date_str(d: str) -> int:
    local_zone = tz.tzlocal()
    dt_local = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=local_zone, hour=0, minute=0, second=0, microsecond=0)
    dt_utc = dt_local.astimezone(tz.tzutc())
    return int(dt_utc.timestamp())
def now_epoch_utc() -> int:
    return int(datetime.now(tz.tzutc()).timestamp())
def exclusive_epoch_for_local_day_end(day_str: str) -> int:
    local_zone = tz.tzlocal()
    dt_local = datetime.strptime(day_str, "%Y-%m-%d").replace(tzinfo=local_zone, hour=0, minute=0, second=0, microsecond=0)
    next_day_local = dt_local + timedelta(days=1)
    dt_utc = next_day_local.astimezone(tz.tzutc())
    return int(dt_utc.timestamp())
def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
def ensure_data_dir():
    d = "data"
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    return d
def default_tokens_path() -> str:
    sys = platform.system()
    if sys == "Windows":
        base = os.getenv("APPDATA", os.path.expanduser(r"~\AppData\Roaming"))
    elif sys == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    p = os.path.join(base, "strava-json-downloader")
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, ".tokens.json")
