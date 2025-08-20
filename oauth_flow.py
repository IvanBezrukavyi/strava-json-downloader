
import os, threading, time, socket, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode

def _auth_url() -> str:
    base = os.getenv("STRAVA_AUTH_URL") or os.getenv("STRAVA_BASE_URL","https://www.strava.com")
    return base.rstrip("/") + "/oauth/authorize"

def _find_free_port(preferred: int) -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", preferred)); return preferred
    except OSError:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0)); return s.getsockname()[1]

class _CodeCatcher(BaseHTTPRequestHandler):
    code_value = None
    def do_GET(self):
        parsed = urlparse(self.path); qs = parse_qs(parsed.query or "")
        if parsed.path.endswith("/exchange_token") and "code" in qs:
            _CodeCatcher.code_value = qs.get("code", [""])[0]
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(b"<h2>Authorization complete.</h2><p>You can close this tab.</p>")
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *args, **kwargs): return

def run_local_authorization_flow(client_id: str, scope: str="read,activity:read_all", redirect_host: str="127.0.0.1", redirect_port: int=8723, open_browser: bool=True, timeout_sec: int=300) -> str:
    port = _find_free_port(redirect_port)
    redirect_uri = f"http://{redirect_host}:{port}/exchange_token"
    url = _auth_url() + "?" + urlencode({"client_id": client_id, "response_type":"code", "redirect_uri": redirect_uri, "approval_prompt":"auto", "scope": scope})
    print(f"If your browser didn't open automatically, open this URL:\n{url}")
    httpd = HTTPServer((redirect_host, port), _CodeCatcher); t = threading.Thread(target=httpd.serve_forever, daemon=True); t.start()
    if open_browser:
        try: webbrowser.open(url, new=1)
        except Exception: pass
    start = time.time()
    while time.time() - start < timeout_sec:
        if _CodeCatcher.code_value is not None:
            httpd.shutdown(); return _CodeCatcher.code_value
        time.sleep(0.2)
    httpd.shutdown(); raise TimeoutError("Timed out waiting for authorization code.")
