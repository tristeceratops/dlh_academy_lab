
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from endpoints.load_nginx_headers import load_nginx_headers
from endpoints.xml_cgi import read_date_time, getauth

ROOT = Path(__file__).resolve().parent.parent
WWW = ROOT / "www"


class RequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WWW), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query, keep_blank_values=True)

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
                self.send_response(303)
                self.send_header("Location", "/dashboard.html")
                self.end_headers()
            else:
                self.send_response(303)
                self.send_header("Location", "/?error=1")
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

