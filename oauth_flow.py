import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import webbrowser
import time
import socket

AUTH_URL = "https://www.strava.com/oauth/authorize"


def _find_free_port(preferred: int) -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", preferred))
            return preferred
    except OSError:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


class _CodeCatcher(BaseHTTPRequestHandler):
    code_value = None

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query or "")
        if parsed.path.endswith("/exchange_token") and "code" in qs:
            _CodeCatcher.code_value = qs.get("code", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h2>Authorization complete.</h2><p>You can close this tab.</p>"
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # silence default HTTP server logging
        return


def run_local_authorization_flow(
    client_id: str,
    scope: str = "read,activity:read_all",
    redirect_host: str = "127.0.0.1",
    redirect_port: int = 8723,
    open_browser: bool = True,
    timeout_sec: int = 300,
) -> str:
    """
    Runs a local HTTP server and opens the user's browser to Strava's OAuth page.
    Returns the authorization code captured by the redirect.
    Raises TimeoutError if not completed in time.
    """
    port = _find_free_port(redirect_port)
    redirect_uri = f"http://{redirect_host}:{port}/exchange_token"

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "approval_prompt": "auto",
        "scope": scope,
    }
    url = f"{AUTH_URL}?{urlencode(params)}"
    print(f"If your browser didn't open automatically, open this URL:\n{url}")

    httpd = HTTPServer((redirect_host, port), _CodeCatcher)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    if open_browser:
        try:
            webbrowser.open(url, new=1)
        except Exception:
            pass

    start = time.time()
    while time.time() - start < timeout_sec:
        if _CodeCatcher.code_value is not None:
            httpd.shutdown()
            return _CodeCatcher.code_value
        time.sleep(0.2)

    httpd.shutdown()
    raise TimeoutError("Timed out waiting for authorization code.")