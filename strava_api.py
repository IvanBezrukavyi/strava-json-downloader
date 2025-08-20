
import json, os, time, requests, certifi
from typing import Dict, List, Optional
TOKEN_URL = "/oauth/token"
ACTIVITIES_URL = "/api/v3/athlete/activities"
class StravaClient:
    def __init__(self, base_url: str, client_id: str, client_secret: str, tokens_file: str=".tokens.json", verbose: bool=False):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokens_file = tokens_file
        self.verbose = verbose
        self._tokens: Optional[Dict] = None
        verify_flag = os.getenv("STRAVA_VERIFY_SSL","true").lower() in ("1","true","yes","y")
        ca_bundle = (os.getenv("STRAVA_CA_BUNDLE") or os.getenv("REQUESTS_CA_BUNDLE") or os.getenv("CURL_CA_BUNDLE") or certifi.where())
        self._verify = ca_bundle if verify_flag else False
        if self.verbose: print(f"SSL verify: {verify_flag}, CA bundle: {ca_bundle if verify_flag else 'DISABLED'}")
    def _load_tokens_from_disk(self) -> Optional[Dict]:
        if os.path.isfile(self.tokens_file):
            try:
                return json.load(open(self.tokens_file, "r", encoding="utf-8"))
            except Exception: return None
        return None
    def _save_tokens_to_disk(self, tokens: Dict):
        json.dump(tokens, open(self.tokens_file, "w", encoding="utf-8"), indent=2)
    def _have_valid_access_token(self) -> bool:
        t = self._tokens or {}; exp = int(t.get("expires_at", 0))
        return bool(t.get("access_token")) and exp > int(time.time())+30
    def _exchange_code_for_tokens(self, code: str) -> Dict:
        url = f"{self.base_url}{TOKEN_URL}"
        payload = {"client_id": self.client_id, "client_secret": self.client_secret, "code": code, "grant_type": "authorization_code"}
        r = requests.post(url, json=payload, timeout=30, verify=self._verify)
        if r.status_code != 200: raise RuntimeError(f"Token exchange failed: {r.status_code} {r.text}")
        if self.verbose: print("Exchanged authorization code for tokens.")
        return r.json()
    def _refresh_access_token(self, refresh_token: str) -> Dict:
        url = f"{self.base_url}{TOKEN_URL}"
        payload = {"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "refresh_token", "refresh_token": refresh_token}
        r = requests.post(url, json=payload, timeout=30, verify=self._verify)
        if r.status_code != 200: raise RuntimeError(f"Token refresh failed: {r.status_code} {r.text}")
        if self.verbose: print("Refreshed access token.")
        return r.json()
    def ensure_access_token(self, auth_code: Optional[str]=None) -> str:
        if not self._tokens: self._tokens = self._load_tokens_from_disk()
        if self._have_valid_access_token(): return self._tokens["access_token"]
        if self._tokens and self._tokens.get("refresh_token"):
            self._tokens = self._refresh_access_token(self._tokens["refresh_token"]); self._save_tokens_to_disk(self._tokens); return self._tokens["access_token"]
        if not auth_code: raise RuntimeError("No valid tokens found and no STRAVA_AUTH_CODE provided.")
        self._tokens = self._exchange_code_for_tokens(auth_code); self._save_tokens_to_disk(self._tokens); return self._tokens["access_token"]
    def _auth_headers(self) -> Dict[str,str]:
        if not (self._tokens and self._tokens.get("access_token")): raise RuntimeError("Access token not available.")
        return {"Authorization": f"Bearer {self._tokens['access_token']}"}
    def get_activities(self, after: int, before: Optional[int]=None, per_page: int=200, max_pages: int=10, only_runs: bool=True) -> List[Dict]:
        url = f"{self.base_url}{ACTIVITIES_URL}"; page=1; all_items=[]
        while page <= max_pages:
            params={"after": after, "per_page": per_page, "page": page}; 
            if before is not None: params["before"]=before
            r = requests.get(url, headers=self._auth_headers(), params=params, timeout=30, verify=self._verify)
            if r.status_code==429: raise RuntimeError(f"Rate limited. Headers: {r.headers}")
            if r.status_code!=200: raise RuntimeError(f"Activities request failed: {r.status_code} {r.text}")
            items=r.json(); 
            if not items: break
            if only_runs: items=[it for it in items if it.get("type")=="Run"]
            all_items.extend(items)
            if len(items) < per_page: break
            page+=1
        return all_items
