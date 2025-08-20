
import argparse, json, os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from strava_api import StravaClient
from utils import (to_epoch_seconds_from_date_str, now_stamp, ensure_data_dir, now_epoch_utc, exclusive_epoch_for_local_day_end, default_tokens_path)
from secrets_store import get_client_id as kc_get_id, get_client_secret as kc_get_secret, set_credentials
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch Strava activities as JSON.")
    sub = p.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init", help="Interactive setup: save client_id/secret to OS keychain and create minimal .env")
    init.add_argument("--client-id", type=str, help="Strava client_id (optional; will prompt if missing)")
    f = sub.add_parser("fetch", help="Fetch activities")
    g = f.add_argument_group("Time window (choose date OR epoch)")
    g.add_argument("--after", type=str, help="Start date (YYYY-MM-DD, local)")
    g.add_argument("--before", type=str, help="End date (YYYY-MM-DD, local, exclusive)")
    g.add_argument("--after-epoch", type=int, help="Start epoch seconds (UTC)")
    g.add_argument("--before-epoch", type=int, help="End epoch seconds (UTC)")
    f.add_argument("--per-page", type=int, default=200, help="Items per page (max 200)")
    f.add_argument("--max-pages", type=int, default=10, help="Max pages to fetch")
    f.add_argument("--only-runs", dest="only_runs", action="store_true", help="Filter to type == Run (default)")
    f.add_argument("--all-types", dest="only_runs", action="store_false", help="Include all activity types")
    f.set_defaults(only_runs=True)
    f.add_argument("--out", type=str, default=None, help="Output JSON file path")
    f.add_argument("--append", action="store_true", help="Append to --out by merging & deduping by activity id")
    f.add_argument("-v", "--verbose", action="store_true", help="Verbose logs")
    return p.parse_args()
def fmt_min_per_km(seconds_per_km: float) -> str:
    if seconds_per_km <= 0 or not (seconds_per_km == seconds_per_km): return "-"
    minutes = int(seconds_per_km // 60); secs = int(round(seconds_per_km % 60))
    return f"{minutes}:{secs:02d} min/km"
def summarize(activities: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(activities); dist_m = sum((a.get("distance") or 0) for a in activities); moving_s = sum((a.get("moving_time") or 0) for a in activities)
    dist_km = dist_m / 1000.0; hours = moving_s / 3600.0; pace_sec_per_km = (moving_s / dist_km) if dist_km > 0 else float("nan")
    longest_m = 0.0; latest_dt: Optional[str] = None
    for a in activities:
        d = a.get("distance") or 0; 
        if d > longest_m: longest_m = d
        sd = a.get("start_date_local") or a.get("start_date")
        if isinstance(sd, str) and (latest_dt is None or sd > latest_dt): latest_dt = sd
    return {"total_activities": total, "total_distance_km": round(dist_km, 2), "total_moving_hours": round(hours, 2), "avg_pace_min_per_km": fmt_min_per_km(pace_sec_per_km), "longest_run_km": round(longest_m / 1000.0, 2), "latest_activity_datetime": latest_dt}
def merge_dedupe(existing: Optional[List[Any]], new_items: Optional[List[Any]]) -> List[Dict[str, Any]]:
    by_id: Dict[Any, Dict[str, Any]] = {}
    for a in (existing or []):
        if isinstance(a, dict) and "id" in a: by_id[a["id"]] = a
    for a in (new_items or []):
        if isinstance(a, dict) and "id" in a: by_id[a["id"]] = a
    arr = list(by_id.values())
    def keyfunc(a: Dict[str, Any]) -> str: return str(a.get("start_date_local") or a.get("start_date") or "")
    arr.sort(key=keyfunc, reverse=True); return arr
def _validate_time_args(args: argparse.Namespace) -> None:
    if args.cmd != "fetch": return
    if args.after and args.after_epoch is not None: raise SystemExit("Use either --after or --after-epoch, not both.")
    if args.before and args.before_epoch is not None: raise SystemExit("Use either --before or --before-epoch, not both.")
    if args.after:
        try: datetime.strptime(args.after, "%Y-%m-%d")
        except ValueError: raise SystemExit("--after must be in YYYY-MM-DD format.")
    if args.before:
        try: datetime.strptime(args.before, "%Y-%m-%d")
        except ValueError: raise SystemExit("--before must be in YYYY-MM-DD format.")
def do_init(client_id_arg: Optional[str] = None) -> None:
    cid = client_id_arg or input("Your Strava CLIENT_ID: ").strip()
    from getpass import getpass; csec = getpass("Your Strava CLIENT_SECRET (hidden): ").strip()
    if not cid or not csec: raise SystemExit("Both client_id and client_secret are required.")
    set_credentials(cid, csec)
    tokens_default = default_tokens_path()
    open(".env","w",encoding="utf-8").write("STRAVA_BASE_URL=https://www.strava.com\n"+f"STRAVA_TOKENS_FILE={tokens_default}\n"+"STRAVA_OPEN_BROWSER=true\n")
    print(f"Saved credentials to OS keychain and wrote minimal .env with STRAVA_TOKENS_FILE={tokens_default}")
def main() -> None:
    args = parse_args(); _validate_time_args(args); load_dotenv()
    if args.cmd == "init": do_init(args.client_id); return
    base_url = os.getenv("STRAVA_BASE_URL","https://www.strava.com")
    client_id = os.getenv("STRAVA_CLIENT_ID") or kc_get_id()
    client_secret = os.getenv("STRAVA_CLIENT_SECRET") or kc_get_secret()
    if not (client_id and client_secret): raise SystemExit("Missing credentials. Run: python main.py init")
    auth_code = os.getenv("STRAVA_AUTH_CODE"); tokens_file = os.getenv("STRAVA_TOKENS_FILE") or default_tokens_path()
    client = StravaClient(base_url=base_url, client_id=str(client_id), client_secret=str(client_secret), tokens_file=str(tokens_file), verbose=args.verbose)
    try:
        if args.verbose: print("Ensuring access token...")
        client.ensure_access_token(auth_code=auth_code)
    except RuntimeError as e:
        msg = str(e)
        if ("No valid tokens found and no STRAVA_AUTH_CODE provided" in msg) or ("No valid tokens found" in msg):
            from oauth_flow import run_local_authorization_flow
            redirect_host = os.getenv("STRAVA_REDIRECT_HOST","127.0.0.1"); redirect_port = int(os.getenv("STRAVA_REDIRECT_PORT","8723"))
            scope = os.getenv("STRAVA_SCOPE","read,activity:read_all"); open_browser = os.getenv("STRAVA_OPEN_BROWSER","true").lower() in ("1","true","yes","y")
            print("Starting local OAuth flow..."); code = run_local_authorization_flow(client_id=str(client_id), scope=scope, redirect_host=redirect_host, redirect_port=redirect_port, open_browser=open_browser)
            print("Got authorization code. Exchanging for tokens..."); client.ensure_access_token(auth_code=code)
        else: raise
    if args.after_epoch is not None: after = args.after_epoch
    elif args.after: after = to_epoch_seconds_from_date_str(args.after)
    else: raise SystemExit("Please provide --after or --after-epoch")
    if args.before_epoch is not None: before = args.before_epoch
    elif args.before: before = to_epoch_seconds_from_date_str(args.before)
    else: before = now_epoch_utc()
    if args.verbose: print(f"Fetching activities (after={after}, before={before})...")
    activities = client.get_activities(after=after, before=before, per_page=args.per_page, max_pages=args.max_pages, only_runs=args.only_runs)
    user_provided_before = (args.before_epoch is not None) or (args.before is not None)
    if not activities and not user_provided_before:
        if args.verbose: print("No activities in after..now window. Trying the most recent day with results...")
        latest = client.get_activities(after=after, before=before, per_page=1, max_pages=10, only_runs=args.only_runs)
        if latest:
            latest_day = (latest[0].get("start_date_local") or latest[0].get("start_date") or "")[:10]
            if latest_day:
                before = exclusive_epoch_for_local_day_end(latest_day)
                if args.verbose: print(f"Refetching up to end of {latest_day} (exclusive epoch {before})...")
                activities = client.get_activities(after=after, before=before, per_page=args.per_page, max_pages=args.max_pages, only_runs=args.only_runs)
    ensure_data_dir(); out_path = args.out or f"data/activities_{now_stamp()}.json"
    if args.append and os.path.isfile(out_path):
        try: existing = json.load(open(out_path,"r",encoding="utf-8"))
        except Exception: existing = []
        if not isinstance(existing, list): existing = []
        merged = merge_dedupe(existing, activities); payload = merged
    else:
        merged = merge_dedupe([], activities); payload = activities
    json.dump(payload, open(out_path,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    summary = summarize(merged if args.append else activities)
    print(f"Fetched {len(activities)} new activities{' (runs only)' if args.only_runs else ''}.")
    if args.append: print(f"Merged dataset size: {len(merged)} activities -> {out_path}")
    else: print(f"Saved to {out_path}")
    print("Quick summary:", json.dumps(summary, indent=2))
if __name__ == "__main__": main()
