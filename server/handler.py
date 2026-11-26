from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from http.cookies import SimpleCookie
import secrets

from endpoints.load_nginx_headers import load_nginx_headers
from endpoints.xml_cgi import read_date_time, getauth

ROOT = Path(__file__).resolve().parent.parent
WWW = ROOT / "www"

# In-memory session storage
sessions = {}


class RequestHandler(SimpleHTTPRequestHandler):

    protected_pages = [
        "/dashboard.html",
        "/settings.html"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WWW), **kwargs)

    def get_session(self):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        session = cookie.get("session_id")

        if session:
            return sessions.get(session.value)

        return None

    def is_authenticated(self):
        return self.get_session() is not None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query, keep_blank_values=True)

        # Protect dashboard and settings
        if parsed.path in self.protected_pages:
            if not self.is_authenticated():
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
                return

        if parsed.path == "/load_nginx_headers":
            self.respond(load_nginx_headers())

        elif parsed.path == "/xml.cgi":

            if "read_date_time" in params:
                self.respond(read_date_time())

            elif "getauth" in params:
                username = params.get("username", [""])[0]
                password = params.get("password", [""])[0]
                self.respond(getauth(username, password))

            else:
                self.respond("Unknown CGI command")

        else:
            super().do_GET()

    def do_POST(self):

        if self.path == "/login":

            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length).decode("utf-8")
            params = parse_qs(data)

            username = params.get("username", [""])[0]
            password = params.get("password", [""])[0]

            result = getauth(username, password)

            if result == "Connection granted":

                # Generate session token
                token = secrets.token_urlsafe(32)

                # Save session
                sessions[token] = username

                self.send_response(303)
                self.send_header("Location", "/dashboard.html")
                self.send_header(
                    "Set-Cookie",
                    f"session_id={token}; HttpOnly; SameSite=Strict; Path=/"
                )
                self.end_headers()

            else:
                self.send_response(303)
                self.send_header("Location", "/?error=1")
                self.end_headers()

        elif self.path == "/logout":

            cookie = SimpleCookie(self.headers.get("Cookie", ""))
            session = cookie.get("session_id")

            if session:
                sessions.pop(session.value, None)

            self.send_response(303)
            self.send_header("Location", "/")
            self.send_header(
                "Set-Cookie",
                "session_id=; HttpOnly; Max-Age=0; Path=/"
            )
            self.end_headers()

        else:
            self.send_error(404)

    def respond(self, content):
        body = content.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
